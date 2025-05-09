"""
반성 생성 모듈

메모리 데이터와 이전 반성을 기반으로 새로운 반성을 생성합니다.
Ollama API(gemma3)를 사용하여 반성을 생성하고, 반성 파일에 저장합니다.
"""

import os
import json
import re
import datetime
import logging
import requests
from typing import Dict, List, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ReflectionGenerator")

class ReflectionGenerator:
    def __init__(self, reflection_file_path: str):
        """
        반성 생성기 초기화
        
        Parameters:
        - reflection_file_path: 반성 JSON 파일 경로
        """
        self.reflection_file_path = reflection_file_path
        
        # Ollama API 설정
        self.OLLAMA_URL = "http://localhost:11434/api/generate"
        self.MODEL = "gemma3"
        self.DEFAULT_TIMEOUT = 60  # 기본 타임아웃 60초
        
        # 이전 반성 반영을 위한 설정
        self.MAX_PREV_REFLECTIONS = 5  # 최대 이전 반성 수
        self.RECENCY_WEIGHT = 0.7  # 최근성 가중치
        self.IMPORTANCE_WEIGHT = 0.3  # 중요도 가중치
        
        # 폴더 생성
        os.makedirs(os.path.dirname(reflection_file_path), exist_ok=True)
        
        logger.info(f"반성 생성기 초기화 (파일: {reflection_file_path})")
    
    def load_reflections(self) -> Dict:
        """
        반성 JSON 파일 로드
        
        Returns:
        - 로드된 반성 데이터
        """
        try:
            with open(self.reflection_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"반성 파일 로드 완료: {self.reflection_file_path}")
            return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"반성 파일 로드 오류 (새 파일 생성 예정): {e}")
            return {}
    
    def save_reflections(self, agent_name: str, reflections: List[Dict]) -> bool:
        """
        반성을 파일에 저장
        
        Parameters:
        - agent_name: 에이전트 이름
        - reflections: 반성 목록
        
        Returns:
        - 저장 성공 여부
        """
        try:
            # 기존 반성 파일 로드
            reflection_data = self.load_reflections()
            
            # 에이전트가 없으면 생성
            if agent_name not in reflection_data:
                reflection_data[agent_name] = {"reflections": []}
            
            # 반성 추가
            for reflection in reflections:
                reflection_data[agent_name]["reflections"].append(reflection)
                logger.info(f"{agent_name}의 반성 '{reflection.get('event', '')}' 가 추가되었습니다.")
            
            # 파일 저장
            with open(self.reflection_file_path, 'w', encoding='utf-8') as f:
                json.dump(reflection_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"반성 파일 저장 완료: {self.reflection_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"반성 저장 오류: {e}")
            return False
    
    def get_previous_reflections(self, agent_name: str) -> List[Dict]:
        """
        관련성 높은 이전 반성 가져오기
        
        Parameters:
        - agent_name: 에이전트 이름
        
        Returns:
        - 관련성 높은 이전 반성 목록
        """
        # 현재 날짜
        current_date = datetime.datetime.now().strftime("%Y.%m.%d")
        
        # 반성 데이터 로드
        reflection_data = self.load_reflections()
        
        if not reflection_data or agent_name not in reflection_data or "reflections" not in reflection_data[agent_name]:
            return []
        
        try:
            # 현재 날짜를 datetime 객체로 변환
            current_date_obj = datetime.datetime.strptime(current_date, "%Y.%m.%d")
            
            # 이전 반성 목록
            previous_reflections = []
            
            for reflection in reflection_data[agent_name]["reflections"]:
                created_time = reflection.get("created", "")
                
                # created 필드에서 날짜 추출
                date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', created_time)
                if date_match:
                    reflection_date_str = date_match.group(1)
                    try:
                        # 반성 날짜를 datetime 객체로 변환
                        reflection_date_obj = datetime.datetime.strptime(reflection_date_str, "%Y.%m.%d")
                        
                        # 현재 날짜보다 이전 날짜인 경우만 처리
                        if reflection_date_obj < current_date_obj:
                            # 날짜 차이 계산 (일 단위)
                            days_diff = (current_date_obj - reflection_date_obj).days
                            
                            # 최근성 점수 계산 (0에 가까울수록 최근)
                            recency_score = 1.0 / (1.0 + days_diff)
                            
                            # 중요도 점수 계산 (0-10 범위를 0-1 범위로 정규화)
                            importance_score = reflection.get("importance", 0) / 10.0
                            
                            # 최종 관련성 점수 계산 (가중치 적용)
                            relevance_score = (self.RECENCY_WEIGHT * recency_score) + (self.IMPORTANCE_WEIGHT * importance_score)
                            
                            # 반성에 관련성 점수 추가
                            reflection_with_score = reflection.copy()
                            reflection_with_score["relevance_score"] = relevance_score
                            reflection_with_score["days_ago"] = days_diff
                            
                            previous_reflections.append(reflection_with_score)
                    except:
                        continue
            
            # 관련성 점수 기준 내림차순 정렬
            sorted_reflections = sorted(
                previous_reflections, 
                key=lambda x: x.get("relevance_score", 0), 
                reverse=True
            )
            
            # 상위 N개 반환
            top_reflections = sorted_reflections[:self.MAX_PREV_REFLECTIONS]
            logger.info(f"{len(top_reflections)}개의 이전 반성을 참조합니다.")
            
            return top_reflections
            
        except Exception as e:
            logger.error(f"이전 반성 처리 중 오류 발생: {e}")
            return []
    
    def generate_reflections(self, agent_name: str, important_memories: List[Dict], 
                            previous_reflections: List[Dict] = None) -> List[Dict]:
        """
        반성 생성
        
        Parameters:
        - agent_name: 에이전트 이름
        - important_memories: 중요한 메모리 목록
        - previous_reflections: 이전 반성 목록 (None인 경우 자동으로 가져옴)
        
        Returns:
        - 생성된 반성 목록
        """
        # 이전 반성이 제공되지 않은 경우 자동으로 가져옴
        if previous_reflections is None:
            previous_reflections = self.get_previous_reflections(agent_name)
        
        # 반성할 메모리가 없으면 빈 리스트 반환
        if not important_memories:
            logger.warning("반성할 중요한 메모리가 없습니다.")
            return []
        
        # 1. 프롬프트 생성
        prompt = self._create_reflection_prompt(agent_name, important_memories, previous_reflections)
        
        # 2. Ollama API 호출
        logger.info(f"{len(important_memories)}개 메모리에 대한 반성 생성 중...")
        response = self._call_ollama(prompt)
        
        if response["status"] != "success":
            logger.error(f"반성 생성 API 호출 실패: {response['status']}")
            return []
        
        # 3. 응답에서 JSON 추출
        json_data = self._extract_json_from_response(response["response"])
        
        if "error" in json_data:
            logger.error(f"JSON 추출 실패: {json_data['error']}")
            return []
        
        # 4. 반성 생성
        reflections = []
        current_date = datetime.datetime.now().strftime("%Y.%m.%d")
        
        if "reflections" in json_data and isinstance(json_data["reflections"], list):
            # 각 반성 처리
            for i, reflection_data in enumerate(json_data["reflections"]):
                if i < len(important_memories):
                    # 메모리에서 날짜 추출
                    memory_time = important_memories[i].get("time", "")
                    memory_date = self._extract_date_from_time(memory_time)
                    
                    if not memory_date:
                        memory_date = current_date
                    
                    # 생성 시간 설정 (메모리 날짜의 22:00)
                    created_time = self._create_date_with_evening_time(memory_date)
                    
                    # 빈 임베딩 추가
                    reflection = {
                        "created": created_time,
                        "event": important_memories[i].get("event", ""),
                        "thought": reflection_data.get("thought", ""),
                        "importance": reflection_data.get("importance", important_memories[i].get("importance", 0)),
                        "embeddings": []
                    }
                    
                    # 반성 목록에 추가
                    reflections.append(reflection)
        
        logger.info(f"{len(reflections)}개의 반성이 생성되었습니다.")
        return reflections
    
    def _extract_date_from_time(self, time_str: str) -> str:
        """
        시간 문자열에서 날짜 부분 추출
        
        Parameters:
        - time_str: 시간 문자열 (YYYY.MM.DD.HH:MM 형식)
        
        Returns:
        - 날짜 문자열 (YYYY.MM.DD 형식)
        """
        match = re.match(r'(\d{4}\.\d{2}\.\d{2})', time_str)
        if match:
            return match.group(1)
        return ""
    
    def _create_date_with_evening_time(self, date_str: str) -> str:
        """
        날짜 문자열에 저녁 시간(22:00)을 추가
        
        Parameters:
        - date_str: 날짜 문자열 (YYYY.MM.DD 형식)
        
        Returns:
        - 시간이 추가된 날짜 문자열 (YYYY.MM.DD.22:00 형식)
        """
        return f"{date_str}.22:00"
    
    def _create_reflection_prompt(self, agent_name: str, memories: List[Dict], 
                                 previous_reflections: List[Dict] = None) -> str:
        """
        반성 생성 프롬프트 작성
        
        Parameters:
        - agent_name: 에이전트 이름
        - memories: 중요한 메모리 목록
        - previous_reflections: 이전 반성 목록
        
        Returns:
        - 프롬프트 텍스트
        """
        current_date = datetime.datetime.now().strftime("%Y.%m.%d")
        
        # 각 메모리에 대한 섹션 생성
        memory_sections = []
        for i, memory in enumerate(memories):
            event = memory.get("event", "")
            time_str = memory.get("time", "")
            importance = memory.get("importance", 0)
            
            memory_section = f"""
MEMORY #{i+1}:
Event: "{event}"
Time: {time_str}
Importance: {importance}
"""
            memory_sections.append(memory_section)
        
        memories_text = "\n".join(memory_sections)
        
        # 이전 반성 섹션 추가 (있는 경우)
        previous_reflections_text = ""
        if previous_reflections and len(previous_reflections) > 0:
            previous_reflections_sections = []
            
            for i, reflection in enumerate(previous_reflections):
                event = reflection.get("event", "")
                thought = reflection.get("thought", "")
                importance = reflection.get("importance", 0)
                days_ago = reflection.get("days_ago", 0)
                
                section = f"""
PREVIOUS REFLECTION #{i+1} (from {days_ago} days ago):
Event: "{event}"
Thought: "{thought}"
Importance: {importance}
"""
                previous_reflections_sections.append(section)
            
            previous_reflections_text = "\n".join(previous_reflections_sections)
            previous_reflections_text = f"""
RECENT REFLECTIONS (Consider these for context when generating today's reflections):
{previous_reflections_text}
"""
        
        # 기본 프롬프트 생성
        prompt = f"""
TASK:
Create {len(memories)} separate, independent reflections for agent {agent_name} based on the provided memories.

AGENT: {agent_name}
DATE: {current_date}

{memories_text}
"""

        # 이전 반성이 있으면 추가
        if previous_reflections_text:
            prompt += previous_reflections_text
        
        # 지시사항 및 출력 형식 추가
        reflection_format = ""
        for i, memory in enumerate(memories):
            reflection_format += f"""    {{
      "memory_index": {i+1},
      "event": "{memory.get('event', '')}",
      "thought": "extremely_simple_reflection_in_2_or_3_basic_sentences",
      "importance": importance_rating_{i+1}
    }}{", " if i < len(memories)-1 else ""}
"""
        
        prompt += f"""
INSTRUCTIONS:
- Process each memory SEPARATELY and create an independent reflection for each
- Each reflection should be 2-3 VERY SIMPLE sentences
- If previous reflections are provided, use them for context and continuity
- Each reflection should PRIMARILY be based on its corresponding memory
- Use first-person perspective as if the agent is reflecting
- Keep each reflection concise but impactful
- Consider how current reflections might connect to previous ones
- Respect the character's past thoughts and growth

OUTPUT FORMAT (provide ONLY valid JSON):
{{
  "reflections": [
{reflection_format}
  ]
}}

IMPORTANCE RATING GUIDELINES:
1-3: Minor everyday reflections
4-6: Moderate insights about regular experiences
7-8: Significant personal insights
9-10: Major life-changing reflections

REFLECTION GUIDELINES:
- Each reflection must be based primarily on its corresponding memory
- Previous reflections provide context but shouldn't overshadow the current memory
- Each memory should have its own distinct reflection
- Keep reflection to MAXIMUM 3 sentences
- Focus only on the most meaningful insights or feelings
- Write in first-person perspective as if the agent is reflecting
- Be concise but impactful
- Make sure the reflection is complete and coherent despite its brevity
"""
        
        return prompt
    
    def _call_ollama(self, prompt: str, timeout: int = None) -> Dict[str, Any]:
        """
        Ollama API 호출
        
        Parameters:
        - prompt: 프롬프트 텍스트
        - timeout: 타임아웃 시간(초)
        
        Returns:
        - API 응답
        """
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT
            
        # API 요청 구성
        payload = {
            "model": self.MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "frequency_penalty": 0.3,
                "presence_penalty": 0.3
            }
        }
        
        try:
            # API 호출
            response = requests.post(self.OLLAMA_URL, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("response", ""),
                    "status": "success"
                }
            else:
                return {
                    "response": f"Error: HTTP status code {response.status_code}",
                    "status": "error"
                }
        except requests.exceptions.Timeout:
            return {
                "response": f"Error: Request timed out after {timeout} seconds",
                "status": "timeout"
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "status": "exception"
            }
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        LLM 응답에서 JSON 추출
        
        Parameters:
        - response_text: LLM 응답 텍스트
        
        Returns:
        - 추출된 JSON 객체
        """
        try:
            # JSON 코드 블록 탐색
            json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
            matches = re.findall(json_pattern, response_text)
            
            if matches:
                # 첫 번째 JSON 블록 사용
                json_str = matches[0].strip()
                return json.loads(json_str)
            
            # 블록 없이 직접 JSON 형식이 있는지 확인
            json_pattern = r'({[\s\S]*})'
            matches = re.findall(json_pattern, response_text)
            
            if matches:
                # 가장 긴 JSON 문자열 찾기
                json_str = max(matches, key=len)
                return json.loads(json_str)
            
            # JSON을 찾을 수 없음
            return {"error": "No valid JSON found in response"}
        
        except json.JSONDecodeError as e:
            # JSON 파싱 오류
            return {
                "error": f"JSON parsing error: {str(e)}",
                "original_response": response_text
            }
        except Exception as e:
            # 기타 오류
            return {
                "error": f"Error extracting JSON: {str(e)}",
                "original_response": response_text
            }

# 테스트 코드
if __name__ == "__main__":
    # 현재 디렉토리 기준 반성 파일 경로
    current_dir = os.path.dirname(os.path.abspath(__file__))
    reflection_file_path = os.path.join(current_dir, "./reflect/reflections.json")
    
    # 반성 생성기 초기화
    generator = ReflectionGenerator(reflection_file_path)
    
    # 테스트 메모리
    test_memories = [
        {
            "event": "observe stone Forest stream_bank",
            "time": "2025.05.08.08:10",
            "importance": 6
        },
        {
            "event": "eat raspberry Forest stream_bank",
            "time": "2025.05.08.11:00",
            "importance": 3
        }
    ]
    
    # 반성 생성
    print("반성 생성 테스트...")
    reflections = generator.generate_reflections("John", test_memories)
    
    # 결과 출력
    for i, reflection in enumerate(reflections):
        print(f"\n반성 #{i+1}:")
        print(f"  이벤트: {reflection.get('event', '')}")
        print(f"  생각: {reflection.get('thought', '')}")
        print(f"  중요도: {reflection.get('importance', 0)}")
        print(f"  생성 시간: {reflection.get('created', '')}")