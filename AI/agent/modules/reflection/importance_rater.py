"""
메모리 중요도 평가 모듈 (배치 처리 방식)

메모리의 중요도를 평가하여 importance 필드를 추가합니다.
Ollama API(gemma3)를 사용하여 1-10 척도로 중요도를 평가합니다.
여러 메모리를 한 번에 처리하는 배치 방식 지원.
"""

import re
import json
import logging
import asyncio
from typing import Dict, List, Any
from ..ollama_client import OllamaClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ImportanceRater")

class ImportanceRater:
    def __init__(self, ollama_client: OllamaClient):
        """
        메모리 중요도 평가기 초기화 (배치 처리 방식)
        
        Args:
            ollama_client: Ollama API 클라이언트 인스턴스
        """
        self.ollama_client = ollama_client
        self.MAX_BATCH_SIZE = 20  # 한 번에 처리할 최대 메모리 개수
        logger.info(f"메모리 중요도 평가기 초기화 (배치 처리 방식, 최대 배치 크기: {self.MAX_BATCH_SIZE})")
    
    async def add_importance_to_memories(self, memories: Dict, agent_name: str, target_memories: List[Dict]) -> Dict:
        """
        메모리에 importance 필드 추가 (배치 처리 방식)
        
        Parameters:
        - memories: 전체 메모리 데이터
        - agent_name: 에이전트 이름
        - target_memories: importance를 추가할 대상 메모리 목록
        
        Returns:
        - 업데이트된 메모리 데이터
        """
        updated_memories = memories.copy()
        
        # 중요도가 필요한 메모리만 필터링
        memories_to_rate = []
        for target_memory in target_memories:
            if "importance" not in target_memory:
                memories_to_rate.append(target_memory)
            else:
                logger.info(f"메모리 '{target_memory.get('event', '')}'는 이미 중요도가 있습니다: {target_memory.get('importance', 0)}")
        
        if not memories_to_rate:
            logger.info("중요도를 평가할 메모리가 없습니다.")
            return updated_memories
        
        # 배치 단위로 처리
        total_memories = len(memories_to_rate)
        logger.info(f"총 {total_memories}개 메모리에 대한 배치 중요도 평가 시작")
        
        # 메모리 배치로 나누기
        batches = [memories_to_rate[i:i + self.MAX_BATCH_SIZE] 
                  for i in range(0, len(memories_to_rate), self.MAX_BATCH_SIZE)]
        
        logger.info(f"{len(batches)}개 배치로 처리 예정")
        
        # 각 배치 처리
        for batch_index, batch in enumerate(batches):
            logger.info(f"배치 {batch_index+1}/{len(batches)} 처리 중 ({len(batch)}개 메모리)")
            
            # 배치 평가 프롬프트 생성
            prompt = self._create_batch_importance_rating_prompt(batch)
            logger.debug(f"생성된 배치 프롬프트:\n{prompt}")
            
            try:
                logger.info(f"Ollama API 호출 시작 - 배치 {batch_index+1}")
                response = await self.ollama_client.process_prompt(
                    prompt=prompt,
                    system_prompt="You are a helpful AI assistant that rates memory importance as instructed. Always respond only with the requested JSON format.",
                    model_name="gemma3",
                    options={
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "frequency_penalty": 0.0,
                        "presence_penalty": 0.0
                    }
                )
                
                if response and response.get("status") == "success":
                    logger.info(f"배치 {batch_index+1} 응답 수신 성공")
                    
                    # JSON 응답에서 중요도 추출
                    importance_ratings = self._extract_batch_importance_ratings(
                        response["response"], 
                        batch
                    )
                    
                    if importance_ratings:
                        # 각 메모리에 중요도 적용
                        for i, memory_to_rate in enumerate(batch):
                            if i < len(importance_ratings):
                                memory_id = memory_to_rate.get("memory_id")
                                importance = importance_ratings[i]
                                
                                # 원본 메모리에 중요도 추가
                                if memory_id and memory_id in updated_memories[agent_name]["memories"]:
                                    updated_memories[agent_name]["memories"][memory_id]["importance"] = importance
                                    logger.info(f"메모리 ID {memory_id}에 중요도 {importance} 추가됨")
                    else:
                        logger.warning(f"배치 {batch_index+1}의 중요도 목록을 추출할 수 없습니다. 개별 평가로 전환합니다.")
                        await self._rate_memories_individually(updated_memories, agent_name, batch)
                else:
                    logger.warning(f"배치 {batch_index+1} 평가 실패 - 응답 상태: {response.get('status') if response else 'None'}")
                    # 실패 시 개별 평가로 폴백
                    logger.info(f"배치 {batch_index+1}을 개별 평가로 폴백합니다.")
                    await self._rate_memories_individually(updated_memories, agent_name, batch)
                    
            except Exception as e:
                logger.error(f"배치 {batch_index+1} 평가 중 오류 발생: {str(e)}")
                logger.error(f"오류 상세 정보: {type(e).__name__}")
                import traceback
                logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
                # 오류 발생 시 개별 평가로 폴백
                logger.info(f"배치 {batch_index+1}을 개별 평가로 폴백합니다.")
                await self._rate_memories_individually(updated_memories, agent_name, batch)
        
        return updated_memories
    
    async def _rate_memories_individually(self, memories: Dict, agent_name: str, target_memories: List[Dict]) -> None:
        """
        각 메모리를 개별적으로 평가 (배치 처리 실패 시 폴백)
        
        Parameters:
        - memories: 전체 메모리 데이터
        - agent_name: 에이전트 이름
        - target_memories: importance를 추가할 대상 메모리 목록
        """
        logger.info(f"{len(target_memories)}개 메모리에 대한 개별 평가로 전환")
        
        for target_memory in target_memories:
            # 메모리 ID 가져오기
            memory_id = target_memory.get("memory_id")
            
            if not memory_id:
                logger.warning("메모리 ID가 없어 평가를 건너뜁니다.")
                continue
            
            logger.info(f"메모리 ID {memory_id}의 중요도 개별 평가 중...")
            
            # 중요도 평가 프롬프트 생성
            prompt = self._create_single_importance_rating_prompt(target_memory)
            
            try:
                response = await self.ollama_client.process_prompt(
                    prompt=prompt,
                    system_prompt="You are a helpful AI assistant that rates memory importance.",
                    model_name="gemma3",
                    options={
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "frequency_penalty": 0.0,
                        "presence_penalty": 0.0
                    }
                )
                
                if response and response.get("status") == "success":
                    # 중요도 추출
                    importance = self._extract_importance_rating(response["response"])
                    
                    # 원본 메모리에 중요도 추가
                    if memory_id in memories[agent_name]["memories"]:
                        memories[agent_name]["memories"][memory_id]["importance"] = importance
                        logger.info(f"메모리 ID {memory_id}에 중요도 {importance} 추가됨")
                else:
                    logger.warning(f"메모리 ID {memory_id}의 중요도 개별 평가 실패 - 기본값 적용")
                    # 기본 중요도 설정
                    if memory_id in memories[agent_name]["memories"]:
                        memories[agent_name]["memories"][memory_id]["importance"] = 5
                        logger.info(f"메모리 ID {memory_id}에 기본 중요도 5 추가됨")
            except Exception as e:
                logger.error(f"메모리 ID {memory_id}의 중요도 개별 평가 중 오류 발생: {str(e)}")
                # 기본 중요도 설정
                if memory_id in memories[agent_name]["memories"]:
                    memories[agent_name]["memories"][memory_id]["importance"] = 5
                    logger.info(f"메모리 ID {memory_id}에 기본 중요도 5 추가됨")
                        
            # 연속 API 호출 사이에 짧은 지연 추가
            await asyncio.sleep(0.2)
    
    def _create_batch_importance_rating_prompt(self, memories: List[Dict]) -> str:
        """
        여러 메모리의 중요도를 일괄 평가하기 위한 프롬프트 생성
        
        Parameters:
        - memories: 평가할 메모리 목록
        
        Returns:
        - 프롬프트 텍스트
        """
        # 메모리 목록 생성
        memory_list = ""
        for i, memory in enumerate(memories):
            event = memory.get("event", "")
            action = memory.get("action", "")
            feedback = memory.get("feedback", "")
            time_str = memory.get("time", "")
            
            # 메모리 내용 구성
            memory_content = []
            if event:
                memory_content.append(f"Event: {event}")
            if action:
                memory_content.append(f"Action: {action}")
            if feedback:
                memory_content.append(f"Feedback: {feedback}")
            
            memory_str = "\n".join(memory_content)
            memory_list += f"MEMORY #{i+1}:\n{memory_str}\nat time {time_str}\n\n"
        
        # JSON 출력 형식 구성
        json_format = "{\n  \"ratings\": [\n"
        for i, memory in enumerate(memories):
            json_format += f"    {{\n      \"memory_index\": {i+1},\n      \"importance\": importance_rating_{i+1}\n    }}"
            if i < len(memories) - 1:
                json_format += ",\n"
            else:
                json_format += "\n"
        json_format += "  ]\n}"
        
        prompt = f"""
TASK:
Rate the importance/poignancy of each of the following memory events on a scale of 1 to 10.

MEMORIES TO RATE:
{memory_list}

MEMORY RATING RULES:
On a scale of 1 to 10, where:
  1 = purely mundane (e.g., brushing teeth, making bed)
  3 = minor daily event (e.g., short conversation, shopping)
  5 = moderately significant (e.g., playing games with friends)
  7 = important event (e.g., having dinner with friends)
  10 = extremely poignant (e.g., a breakup, college acceptance)

For each memory, consider:
- All aspects of the memory (event, action, and feedback)
- The significance of the activity to daily life
- The emotional impact of this type of event
- The potential long-term impact of this type of event

RESPONSE FORMAT:
Provide a JSON object with ratings for each memory. Each rating should be an integer from 1 to 10.

{json_format}

IMPORTANT: Only provide the JSON object with no additional text.
"""
        return prompt
    
    def _create_single_importance_rating_prompt(self, memory: Dict) -> str:
        """
        단일 메모리의 중요도를 평가하기 위한 프롬프트 생성
        
        Parameters:
        - memory: 평가할 메모리 데이터
        
        Returns:
        - 프롬프트 텍스트
        """
        event = memory.get("event", "")
        action = memory.get("action", "")
        feedback = memory.get("feedback", "")
        time_str = memory.get("time", "")
        
        # 메모리 내용 구성
        memory_content = []
        if event:
            memory_content.append(f"Event: {event}")
        if action:
            memory_content.append(f"Action: {action}")
        if feedback:
            memory_content.append(f"Feedback: {feedback}")
        
        memory_str = "\n".join(memory_content)
        
        prompt = f"""
TASK:
Rate the importance/poignancy of the following memory event on a scale of 1 to 10.

MEMORY: 
{memory_str}
at time {time_str}

MEMORY RATING RULES:
On a scale of 1 to 10, where 
  1 = purely mundane (e.g., brushing teeth, making bed)
  3 = minor daily event (e.g., short conversation, shopping)
  5 = moderately significant (e.g., playing games with friends)
  7 = important event (e.g., having dinner with friends)
  10 = extremely poignant (e.g., a breakup, college acceptance)
rate the poignancy/importance of this memory.

Please analyze exactly what is happening in the memory:
- Consider all aspects of the memory (event, action, and feedback)
- Consider the significance of the activity to daily life
- Consider the emotional impact of this type of event
- Consider the potential long-term impact of this type of event

RESPONSE FORMAT:
Provide ONLY a single integer rating from 1 to 10 with no additional text.
"""
        return prompt
    
    def _extract_batch_importance_ratings(self, response_text: str, memories: List[Dict]) -> List[int]:
        """
        LLM 응답에서 배치 중요도 평가 추출
        
        Parameters:
        - response_text: LLM 응답 텍스트
        - memories: 평가한 메모리 목록 (개수 확인용)
        
        Returns:
        - 중요도 평가 목록 (1-10 정수 리스트)
        """
        try:
            logger.info(f"배치 중요도 추출 시작 - 원본 응답: '{response_text}'")
            
            # JSON 추출
            json_match = re.search(r'({[\s\S]*})', response_text)
            if not json_match:
                logger.warning("응답에서 JSON을 찾을 수 없습니다.")
                return []
            
            json_str = json_match.group(1)
            logger.info(f"추출된 JSON 문자열: {json_str}")
            
            try:
                data = json.loads(json_str)
                logger.info(f"파싱된 JSON 데이터: {data}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {e}")
                # 정제 시도
                json_str = re.sub(r'\\n', '', json_str)  # 개행 문자 제거
                json_str = re.sub(r'\\', '', json_str)   # 백슬래시 제거
                try:
                    data = json.loads(json_str)
                    logger.info(f"정제 후 파싱된 JSON 데이터: {data}")
                except:
                    logger.error("정제 시도 후에도 JSON 파싱 실패")
                    return []
            
            # ratings 필드 확인
            if "ratings" not in data or not isinstance(data["ratings"], list):
                logger.warning("JSON 응답에 ratings 배열이 없습니다.")
                return []
            
            # 중요도 추출
            ratings = []
            for rating_item in data["ratings"]:
                if "importance" in rating_item:
                    importance = rating_item["importance"]
                    # 숫자로 변환 및 범위 확인
                    if isinstance(importance, int) and 1 <= importance <= 10:
                        ratings.append(importance)
                    else:
                        # 문자열인 경우 숫자로 변환 시도
                        try:
                            importance_int = int(importance)
                            if 1 <= importance_int <= 10:
                                ratings.append(importance_int)
                            else:
                                ratings.append(5)  # 범위 외 값은 중간값으로 대체
                        except:
                            ratings.append(5)  # 변환 실패 시 중간값 사용
            
            # 메모리 개수와 일치하는지 확인
            if len(ratings) != len(memories):
                logger.warning(f"중요도 개수({len(ratings)})가 메모리 개수({len(memories)})와 일치하지 않습니다.")
                # 부족한 경우 기본값으로 채우기
                while len(ratings) < len(memories):
                    ratings.append(5)
                # 초과하는 경우 잘라내기
                ratings = ratings[:len(memories)]
            
            logger.info(f"추출된 중요도 목록: {ratings}")
            return ratings
            
        except Exception as e:
            logger.error(f"배치 중요도 추출 중 오류 발생: {str(e)}")
            return []
    
    def _extract_importance_rating(self, response_text: str) -> int:
        """
        단일 LLM 응답에서 중요도 평가 추출
        
        Parameters:
        - response_text: LLM 응답 텍스트
        
        Returns:
        - 중요도 평가 (1-10 정수, 실패 시 기본값 5)
        """
        try:
            logger.info(f"중요도 추출 시작 - 원본 응답: '{response_text}'")
            # 응답에서 모든 공백과 개행문자 제거
            cleaned_response = response_text.strip()
            logger.info(f"정제된 응답: '{cleaned_response}'")
            
            # 숫자만 추출
            digits = re.findall(r'\d+', cleaned_response)
            logger.info(f"추출된 숫자들: {digits}")
            
            if digits:
                # 첫 번째 숫자 사용
                rating = int(digits[0])
                logger.info(f"첫 번째 숫자 변환 결과: {rating}")
                
                # 범위 확인 (1-10)
                if 1 <= rating <= 10:
                    logger.info(f"유효한 중요도 추출 완료: {rating}")
                    return rating
                else:
                    logger.warning(f"추출된 숫자가 범위를 벗어남: {rating} (1-10 범위가 아님)")
            else:
                logger.warning(f"응답에서 숫자를 찾을 수 없음: '{cleaned_response}'")
            
            # 실패 시 기본값 반환
            logger.warning(f"기본 중요도 5 반환")
            return 5
        except Exception as e:
            # 예외 발생 시 기본값 반환
            logger.error(f"중요도 추출 중 오류 발생: {str(e)}, 응답: '{response_text}'")
            return 5

