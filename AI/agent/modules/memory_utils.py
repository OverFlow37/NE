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
                        # 새로운 메모리 구조로 초기화
                        json.dump({
                            "John": {
                                "memories": {},
                                "embeddings": {}
                            },
                            "Sarah": {
                                "memories": {},
                                "embeddings": {}
                            }
                        }, f, ensure_ascii=False, indent=2)
                    elif file_path == self.reflections_file:
                        json.dump({"John": {"reflections": []}, "Sarah": {"reflections": []}}, f, ensure_ascii=False, indent=2)
                    else:
                        json.dump({"John": [], "Sarah": []}, f, ensure_ascii=False, indent=2)

    def _load_memories(self) -> Dict[str, Dict[str, Dict[str, Dict[str, Any]]]]:
        """메모리 데이터 로드"""
        try:
            with open(self.memories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"메모리 로드 중 오류 발생: {e}")
            return {
                "John": {
                    "memories": {},
                    "embeddings": {}
                },
                "Sarah": {
                    "memories": {},
                    "embeddings": {}
                }
            }

    def _save_memories(self, memories: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]]):
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

    def _get_next_memory_id(self, agent_name: str) -> str:
        """에이전트의 다음 메모리 ID를 가져옴"""
        memories = self._load_memories()
        
        if agent_name not in memories or "memories" not in memories[agent_name]:
            return "1"
            
        agent_memories = memories[agent_name]["memories"]
        if not agent_memories:
            return "1"
            
        # 현재 메모리 ID 중 가장 큰 값을 찾음
        try:
            memory_ids = [int(id) for id in agent_memories.keys()]
            return str(max(memory_ids) + 1)
        except ValueError:
            return "1"

    def save_memory(self, event_sentence: str, embedding: List[float], event_time: str, agent_name: str, event_id: int = None, event_role: str = "", importance:int = 0):
        """새로운 메모리 저장"""
        memories = self._load_memories()
        
        if agent_name not in memories:
            memories[agent_name] = {
                "memories": {},
                "embeddings": {}
            }
            
        # 현재 시간이 제공되지 않은 경우 현재 시간 사용
        if not event_time:
            event_time = datetime.now().strftime("%Y.%m.%d.%H:%M")
        
        # 새 메모리 ID 생성
        memory_id = self._get_next_memory_id(agent_name)
            
        # 메모리 데이터 저장
        memory = {
            "event_role": event_role,
            "event": event_sentence,
            "action": "",
            "feedback": "",
            "conversation_detail": "",
            "time": event_time
        }
        
        # if event_role != "" and event_role != " ":
        #     memory["importance"] = 8
        
        ## 10 이상의 importance -> 10 처리
        if importance > 10 : 
            importance = 10

        ## importance가 디폴트 값이 아니면 메모리에 저장
        if importance != 0 : 
            memory["importance"] = importance

        # 메모리와 임베딩을 별도로 저장
        memories[agent_name]["memories"][memory_id] = memory
        
        # 임베딩 데이터 저장
        embeddings = {
            "event": self.get_embedding(event_sentence),
            "action": [],
            "feedback": []
        }
        memories[agent_name]["embeddings"][memory_id] = embeddings
        
        self._save_memories(memories)
        
        return memory_id

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
        event_description = event.get("event_description", "")
        event_location = event.get("event_location", "")
        
        if event_location != "" and event_location != " ":
            return f"{event_description} at {event_location}"
        return event_description

    def save_perception(self, event: Dict[str, Any], agent_name: str) -> bool:
        """관찰 정보를 메모리에 저장"""
        try:
            event_sentence = ""
            if event.get("event_location", "") != "" and event.get("event_location", "") != " ":
                event_sentence = f'{event.get("event_description", "")} at {event.get("event_location", "")}'
            else:
                event_sentence = event.get("event_description", "")
            embedding = self.get_embedding(event_sentence)
            event_time = event.get("time", datetime.now().strftime("%Y.%m.%d.%H:%M"))
            
            memory_id = self.save_memory(event_sentence, embedding, event_time, agent_name)
            return True
        except Exception as e:
            print(f"관찰 정보 저장 실패: {e}")
            return False