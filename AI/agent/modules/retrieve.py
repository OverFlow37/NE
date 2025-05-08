import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

class Retrieve:
    def __init__(self):
        """
        Retrieve 모듈 초기화
        """
        # 현재 파일의 절대 경로를 기준으로 상위 디렉토리 찾기
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent.parent  # AI 디렉토리
        self.agent_path = root_dir / "agent" / "data" / "agent.json"
        print(f"📁 agent.json 경로: {self.agent_path}")

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
            if not self.agent_path.exists():
                print("❌ 메모리 파일이 존재하지 않습니다.")
                return []
                
            with open(self.agent_path, 'r', encoding='utf-8') as f:
                memories_data = json.load(f)
            
            similarities = []
            # 모든 메모리에 대해 유사도 계산
            for memory in memories_data[agent_name]["memories"]:
                if "embeddings" in memory:
                    similarity = self._calculate_cosine_similarity(
                        event_embedding,
                        memory["embeddings"]
                    )
                    similarities.append((memory, similarity))
            
            # 유사도 기준 내림차순 정렬
            sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
            
            print(f"🔍 유사 메모리 검색 결과: {len(sorted_similarities)}개 발견")
            for memory, similarity in sorted_similarities[:top_k]:
                print(f"  - 유사도: {similarity:.3f}, 이벤트: {memory.get('event', '')}")
            
            return sorted_similarities[:top_k]
            
        except Exception as e:
            print(f"❌ 유사 메모리 검색 중 오류 발생: {e}")
            return []

    def create_reaction_prompt(self, event_sentence: str, event_embedding: List[float], agent_name: str, prompt_template: str, similar_data_cnt: int = 3, similarity_threshold: float = 0.5) -> Optional[str]:
        """
        이벤트에 대한 반응을 결정하기 위한 프롬프트 생성
        
        Args:
            event_sentence: 이벤트 문장
            event_embedding: 이벤트 임베딩 벡터
            agent_name: 검색할 에이전트 이름
            prompt_template: 프롬프트 템플릿 문자열
            similar_data_cnt: 포함할 유사 이벤트 개수 (기본값: 3)
            similarity_threshold: 유사도 기준값 (0.0 ~ 1.0, 기본값: 0.5)
        
        Returns:
            Optional[str]: 생성된 프롬프트
        """
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