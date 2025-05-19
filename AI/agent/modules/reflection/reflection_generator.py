"""
반성 생성 모듈 (새로운 메모리 구조 대응)

메모리 데이터와 이전 반성을 기반으로 새로운 반성을 생성합니다.
Ollama API(gemma3)를 사용하여 반성을 생성하고, 반성 파일에 저장합니다.
"""

import os
import json
import re
import datetime
import logging
import asyncio
from typing import Dict, List, Any, Tuple
from ..ollama_client import OllamaClient
import numpy as np

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ReflectionGenerator")

class ReflectionGenerator:
    def __init__(self, reflection_file_path: str, ollama_client: OllamaClient, embedding_model=None):
        """
        반성 생성기 초기화
        
        Args:
            reflection_file_path: 반성 데이터 파일 경로
            ollama_client: Ollama API 클라이언트 인스턴스
            embedding_model: 임베딩 모델 (word2vec 등)
        """
        self.reflection_file_path = reflection_file_path
        self.ollama_client = ollama_client
        self.embedding_model = embedding_model
        
        logger.info(f"ReflectionGenerator 초기화 완료")
        logger.info(f"임베딩 모델 상태: {'사용 가능' if self.embedding_model else '사용 불가'}")
        if self.embedding_model:
            logger.info(f"임베딩 모델 타입: {type(self.embedding_model)}")
            logger.info(f"임베딩 모델 메서드: {dir(self.embedding_model)}")
        
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
    
    def get_previous_reflections(self, agent_name: str, current_time: str = None) -> List[Dict]:
        """
        관련성 높은 이전 반성 가져오기
        
        Parameters:
        - agent_name: 에이전트 이름
        - current_time: 현재 시간 (YYYY.MM.DD.HH:MM 형식)
        
        Returns:
        - 관련성 높은 이전 반성 목록
        """
        if not current_time:
            logger.warning("현재 시간이 제공되지 않았습니다.")
            return []
            
        logger.info(f"현재 시간: {current_time}")
        
        # 반성 데이터 로드
        reflection_data = self.load_reflections()
        # logger.info(f"로드된 반성 데이터: {reflection_data}")
        
        if not reflection_data:
            logger.warning("반성 데이터가 없습니다.")
            return []
            
        if agent_name not in reflection_data:
            logger.warning(f"에이전트 '{agent_name}'의 반성 데이터가 없습니다.")
            return []
            
        if "reflections" not in reflection_data[agent_name]:
            logger.warning(f"에이전트 '{agent_name}'의 반성 목록이 없습니다.")
            return []
        
        try:
            # 현재 시간을 datetime 객체로 변환
            current_time_obj = datetime.datetime.strptime(current_time, "%Y.%m.%d.%H:%M")
            
            # 이전 반성 목록
            previous_reflections = []
            
            for reflection in reflection_data[agent_name]["reflections"]:
                reflection_time = reflection.get("time", "")
                logger.debug(f"반성 생성 시간: {reflection_time}")
                
                # time 필드에서 날짜 추출
                date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', reflection_time)
                if date_match:
                    reflection_date_str = date_match.group(1)
                    logger.debug(f"추출된 반성 날짜: {reflection_date_str}")
                    try:
                        # 반성 날짜를 datetime 객체로 변환
                        reflection_date_obj = datetime.datetime.strptime(reflection_date_str, "%Y.%m.%d")
                        
                        # 현재 날짜보다 이전 날짜인 경우만 처리
                        if reflection_date_obj < current_time_obj:
                            # 날짜 차이 계산 (일 단위)
                            days_diff = (current_time_obj - reflection_date_obj).days
                            logger.debug(f"날짜 차이: {days_diff}일")
                            
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
                            logger.debug(f"반성 추가됨 - 이벤트: {reflection.get('event', '')}, 관련성 점수: {relevance_score}")
                    except Exception as e:
                        logger.error(f"반성 날짜 처리 중 오류 발생: {str(e)}")
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
            logger.error(f"이전 반성 처리 중 오류 발생: {str(e)}")
            return []
    
    async def generate_reflections(self, agent_name: str, important_memories: Dict[str, Dict], 
                                 previous_reflections: List[Dict] = None, time: str = None) -> List[Dict]:
        """
        반성 생성
        Parameters:
        - agent_name: 에이전트 이름
        - important_memories: 중요한 메모리 목록 (ID를 키로 사용)
        - previous_reflections: 이전 반성 목록 (None인 경우 자동으로 가져옴)
        - time: 서버에서 받은 시간 (YYYY.MM.DD.HH:MM 형식)
        Returns:
        - 생성된 반성 목록
        """
        if not important_memories:
            logger.warning("반성할 중요한 메모리가 없습니다.")
            return []
            
        if not time:
            logger.error("시간 정보가 제공되지 않았습니다.")
            return []
            
        # 서버에서 받은 시간 사용
        current_time = time
        logger.info(f"반성 생성 시간: {current_time}")
        
        if previous_reflections is None:
            previous_reflections = self.get_previous_reflections(agent_name, current_time)
            logger.info(f"이전 반성 수: {len(previous_reflections)}")
        
        # 각 메모리의 통합 이벤트 필드 생성
        for memory_id, memory in important_memories.items():
            event_role = memory.get("event_role", "").strip()
            event = memory.get("event", "").strip()
            action = memory.get("action", "").strip()
            feedback = memory.get("feedback", "").strip()
            
            # 통합 이벤트 필드 생성
            combined_event = ""
            if event_role:
                combined_event += f"{event_role} "
            if event:
                combined_event += f"{event} "
            if action:
                combined_event += f"{action} "
            if feedback:
                combined_event += f"{feedback}"
            
            memory["combined_event"] = combined_event.strip()
            logger.debug(f"메모리 ID {memory_id}의 통합 이벤트 필드: '{memory['combined_event']}'")
        
        prompt = self._create_reflection_prompt(agent_name, important_memories, previous_reflections)
        
        try:
            response = await self.ollama_client.process_prompt(
                prompt=prompt,
                system_prompt="You are a helpful AI assistant that generates reflections based on memories.",
                model_name="gemma3",
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "frequency_penalty": 0.1,
                    "presence_penalty": 0.1
                }
            )
            
            if response.get("status") != "success":
                logger.error(f"반성 생성 API 호출 실패: {response.get('status')}")
                return []
                
            json_data = self._extract_json_from_response(response["response"])
            
            if "error" in json_data:
                logger.error(f"JSON 추출 실패: {json_data['error']}")
                return []
                
            reflections = []
            for reflection in json_data.get("reflections", []):
                reflection["time"] = current_time  # 수정된 시간 형식 사용
                
                # 메모리 ID 추가
                memory_id = reflection.get("memory_id", "")
                if memory_id and memory_id in important_memories:
                    # 해당 메모리 정보 가져오기
                    memory = important_memories[memory_id]
                    original_event = memory.get("event", "")
                    combined_event = memory.get("combined_event", "")
                    
                    # 반성에 원본 이벤트와 통합 이벤트 저장
                    reflection["event"] = combined_event
                    # reflection["original_event"] = original_event
                    
                    # 통찰(thought)에 대한 임베딩 생성
                    if self.embedding_model and "thought" in reflection:
                        try:
                            thought = reflection.get("thought", "")
                            if thought:
                                logger.info(f"통찰 '{thought}'에 대한 임베딩 생성 시작")
                                
                                # 토큰화 및 소문자 변환
                                tokens = [w.lower() for w in thought.split() if w.lower() in self.embedding_model]
                                if not tokens:
                                    embedding = [0.0] * self.embedding_model.vector_size
                                else:
                                    # 단어 벡터의 평균을 문장 벡터로 사용
                                    word_vectors = [self.embedding_model[w] for w in tokens]
                                    sentence_vector = np.mean(word_vectors, axis=0)
                                    # 정규화
                                    norm = np.linalg.norm(sentence_vector)
                                    if norm > 0:
                                        sentence_vector = sentence_vector / norm
                                    embedding = sentence_vector.tolist()
                                reflection["embedding"] = embedding
                                logger.info(f"통찰 '{thought}'에 대한 임베딩 생성 완료")
                            else:
                                logger.warning("통찰이 비어있어 임베딩을 생성할 수 없습니다.")
                        except Exception as e:
                            logger.error(f"임베딩 생성 중 오류 발생: {str(e)}")
                else:
                    logger.warning(f"메모리 ID {memory_id}에 해당하는 메모리를 찾을 수 없습니다.")
                
                reflections.append(reflection)
                
            logger.info(f"{len(reflections)}개의 반성이 생성되었습니다.")
            return reflections
            
        except Exception as e:
            logger.error(f"반성 생성 중 오류 발생: {str(e)}")
            return []
    
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
    
    def _create_reflection_prompt(self, agent_name: str, memories: Dict[str, Dict], 
                                 previous_reflections: List[Dict] = None) -> str:
        """
        반성 생성 프롬프트 작성
        
        Parameters:
        - agent_name: 에이전트 이름
        - memories: 중요한 메모리 목록 (ID를 키로 사용)
        - previous_reflections: 이전 반성 목록
        
        Returns:
        - 프롬프트 텍스트
        """
        current_date = datetime.datetime.now().strftime("%Y.%m.%d")
        
        # 각 메모리에 대한 섹션 생성
        memory_sections = []
        memory_ids = list(memories.keys())
        for i, memory_id in enumerate(memory_ids):
            memory = memories[memory_id]
            combined_event = memory.get("combined_event", "")
            time_str = memory.get("time", "")
            importance = memory.get("importance", 0)
            
            memory_section = f"""
MEMORY #{i+1} (ID: {memory_id}):
Event: "{combined_event}"
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
        for i, memory_id in enumerate(memory_ids):
            memory = memories[memory_id]
            combined_event = memory.get("combined_event", "")
            reflection_format += f"""    {{
      "memory_id": "{memory_id}",
      "event": "{combined_event}",
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
- Consider all aspects of the event in each memory

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
    
    # OllamaClient 초기화
    from ..ollama_client import OllamaClient
    ollama_client = OllamaClient()
    
    # 반성 생성기 초기화
    generator = ReflectionGenerator(reflection_file_path, ollama_client)
    
    # 테스트 메모리
    test_memories = {
        "1": {
            "event": "observe stone Forest stream_bank",
            "event_role": "observer",
            "action": "examine stone closely",
            "feedback": "noticed unusual markings",
            "time": "2025.05.08.08:10",
            "importance": 6
        },
        "2": {
            "event": "eat raspberry Forest stream_bank",
            "event_role": "actor",
            "action": "pick more raspberries",
            "feedback": "enjoyed the sweet taste",
            "time": "2025.05.08.11:00",
            "importance": 3
        }
    }
    
    # 반성 생성
    import asyncio
    
    async def test_reflection():
        print("반성 생성 테스트...")
        reflections = await generator.generate_reflections("Tom", test_memories, time="2025.05.08.22:00")
        
        # 결과 출력
        for i, reflection in enumerate(reflections):
            print(f"\n반성 #{i+1}:")
            print(f"  메모리 ID: {reflection.get('memory_id', '')}")
            print(f"  이벤트: {reflection.get('event', '')}")
            print(f"  원본 이벤트: {reflection.get('original_event', '')}")
            print(f"  생각: {reflection.get('thought', '')}")
            print(f"  중요도: {reflection.get('importance', 0)}")
            print(f"  생성 시간: {reflection.get('time', '')}")
    
    asyncio.run(test_reflection())