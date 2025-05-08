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
        root_dir = current_dir.parent.parent  # AI 디렉토리
        self.agent_path = root_dir / "agent" / "data" / "agent.json"
        print(f"📁 agent.json 경로: {self.agent_path}")

    def event_to_sentence(self, event_obj: Dict[str, Any]) -> str:
        """
        이벤트 객체를 문장으로 변환
        
        Args:
            event_obj: 이벤트 객체 (event_type만 사용)
        
        Returns:
            str: 변환된 문장
        """
        event_type = event_obj.get("type")
        if not event_type or event_type not in EVENT_SENTENCE_TEMPLATES:
            return "unknown event occurred"
            
        return EVENT_SENTENCE_TEMPLATES[event_type]["example"]

    def get_embedding(self, text: str) -> List[float]:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트
        
        Returns:
            List[float]: 임베딩 벡터
        """
        tokens = [w.lower() for w in text.split() if w.lower() in self.model]
        if not tokens:
            return [0.0] * self.vector_size
        
        # 단어 벡터의 평균을 문장 벡터로 사용
        vector = np.mean([self.model[w] for w in tokens], axis=0)
        return vector.tolist()

    def save_memory(self, event_sentence: str, embedding: List[float], event_time: str, agent_name: str, importance: str = "normal") -> bool:
        """
        메모리를 agent.json에 저장
        
        Args:
            event_sentence: 이벤트 문장
            embedding: 임베딩 벡터
            event_time: 이벤트 시간 (datetime 문자열)
            agent_name: 메모리를 저장할 에이전트 이름
            importance: 중요도 ("high", "normal", "low")
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 기존 데이터 로드
            with open(self.agent_path, 'r', encoding='utf-8') as f:
                agent_data = json.load(f)
            
            # 새 메모리 객체 생성
            new_memory = {
                "event": event_sentence,
                "time": event_time,
                "importance": importance,
                "embeddings": embedding
            }
            
            # 지정된 에이전트의 memories에만 추가
            if agent_name in agent_data:
                agent_data[agent_name]["memories"].append(new_memory)
                print(f"💾 {agent_name}의 메모리 저장 완료")
            else:
                print(f"❌ {agent_name} 에이전트를 찾을 수 없음")
                return False
            
            # 저장
            with open(self.agent_path, 'w', encoding='utf-8') as f:
                json.dump(agent_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"메모리 저장 중 오류 발생: {e}")
            return False 