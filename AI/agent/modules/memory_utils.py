import json
import numpy as np
from datetime import datetime
from pathlib import Path
import gensim.downloader as api
from typing import Dict, Any, List, Optional

class MemoryUtils:
    def __init__(self, model_name: str = "word2vec-google-news-300"):
        """
        메모리 유틸리티 초기화
        
        Args:
            model_name: 사용할 Word2Vec 모델 이름
        """
        self.model = api.load(model_name)
        self.vector_size = self.model.vector_size

    def event_to_sentence(self, event_obj: Dict[str, Any]) -> str:
        """
        이벤트 객체를 문장으로 변환
        
        Args:
            event_obj: 이벤트 객체
                {
                    "type": str,  # 이벤트 타입
                    "subject": str,  # 주체
                    "action": str,  # 행동
                    "object": str,  # 대상
                    "location": str,  # 위치
                    "time": str,  # 시간
                    "emotion": str,  # 감정
                    "importance": str  # 중요도
                }
        
        Returns:
            str: 이벤트를 설명하는 문장
        """
        # TODO: 실제 이벤트 객체 구조에 맞게 수정 필요
        return f"{event_obj.get('subject', '')} {event_obj.get('action', '')} {event_obj.get('object', '')} at {event_obj.get('location', '')}"

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

    def save_memory(self, event_sentence: str, embedding: List[float], event_time: str, importance: str = "normal") -> bool:
        """
        메모리를 agent.json에 저장
        
        Args:
            event_sentence: 이벤트 문장
            embedding: 임베딩 벡터
            event_time: 이벤트 시간 (datetime 문자열)
            importance: 중요도 ("high", "normal", "low")
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # agent.json 파일 경로
            agent_path = Path("AI/agent/data/agent.json")
            
            # 기존 데이터 로드
            with open(agent_path, 'r', encoding='utf-8') as f:
                agent_data = json.load(f)
            
            # 새 메모리 객체 생성
            new_memory = {
                "event": event_sentence,
                "time": event_time,
                "importance": importance,
                "embeddings": embedding
            }
            
            # 각 에이전트의 memories에 추가
            for agent_name in agent_data:
                agent_data[agent_name]["memories"].append(new_memory)
            
            # 저장
            with open(agent_path, 'w', encoding='utf-8') as f:
                json.dump(agent_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"메모리 저장 중 오류 발생: {e}")
            return False 