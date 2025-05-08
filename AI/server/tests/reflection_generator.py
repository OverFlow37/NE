"""
20250505 MON 결과물
반성 생성과 관리
- 메모리와 반성 데이터를 로드
- 오늘의 메모리를 필터링하고 중요도 순으로 정렬
- 반성 생성 프롬프트를 만들고 Ollama API를 호출
- 생성된 반성을 반성 메모리에 추가
"""

import os
import json
import time
import numpy as np
import datetime
from typing import List, Dict, Any, Tuple
import requests
import re

# 반성 생성과 관리를 위한 클래스
class MemoryReflectionSystem:
    def __init__(self, memory_file_path: str, reflection_file_path: str, results_folder: str):
        """
        메모리 기반 반성 시스템 초기화
        
        Parameters:
        - memory_file_path: 메모리 JSON 파일 경로
        - reflection_file_path: 반성 JSON 파일 경로
        - results_folder: 결과 저장할 폴더 경로
        """
        self.memory_file_path = memory_file_path
        self.reflection_file_path = reflection_file_path
        self.results_folder = results_folder
        
        # 폴더 생성
        os.makedirs(results_folder, exist_ok=True)
        os.makedirs(os.path.dirname(reflection_file_path), exist_ok=True)
        
        # 메모리 로드
        print(f"메모리 로딩 중: {memory_file_path}...")
        self.memory_data = self._load_json_file(memory_file_path)
        
        # 반성 로드 (파일이 없으면 빈 구조 생성)
        print(f"반성 로딩 중: {reflection_file_path}...")
        self.reflection_data = self._load_json_file(reflection_file_path)
        
        # Ollama API 설정
        self.OLLAMA_URL = "http://localhost:11434/api/generate"
        self.MODEL = "gemma3"
        self.DEFAULT_TIMEOUT = 600  # 기본 타임아웃 600초 (CPU에서도 동작할 수 있도록 600)
    
    def _load_json_file(self, file_path: str) -> Dict:
        """
        JSON 파일 로드
        
        Parameters:
        - file_path: JSON 파일 경로
        
        Returns:
        - 로드된 데이터 (파일이 없으면 빈 구조)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"파일 로드 오류: {e}")
            # 파일이 없거나 손상된 경우 빈 구조 생성
            return {"John": {"reflections": []}}
    
    def _save_json_file(self, data: Dict, file_path: str):
        """
        JSON 파일 저장
        
        Parameters:
        - data: 저장할 데이터
        - file_path: 저장할 파일 경로
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"파일 저장 완료: {file_path}")
        except Exception as e:
            print(f"파일 저장 오류: {e}")
    
    def get_todays_memories(self, agent_name: str, date_str: str = None) -> List[Dict]:
        """
        오늘 날짜의 메모리 가져오기
        
        Parameters:
        - agent_name: 에이전트 이름
        - date_str: 날짜 문자열 (None인 경우 현재 날짜 사용)
        
        Returns:
        - 오늘 날짜의 메모리 리스트
        """
        if date_str is None:
            # 현재 날짜 사용
            today = datetime.datetime.now()
            date_str = today.strftime("%Y.%m.%d")
        
        today_memories = []
        
        # 메모리 데이터에서 오늘 날짜의 메모리만 필터링
        if agent_name in self.memory_data and "memories" in self.memory_data[agent_name]:
            for memory in self.memory_data[agent_name]["memories"]:
                memory_time = memory.get("time", "")
                # 날짜 형식이 다양할 수 있으므로 여러 형식 지원
                if date_str in memory_time or self._is_today(memory_time, date_str):
                    today_memories.append(memory)
        
        return today_memories
    
    def _is_today(self, memory_time: str, date_str: str) -> bool:
        """
        메모리 시간이 오늘인지 확인 (다양한 날짜 형식 지원)
        
        Parameters:
        - memory_time: 메모리의 시간 문자열
        - date_str: 비교할 날짜 문자열
        
        Returns:
        - 오늘 날짜인지 여부
        """
        # 다양한 날짜 형식 처리
        try:
            # YYYY.MM.DD 형식
            if re.search(r'\d{4}\.\d{2}\.\d{2}', memory_time):
                memory_date = re.search(r'\d{4}\.\d{2}\.\d{2}', memory_time).group()
                return memory_date == date_str
            
            # YYYY-MM-DD 형식
            elif re.search(r'\d{4}-\d{2}-\d{2}', memory_time):
                memory_date = re.search(r'\d{4}-\d{2}-\d{2}', memory_time).group()
                # 형식 변환
                memory_date = memory_date.replace('-', '.')
                return memory_date == date_str
            
            # Day N 형식 (게임 내 시간)
            elif "Day" in memory_time:
                # date_str에서 Day 번호 추출
                day_num_in_date = re.search(r'Day\s+(\d+)', date_str)
                if day_num_in_date:
                    day_num_in_date = day_num_in_date.group(1)
                    # memory_time에서 Day 번호 추출
                    day_num_in_memory = re.search(r'Day\s+(\d+)', memory_time)
                    if day_num_in_memory:
                        day_num_in_memory = day_num_in_memory.group(1)
                        return day_num_in_memory == day_num_in_date
            
            return False
        except:
            return False
    
    def get_important_memories(self, memories: List[Dict], top_k: int = 3) -> List[Dict]:
        """
        중요도가 높은 메모리 가져오기
        
        Parameters:
        - memories: 메모리 리스트
        - top_k: 반환할 메모리 수
        
        Returns:
        - 중요도 순으로 정렬된 상위 k개 메모리
        """
        # 중요도 필드가 있는 메모리만 필터링
        memories_with_importance = [m for m in memories if "importance" in m]
        
        # 중요도 기준 내림차순 정렬
        sorted_memories = sorted(memories_with_importance, key=lambda x: x.get("importance", 0), reverse=True)
        
        # 상위 k개 반환
        return sorted_memories[:top_k]
    
    def create_single_memory_reflection_prompt(self, agent_name: str, memory: Dict) -> str:
        """
        단일 메모리에 대한 반성 생성을 위한 프롬프트 생성
        
        Parameters:
        - agent_name: 에이전트 이름
        - memory: 반성할 메모리
        
        Returns:
        - 프롬프트 텍스트
        """
        current_date = datetime.datetime.now().strftime("%Y.%m.%d")
        
        event = memory.get("event", "")
        action = memory.get("action", "")
        importance = memory.get("importance", 0)
        
        prompt = f"""
    TASK:
    Create a short reflection for agent {agent_name} based on a single important memory.

    AGENT: {agent_name}
    DATE: {current_date}

    MEMORY TO REFLECT ON:
    Event: "{event}"
    Action: "{action}"
    Importance: {importance}

    INSTRUCTIONS:
    Create an extremely simple reflective thought about this memory in exactly 2-3 VERY SIMPLE sentences.

    OUTPUT FORMAT (provide ONLY valid JSON):
    {{
        "reflection": {{
            "created": "YYYY.MM.DD.HH:MM",
            "event": "{event}",
            "action": "{action}",
            "thought": "extremely_simple_reflection_in_2_or_3_basic_sentences",
            "importance": importance_rating
        }}
    }}

    IMPORTANCE RATING GUIDELINES:
    1-3: Minor everyday reflections
    4-6: Moderate insights about regular experiences
    7-8: Significant personal insights
    9-10: Major life-changing reflections

    REFLECTION GUIDELINES:
    - Keep reflection to MAXIMUM 3 sentences
    - Focus only on the most meaningful insights or feelings
    - Write in first-person perspective as if the agent is reflecting
    - Be concise but impactful
    - Make sure the reflection is complete and coherent despite its brevity
    """
        
        return prompt
    

    def call_ollama(self, prompt: str, timeout: int = None) -> Dict[str, Any]:
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
            
        start_time = time.time()
        
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
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("response", ""),
                    "elapsed_time": elapsed_time,
                    "status": "success"
                }
            else:
                return {
                    "response": f"Error: HTTP status code {response.status_code}",
                    "elapsed_time": elapsed_time,
                    "status": "error"
                }
        except requests.exceptions.Timeout:
            return {
                "response": f"Error: Request timed out after {timeout} seconds",
                "elapsed_time": timeout,
                "status": "timeout"
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "elapsed_time": time.time() - start_time,
                "status": "exception"
            }
    
    def extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
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
    
    def generate_reflections(self, agent_name: str, date_str: str = None) -> Dict:
        """
        에이전트의 반성 생성 (각 중요 메모리별로 개별 반성 생성)
        
        Parameters:
        - agent_name: 에이전트 이름
        - date_str: 날짜 문자열 (None인 경우 현재 날짜 사용)
        
        Returns:
        - 생성된 반성 데이터
        """
        # 1. 오늘의 메모리 가져오기
        todays_memories = self.get_todays_memories(agent_name, date_str)
        
        if not todays_memories:
            print(f"경고: 오늘({date_str}) 메모리가 없습니다.")
            return {"error": "No memories found for today"}
        
        # 2. 중요한 메모리 선택
        important_memories = self.get_important_memories(todays_memories, top_k=3)
        
        if not important_memories:
            print(f"경고: 중요한 메모리를 찾을 수 없습니다.")
            return {"error": "No important memories found"}
        
        # 3. 각 메모리에 대해 개별적으로 반성 생성
        reflections = []
        
        for memory in important_memories:
            # 3.1. 단일 메모리에 대한 프롬프트 생성
            prompt = self.create_single_memory_reflection_prompt(agent_name, memory)
            
            # 3.2. Ollama API 호출
            print(f"메모리 '{memory.get('event', '')}' 에 대한 반성 생성 중...")
            ollama_response = self.call_ollama(prompt)
            
            # 3.3. 결과 처리
            if ollama_response["status"] == "success":
                # 결과 추출
                response_text = ollama_response["response"]
                json_data = self.extract_json_from_response(response_text)
                
                if "reflection" in json_data:
                    # 현재 시간 설정
                    current_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")
                    json_data["reflection"]["created"] = current_time
                    
                    # 빈 embeddings 필드 추가
                    json_data["reflection"]["embeddings"] = []
                    
                    # 반성 추가
                    reflection = json_data.get("reflection", {})
                    reflections.append(reflection)
                    
                    # 반성 메모리에 추가
                    self._add_reflection_to_memory(agent_name, reflection)
                else:
                    print(f"경고: 반성 데이터가 없습니다. 응답: {response_text}")
            else:
                print(f"Ollama API 호출 오류: {ollama_response['status']}")
                print(f"응답: {ollama_response['response']}")
                # 오류 발생해도 계속 진행
        
        # 4. 결과 객체 구성
        result = {
            "reflections": reflections,
            "count": len(reflections),
            "status": "success" if reflections else "error",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return result
    
    def _add_reflection_to_memory(self, agent_name: str, reflection: Dict):
        """
        반성을 메모리에 추가
        
        Parameters:
        - agent_name: 에이전트 이름
        - reflection: 반성 데이터
        """
        # embeddings 필드가 없으면 추가
        if "embeddings" not in reflection:
            reflection["embeddings"] = []
        
        # 에이전트가 반성 데이터에 없으면 생성
        if agent_name not in self.reflection_data:
            self.reflection_data[agent_name] = {"reflections": []}
        
        # 반성 추가
        self.reflection_data[agent_name]["reflections"].append(reflection)
        
        # 반성 데이터 저장
        self._save_json_file(self.reflection_data, self.reflection_file_path)
        
        print(f"{agent_name}의 반성 '{reflection.get('event', '')}' 가 메모리에 추가되었습니다.")


# 메인 함수
def generate_daily_reflections(agent_name: str, memory_file_path: str, reflection_file_path: str, results_folder: str, date_str: str = None):
    """
    일일 반성 생성
    
    Parameters:
    - agent_name: 에이전트 이름
    - memory_file_path: 메모리 JSON 파일 경로
    - reflection_file_path: 반성 JSON 파일 경로
    - results_folder: 결과 저장 폴더
    - date_str: 날짜 문자열 (None인 경우 현재 날짜 사용)
    """
    # 반성 시스템 초기화
    reflection_system = MemoryReflectionSystem(memory_file_path, reflection_file_path, results_folder)
    
    # 반성 생성 (각 중요 메모리별로 개별 반성 생성)
    result = reflection_system.generate_reflections(agent_name, date_str)
    
    # 결과 출력
    if "error" not in result:
        print("\n생성된 반성 목록:")
        for i, reflection in enumerate(result.get("reflections", [])):
            print(f"\n반성 #{i+1}:")
            print(f"  이벤트: {reflection.get('event', '')}")
            print(f"  행동: {reflection.get('action', '')}")
            print(f"  생각: {reflection.get('thought', '')}")
            print(f"  중요도: {reflection.get('importance', 0)}")
    else:
        print(f"\n오류: {result.get('error', '알 수 없는 오류')}")
    
    return result


# 메인 실행 코드
if __name__ == "__main__":
    # 현재 스크립트 파일의 디렉토리 경로 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 메모리 파일 경로
    memory_file_path = os.path.join(current_dir, "memories.json")
    
    # 반성 파일 경로
    reflection_file_path = os.path.join(current_dir, "./reflect/reflections.json")
    
    # 결과 저장 폴더
    results_folder = os.path.join(current_dir, "reflection_results")
    
    # 에이전트 이름
    agent_name = "John"
    
    # 날짜 지정 (테스트용, None으로 설정하면 현재 날짜 사용)
    # 게임 내 시간 형식: "Day 5"
    date_str = "2025.05.04"  # 또는 None
    
    # 반성 생성
    result = generate_daily_reflections(agent_name, memory_file_path, reflection_file_path, results_folder, date_str)
    
    # 결과 출력
    print("\n처리 결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))