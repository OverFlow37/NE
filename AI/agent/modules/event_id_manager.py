"""
이벤트 ID 관리 모듈

비슷한 이벤트를 그룹화하여 event_id를 관리합니다.
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pathlib import Path
from datetime import datetime

class EventIdManager:
    def __init__(self, memory_utils, similarity_threshold: float = 0.75):
        """
        이벤트 ID 관리자 초기화
        
        Args:
            memory_utils: MemoryUtils 인스턴스
            similarity_threshold: 동일한 이벤트로 간주할 유사도 임계값
        """
        self.memory_utils = memory_utils
        self.similarity_threshold = similarity_threshold
        
        # 현재 파일의 절대 경로를 기준으로 상위 디렉토리 찾기
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent.parent  # AI 디렉토리
        agent_dir = root_dir / "agent"
        data_dir = agent_dir / "data"
        
        self.event_id_file = str(data_dir / "event_ids.json")
        self._ensure_event_id_file_exists()
        
    def _ensure_event_id_file_exists(self):
        """event_ids.json 파일이 존재하는지 확인하고, 없다면 생성"""
        if not os.path.exists(self.event_id_file):
            os.makedirs(os.path.dirname(self.event_id_file), exist_ok=True)
            with open(self.event_id_file, 'w', encoding='utf-8') as f:
                json.dump({"next_id": 1, "agents": {}}, f, ensure_ascii=False, indent=2)
    
    def _load_event_ids(self) -> Dict[str, Any]:
        """이벤트 ID 데이터 로드"""
        try:
            with open(self.event_id_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"이벤트 ID 로드 중 오류 발생: {e}")
            return {"next_id": 1, "agents": {}}
    
    def _save_event_ids(self, event_ids: Dict[str, Any]):
        """이벤트 ID 데이터 저장"""
        try:
            with open(self.event_id_file, 'w', encoding='utf-8') as f:
                json.dump(event_ids, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"이벤트 ID 저장 중 오류 발생: {e}")
    
    def get_event_id(self, event: Dict[str, Any], agent_name: str, game_time: str = None) -> int:
        """
        이벤트에 대한 ID를 가져오거나 새로 생성
        
        Args:
            event: 이벤트 데이터
            agent_name: 에이전트 이름
            game_time: 게임 내 시간 (없으면 현재 시간 사용)
                
        Returns:
            int: 이벤트 ID
        """
        # 이벤트를 문장으로 변환
        event_sentence = self.memory_utils.event_to_sentence(event)
        
        # 임베딩 생성
        event_embedding = self.memory_utils.get_embedding(event_sentence)
        
        # 메모리에서 유사한 이벤트 검색
        event_ids = self._load_event_ids()
        
        if agent_name not in event_ids["agents"]:
            event_ids["agents"][agent_name] = []
        
        # 에이전트의 이벤트 ID 리스트
        agent_event_ids = event_ids["agents"][agent_name]
        
        # 가장 유사한 이벤트 찾기
        max_similarity = 0
        most_similar_id = None
        
        for event_id_data in agent_event_ids:
            embedding = event_id_data.get("embedding", [])
            if not embedding:
                continue
            
            # 코사인 유사도 계산
            similarity = np.dot(event_embedding, embedding) / (
                np.linalg.norm(event_embedding) * np.linalg.norm(embedding)
            )
            
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_id = event_id_data.get("id")
        
        # 유사도가 임계값보다 크면 기존 ID 사용
        if max_similarity >= self.similarity_threshold and most_similar_id is not None:
            print(f"유사한 이벤트 ID 발견: {most_similar_id}, 유사도: {max_similarity:.4f}")
            return most_similar_id
        
        # 새 ID 생성
        new_id = event_ids["next_id"]
        event_ids["next_id"] += 1
        
        # 게임 시간 사용 (없으면 이벤트의 time 필드 사용, 그것도 없으면 현재 시간)
        if not game_time:
            game_time = event.get("time", datetime.now().strftime("%Y.%m.%d.%H:%M"))
        
        # 새 이벤트 ID 데이터 추가
        agent_event_ids.append({
            "id": new_id,
            "event_type": event.get("event_type", ""),
            "object": event.get("object", ""),
            "location": event.get("event_location", ""),
            "embedding": event_embedding,
            "created": game_time  # 게임 시간 사용
        })
        
        # 데이터 저장
        self._save_event_ids(event_ids)
        
        print(f"새 이벤트 ID 생성: {new_id}, 게임 시간: {game_time}")
        return new_id