"""
메모리 중요도 평가 모듈

메모리의 중요도를 평가하여 importance 필드를 추가합니다.
Ollama API(gemma3)를 사용하여 1-10 척도로 중요도를 평가합니다.
"""

import re
import logging
import requests
from typing import Dict, List, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ImportanceRater")

class ImportanceRater:
    def __init__(self):
        """
        메모리 중요도 평가기 초기화
        """
        # Ollama API 설정
        self.OLLAMA_URL = "http://localhost:11434/api/generate"
        self.MODEL = "gemma3"
        self.DEFAULT_TIMEOUT = 30  # 기본 타임아웃 30초
        
        logger.info("메모리 중요도 평가기 초기화")
    
    def add_importance_to_memories(self, memories: Dict, agent_name: str, target_memories: List[Dict]) -> Dict:
        """
        메모리에 importance 필드 추가
        
        Parameters:
        - memories: 전체 메모리 데이터
        - agent_name: 에이전트 이름
        - target_memories: importance를 추가할 대상 메모리 목록
        
        Returns:
        - 업데이트된 메모리 데이터
        """
        # 메모리 복사본 생성
        updated_memories = memories.copy()
        
        # 각 대상 메모리 처리
        for target_memory in target_memories:
            # 중요도가 이미 있으면 건너뛰기
            if "importance" in target_memory:
                continue
            
            # 메모리 이벤트 및 시간
            event = target_memory.get("event", "")
            time_str = target_memory.get("time", "")
            
            logger.info(f"메모리 '{event}'의 중요도 평가 중...")
            
            # 중요도 평가 프롬프트 생성
            prompt = self._create_importance_rating_prompt(target_memory)
            
            # Ollama API 호출하여 중요도 평가
            response = self._call_ollama(prompt)
            
            if response["status"] == "success":
                # 중요도 추출
                importance = self._extract_importance_rating(response["response"])
                
                # 원본 메모리에 중요도 추가
                for i, memory in enumerate(updated_memories[agent_name]["memories"]):
                    if memory.get("time", "") == time_str and memory.get("event", "") == event:
                        updated_memories[agent_name]["memories"][i]["importance"] = importance
                        logger.info(f"메모리 '{event}'에 중요도 {importance} 추가됨")
                        break
            else:
                logger.warning(f"메모리 '{event}'의 중요도 평가 실패: {response['status']}")
        
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
                "temperature": 0.1,  # 낮은 temperature로 일관된 결과 유도
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
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
    
    def _extract_importance_rating(self, response_text: str) -> int:
        """
        LLM 응답에서 중요도 평가 추출
        
        Parameters:
        - response_text: LLM 응답 텍스트
        
        Returns:
        - 중요도 평가 (1-10 정수, 실패 시 기본값 3)
        """
        try:
            # 숫자만 추출
            digits = re.findall(r'\d+', response_text)
            if digits:
                # 첫 번째 숫자 사용
                rating = int(digits[0])
                # 범위 확인 (1-10)
                if 1 <= rating <= 10:
                    return rating
            
            # 실패 시 기본값 반환
            return 3
        except:
            # 예외 발생 시 기본값 반환
            return 3

# 테스트 코드
if __name__ == "__main__":
    # 테스트 메모리
    test_memory = {
        "event": "discover old_blueprint Village storage",
        "time": "2025.05.06.09:35"
    }
    
    # 중요도 평가기 초기화
    rater = ImportanceRater()
    
    # 중요도 평가 프롬프트 생성
    prompt = rater._create_importance_rating_prompt(test_memory)
    print(f"생성된 프롬프트:\n{prompt}")
    
    # Ollama API 호출
    print("\nOllama API 호출 중...")
    response = rater._call_ollama(prompt)
    
    if response["status"] == "success":
        print(f"응답: {response['response']}")
        importance = rater._extract_importance_rating(response["response"])
        print(f"추출된 중요도: {importance}")
    else:
        print(f"API 호출 실패: {response['status']}")
        print(f"응답: {response.get('response', '')}")