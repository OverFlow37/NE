"""
계획 생성 모듈

반성 데이터와 이전 계획을 기반으로 새로운 계획을 생성합니다.
Ollama API(gemma3)를 사용하여 계획을 생성하고, 계획 파일에 저장합니다.
"""

import os
import json
import logging
import re
from typing import Dict, List, Any
from ..ollama_client import OllamaClient
import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PlanGenerator")

class PlanGenerator:
    def __init__(self, plan_file_path: str, reflection_file_path: str, ollama_client: OllamaClient):
        """
        계획 생성기 초기화
        
        Args:
            plan_file_path: 계획 데이터 파일 경로
            reflection_file_path: 반성 데이터 파일 경로
            ollama_client: Ollama API 클라이언트 인스턴스
        """
        # 현재 파일의 절대 경로를 기준으로 상대 경로 계산
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))  # AI 디렉토리
        
        # 파일 경로 설정
        self.plan_file_path = os.path.join(root_dir, "agent", "data", "plans.json")
        self.reflection_file_path = os.path.join(root_dir, "agent", "data", "reflections.json")
        self.ollama_client = ollama_client
        
        # 프롬프트 파일 경로 설정
        self.prompt_dir = os.path.join(root_dir, "agent", "prompts", "plan")
        self.prompt_path = os.path.join(self.prompt_dir, "plan_prompt.txt")
        self.system_path = os.path.join(self.prompt_dir, "plan_system.txt")
        
        # 폴더 생성
        os.makedirs(os.path.dirname(self.plan_file_path), exist_ok=True)
        
        logger.info(f"계획 생성기 초기화 (계획 파일: {self.plan_file_path}, 반성 파일: {self.reflection_file_path})")
    
    def load_plans(self) -> Dict:
        """계획 JSON 파일 로드"""
        try:
            with open(self.plan_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"계획 파일 로드 완료: {self.plan_file_path}")
            return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"계획 파일 로드 오류 (새 파일 생성 예정): {e}")
            return {}
    
    def load_reflections(self) -> Dict:
        """반성 JSON 파일 로드"""
        try:
            with open(self.reflection_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"반성 파일 로드 완료: {self.reflection_file_path}")
            return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"반성 파일 로드 오류: {e}")
            return {}
    
    def save_plans(self, agent_name: str, date: str, plans: Dict) -> bool:
        """계획을 파일에 저장"""
        try:
            # 기존 계획 파일 로드
            plan_data = self.load_plans()
            
            # 에이전트가 없으면 생성
            if agent_name not in plan_data:
                plan_data[agent_name] = {"plans": {}}
            
            # plans 필드가 없으면 생성
            if "plans" not in plan_data[agent_name]:
                plan_data[agent_name]["plans"] = {}
            
            # 계획 추가
            plan_data[agent_name]["plans"][date] = plans
            logger.info(f"{agent_name}의 {date} 계획이 추가되었습니다.")
            
            # 파일 저장
            with open(self.plan_file_path, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"계획 파일 저장 완료: {self.plan_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"계획 저장 오류: {e}")
            return False
    
    def _load_prompt_template(self) -> str:
        """프롬프트 템플릿 로드"""
        try:
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"프롬프트 템플릿 로드 실패: {e}")
            return ""
    
    def _load_system_prompt(self) -> str:
        """시스템 프롬프트 로드"""
        try:
            with open(self.system_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"시스템 프롬프트 로드 실패: {e}")
            return "You are a helpful AI assistant that creates daily plans in JSON format."
    
    def _create_plan_prompt(self, agent_name: str, date: str, reflections: List[Dict], previous_plans: Dict) -> str:
        """계획 생성 프롬프트 생성"""
        template = self._load_prompt_template()
        
        # 반성 데이터 포맷팅
        reflections_text = ""
        for r in reflections:
            reflections_text += f"- event: {r.get('event', '')}, thought: {r.get('thought', '')}\n"
        
        # 이전 계획 포맷팅
        previous_plans_text = ""
        if isinstance(previous_plans, dict):
            previous_plans_text = json.dumps(previous_plans, ensure_ascii=False)
        
        # 프롬프트 생성
        prompt = template.format(
            AGENT_NAME=agent_name,
            DATE=date,
            REFLECTIONS=reflections_text,
            PREVIOUS_PLANS=previous_plans_text
        )
        
        # JSON 형식의 변수 치환
        prompt = prompt.replace("AGENT_NAME_PLACEHOLDER", agent_name)
        prompt = prompt.replace("DATE_PLACEHOLDER", date)
        
        return prompt
    
    async def generate_plans(self, agent_name: str, time: str) -> Dict:
        """
        계획 생성 (1단계)
        Parameters:
        - agent_name: 에이전트 이름
        - time: 서버에서 받은 시간 (YYYY.MM.DD.HH:MM 형식)
        Returns:
        - 생성된 계획 JSON
        """
        try:
            if not time:
                logger.error("시간 정보가 제공되지 않았습니다.")
                return {}
                
            # 서버에서 받은 시간 사용
            current_time = time
            logger.info(f"계획 생성 시간: {current_time}")
            
            # 다음 날짜 계산
            date_parts = current_time.split(".")[:3]  # YYYY.MM.DD 부분만 추출
            current_date = datetime.datetime.strptime(".".join(date_parts), "%Y.%m.%d")
            next_date = (current_date + datetime.timedelta(days=1)).strftime("%Y.%m.%d")
            logger.info(f"다음 날짜: {next_date}")
            
            # 반성 데이터 로드
            reflection_data = self.load_reflections()
            if not reflection_data or agent_name not in reflection_data:
                logger.warning(f"{agent_name}의 반성 데이터가 없습니다.")
                return {}
            
            # 오늘의 반성 필터링 (time 필드 사용)
            today_reflections = []
            for reflection in reflection_data[agent_name].get("reflections", []):
                reflection_time = reflection.get("time", "")
                importance = reflection.get("importance", 0)
                if reflection_time == current_time or importance >= 7:  # 정확한 시간 비교 또는 중요도 7 이상
                    today_reflections.append(reflection)
            
            # 중요도 순으로 정렬
            today_reflections.sort(key=lambda x: x.get("importance", 0), reverse=True)
            
            # 이전 계획 로드
            plan_data = self.load_plans()
            previous_plans = {}
            if agent_name in plan_data and "plans" in plan_data[agent_name]:
                # 가장 최근 계획 찾기
                dates = sorted(plan_data[agent_name]["plans"].keys())
                if dates:
                    previous_plans = plan_data[agent_name]["plans"][dates[-1]]
            
            # 프롬프트 생성
            prompt = self._create_plan_prompt(agent_name, next_date, today_reflections, previous_plans)
            logger.info(f"생성된 프롬프트:\n{prompt}")
            
            # 시스템 프롬프트 로드
            system_prompt = self._load_system_prompt()
            
            # Ollama API 호출
            response = await self.ollama_client.process_prompt(
                prompt=prompt,
                system_prompt=system_prompt,
                model_name="gemma3"
            )
            
            if response.get("status") != "success":
                logger.error(f"계획 생성 API 호출 실패: {response.get('status')}")
                return {}
            
            # API 응답 로깅
            logger.info(f"API 응답: {response.get('response')}")
            
            # JSON 파싱
            try:
                # 응답에서 JSON 추출
                response_text = response["response"]
                # JSON 코드 블록 탐색
                json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
                matches = re.findall(json_pattern, response_text)
                
                if matches:
                    # 첫 번째 JSON 블록 사용
                    json_str = matches[0].strip()
                    plans = json.loads(json_str)
                else:
                    # 블록 없이 직접 JSON 형식이 있는지 확인
                    json_pattern = r'({[\s\S]*})'
                    matches = re.findall(json_pattern, response_text)
                    
                    if matches:
                        # 가장 긴 JSON 문자열 찾기
                        json_str = max(matches, key=len)
                        plans = json.loads(json_str)
                    else:
                        logger.error("응답에서 JSON을 찾을 수 없습니다.")
                        return {}
                
                logger.info(f"생성된 계획: {plans}")
                
                # 계획 저장 (다음 날짜로 저장)
                if self.save_plans(agent_name, next_date, plans):
                    return plans
                return {}
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {e}")
                return {}
            
        except Exception as e:
            logger.error(f"계획 생성 중 오류 발생: {str(e)}")
            return {}
        
