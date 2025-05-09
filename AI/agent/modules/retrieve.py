import json
import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
from pathlib import Path

class Retrieve:
    def __init__(self):
        # 현재 파일의 절대 경로를 기준으로 상위 디렉토리 찾기
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent  # agent 디렉토리
        data_dir = root_dir / "data"
        
        self.memories_file = data_dir / "memories.json"
        
        # data 디렉토리가 없으면 생성
        data_dir.mkdir(exist_ok=True)
        
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """memories.json 파일이 존재하는지 확인하고, 없다면 생성"""
        if not self.memories_file.exists():
            with open(self.memories_file, 'w', encoding='utf-8') as f:
                json.dump({"John": [], "Sarah": []}, f, ensure_ascii=False, indent=2)

    def _load_memories(self) -> Dict[str, List[Dict[str, Any]]]:
        """메모리 데이터 로드"""
        try:
            with open(self.memories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"메모리 로드 중 오류 발생: {e}")
            return {"John": [], "Sarah": []}

    def should_react(self, event: Dict[str, Any]) -> bool:
        """이벤트에 반응해야 하는지 결정"""
        # 현재는 모든 이벤트에 반응
        return True

    def _find_similar_memories(self, event_embedding: List[float], agent_name: str, top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """유사한 메모리 검색"""
        memories = self._load_memories()
        
        if agent_name not in memories or not memories[agent_name]:
            return []
            
        # 코사인 유사도 계산
        similarities = []
        for memory in memories[agent_name]:
            memory_embedding = memory.get("embeddings", [])
            if memory_embedding:
                similarity = self._cosine_similarity(event_embedding, memory_embedding)
                similarities.append((memory, similarity))
        
        # 유사도 기준으로 정렬하고 상위 k개 반환
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """코사인 유사도 계산"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def create_reaction_prompt(self, event_sentence: str, event_embedding: List[float], agent_name: str, prompt_template: str, similar_data_cnt: int = 3, similarity_threshold: float = 0.5) -> Optional[str]:
        """이벤트에 대한 반응을 결정하기 위한 프롬프트 생성"""
        # 반응 여부 결정
        if not self.should_react({"event": event_sentence}):
            return None
        
        # 유사한 메모리 검색
        similar_memories = self._find_similar_memories(event_embedding, agent_name, top_k=similar_data_cnt)
        
        # 유사한 이벤트 문자열 생성 (유사도 기준값 이상인 것만 포함)
        similar_events = []
        for memory, similarity in similar_memories:
            if similarity >= similarity_threshold:
                event = memory.get("event", "")
                if event:
                    similar_events.append(f"- {event}")
        
        similar_event_str = "\n".join(similar_events) if similar_events else "No similar past events found."
        
        # 프롬프트 생성
        try:
            prompt = prompt_template.format(
                AGENT_NAME=agent_name,
                EVENT_CONTENT=event_sentence,
                SIMILAR_EVENT=similar_event_str
            )
            return prompt
        except Exception as e:
            print(f"프롬프트 생성 중 오류 발생: {e}")
            return None 