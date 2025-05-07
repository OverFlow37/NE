import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

class Retrieve:
    def __init__(self):
        """
        Retrieve 모듈 초기화
        """
        self.agent_path = Path("AI/agent/data/agent.json")

    def should_react(self, event_obj: Dict[str, Any]) -> bool:
        """
        이벤트에 반응할지 결정
        
        Args:
            event_obj: 이벤트 객체
        
        Returns:
            bool: 반응 여부
        """
        # TODO: 실제 반응 기준 구현 필요
        return True

    def _calculate_cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """
        두 벡터 간의 코사인 유사도 계산
        
        Args:
            v1: 첫 번째 벡터
            v2: 두 번째 벡터
        
        Returns:
            float: 코사인 유사도 (0~1 사이 값)
        """
        v1_array = np.array(v1)
        v2_array = np.array(v2)
        
        if np.all(v1_array == 0) or np.all(v2_array == 0):
            return 0.0
            
        return float(np.dot(v1_array, v2_array) / (np.linalg.norm(v1_array) * np.linalg.norm(v2_array)))

    def _find_similar_memories(self, event_embedding: List[float], agent_name: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        특정 에이전트의 메모리에서 이벤트와 유사한 메모리 검색
        
        Args:
            event_embedding: 이벤트 임베딩 벡터
            agent_name: 검색할 에이전트 이름
            top_k: 반환할 최대 메모리 수
        
        Returns:
            List[Tuple[Dict, float]]: 유사도 순으로 정렬된 (메모리, 유사도) 튜플 리스트
        """
        try:
            with open(self.agent_path, 'r', encoding='utf-8') as f:
                agent_data = json.load(f)
            
            similarities = []
            
            # 특정 에이전트의 메모리에 대해서만 유사도 계산
            if agent_name in agent_data:
                for memory in agent_data[agent_name].get("memories", []):
                    if "embeddings" in memory:
                        similarity = self._calculate_cosine_similarity(
                            event_embedding,
                            memory["embeddings"]
                        )
                        similarities.append((memory, similarity))
            
            # 유사도 기준 내림차순 정렬
            sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
            
            return sorted_similarities[:top_k]
            
        except Exception as e:
            print(f"유사 메모리 검색 중 오류 발생: {e}")
            return []

    def create_reaction_prompt(self, event_obj: Dict[str, Any], event_embedding: List[float], agent_name: str) -> Optional[str]:
        """
        이벤트에 대한 반응을 결정하기 위한 프롬프트 생성
        
        Args:
            event_obj: 이벤트 객체
            event_embedding: 이벤트 임베딩 벡터
            agent_name: 검색할 에이전트 이름
        
        Returns:
            Optional[str]: 생성된 프롬프트
        """
        # 반응 여부 결정
        if not self.should_react(event_obj):
            return None
        
        # 유사한 메모리 검색
        similar_memories = self._find_similar_memories(event_embedding, agent_name)
        
        # 프롬프트 생성
        prompt = "Based on the following event and similar past memories, decide how to react:\n\n"
        
        # 현재 이벤트 정보 추가
        prompt += "CURRENT EVENT:\n"
        prompt += f"Event: {event_obj}\n\n"
        
        # 유사한 메모리 정보 추가 (이벤트 내용만)
        if similar_memories:
            prompt += "SIMILAR PAST MEMORIES:\n"
            for i, (memory, _) in enumerate(similar_memories, 1):
                prompt += f"{i}. {memory['event']}\n"
            prompt += "\n"
        
        # 응답 형식 지정
        prompt += "Please provide your response in the following JSON format:\n"
        prompt += '{\n  "action": "string",\n  "reason": "string",\n  "emotion": "string"\n}'
        
        return prompt 