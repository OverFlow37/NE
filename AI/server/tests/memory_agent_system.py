"""
**20250502 FRI 최종 결과물**
메모리 기반 에이전트 행동 생성 시스템
- 이벤트 유형, 타겟, 위치를 포함한 이벤트 텍스트 구성
- 이벤트 임베딩 및 유사 메모리 검색
- 에이전트 상태와 성격을 고려한 행동 생성
- 게임 내 시간 반영
"""

import os
import json
import time
import numpy as np
import gensim.downloader as api
from numpy import dot
from numpy.linalg import norm
from typing import List, Dict, Any, Tuple
import requests
import datetime
import re

# NumPy 배열을 JSON 직렬화 가능한 형식으로 변환하는 전역 함수
def convert_numpy_to_json_serializable(obj):
    """
    NumPy 배열을 포함한 객체를 JSON 직렬화 가능한 형태로 변환
    
    Parameters:
    - obj: 변환할 객체
    
    Returns:
    - JSON 직렬화 가능한 객체
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_to_json_serializable(item) for item in obj)
    elif hasattr(obj, 'dtype') and hasattr(obj, 'item'):  # np.int32, np.float64 등
        return obj.item()
    else:
        return obj

# Ollama API 설정
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3"
DEFAULT_TIMEOUT = 60  # 기본 타임아웃 60초

# 이벤트 유형 딕셔너리
EVENT_TYPES = {
    "POWER_USAGE_DETECTED": "시야 내에 권능 사용(에이전트가 인식할 수 있는 어떤 것이든)",
    "INTERACTION_REQUEST_RECEIVED": "다른 에이전트의 상호작용 요청",
    "EMOTION_CHANGED": "감정의 변화",
    "DISCOVERY_NEW_OBJECT_TYPE": "에이전트가 처음 보는 종류의 오브젝트 발견",
    "DISCOVERY_NEW_AREA": "새로운 지역 발견",
    "OBSERVE_PREFERRED_OBJECT": "에이전트가 선호하는 오브젝트 관찰(다른 에이전트 포함)",
    "OBSERVE_OTHER_AGENT": "다른 에이전트 관찰",
    "DISCOVERY_NEW_OBJECT_INSTANCE": "에이전트가 처음 보는 오브젝트 발견(오브젝트별로)",
    "DISCOVERY_NEW_OBJECT": "에이전트가 처음 보는 오브젝트 발견"
}

class MemoryAgentSystem:
    def __init__(self, memory_file_path: str, results_folder: str, model_name: str = "word2vec-google-news-300"):
        """
        메모리 기반 에이전트 행동 생성 시스템 초기화
        
        Parameters:
        - memory_file_path: 메모리 JSON 파일 경로
        - results_folder: 결과 저장할 폴더 경로
        - model_name: 사용할 Word2Vec 모델 이름
        """
        self.memory_file_path = memory_file_path
        self.results_folder = results_folder
        
        # 폴더 생성
        os.makedirs(results_folder, exist_ok=True)
        
        # 시간 측정 시작
        start_time = time.time()
        print(f"로딩 시작: Word2Vec 모델 '{model_name}'...")
        
        # Word2Vec 모델 로드
        self.model = api.load(model_name)
        
        # 모델 로딩 시간 출력
        model_load_time = time.time() - start_time
        print(f"모델 로딩 완료 (소요 시간: {model_load_time:.2f}초)")
        
        # 메모리 로드
        start_time = time.time()
        print(f"메모리 로딩 중: {memory_file_path}...")
        self.memory_data = self._load_memory(memory_file_path)
        
        # 메모리 로딩 시간 출력
        memory_load_time = time.time() - start_time
        print(f"메모리 로드 완료 (소요 시간: {memory_load_time:.2f}초)")
        
        # 메모리 중복 제거
        self._remove_duplicates()
        
        # 메모리에 임베딩 추가
        start_time = time.time()
        print("메모리 임베딩 생성 중...")
        self._add_embeddings_to_memories()
        
        # 임베딩 생성 시간 출력
        embedding_time = time.time() - start_time
        print(f"임베딩 생성 완료 (소요 시간: {embedding_time:.2f}초)")
        
        # 임베딩이 추가된 메모리 저장
        output_path = os.path.splitext(memory_file_path)[0] + "_with_embeddings.json"
        self._save_memory_with_embeddings(output_path)

    def _load_memory(self, memory_file_path: str) -> Dict:
        """
        메모리 파일 로드
        
        Parameters:
        - memory_file_path: 메모리 JSON 파일 경로
        
        Returns:
        - 메모리 데이터
        """
        try:
            with open(memory_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"메모리 파일 로드 오류: {e}")
            # 파일이 없거나 손상된 경우 빈 메모리 구조 생성
            return {"John": {"memories": []}}
    
    def _remove_duplicates(self):
        """메모리에서 중복된 이벤트-액션 쌍 제거"""
        for agent_name, agent_data in self.memory_data.items():
            # 중복 체크를 위한 집합
            seen_events = set()
            unique_memories = []
            
            for memory in agent_data["memories"]:
                # 이벤트와 액션을 결합하여 중복 체크
                event_action_pair = (memory["event"], memory["action"])
                
                if event_action_pair not in seen_events:
                    seen_events.add(event_action_pair)
                    unique_memories.append(memory)
            
            # 중복이 제거된 메모리로 업데이트
            self.memory_data[agent_name]["memories"] = unique_memories
            
            print(f"중복 제거: {len(agent_data['memories']) - len(unique_memories)}개 중복 메모리 제거됨")

    def _save_memory_with_embeddings(self, output_path: str):
        """
        임베딩이 추가된 메모리 저장
        
        Parameters:
        - output_path: 저장할 파일 경로
        """
        try:
            # 임베딩 벡터는 ndarray이므로 JSON으로 직접 저장할 수 없음
            # 벡터를 리스트로 변환하여 저장
            serializable_data = {}
            
            for agent_name, agent_data in self.memory_data.items():
                serializable_data[agent_name] = {"memories": []}
                
                for memory in agent_data["memories"]:
                    memory_copy = memory.copy()
                    # 임베딩 벡터를 리스트로 변환
                    if "embedding_vector" in memory_copy:
                        memory_copy["embedding"] = memory_copy["embedding_vector"].tolist()
                        del memory_copy["embedding_vector"]
                    serializable_data[agent_name]["memories"].append(memory_copy)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            
            print(f"임베딩이 추가된 메모리 저장 완료: {output_path}")
        except Exception as e:
            print(f"메모리 저장 오류: {e}")

    def _get_sentence_vector(self, sentence: str) -> np.ndarray:
        """
        문장을 임베딩 벡터로 변환
        
        Parameters:
        - sentence: 임베딩할 문장
        
        Returns:
        - 문장 임베딩 벡터
        """
        tokens = [w.lower() for w in sentence.split() if w.lower() in self.model]
        if not tokens:
            print(f"경고: '{sentence}'에서 모델에 존재하는 단어를 찾을 수 없습니다.")
            return np.zeros(self.model.vector_size)
        
        # 단어 벡터의 평균을 문장 벡터로 사용
        return np.mean([self.model[w] for w in tokens], axis=0)

    def _calculate_cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """
        두 벡터 간의 코사인 유사도 계산
        
        Parameters:
        - v1: 첫 번째 벡터
        - v2: 두 번째 벡터
        
        Returns:
        - 코사인 유사도 (0~1 사이 값)
        """
        if np.all(v1 == 0) or np.all(v2 == 0):
            return 0.0
        return float(dot(v1, v2) / (norm(v1) * norm(v2)))

    def _add_embeddings_to_memories(self):
        """
        모든 메모리에 임베딩 추가
        """
        total_memories = 0
        
        for agent_name, agent_data in self.memory_data.items():
            memories = agent_data["memories"]
            total_memories += len(memories)
            
            for i, memory in enumerate(memories):
                # event와 action을 합쳐서 임베딩 생성
                combined_text = f"{memory['event']} {memory['action']}"
                
                # 임베딩 벡터 생성
                embedding_vector = self._get_sentence_vector(combined_text)
                
                # 메모리에 임베딩 벡터 추가
                self.memory_data[agent_name]["memories"][i]["embedding_vector"] = embedding_vector
                
                # 진행 상황 출력 (10개마다)
                if (i + 1) % 10 == 0 or i + 1 == len(memories):
                    print(f"임베딩 생성 진행 중: {i + 1}/{len(memories)}")

    def create_event_text(self, agent_data: Dict) -> str:
        """
        입력 데이터에서 이벤트 텍스트 생성
        
        Parameters:
        - agent_data: 에이전트 데이터 (입력 JSON)
        
        Returns:
        - 이벤트 텍스트
        """
        agent_info = agent_data.get("agent", {})
        event_type = agent_info.get("event", "")
        target = agent_info.get("target", "")
        section = agent_info.get("section", "")
        location = agent_info.get("location", "")
        
        # 이벤트 텍스트 형식: "이벤트유형 타겟 섹션 위치"
        event_text = f"{event_type} {target} {section} {location}"
        print(f"생성된 이벤트 텍스트: {event_text}")
        
        return event_text

    def find_similar_memories(self, event_text: str, top_k: int = 5, similarity_threshold: float = 0.3) -> List[Tuple[Dict, float]]:
        """
        이벤트와 유사한 메모리 검색
        
        Parameters:
        - event_text: 이벤트 텍스트
        - top_k: 반환할 최대 메모리 수
        - similarity_threshold: 유사도 임계값 (이보다 낮은 유사도는 제외)
        
        Returns:
        - 유사도 순으로 정렬된 (메모리, 유사도) 튜플 리스트
        """
        start_time = time.time()
        
        # 이벤트 임베딩 생성
        event_vector = self._get_sentence_vector(event_text)
        event_embedding_time = time.time() - start_time
        print(f"이벤트 임베딩 생성 완료 (소요 시간: {event_embedding_time:.4f}초)")
        
        similarities = []
        
        # 모든 에이전트의 메모리에 대해 유사도 계산
        similarity_start_time = time.time()
        for agent_name, agent_data in self.memory_data.items():
            for memory in agent_data["memories"]:
                # 메모리 임베딩 벡터 가져오기
                memory_vector = memory.get("embedding_vector")
                
                if memory_vector is not None:
                    # 코사인 유사도 계산
                    similarity = self._calculate_cosine_similarity(event_vector, memory_vector)
                    if similarity >= similarity_threshold:
                        similarities.append((memory, similarity))
        
        similarity_time = time.time() - similarity_start_time
        print(f"유사도 계산 완료 (소요 시간: {similarity_time:.4f}초)")
        
        # 유사도 기준 내림차순 정렬
        sort_start_time = time.time()
        sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
        sort_time = time.time() - sort_start_time
        print(f"정렬 완료 (소요 시간: {sort_time:.4f}초)")
        
        # 상위 k개 반환
        total_time = time.time() - start_time
        print(f"전체 검색 완료 (소요 시간: {total_time:.4f}초)")
        
        # 결과 요약 출력
        print(f"검색된 유사 메모리 수: {len(sorted_similarities)}")
        if sorted_similarities:
            print(f"최고 유사도: {sorted_similarities[0][1]:.4f}")
        
        # 유사도가 임계값 이상인 결과 중 상위 k개 반환
        return sorted_similarities[:top_k]

    def create_prompt(self, agent_data: Dict, similar_memories: List[Tuple[Dict, float]]) -> str:
        """
        행동 생성을 위한 프롬프트 생성
        
        Parameters:
        - agent_data: 에이전트 데이터 (입력 JSON)
        - similar_memories: 유사한 메모리 리스트
        
        Returns:
        - 프롬프트 텍스트
        """
        agent_info = agent_data.get("agent", {})
        agent_name = agent_info.get("name", "")
        state = agent_info.get("state", {})
        event_type = agent_info.get("event", "")
        target = agent_info.get("target", "")
        section = agent_info.get("section", "")
        location = agent_info.get("location", "")
        personality = agent_info.get("personality", "")
        game_date = agent_info.get("date", "")
        game_time = agent_info.get("time", "")
        
        # 프롬프트 기본 구조 생성
        prompt = f"""