# 테스트 코드
if __name__ == "__main__":
    # 테스트 메모리 리스트
    test_memories = [
        {
            "event": "discover old_blueprint Village storage",
            "time": "2025.05.06.09:35"
        },
        {
            "event": "eat raspberry Forest stream_bank",
            "time": "2025.05.06.11:00"
        },
        {
            "event": "sleep Village house",
            "time": "2025.05.06.22:00"
        }
    ]
    
    # 중요도 평가기 초기화
    import asyncio
    from ollama_client import OllamaClient
    
    async def test_batch_rating():
        ollama_client = OllamaClient()
        rater = ImportanceRater(ollama_client)
        
        # 배치 중요도 평가 테스트
        print("\n=== 배치 중요도 평가 테스트 ===")
        prompt = rater._create_batch_importance_rating_prompt(test_memories)
        print(f"생성된 배치 프롬프트:\n{prompt}")
        
        # Ollama API 호출
        print("\nOllama API 배치 호출 중...")
        response = await ollama_client.process_prompt(
            prompt=prompt,
            system_prompt="You are a helpful AI assistant that rates memory importance as instructed.",
            model_name="gemma3"
        )
        
        if response and response.get("status") == "success":
            print(f"배치 응답: {response['response']}")
            ratings = rater._extract_batch_importance_ratings(response["response"], test_memories)
            print(f"추출된 중요도 목록: {ratings}")
            
            # 각 메모리와 중요도 매핑
            for i, memory in enumerate(test_memories):
                if i < len(ratings):
                    print(f"메모리: {memory['event']}, 중요도: {ratings[i]}")
        else:
            print(f"API 호출 실패: {response.get('status') if response else 'None'}")
    
    asyncio.run(test_batch_rating())