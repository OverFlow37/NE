"""
20250508 THU 결과물
배치 처리 기반 반성 생성과 관리
- 메모리와 반성 데이터를 로드
- 오늘의 메모리를 필터링하고 중요도 순으로 정렬
- 이전 반성 데이터를 날짜 및 중요도 기준으로 필터링하여 현재 반성에 반영
- 여러 메모리에 대한 반성 동시 생성 프롬프트 작성
- 생성된 각 반성을 반성 메모리에 추가 (created 필드는 메모리 날짜의 22:00으로 설정)
- 반성 생성 시간 측정 및 기록
"""

import os
import json
import time
import datetime
import re
import requests
from typing import List, Dict, Any
import math

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
            self.timing_data = {"batch_reflections": []}
        
        # Ollama API 설정
        self.OLLAMA_URL = "http://localhost:11434/api/generate"
        self.MODEL = "gemma3"
        self.DEFAULT_TIMEOUT = 600  # 기본 타임아웃 600초 (CPU에서도 동작할 수 있도록 600)
        
        # 이전 반성 반영을 위한 설정
        self.MAX_PREV_REFLECTIONS = 5  # 최대 이전 반성 수
        self.RECENCY_WEIGHT = 0.7  # 최근성 가중치 (값이 클수록 최근 반성이 더 중요)
        self.IMPORTANCE_WEIGHT = 0.3  # 중요도 가중치 (값이 클수록 중요한 반성이 더 중요)
    
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
    
    def get_relevant_previous_reflections(self, agent_name: str, current_date: str) -> List[Dict]:
        """
        현재 날짜에 가깝고 중요도가 높은 이전 반성 가져오기
        
        Parameters:
        - agent_name: 에이전트 이름
        - current_date: 현재 날짜 문자열 (YYYY.MM.DD 형식)
        
        Returns:
        - 관련성 높은 이전 반성 리스트
        """
        if agent_name not in self.reflection_data or "reflections" not in self.reflection_data[agent_name]:
            return []
        
        try:
            # 현재 날짜를 datetime 객체로 변환
            current_date_obj = datetime.datetime.strptime(current_date, "%Y.%m.%d")
            
            # 이전 반성 목록
            previous_reflections = []
            
            for reflection in self.reflection_data[agent_name]["reflections"]:
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
            sorted_reflections = sorted(previous_reflections, key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            # 상위 N개 반환
            return sorted_reflections[:self.MAX_PREV_REFLECTIONS]
            
        except Exception as e:
            print(f"이전 반성 처리 중 오류 발생: {e}")
            return []
    
    def create_date_with_evening_time(self, date_str: str) -> str:
        """
        날짜 문자열에 저녁 시간(22:00)을 추가
        
        Parameters:
        - date_str: 날짜 문자열 (YYYY.MM.DD 형식)
        
        Returns:
        - 시간이 추가된 날짜 문자열 (YYYY.MM.DD.22:00 형식)
        """
        return f"{date_str}.22:00"
    
    def create_batch_memory_reflection_prompt(self, agent_name: str, memories: List[Dict], 
                                              previous_reflections: List[Dict] = None) -> str:
        """
        여러 메모리와 이전 반성을 일괄 처리하기 위한 프롬프트 생성
        
        Parameters:
        - agent_name: 에이전트 이름
        - memories: 반성할 메모리 목록
        - previous_reflections: 관련 이전 반성 목록 (None인 경우 이전 반성 없음)
        
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
Create three separate, independent reflections for agent {agent_name} based on three distinct memories.

AGENT: {agent_name}
DATE: {current_date}

{memories_text}
"""

        # 이전 반성이 있으면 추가
        if previous_reflections_text:
            prompt += previous_reflections_text
        
        # 지시사항 및 출력 형식 추가
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
    
    def extract_date_from_memory(self, memory: Dict) -> str:
        """
        메모리에서 날짜 추출
        
        Parameters:
        - memory: 메모리 데이터
        
        Returns:
        - 날짜 문자열 (YYYY.MM.DD 형식) 또는 빈 문자열
        """
        memory_time = memory.get("time", "")
        
        # YYYY.MM.DD 형식 추출
        date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', memory_time)
        if date_match:
            return date_match.group(1)
        
        # YYYY-MM-DD 형식 추출 및 변환
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', memory_time)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}.{month}.{day}"
        
        return ""
    
    def generate_batch_reflections(self, agent_name: str, date_str: str = None) -> Dict:
        """
        에이전트의 메모리에 대한 반성을 일괄 생성 (이전 반성 포함)
        
        Parameters:
        - agent_name: 에이전트 이름
        - date_str: 날짜 문자열 (None인 경우 현재 날짜 사용)
        
        Returns:
        - 생성된 반성 데이터
        """
        process_start_time = time.time()
        
        # 현재 날짜 설정
        if date_str is None:
            current_date = datetime.datetime.now().strftime("%Y.%m.%d")
        else:
            current_date = date_str
            
        print(f"처리할 날짜: {current_date}")
        
        # 1. 오늘의 메모리 가져오기
        todays_memories = self.get_todays_memories(agent_name, current_date)
        
        if not todays_memories:
            print(f"경고: 오늘({current_date}) 메모리가 없습니다.")
            return {"error": "No memories found for today"}
        
        # 2. 중요한 메모리 선택
        important_memories = self.get_important_memories(todays_memories, top_k=3)
        
        if not important_memories:
            print(f"경고: 중요한 메모리를 찾을 수 없습니다.")
            return {"error": "No important memories found"}
        
        # 3. 관련 이전 반성 가져오기
        previous_reflections = self.get_relevant_previous_reflections(agent_name, current_date)
        
        if previous_reflections:
            print(f"관련 이전 반성 {len(previous_reflections)}개를 찾았습니다.")
        else:
            print("관련 이전 반성을 찾을 수 없습니다.")
        
        # 4. 일괄 반성 프롬프트 생성 (이전 반성 포함)
        prompt = self.create_batch_memory_reflection_prompt(agent_name, important_memories, previous_reflections)
        
        # 5. Ollama API 호출
        print(f"일괄 모드에서 {len(important_memories)}개 메모리에 대한 반성 생성 중...")
        
        # API 호출 시간 측정
        api_start_time = time.time()
        ollama_response = self.call_ollama(prompt)
        api_elapsed_time = time.time() - api_start_time
        
        # 6. 결과 처리
        reflections = []
        
        if ollama_response["status"] == "success":
            # 결과 추출
            response_text = ollama_response["response"]
            json_data = self.extract_json_from_response(response_text)
            
            if "reflections" in json_data and isinstance(json_data["reflections"], list):
                # 각 반성 처리
                for i, reflection_data in enumerate(json_data["reflections"]):
                    if i < len(important_memories):
                        # 메모리에서 날짜 추출
                        memory_date = self.extract_date_from_memory(important_memories[i])
                        
                        # 생성 시간 설정 (메모리 날짜의 22:00)
                        created_time = self.create_date_with_evening_time(memory_date if memory_date else current_date)
                        
                        # 빈 임베딩 추가
                        reflection = {
                            "created": created_time,
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
        
        # 이전 반성 정보 기록
        previous_reflection_details = [
            {
                "event": r.get("event", ""),
                "importance": r.get("importance", 0),
                "days_ago": r.get("days_ago", 0),
                "relevance_score": r.get("relevance_score", 0)
            }
            for r in previous_reflections
        ]
        
        # 시간 측정 데이터 저장
        timing_entry = {
            "date": current_date,
            "agent_name": agent_name,
            "total_time": process_elapsed_time,
            "api_time": api_elapsed_time,
            "memory_count": len(important_memories),
            "memory_details": memory_details,
            "previous_reflection_count": len(previous_reflections),
            "previous_reflection_details": previous_reflection_details,
            "status": ollama_response["status"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.timing_data["batch_reflections"].append(timing_entry)
        self._save_timing_data()
        
        # 7. 결과 객체 구성
        result = {
            "reflections": reflections,
            "count": len(reflections),
            "status": "success" if reflections else "error",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time": process_elapsed_time,
            "api_time": api_elapsed_time,
            "previous_reflections_used": len(previous_reflections)
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
def generate_daily_reflections(agent_name: str, memory_file_path: str, reflection_file_path: str, results_folder: str, 
                               date_str: str = None):
    """
    일일 반성 생성
    
    Parameters:
    - agent_name: 에이전트 이름
    - memory_file_path: 메모리 JSON 파일 경로
    - reflection_file_path: 반성 JSON 파일 경로
    - results_folder: 결과 저장 폴더
    - date_str: 날짜 문자열 (None인 경우 현재 날짜 사용)
    
    Returns:
    - 생성된 반성 데이터
    """
    # 반성 시스템 초기화
    reflection_system = BatchMemoryReflectionSystem(
        memory_file_path=memory_file_path,
        reflection_file_path=reflection_file_path,
        results_folder=results_folder
    )
    
    print("배치 처리 모드에서 반성 생성 중...")
    result = reflection_system.generate_batch_reflections(agent_name, date_str)
    
    # 결과 출력
    if "error" not in result:
        print("\n생성된 반성 목록:")
        for i, reflection in enumerate(result.get("reflections", [])):
            print(f"\n반성 #{i+1}:")
            print(f"  이벤트: {reflection.get('event', '')}")
            print(f"  행동: {reflection.get('action', '')}")
            print(f"  생각: {reflection.get('thought', '')}")
            print(f"  중요도: {reflection.get('importance', 0)}")
            print(f"  생성 시간: {reflection.get('created', '')}")
        
        if result.get("previous_reflections_used", 0) > 0:
            print(f"\n이전 반성 {result.get('previous_reflections_used', 0)}개가 참조되었습니다.")
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
    
    # 대화형 메뉴 표시
    print("\n===== 메모리 기반 반성 생성 시스템 =====")
    
    # 날짜 입력 받기 (선택 사항)
    custom_date = input("\n날짜를 입력하세요 (YYYY.MM.DD, 빈칸=오늘): ")
    date_str = custom_date if custom_date else None
    
    if date_str:
        print(f"\n날짜: {date_str}로 설정되었습니다.")
    else:
        print("\n날짜: 오늘로 설정되었습니다.")
    
    # 에이전트 이름 입력 받기 (선택 사항)
    custom_agent = input("\n에이전트 이름을 입력하세요 (빈칸=John): ")
    if custom_agent:
        agent_name = custom_agent
    
    print(f"\n에이전트: {agent_name}로 설정되었습니다.")
    print("\n==================================")
    
    # 반성 생성
    result = generate_daily_reflections(
        agent_name=agent_name,
        memory_file_path=memory_file_path,
        reflection_file_path=reflection_file_path,
        results_folder=results_folder,
        date_str=date_str
    )
    
    # 성능 결과 요약 출력
    print("\n===== 성능 결과 요약 =====")
    print(f"생성된 반성 수: {result.get('count', 0)}")
    print(f"참조된 이전 반성 수: {result.get('previous_reflections_used', 0)}")
    print(f"총 처리 시간: {result.get('total_time', 0):.2f}초")
    print(f"API 호출 시간: {result.get('api_time', 0):.2f}초")
    
    print("\n프로그램 실행이 완료되었습니다.")