import json
import os
from typing import List, Dict, Any
import numpy as np
from datetime import datetime
from pathlib import Path
from numpy import dot
from numpy.linalg import norm

class MemoryUtils:
    def __init__(self, word2vec_model):
        # 현재 파일의 절대 경로를 기준으로 상위 디렉토리 찾기
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent.parent  # AI 디렉토리
        agent_dir = root_dir / "agent"
        data_dir = agent_dir / "data"
        
        self.memories_file = str(data_dir / "memories.json")
        self.plans_file = str(data_dir / "plans.json")
        self.reflections_file = str(data_dir / "reflections.json")
        
        # Word2Vec 모델 설정
        self.model = word2vec_model
        
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """필요한 JSON 파일들이 존재하는지 확인하고, 없다면 생성"""
        for file_path in [self.memories_file, self.plans_file, self.reflections_file]:
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    if file_path == self.memories_file:
                        json.dump({"John": {"memories": []}, "Sarah": {"memories": []}}, f, ensure_ascii=False, indent=2)
                    elif file_path == self.reflections_file:
                        json.dump({"John": {"reflections": []}, "Sarah": {"reflections": []}}, f, ensure_ascii=False, indent=2)
                    else:
                        json.dump({"John": [], "Sarah": []}, f, ensure_ascii=False, indent=2)

    def _load_memories(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """메모리 데이터 로드"""
        try:
            with open(self.memories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"메모리 로드 중 오류 발생: {e}")
            return {"John": {"memories": []}, "Sarah": {"memories": []}}

    def _save_memories(self, memories: Dict[str, Dict[str, List[Dict[str, Any]]]]):
        """메모리 데이터 저장"""
        try:
            with open(self.memories_file, 'w', encoding='utf-8') as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"메모리 저장 중 오류 발생: {e}")

    def _load_reflections(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """반성 데이터 로드"""
        try:
            with open(self.reflections_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"반성 데이터 로드 중 오류 발생: {e}")
            return {"John": {"reflections": []}, "Sarah": {"reflections": []}}

    def _save_reflections(self, reflections: Dict[str, Dict[str, List[Dict[str, Any]]]]):
        """반성 데이터 저장"""
        try:
            with open(self.reflections_file, 'w', encoding='utf-8') as f:
                json.dump(reflections, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"반성 데이터 저장 중 오류 발생: {e}")

    def save_memory(self, event_sentence: str, embedding: List[float], event_time: str, agent_name: str):
        """새로운 메모리 저장"""
        memories = self._load_memories()
        
        if agent_name not in memories:
            memories[agent_name] = {"memories": []}
            
        # 현재 시간이 제공되지 않은 경우 현재 시간 사용
        if not event_time:
            event_time = datetime.now().strftime("%Y.%m.%d.%H:%M")
            
        memory = {
            "event": event_sentence,
            "time": event_time,
            "embeddings": embedding
        }
        
        memories[agent_name]["memories"].append(memory)
        self._save_memories(memories)

    def get_embedding(self, text: str) -> List[float]:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트
        
        Returns:
            List[float]: 임베딩 벡터
        """
        # 토큰화 및 소문자 변환
        tokens = [w.lower() for w in text.split() if w.lower() in self.model]
        
        if not tokens:
            return [0.0] * self.model.vector_size
        
        # 단어 벡터의 평균을 문장 벡터로 사용
        word_vectors = [self.model[w] for w in tokens]
        sentence_vector = np.mean(word_vectors, axis=0)
        
        # 정규화
        norm = np.linalg.norm(sentence_vector)
        if norm > 0:
            sentence_vector = sentence_vector / norm
            
        return sentence_vector.tolist()

    def event_to_sentence(self, event: Dict[str, Any]) -> str:
        """이벤트를 문장으로 변환"""
        event_type = event.get("event_type", "")
        location = event.get("event_location", "")
        object = event.get("object", "")
        
        if event_type == "witness":
            return f"witness {object} at {location}"
        elif event_type == "request":
            return f"request {object} at {location}"
        elif event_type == "feel":
            return f"feel {object} at {location}"
        elif event_type == "discover":
            return f"discover {object} at {location}"
        elif event_type == "new_object_type":
            return f"discover new {object} at {location}"
        elif event_type == "new_area":
            return f"discover new {location} area"
        elif event_type == "preferred_object":
            return f"observe favorite {object} at {location}"
        elif event_type == "agent_observation":
            return f"observe {object} at {location}"
        elif event_type == "new_object":
            return f"discover {object} at {location}"
        else:
            return f"{object} at {location}" 