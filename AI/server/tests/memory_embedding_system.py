"""
OLLAMA를 사용하지 않고 임베딩 -> 임베딩 파일 생성
"""

import json
import gensim.downloader as api
import numpy as np
from numpy import dot
from numpy.linalg import norm
import time
from typing import List, Dict, Any, Tuple
import os


class MemoryEmbeddingSystem:
    def __init__(self, memory_file_path: str, model_name: str = "word2vec-google-news-300"):
        """
        메모리 임베딩 시스템 초기화
        
        Parameters:
        - memory_file_path: 메모리 JSON 파일 경로
        - model_name: 사용할 Word2Vec 모델 이름
        """
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
        
        # 메모리 저장
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
            return {}
    
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
            # 벡터를 리스트로 변환하여 저장 (메모리 용량이 크더라도 개발 단계에서는 편의성 우선)
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
                
                # 임베딩 벡터 생성 - 실제 계산이 일어나는 부분
                embedding_vector = self._get_sentence_vector(combined_text)
                
                # 메모리에 임베딩 벡터 추가
                self.memory_data[agent_name]["memories"][i]["embedding_vector"] = embedding_vector
                
                # 진행 상황 출력 (10개마다)
                if (i + 1) % 10 == 0 or i + 1 == len(memories):
                    print(f"임베딩 생성 진행 중: {i + 1}/{len(memories)}")

    def find_similar_memories(self, query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """
        쿼리와 유사한 메모리 검색
        
        Parameters:
        - query: 검색 쿼리
        - top_k: 반환할 최대 메모리 수
        
        Returns:
        - 유사도 순으로 정렬된 (메모리, 유사도) 튜플 리스트
        """
        start_time = time.time()
        
        # 쿼리 임베딩 생성
        query_vector = self._get_sentence_vector(query)
        query_embedding_time = time.time() - start_time
        print(f"쿼리 임베딩 생성 완료 (소요 시간: {query_embedding_time:.4f}초)")
        
        similarities = []
        
        # 모든 에이전트의 메모리에 대해 유사도 계산
        similarity_start_time = time.time()
        for agent_name, agent_data in self.memory_data.items():
            for memory in agent_data["memories"]:
                # 메모리 임베딩 벡터 가져오기
                memory_vector = memory.get("embedding_vector")
                
                if memory_vector is not None:
                    # 코사인 유사도 계산
                    similarity = self._calculate_cosine_similarity(query_vector, memory_vector)
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
        
        return sorted_similarities[:top_k]


def main():
    """
    메인 함수
    """
    # 메모리 파일 경로
    memory_file_path = "memories.json"
    
    # 메모리 임베딩 시스템 초기화
    memory_system = MemoryEmbeddingSystem(memory_file_path)
    
    # 사용자 입력 처리
    while True:
        query = input("\n검색할 이벤트를 입력하세요 (종료하려면 'exit' 입력): ")
        
        if query.lower() == 'exit':
            break
        
        # 유사한 메모리 검색
        similar_memories = memory_system.find_similar_memories(query)
        
        # 결과 출력
        print("\n=== 검색 결과 ===")
        for i, (memory, similarity) in enumerate(similar_memories):
            print(f"{i+1}. 유사도: {similarity:.4f}")
            print(f"   이벤트: {memory['event']}")
            print(f"   액션: {memory['action']}")
            print()


if __name__ == "__main__":
    main()