AGENT DATA:
Name: {agent_name}
State:
  - Hunger: {state.get('hunger', 0)}
  - Sleepiness: {state.get('sleepiness', 0)}
  - Loneliness: {state.get('loneliness', 0)}
Location: {section}, {location}
Date and Time: {game_date} {game_time}
Personality: {personality}

EVENT:
Type: {event_type}
Target: {target}

VISIBLE OBJECTS:
"""
        
        # 보이는 객체 정보 추가
        visible_objects = agent_info.get("visible_objects", {}).get("sections", [])
        for section_info in visible_objects:
            section_name = section_info.get("section_name", "")
            prompt += f"Section: {section_name}\n"
            
            for location_info in section_info.get("locations", []):
                loc_name = location_info.get("location", "")
                objects = location_info.get("objects", [])
                prompt += f"  Location: {loc_name}\n"
                prompt += f"    Objects: {', '.join(objects)}\n"
        
        # 주변 에이전트 정보 추가
        nearby_agents = agent_info.get("nearby_agents", [])
        prompt += "\nNEARBY AGENTS:\n"
        if nearby_agents:
            for nearby_agent in nearby_agents:
                prompt += f"  - {nearby_agent}\n"
        else:
            prompt += "  None\n"
        
        # 유사 메모리 정보 추가
        prompt += "\nRELEVANT MEMORIES:\n"
        if similar_memories:
            for i, (memory, similarity) in enumerate(similar_memories):
                prompt += f"{i+1}. Event: \"{memory.get('event', '')}\"\n"
                prompt += f"   Action: \"{memory.get('action', '')}\"\n"
                prompt += f"   Similarity: {similarity:.4f}\n\n"
        else:
            prompt += "No relevant memories found.\n\n"
        
        # 이벤트 유형 설명 추가
        event_desc = EVENT_TYPES.get(event_type, "알 수 없는 이벤트 유형")
        prompt += f"\nEVENT DESCRIPTION:\n{event_type} - {event_desc}\n\n"
        
        # 행동 생성 요청
        prompt += f"""
