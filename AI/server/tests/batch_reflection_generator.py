"""
20250506 TUE 결과물
배치 처리 기반 반성 생성과 관리
- 메모리와 반성 데이터를 로드
- 오늘의 메모리를 필터링하고 중요도 순으로 정렬
- 여러 메모리에 대한 반성 동시 생성 프롬프트 작성
- 생성된 각 반성을 반성 메모리에 추가
- 반성 생성 시간 측정 및 기록
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
class BatchMemoryReflectionSystem:
    def __init__(self, memory_file_path: str, reflection_file_path: str, results_folder: str):
        """
        메모리 기반 배치 반성 시스템 초기화
        
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
        
        # 시간 측정 로그 파일 경로
        self.timing_log_path = os.path.join(results_folder, "reflection_timing.json")
        
        # 메모리 로드
        print(f"메모리 로딩 중: {memory_file_path}...")
        self.memory_data = self._load_json_file(memory_file_path)
        
        # 반성 로드 (파일이 없으면 빈 구조 생성)
        print(f"반성 로딩 중: {reflection_file_path}...")
        self.reflection_data = self._load_json_file(reflection_file_path)
        
        # 시간 측정 로그 로드 (파일이 없으면 빈 구조 생성)
        print(f"시간 측정 로그 로딩 중: {self.timing_log_path}...")
        self.timing_data = self._load_json_file(self.timing_log_path)
        if not self.timing_data:
            self.timing_data = {"batch_reflections": [], "single_reflections": []}
        
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
            return {}
    
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
    
    def _save_timing_data(self):
        """
        시간 측정 데이터 저장
        """
        self._save_json_file(self.timing_data, self.timing_log_path)
    
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
    
    def create_batch_memory_reflection_prompt(self, agent_name: str, memories: List[Dict]) -> str:
        """
        여러 메모리를 일괄 처리하기 위한 프롬프트 생성
        
        Parameters:
        - agent_name: 에이전트 이름
        - memories: 반성할 메모리 목록
        
        Returns:
        - 일괄 반성 생성을 위한 프롬프트 텍스트
        """
        current_date = datetime.datetime.now().strftime("%Y.%m.%d")
        
        # 각 메모리에 대한 섹션 생성
        memory_sections = []
        for i, memory in enumerate(memories):
            event = memory.get("event", "")
            action = memory.get("action", "")
            importance = memory.get("importance", 0)
            
            memory_section = f"""
MEMORY #{i+1}:
Event: "{event}"
Action: "{action}"
Importance: {importance}
"""
            memory_sections.append(memory_section)
        
        memories_text = "\n".join(memory_sections)
        
        prompt = f"""
TASK:
Create three separate, independent reflections for agent {agent_name} based on three distinct memories.

AGENT: {agent_name}
DATE: {current_date}

{memories_text}

INSTRUCTIONS:
- Process each memory SEPARATELY and create an independent reflection for each
- Each reflection should be 2-3 VERY SIMPLE sentences
- Do NOT reference or include information from the other memories in each reflection
- Each reflection should ONLY be based on its corresponding memory
- Use first-person perspective as if the agent is reflecting
- Keep each reflection concise but impactful

OUTPUT FORMAT (provide ONLY valid JSON):
{{
  "reflections": [
    {{
      "memory_index": 1,
      "event": "{memories[0].get('event', '')}",
      "action": "{memories[0].get('action', '')}",
      "thought": "extremely_simple_reflection_in_2_or_3_basic_sentences",
      "importance": importance_rating_1
    }},
    {{
      "memory_index": 2,
      "event": "{memories[1].get('event', '')}",
      "action": "{memories[1].get('action', '')}",
      "thought": "extremely_simple_reflection_in_2_or_3_basic_sentences",
      "importance": importance_rating_2
    }},
    {{
      "memory_index": 3,
      "event": "{memories[2].get('event', '')}",
      "action": "{memories[2].get('action', '')}",
      "thought": "extremely_simple_reflection_in_2_or_3_basic_sentences",
      "importance": importance_rating_3
    }}
  ]
}}

IMPORTANCE RATING GUIDELINES:
1-3: Minor everyday reflections
4-6: Moderate insights about regular experiences
7-8: Significant personal insights
9-10: Major life-changing reflections

CRITICAL:
- Each reflection must be independent and only based on its corresponding memory
- Do NOT mix details or themes between reflections
- Each memory should have its own distinct reflection
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
    
    def generate_single_reflections(self, agent_name: str, date_str: str = None) -> Dict:
        """
        에이전트의 반성 생성 (각 중요 메모리별로 개별 반성 생성)
        
        Parameters:
        - agent_name: 에이전트 이름
        - date_str: 날짜 문자열 (None인 경우 현재 날짜 사용)
        
        Returns:
        - 생성된 반성 데이터
        """
        process_start_time = time.time()
        
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
        individual_times = []
        
        for memory in important_memories:
            # 3.1. 단일 메모리에 대한 프롬프트 생성
            prompt = self.create_single_memory_reflection_prompt(agent_name, memory)
            
            # 3.2. Ollama API 호출
            print(f"메모리 '{memory.get('event', '')}' 에 대한 반성 생성 중...")
            
            memory_start_time = time.time()
            ollama_response = self.call_ollama(prompt)
            memory_elapsed_time = time.time() - memory_start_time
            
            # 시간 기록
            individual_times.append({
                "event": memory.get("event", ""),
                "importance": memory.get("importance", 0),
                "elapsed_time": memory_elapsed_time,
                "status": ollama_response["status"]
            })
            
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
        
        # 처리 시간 계산
        process_elapsed_time = time.time() - process_start_time
        
        # 시간 측정 데이터 저장
        timing_entry = {
            "date": date_str or datetime.datetime.now().strftime("%Y.%m.%d"),
            "agent_name": agent_name,
            "total_time": process_elapsed_time,
            "memory_count": len(important_memories),
            "individual_times": individual_times,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.timing_data["single_reflections"].append(timing_entry)
        self._save_timing_data()
        
        # 4. 결과 객체 구성
        result = {
            "reflections": reflections,
            "count": len(reflections),
            "status": "success" if reflections else "error",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time": process_elapsed_time,
            "individual_times": individual_times
        }
        
        return result
    
    def generate_batch_reflections(self, agent_name: str, date_str: str = None) -> Dict:
        """
        에이전트의 메모리에 대한 반성을 일괄 생성
        
        Parameters:
        - agent_name: 에이전트 이름
        - date_str: 날짜 문자열 (None인 경우 현재 날짜 사용)
        
        Returns:
        - 생성된 반성 데이터
        """
        process_start_time = time.time()
        
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
        
        # 3. 일괄 반성 프롬프트 생성
        prompt = self.create_batch_memory_reflection_prompt(agent_name, important_memories)
        
        # 4. Ollama API 호출
        print(f"일괄 모드에서 {len(important_memories)}개 메모리에 대한 반성 생성 중...")
        
        # API 호출 시간 측정
        api_start_time = time.time()
        ollama_response = self.call_ollama(prompt)
        api_elapsed_time = time.time() - api_start_time
        
        # 5. 결과 처리
        reflections = []
        
        if ollama_response["status"] == "success":
            # 결과 추출
            response_text = ollama_response["response"]
            json_data = self.extract_json_from_response(response_text)
            
            if "reflections" in json_data and isinstance(json_data["reflections"], list):
                # 현재 시간 가져오기
                current_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")
                
                # 각 반성 처리
                for i, reflection_data in enumerate(json_data["reflections"]):
                    if i < len(important_memories):
                        # 생성 시간 및 빈 임베딩 추가
                        reflection = {
                            "created": current_time,
                            "event": important_memories[i].get("event", ""),
                            "action": important_memories[i].get("action", ""),
                            "thought": reflection_data.get("thought", ""),
                            "importance": reflection_data.get("importance", important_memories[i].get("importance", 0)),
                            "embeddings": []
                        }
                        
                        # 반성 목록에 추가
                        reflections.append(reflection)
                        
                        # 반성 메모리에 추가
                        self._add_reflection_to_memory(agent_name, reflection)
            else:
                print(f"경고: 유효하지 않은 반성 데이터 형식입니다. 응답: {response_text}")
        else:
            print(f"Ollama API 호출 오류: {ollama_response['status']}")
            print(f"응답: {ollama_response['response']}")
        
        # 처리 시간 계산
        process_elapsed_time = time.time() - process_start_time
        
        # 각 메모리별 이벤트와 중요도 기록
        memory_details = [
            {"event": m.get("event", ""), "importance": m.get("importance", 0)}
            for m in important_memories
        ]
        
        # 시간 측정 데이터 저장
        timing_entry = {
            "date": date_str or datetime.datetime.now().strftime("%Y.%m.%d"),
            "agent_name": agent_name,
            "total_time": process_elapsed_time,
            "api_time": api_elapsed_time,
            "memory_count": len(important_memories),
            "memory_details": memory_details,
            "status": ollama_response["status"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.timing_data["batch_reflections"].append(timing_entry)
        self._save_timing_data()
        
        # 6. 결과 객체 구성
        result = {
            "reflections": reflections,
            "count": len(reflections),
            "status": "success" if reflections else "error",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time": process_elapsed_time,
            "api_time": api_elapsed_time
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
    
    def compare_performance(self, agent_name: str, date_str: str = None) -> Dict:
        """
        단일 처리와 배치 처리의 성능 비교
        
        Parameters:
        - agent_name: 에이전트 이름
        - date_str: 날짜 문자열 (None인 경우 현재 날짜 사용)
        
        Returns:
        - 성능 비교 결과
        """
        if date_str is None:
            date_str = datetime.datetime.now().strftime("%Y.%m.%d")
        
        print(f"\n{agent_name}의 {date_str} 반성 생성 성능 비교 시작...\n")
        
        # 단일 처리 성능 측정
        print("1. 단일 처리 반성 생성 중...")
        single_result = self.generate_single_reflections(agent_name, date_str)
        
        # 배치 처리 성능 측정
        print("\n2. 배치 처리 반성 생성 중...")
        batch_result = self.generate_batch_reflections(agent_name, date_str)
        
        # 결과 객체 구성
        comparison = {
            "date": date_str,
            "agent_name": agent_name,
            "single_processing": {
                "total_time": single_result.get("total_time", 0),
                "count": single_result.get("count", 0),
                "status": single_result.get("status", "error"),
"individual_times": single_result.get("individual_times", [])
            },
            "batch_processing": {
                "total_time": batch_result.get("total_time", 0),
                "api_time": batch_result.get("api_time", 0),
                "count": batch_result.get("count", 0),
                "status": batch_result.get("status", "error")
            },
            "comparison": {
                "time_difference": single_result.get("total_time", 0) - batch_result.get("total_time", 0),
                "time_ratio": single_result.get("total_time", 0) / max(batch_result.get("total_time", 1), 1),
                "memory_count": len(self.get_important_memories(self.get_todays_memories(agent_name, date_str)))
            },
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 비교 결과 저장
        comparison_file_path = os.path.join(self.results_folder, f"comparison_{date_str.replace('.', '_')}.json")
        self._save_json_file(comparison, comparison_file_path)
        
        # 결과 출력
        print("\n성능 비교 결과:")
        print(f"  단일 처리 총 시간: {comparison['single_processing']['total_time']:.2f}초")
        print(f"  배치 처리 총 시간: {comparison['batch_processing']['total_time']:.2f}초")
        print(f"  시간 차이: {comparison['comparison']['time_difference']:.2f}초")
        print(f"  시간 비율: {comparison['comparison']['time_ratio']:.2f}배")
        
        return comparison


# 메인 함수
def generate_daily_reflections(agent_name: str, memory_file_path: str, reflection_file_path: str, results_folder: str, 
                               date_str: str = None, mode: str = "batch", compare: bool = False):
    """
    일일 반성 생성
    
    Parameters:
    - agent_name: 에이전트 이름
    - memory_file_path: 메모리 JSON 파일 경로
    - reflection_file_path: 반성 JSON 파일 경로
    - results_folder: 결과 저장 폴더
    - date_str: 날짜 문자열 (None인 경우 현재 날짜 사용)
    - mode: 처리 모드 ("single": 개별 처리, "batch": 일괄 처리, "both": 둘 다 실행)
    - compare: 성능 비교 여부
    
    Returns:
    - 생성된 반성 데이터
    """
    # 반성 시스템 초기화
    reflection_system = BatchMemoryReflectionSystem(memory_file_path, reflection_file_path, results_folder)
    
    # 성능 비교 모드
    if compare:
        result = reflection_system.compare_performance(agent_name, date_str)
        return result
    
    # 단일 처리 모드
    if mode == "single":
        print("단일 처리 모드에서 반성 생성 중...")
        result = reflection_system.generate_single_reflections(agent_name, date_str)
    
    # 배치 처리 모드
    elif mode == "batch":
        print("배치 처리 모드에서 반성 생성 중...")
        result = reflection_system.generate_batch_reflections(agent_name, date_str)
    
    # 둘 다 실행 모드
    elif mode == "both":
        print("단일 처리 모드에서 반성 생성 중...")
        single_result = reflection_system.generate_single_reflections(agent_name, date_str)
        
        print("\n배치 처리 모드에서 반성 생성 중...")
        batch_result = reflection_system.generate_batch_reflections(agent_name, date_str)
        
        # 두 결과 비교
        result = {
            "single_processing": single_result,
            "batch_processing": batch_result,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    else:
        print(f"오류: 알 수 없는 모드 '{mode}'. 'single', 'batch', 'both' 중 하나여야 합니다.")
        return {"error": f"Invalid mode: {mode}"}
    
    # 결과 출력
    if "error" not in result:
        if mode == "both":
            # 단일 처리 결과 출력
            print("\n단일 처리 생성된 반성 목록:")
            for i, reflection in enumerate(result["single_processing"].get("reflections", [])):
                print(f"\n반성 #{i+1}:")
                print(f"  이벤트: {reflection.get('event', '')}")
                print(f"  행동: {reflection.get('action', '')}")
                print(f"  생각: {reflection.get('thought', '')}")
                print(f"  중요도: {reflection.get('importance', 0)}")
            
            # 배치 처리 결과 출력
            print("\n배치 처리 생성된 반성 목록:")
            for i, reflection in enumerate(result["batch_processing"].get("reflections", [])):
                print(f"\n반성 #{i+1}:")
                print(f"  이벤트: {reflection.get('event', '')}")
                print(f"  행동: {reflection.get('action', '')}")
                print(f"  생각: {reflection.get('thought', '')}")
                print(f"  중요도: {reflection.get('importance', 0)}")
        else:
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
    
    # 기본 설정
    agent_name = "John"
    memory_file_path = os.path.join(current_dir, "memories.json")
    reflection_file_path = os.path.join(current_dir, "./reflect/reflections.json")
    results_folder = os.path.join(current_dir, "reflection_results")
    date_str = "2025.05.04"  # 기본값
    
    # 대화형 메뉴 표시
    print("\n===== 메모리 기반 반성 생성 시스템 =====")
    print("1. 단일 처리 모드 실행 (각 메모리 개별 처리)")
    print("2. 배치 처리 모드 실행 (메모리 일괄 처리)")
    print("3. 두 모드 모두 실행 및 비교")
    print("4. 직접 성능 비교 (시간 측정 및 분석)")
    print("0. 종료")
    
    # 사용자 입력 받기
    choice = input("\n원하는 모드를 선택하세요 (0-4): ")
    
    if choice == "0":
        print("프로그램을 종료합니다.")
        exit()
    
    # 날짜 입력 받기 (선택 사항)
    custom_date = input("\n날짜를 입력하세요 (YYYY.MM.DD, 빈칸=기본값): ")
    if custom_date:
        date_str = custom_date
    
    print(f"\n날짜: {date_str}로 설정되었습니다.")
    
    # 에이전트 이름 입력 받기 (선택 사항)
    custom_agent = input("\n에이전트 이름을 입력하세요 (빈칸=John): ")
    if custom_agent:
        agent_name = custom_agent
    
    print(f"\n에이전트: {agent_name}로 설정되었습니다.")
    print("\n==================================")
    
    # 선택에 따라 실행
    if choice == "1":
        mode = "single"
        compare = False
        print("\n단일 처리 모드 실행 중...")
    elif choice == "2":
        mode = "batch"
        compare = False
        print("\n배치 처리 모드 실행 중...")
    elif choice == "3":
        mode = "both"
        compare = False
        print("\n두 모드 모두 실행 중...")
    elif choice == "4":
        mode = "batch"  # 사용되지 않음
        compare = True
        print("\n성능 비교 모드 실행 중...")
    else:
        print("\n잘못된 선택입니다. 프로그램을 종료합니다.")
        exit()
    
    # 반성 생성
    result = generate_daily_reflections(
        agent_name=agent_name,
        memory_file_path=memory_file_path,
        reflection_file_path=reflection_file_path,
        results_folder=results_folder,
        date_str=date_str,
        mode=mode,
        compare=compare
    )
    
    # 성능 결과 요약 출력
    print("\n===== 성능 결과 요약 =====")
    if compare or mode == "both":
        if "single_processing" in result and "batch_processing" in result:
            print(f"단일 처리 반성 수: {result['single_processing'].get('count', 0)}")
            print(f"단일 처리 총 시간: {result['single_processing'].get('total_time', 0):.2f}초")
            print(f"배치 처리 반성 수: {result['batch_processing'].get('count', 0)}")
            print(f"배치 처리 총 시간: {result['batch_processing'].get('total_time', 0):.2f}초")
            
            if compare:
                time_diff = result.get('comparison', {}).get('time_difference', 0)
                time_ratio = result.get('comparison', {}).get('time_ratio', 0)
                print(f"시간 차이: {time_diff:.2f}초 (단일 - 배치)")
                print(f"시간 비율: {time_ratio:.2f}배 (단일 / 배치)")
    else:
        print(f"처리 모드: {mode}")
        print(f"생성된 반성 수: {result.get('count', 0)}")
        print(f"총 처리 시간: {result.get('total_time', 0):.2f}초")
        if mode == "batch":
            print(f"API 호출 시간: {result.get('api_time', 0):.2f}초")
    
    print("\n프로그램 실행이 완료되었습니다.")