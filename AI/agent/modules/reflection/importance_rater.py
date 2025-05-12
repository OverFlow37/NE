"""
메모리 중요도 평가 모듈

메모리의 중요도를 평가하여 importance 필드를 추가합니다.
Ollama API(gemma3)를 사용하여 1-10 척도로 중요도를 평가합니다.
"""

import re
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
        메모리 중요도 평가기 초기화
        
        Args:
            ollama_client: Ollama API 클라이언트 인스턴스
        """
        self.ollama_client = ollama_client
        logger.info("메모리 중요도 평가기 초기화")
    
    async def add_importance_to_memories(self, memories: Dict, agent_name: str, target_memories: List[Dict]) -> Dict:
        """
        메모리에 importance 필드 추가
        Parameters:
        - memories: 전체 메모리 데이터
        - agent_name: 에이전트 이름
        - target_memories: importance를 추가할 대상 메모리 목록
        Returns:
        - 업데이트된 메모리 데이터
        """
        updated_memories = memories.copy()
        
        for target_memory in target_memories:
            if "importance" in target_memory:
                continue
                
            event = target_memory.get("event", "")
            time_str = target_memory.get("time", "")
            logger.info(f"메모리 '{event}'의 중요도 평가 중...")
            
            prompt = self._create_importance_rating_prompt(target_memory)
            logger.debug(f"생성된 프롬프트:\n{prompt}")
            
            try:
                logger.info(f"Ollama API 호출 시작 - 메모리: '{event}'")
                response = await self.ollama_client.process_prompt(
                    prompt=prompt,
                    system_prompt="""""",
                    model_name="gemma3",
                    options={
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "frequency_penalty": 0.0,
                        "presence_penalty": 0.0
                    }
                )
                
                logger.info(f"Ollama API 응답 수신 - 메모리: '{event}', 응답: {response}")
                
                if response and response.get("status") == "success":
                    logger.info(f"메모리 '{event}'의 중요도 평가 응답: {response['response']}")
                    importance = self._extract_importance_rating(response["response"])
                    
                    for i, memory in enumerate(updated_memories[agent_name]["memories"]):
                        if memory.get("time", "") == time_str and memory.get("event", "") == event:
                            updated_memories[agent_name]["memories"][i]["importance"] = importance
                            logger.info(f"메모리 '{event}'에 중요도 {importance} 추가됨")
                            break
                else:
                    logger.warning(f"메모리 '{event}'의 중요도 평가 실패 - 응답 상태: {response.get('status') if response else 'None'}")
                    # 기본 중요도 설정
                    for i, memory in enumerate(updated_memories[agent_name]["memories"]):
                        if memory.get("time", "") == time_str and memory.get("event", "") == event:
                            updated_memories[agent_name]["memories"][i]["importance"] = 3
                            logger.info(f"메모리 '{event}'에 기본 중요도 3 추가됨")
                            break
                            
            except Exception as e:
                logger.error(f"메모리 '{event}'의 중요도 평가 중 오류 발생: {str(e)}")
                logger.error(f"오류 상세 정보: {type(e).__name__}")
                import traceback
                logger.error(f"스택 트레이스:\n{traceback.format_exc()}")
                # 오류 발생 시 기본 중요도 설정
                for i, memory in enumerate(updated_memories[agent_name]["memories"]):
                    if memory.get("time", "") == time_str and memory.get("event", "") == event:
                        updated_memories[agent_name]["memories"][i]["importance"] = 3
                        logger.info(f"메모리 '{event}'에 기본 중요도 3 추가됨")
                        break
        
        return updated_memories
    
    def _create_importance_rating_prompt(self, memory: Dict) -> str:
        """
        메모리의 중요도를 평가하기 위한 프롬프트 생성
        
        Parameters:
        - memory: 평가할 메모리 데이터
        
        Returns:
        - 프롬프트 텍스트
        """
        event = memory.get("event", "")
        time_str = memory.get("time", "")
        
        prompt = f"""
TASK:
Rate the importance/poignancy of the following memory event on a scale of 1 to 10.

MEMORY: "{event}" at time {time_str}

MEMORY RATING RULES:
On a scale of 1 to 10, where 
  1 = purely mundane (e.g., brushing teeth, making bed)
  3 = minor daily event (e.g., short conversation, shopping)
  5 = moderately significant (e.g., playing games with friends)
  7 = important event (e.g., having dinner with friends)
  10 = extremely poignant (e.g., a breakup, college acceptance)
rate the poignancy/importance of this memory.

Please analyze exactly what is happening in the memory:
- The event is: "{event}"
- Consider the significance of the activity to daily life
- Consider the emotional impact of this type of event
- Consider the potential long-term impact of this type of event

RESPONSE FORMAT:
Provide ONLY a single integer rating from 1 to 10 with no additional text.
"""
        return prompt
    
    def _extract_importance_rating(self, response_text: str) -> int:
        """
        LLM 응답에서 중요도 평가 추출
        
        Parameters:
        - response_text: LLM 응답 텍스트
        
        Returns:
        - 중요도 평가 (1-10 정수, 실패 시 기본값 3)
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
            logger.warning(f"기본 중요도 3 반환")
            return 3
        except Exception as e:
            # 예외 발생 시 기본값 반환
            logger.error(f"중요도 추출 중 오류 발생: {str(e)}, 응답: '{response_text}'")
            return 3

# 테스트 코드
if __name__ == "__main__":
    # 테스트 메모리
    test_memory = {
        "event": "discover old_blueprint Village storage",
        "time": "2025.05.06.09:35"
    }
    
    # 중요도 평가기 초기화
    ollama_client = OllamaClient()
    rater = ImportanceRater(ollama_client)
    
    # 중요도 평가 프롬프트 생성
    prompt = rater._create_importance_rating_prompt(test_memory)
    print(f"생성된 프롬프트:\n{prompt}")
    
    # Ollama API 호출
    print("\nOllama API 호출 중...")
    response = rater.ollama_client.process_prompt(
        prompt=prompt,
        system_prompt="You are a helpful AI assistant that rates memory importance.",
        model_name="gemma3"
    )
    
    if response:
        print(f"응답: {response['response']}")
        importance = rater._extract_importance_rating(response['response'])
        print(f"추출된 중요도: {importance}")
    else:
        print("API 호출 실패")