TASK:
Determine the appropriate action for the agent based on the current event, agent state, and similar memories.

OUTPUT FORMAT (provide ONLY valid JSON):
{{
    "action":{{
        "agent": "{agent_name}",
        "action": "action_type",
        "details": {{
            "section": "section_name",
            "location": "location_name",
            "target": "object_or_agent"
        }}
    }},
    "memory_update": {{
        "action": "with_whom_and_where_action_took_place",
        "time": "{game_time}", 
        "importance": importance_rating
    }},
    "reason": "Detailed explanation of why this action was chosen based on state, personality, etc."
}}

IMPORTANCE RATING GUIDELINES:
- 1-3: Solo everyday activities with little impact
- 4-7: Interactions with other agents or moderate impact activities
- 8-10: Major events with significant future impact

REASONING GUIDELINES:
- Consider the agent's current state (hunger, sleepiness, loneliness)
- Factor in the agent's personality traits
- Reference similar memories when relevant
- Explain your reasoning in detail
- Provide a natural and context-appropriate response
"""
        
        return prompt

    def call_ollama(self, prompt: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
        """
        Ollama API 호출
        
        Parameters:
        - prompt: 프롬프트 텍스트
        - timeout: 타임아웃 시간(초)
        
        Returns:
        - API 응답
        """
        start_time = time.time()
        
        # API 요청 구성
        payload = {
            "model": MODEL,
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
            response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
            
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

    def process_agent_data(self, agent_data: Dict) -> Dict:
        """
        에이전트 데이터 처리 및 행동 생성
        
        Parameters:
        - agent_data: 에이전트 데이터 (입력 JSON)
        
        Returns:
        - 처리 결과
        """
        # 1. 이벤트 텍스트 생성
        event_text = self.create_event_text(agent_data)
        
        # 2. 이벤트 텍스트 임베딩 및 유사 메모리 검색
        similar_memories = self.find_similar_memories(event_text, top_k=5)
        
        # 3. 프롬프트 생성
        prompt = self.create_prompt(agent_data, similar_memories)
        
        # 4. Ollama API 호출
        print("행동 생성을 위한 Ollama API 호출 중...")
        ollama_response = self.call_ollama(prompt)
        
        # 결과 처리
        if ollama_response["status"] == "success":
            # 결과 추출
            response_text = ollama_response["response"]
            json_data = self.extract_json_from_response(response_text)
            
            # 게임 시간 가져오기
            game_date = agent_data.get("agent", {}).get("date", "")
            game_time = agent_data.get("agent", {}).get("time", "")
            formatted_game_time = f"{game_date} {game_time}"
            
            # 결과 데이터에 시간 추가
            if "memory_update" in json_data and "time" in json_data["memory_update"]:
                time_value = json_data["memory_update"]["time"]
                if time_value == "{current_time}" or time_value == "current_time" or time_value == "{game_time}" or time_value == "game_time":
                    json_data["memory_update"]["time"] = formatted_game_time

            # 결과 객체 구성
            result = {
                "agent_data": agent_data,
                "event_text": event_text,
                "similar_memories": [(memory, float(similarity)) for memory, similarity in similar_memories],
                "action_result": json_data,
                "original_response": response_text,
                "elapsed_time": ollama_response["elapsed_time"],
                "status": ollama_response["status"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 결과 저장
            self._save_result(result)
            
            return result
        else:
            print(f"Ollama API 호출 오류: {ollama_response['status']}")
            print(f"응답: {ollama_response['response']}")
            
            return {
                "status": "error",
                "error_message": ollama_response["response"]
            }

        
    # _save_result 메서드 수정 버전
    def _save_result(self, result: Dict):
        """
        결과 저장
        
        Parameters:
        - result: 처리 결과
        
        Returns:
        - 저장된 파일 경로
        """
        # 결과 파일 경로 생성
        agent_name = result.get("agent_data", {}).get("agent", {}).get("name", "unknown")
        event_type = result.get("agent_data", {}).get("agent", {}).get("event", "unknown")
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        filename = f"{agent_name}_{event_type}_{timestamp}.json"
        filepath = os.path.join(self.results_folder, filename)
        debug_filepath = os.path.join(self.results_folder, f"debug_{filename}")
        
        # 필요한 데이터만 최종 결과로 추출
        action_result = result.get("action_result", {})
        
        # 현재 시간 생성
        current_time = datetime.datetime.now().strftime("%H:%M, Day %d")
        
        # 최종 결과 데이터 구성
        final_result = {}
        
        # 입력 데이터의 JSON 구조에 맞게 결과 구성
        if action_result:
            final_result = {
                "action": action_result.get("action", {}),
                "memory_update": action_result.get("memory_update", {}),
                "reason": action_result.get("reason", "")
            }
            
        # 현재 시간 적용
        if "memory_update" in final_result and "time" in final_result["memory_update"]:
            time_value = final_result["memory_update"]["time"]
            if time_value == "{current_time}" or time_value == "current_time" or time_value == "{game_time}" or time_value == "game_time":
                final_result["memory_update"]["time"] = current_time
        
        # 최종 결과 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        # NumPy 배열을 리스트로 변환 (전역 함수 사용)
        serializable_result = convert_numpy_to_json_serializable(result)
        
        # 디버깅용 전체 결과 저장
        with open(debug_filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        print(f"결과 저장 완료: {filepath}")
        
        # 행동 결과 정보 출력
        if "action" in final_result:
            action = final_result["action"]
            print("\n생성된 행동:")
            print(f"  에이전트: {action.get('agent', '')}")
            print(f"  행동 유형: {action.get('action', '')}")
            print(f"  대상: {action.get('details', {}).get('target', '')}")
            print(f"  위치: {action.get('details', {}).get('section', '')}, {action.get('details', {}).get('location', '')}")
            print(f"  이유: {final_result.get('reason', '')}")
        
        return filepath


    def update_memory(self, result: Dict):
        """
        메모리 업데이트
        
        Parameters:
        - result: 처리 결과
        """
        # 행동 결과 추출
        action_result = result.get("action_result", {})
        agent_data = result.get("agent_data", {}).get("agent", {})
        
        if not action_result or "action" not in action_result:
            print("행동 결과가 없어 메모리를 업데이트할 수 없습니다.")
            return
        
        # 메모리 업데이트 정보 추출
        agent_name = agent_data.get("name", "")
        event = f"{agent_data.get('event', '')} {agent_data.get('target', '')}"
        action_info = action_result.get("action", {})
        action_type = action_info.get("action", "")
        details = action_info.get("details", {})
        section = details.get("section", "")
        location = details.get("location", "")
        target = details.get("target", "")
        
        # 액션 텍스트 구성
        action_text = f"{action_type} {target} {section} {location}"
        
        # 새로운 메모리 항목 생성
        new_memory = {
            "event": event,
            "action": action_text,
            "time": action_result.get("memory_update", {}).get("time", ""),
            "importance": action_result.get("memory_update", {}).get("importance", 1)
        }
        
        # 임베딩 벡터 생성
        combined_text = f"{event} {action_text}"
        embedding_vector = self._get_sentence_vector(combined_text)
        new_memory["embedding_vector"] = embedding_vector
        
        # 메모리 데이터에 추가
        if agent_name in self.memory_data:
            self.memory_data[agent_name]["memories"].append(new_memory)
        else:
            self.memory_data[agent_name] = {"memories": [new_memory]}
        
        print(f"메모리 업데이트 완료: {event} -> {action_text}")
        
        # 업데이트된 메모리 저장
        output_path = os.path.splitext(self.memory_file_path)[0] + "_updated.json"
        self._save_memory_with_embeddings(output_path)
        
        return True


    # 메인 함수
def process_agent_input(input_data: Dict, memory_file_path: str = "memories.json", results_folder: str = "results"):
    """
    에이전트 입력 데이터 처리
    
    Parameters:
    - input_data: 입력 JSON 데이터
    - memory_file_path: 메모리 파일 경로
    - results_folder: 결과 저장 폴더
    
    Returns:
    - 처리 결과
    """
    # 메모리 에이전트 시스템 초기화
    agent_system = MemoryAgentSystem(memory_file_path, results_folder)
    
    # 에이전트 데이터 처리
    result = agent_system.process_agent_data(input_data)
    
    # 메모리 업데이트
    if result.get("status") != "error":
        agent_system.update_memory(result)
    
    # 필요한 데이터만 최종 결과로 추출
    action_result = result.get("action_result", {})
    
    # 최종 결과 데이터 구성
    final_result = {}
    
    # 입력 데이터의 JSON 구조에 맞게 결과 구성
    if action_result:
        final_result = {
            "action": action_result.get("action", {}),
            "memory_update": action_result.get("memory_update", {}),
            "reason": action_result.get("reason", "")
        }
    
    return final_result


# 만약 이 파일이 직접 실행된다면
if __name__ == "__main__":
    # 예제 입력 데이터
    example_input = {
        "agent": {
            "name": "John",
            "state": {
                "hunger": 9,
                "sleepiness": 2,
                "loneliness": 3
            },
            "section": "east_forest",
            "location": "forest",
            "date": "Day 1",
            "time": "14:30",
            "personality": "introverted, practical, punctual",
            "event": "DISCOVERY_NEW_OBJECT_INSTANCE",
            "target": "Raspberry",
            "visible_objects": {
                "sections": [
                    {
                        "section_name": "east_forest",
                        "locations": [
                            {
                                "location": "forest_entrance",
                                "objects": ["oak_tree", "apple"]
                            },
                            {
                                "location": "deep_forest",
                                "objects": ["acorn", "mushroom"]
                            }
                        ]
                    }
                ]
            },
            "nearby_agents": []
        }
    }
    
    # 입력 데이터 처리
    result = process_agent_input(example_input)
    
    # 결과 출력
    print("\n처리 결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))