########################################################
######### 유니티로 반환할 계획(타임슬롯)생성 ##############
########################################################
    async def generate_unity_plan(self, plan_json: Dict) -> Dict:
        """
        Unity용 계획 객체 생성 (2단계)
        Parameters:
        - plan_json: 1단계에서 생성된 계획 JSON
        Returns:
        - Unity용 계획 객체
        """
        try:
            if not plan_json:
                logger.error("계획 JSON이 제공되지 않았습니다.")
                return {}

            # Timeslot 객체 생성 
            prompt = f"""
            The following is the agent's daily plan:
            {json.dumps(plan_json, ensure_ascii=False, indent=2)}

            Based on this plan, generate a valid `time_slots` array that assigns appropriate time blocks to each activity.

            **🕓 PLANNING RULES:**

            * `eat` schedule:

                * Breakfast: around **08:00**
                * Lunch: around **12:00**
                * Dinner: around **18:00**
                * *Avoid scheduling `eat` outside these periods unless strongly justified by reflections or special context.*

            * Each `eat` action must last exactly **1 hour**.

            * Each `use` action must last **at least 2 hours**.

            * ⛔️ No activities may be scheduled between **00:00 and 06:00** — this time is reserved for sleep.

            * All time slots must be **sequential and continuous** from **06:00 to 24:00**:
                * The start time of each slot must match the end time of the previous one.
                * There must be **no gaps** or overlapping intervals.

            * ✅ Example:
                `["use", "shoreline", "crab", "06:00", "08:00", 6]`  
                followed by  
                `["eat", "cafe", "pastry_display", "08:00", "09:00", 5]`

            * ❌ Invalid: gaps (e.g., 11:00–12:00) or overlapping time slots.

            * The **final activity must end at or after 23:00** to ensure the full day is meaningfully utilized.  
            Do not end the schedule early unless strictly required by constraints.


            ---

            ** Importance Scoring Criteria:**

                * **1–3**: Minor everyday actions
                * **4–6**: Moderate insights from regular experiences
                * **7–8**: Significant personal realizations or reflections
                * **9–10**: Major life-changing actions or decisions

                * Importance scores should be **realistically distributed** across the full range (1–10), based on the depth of insight or impact of the activity.
                - Avoid assigning all activities high importance (7+), unless strongly supported by reflections.
                - At least a few actions should fall into the **1–5** range to reflect routine or minor tasks.

            ---

            **IMPORTANT RULES**

            * All `time_slots` must be **sequential and continuous** from **06:00 to 24:00**.

            **📤 OUTPUT FORMAT (strictly JSON):**
            {{ 
                "time_slots": [
                    ["action", "location", "target", "start time", "end time", "importance"],
                    ...
                ]
            }}

            """

            # 시스템 프롬프트
            system_prompt = "You are a helpful AI assistant that converts daily plans into Unity-compatible format."

            # Ollama API 호출
            response = await self.ollama_client.process_prompt(
                prompt=prompt,
                system_prompt=system_prompt,
                model_name="gemma3"
            )

            if response.get("status") != "success":
                logger.error(f"Unity 계획 생성 API 호출 실패: {response.get('status')}")
                return {}

            # API 응답 로깅
            logger.info(f"Unity API 응답: {response.get('response')}")

            # JSON 파싱
            try:
                response_text = response["response"]
                json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
                matches = re.findall(json_pattern, response_text)

                if matches:
                    json_str = matches[0].strip()
                    unity_plan = json.loads(json_str)
                else:
                    json_pattern = r'({[\s\S]*})'
                    matches = re.findall(json_pattern, response_text)
                    
                    if matches:
                        json_str = max(matches, key=len)
                        unity_plan = json.loads(json_str)
                    else:
                        logger.error("응답에서 JSON을 찾을 수 없습니다.")
                        return {}

                logger.info(f"생성된 Unity 계획: {unity_plan}")
                return unity_plan

            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {e}")
                return {}

        except Exception as e:
            logger.error(f"Unity 계획 생성 중 오류 발생: {str(e)}")
            return {} 