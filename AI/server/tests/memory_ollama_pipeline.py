"""
20250430 WED 최종 결과물
메모리 임베딩 기반 Ollama 파이프라인
- event_list 파일에서 이벤트 읽기
- 메모리 임베딩 생성 및 유사도 기반 검색
- 유사 메모리를 프롬프트와 결합
- gemma3 모델을 사용한 액션 생성
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

# Ollama API 설정
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3"
DEFAULT_TIMEOUT = 60  # 기본 타임아웃 60초

class MemoryOllamaPipeline:
    def __init__(self, memory_file_path: str, event_folder: str, prompt_folder: str, results_folder: str, model_name: str = "word2vec-google-news-300"):
        """
        메모리 기반 Ollama 파이프라인 초기화
        
        Parameters:
        - memory_file_path: 메모리 JSON 파일 경로
        - event_folder: 이벤트 파일이 있는 폴더 경로
        - prompt_folder: 프롬프트 파일이 있는 폴더 경로
        - results_folder: 결과 저장할 폴더 경로
        - model_name: 사용할 Word2Vec 모델 이름
        """
        self.memory_file_path = memory_file_path
        self.event_folder = event_folder
        self.prompt_folder = prompt_folder
        self.results_folder = results_folder
        
        # 필요한 폴더 생성
        os.makedirs(event_folder, exist_ok=True)
        os.makedirs(prompt_folder, exist_ok=True)
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
        
        # 샘플 이벤트 파일 생성 (폴더가 비어있을 경우)
        if not os.listdir(event_folder):
            self._create_sample_events()

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

    def _create_sample_events(self):
        """이벤트 폴더에 샘플 이벤트 파일 생성"""
        sample_events = [
            ("event1.txt", "I'm very hungry"),
            ("event2.txt", "Saw a food advertisement on TV."),
            ("event3.txt", "Lying on the bed.")
        ]
        
        for filename, content in sample_events:
            file_path = os.path.join(self.event_folder, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"샘플 이벤트 파일 생성 완료: {', '.join([name for name, _ in sample_events])}")

    def find_similar_memories(self, event_text: str, top_k: int = 20, similarity_threshold: float = 0.5) -> List[Tuple[Dict, float]]:
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
        
        # 유사도가 임계값 이상인 결과만 반환
        return sorted_similarities[:top_k]

    def load_file(self, file_path: str) -> str:
        """
        파일 로드 (이벤트 또는 프롬프트)
        
        Parameters:
        - file_path: 파일 경로
        
        Returns:
        - 파일 내용
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (FileNotFoundError, UnicodeDecodeError) as e:
            print(f"파일 로드 오류: {e}")
            return ""

    def create_ollama_prompt(self, prompt_text: str, event_text: str, relevant_memories: List[Tuple[Dict, float]], k: int) -> str:
        """
        Ollama API에 보낼 프롬프트 생성
        
        Parameters:
        - prompt_text: 원본 프롬프트 내용
        - event_text: 이벤트 텍스트
        - relevant_memories: 관련 메모리 리스트 (메모리, 유사도)
        - k: 포함할 메모리 수
        
        Returns:
        - Ollama용 프롬프트
        """
        # 원본 프롬프트 내용
        prompt = prompt_text
        
        # 관련 메모리를 포함하는 경우
        if relevant_memories and k > 0:
            # 유사도 임계값 이상인 상위 k개 메모리 선택
            selected_memories = relevant_memories[:k]
            
            # 메모리 정보 조합
            memory_section = "\n\nRELEVANT MEMORIES:\n"
            for i, (memory, similarity) in enumerate(selected_memories):
                memory_section += f"{i+1}. Event: \"{memory['event']}\"\n"
                memory_section += f"   Action: \"{memory['action']}\"\n"
                memory_section += f"   Similarity: {similarity:.4f}\n\n"
            
            # 메모리 정보를 프롬프트에 추가
            # TASK 섹션 전에 메모리 정보 삽입
            task_pos = prompt.find("TASK:")
            if task_pos > 0:
                prompt = prompt[:task_pos] + memory_section + prompt[task_pos:]
            else:
                # TASK 섹션이 없으면 끝에 추가
                prompt += memory_section
            
            # 현재 이벤트 정보 추가
            event_section = "\n\nCURRENT EVENT:\n" + event_text + "\n\n"
            task_pos = prompt.find("TASK:")
            if task_pos > 0:
                prompt = prompt[:task_pos] + event_section + prompt[task_pos:]
            else:
                # TASK 섹션이 없으면 끝에 추가
                prompt += event_section
        
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

    def process_event_prompt_pair(self, event_file: str, prompt_file: str):
        """
        이벤트와 프롬프트 파일 쌍 처리
        
        Parameters:
        - event_file: 이벤트 파일 이름
        - prompt_file: 프롬프트 파일 이름
        """
        event_path = os.path.join(self.event_folder, event_file)
        prompt_path = os.path.join(self.prompt_folder, prompt_file)
        
        print(f"\n이벤트 파일 처리 중: {event_file} with 프롬프트: {prompt_file}")
        
        # 이벤트와 프롬프트 로드
        event_text = self.load_file(event_path)
        prompt_text = self.load_file(prompt_path)
        
        if not event_text or not prompt_text:
            print(f"경고: 이벤트 또는 프롬프트 파일이 비어있거나 로드할 수 없습니다.")
            return
        
        # 이벤트 텍스트를 쿼리로 사용하여 유사 메모리 검색
        similar_memories = self.find_similar_memories(event_text, top_k=20)
        
        # 각 k 값(1, 5, 10, 15, 20)에 대해 Ollama API 호출
        k_values = [1, 5, 10, 15, 20]
        
        for k in k_values:
            if k <= len(similar_memories):
                print(f"\n상위 {k}개 메모리 사용하여 액션 생성:")
                
                # Ollama용 프롬프트 생성
                ollama_prompt = self.create_ollama_prompt(prompt_text, event_text, similar_memories[:k], k)
                
                # 프롬프트 저장 (디버깅용)
                base_event_name = os.path.splitext(event_file)[0]
                base_prompt_name = os.path.splitext(prompt_file)[0]
                prompt_filename = f"{base_event_name}_{base_prompt_name}_top{k}.txt"
                prompt_path = os.path.join(self.results_folder, prompt_filename)
                with open(prompt_path, 'w', encoding='utf-8') as f:
                    f.write(ollama_prompt)
                
                # Ollama API 호출
                ollama_response = self.call_ollama(ollama_prompt)
                
                if ollama_response["status"] == "success":
                    # 결과 추출
                    response_text = ollama_response["response"]
                    json_data = self.extract_json_from_response(response_text)
                    
                    # 결과 파일 저장
                    output_filename = f"{base_event_name}_{base_prompt_name}_top{k}.json"
                    output_path = os.path.join(self.results_folder, output_filename)
                    
                    # 결과 객체 구성
                    result = {
                        "original_response": response_text,
                        "parsed_json": json_data,
                        "elapsed_time": ollama_response["elapsed_time"],
                        "status": ollama_response["status"],
                        "k_value": k,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 결과 저장
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    print(f"결과 저장 완료: {output_path}")
                    print(f"소요 시간: {ollama_response['elapsed_time']:.2f}초")
                else:
                    print(f"Ollama API 호출 오류: {ollama_response['status']}")
                    print(f"응답: {ollama_response['response']}")

    def process_all_events(self):
        """
        이벤트 폴더의 모든 이벤트 파일과 프롬프트 폴더의 모든 프롬프트 파일을 조합하여 처리
        """
        # 이벤트 폴더 내 모든 텍스트 파일 검색
        event_files = [f for f in os.listdir(self.event_folder) if f.endswith('.txt')]
        
        # 프롬프트 폴더 내 모든 텍스트 파일 검색
        prompt_files = [f for f in os.listdir(self.prompt_folder) if f.endswith('.txt')]
        
        if not event_files:
            print(f"경고: {self.event_folder} 폴더에 이벤트 파일이 없습니다.")
            return
        
        if not prompt_files:
            print(f"경고: {self.prompt_folder} 폴더에 프롬프트 파일이 없습니다.")
            return
        
        print(f"{len(event_files)}개의 이벤트 파일과 {len(prompt_files)}개의 프롬프트 파일을 조합하여 처리합니다.")
        
        # 모든 이벤트-프롬프트 조합 처리
        for event_file in event_files:
            for prompt_file in prompt_files:
                self.process_event_prompt_pair(event_file, prompt_file)


def main():
    """
    메인 함수
    """
    # 메모리 파일 경로
    memory_file_path = "memories.json"
    
    # 이벤트 폴더 경로
    event_folder = "event_list"
    
    # 프롬프트 폴더 경로
    prompt_folder = "temp_prompt"
    
    # 결과 저장 폴더
    results_folder = "ollama_results"
    
    # 메모리 임베딩 시스템 초기화
    pipeline = MemoryOllamaPipeline(memory_file_path, event_folder, prompt_folder, results_folder)
    
    # 모든 이벤트-프롬프트 조합 처리
    pipeline.process_all_events()


if __name__ == "__main__":
    main()