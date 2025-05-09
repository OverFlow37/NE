import json
import numpy as np
from datetime import datetime
from pathlib import Path
import gensim.downloader as api
from gensim.models import KeyedVectors
from typing import Dict, Any, List, Optional
import os
import time

# 전역 변수로 모델 저장
_word2vec_model = None

def get_word2vec_model(model_name: str = "word2vec-google-news-300"):
    """
    Word2Vec 모델을 싱글톤으로 관리
    
    Args:
        model_name: 사용할 Word2Vec 모델 이름
    
    Returns:
        Word2Vec 모델
    """
    global _word2vec_model
    if _word2vec_model is None:
        print("\n=== Word2Vec 모델 로딩 시작 ===")
        start_time = time.time()
        
        # 1. Gensim 데이터 디렉토리 확인
        gensim_data_dir = os.path.expanduser("~/.gensim-data")
        if os.name == 'nt':  # Windows
            gensim_data_dir = os.path.join(os.environ['USERPROFILE'], 'gensim-data')
        print(f"📁 Gensim 데이터 디렉토리: {gensim_data_dir}")
        
        # 2. 모델 로드 (api.load는 자동으로 캐시를 사용)
        print("📥 모델 로드 중...")
        load_start = time.time()
        _word2vec_model = api.load(model_name)
        load_time = time.time() - load_start
        print(f"⏱ 모델 로드 시간: {load_time:.2f}초")
        
        # 3. 모델 정보 출력
        print(f"📊 모델 정보:")
        print(f"  - 벡터 크기: {_word2vec_model.vector_size}")
        print(f"  - 어휘 크기: {len(_word2vec_model.key_to_index)}")
        
        total_time = time.time() - start_time
        print(f"✅ 모델 로딩 완료 (총 소요시간: {total_time:.2f}초)")
        
    return _word2vec_model

EVENT_SENTENCE_TEMPLATES = {
    "power_usage": {
        "example": "witness fire power phenomenon at ruins"
    },
    "interaction_request": {
        "example": "request talk with John at square"
    },
    "emotion_change": {
        "example": "feel happy at library"
    },
    "new_object_type": {
        "example": "discover new artifact at temple"
    },
    "new_area": {
        "example": "discover new desert area"
    },
    "preferred_object": {
        "example": "observe favorite book at library"
    },
    "agent_observation": {
        "example": "observe John at square"
    },
    "new_object": {
        "example": "discover potion at lab"
    }
}

class MemoryUtils:
    def __init__(self):
        """
        메모리 유틸리티 초기화
        """
        self.model = get_word2vec_model()
        self.vector_size = self.model.vector_size
        
        # 현재 파일의 절대 경로를 기준으로 상위 디렉토리 찾기
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent  # agent 디렉토리
        data_dir = root_dir / "data"
        
        self.memories_file = data_dir / "memories.json"
        self.plans_file = data_dir / "plans.json"
        self.reflections_file = data_dir / "reflections.json"
        
        # data 디렉토리가 없으면 생성
        data_dir.mkdir(exist_ok=True)
        
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """필요한 JSON 파일들이 존재하는지 확인하고, 없다면 생성"""
        for file_path in [self.memories_file, self.plans_file, self.reflections_file]:
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({"John": [], "Sarah": []}, f, ensure_ascii=False, indent=2)

    def _load_memories(self) -> Dict[str, List[Dict[str, Any]]]:
        """메모리 데이터 로드"""
        try:
            with open(self.memories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"메모리 로드 중 오류 발생: {e}")
            return {"John": [], "Sarah": []}

    def _save_memories(self, memories: Dict[str, List[Dict[str, Any]]]):
        """메모리 데이터 저장"""
        try:
            with open(self.memories_file, 'w', encoding='utf-8') as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"메모리 저장 중 오류 발생: {e}")

    def save_memory(self, event_sentence: str, embedding: List[float], event_time: str, agent_name: str):
        """새로운 메모리 저장"""
        memories = self._load_memories()
        
        if agent_name not in memories:
            memories[agent_name] = []
            
        memory = {
            "event": event_sentence,
            "time": event_time,
            "importance": "normal",
            "embeddings": embedding
        }
        
        memories[agent_name].append(memory)
        self._save_memories(memories)

    def get_embedding(self, text: str) -> List[float]:
        """텍스트의 임베딩 벡터 생성 (임시 구현)"""
        # 실제로는 여기에 임베딩 모델을 사용해야 합니다
        return [0.1] * 384  # 384차원 벡터 반환

    def event_to_sentence(self, event: Dict[str, Any]) -> str:
        """이벤트를 문장으로 변환"""
        event_type = event.get("type", "")
        location = event.get("location", "")
        object_type = event.get("object_type", "")
        
        if event_type == "witness":
            return f"witness {object_type} at {location}"
        elif event_type == "request":
            return f"request {object_type} at {location}"
        elif event_type == "feel":
            return f"feel {object_type} at {location}"
        elif event_type == "discover":
            return f"discover {object_type} at {location}"
        else:
            return f"{event_type} {object_type} at {location}" 