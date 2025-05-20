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
                            "Tom": {
                                "memories": {},
                                "embeddings": {}
                            },
                            "Jane": {
                                "memories": {},
                                "embeddings": {}
                            }
                        }, f, ensure_ascii=False, indent=2)
                    elif file_path == self.reflections_file:
                        json.dump({"Tom": {"reflections": []}, "Jane": {"reflections": []}}, f, ensure_ascii=False, indent=2)
                    else:
                        json.dump({"Tom": {}, "Jane": {}}, f, ensure_ascii=False, indent=2)

    def _load_memories(self, sort_by_time: bool = False) -> Dict[str, Dict[str, Dict[str, Dict[str, Any]]]]:
        """메모리 데이터 로드. 필요에 따라 시간순으로 정렬합니다."""
        try:
            with open(self.memories_file, 'r', encoding='utf-8') as f:
                memories_data = json.load(f)
            
            if sort_by_time:
                # 각 에이전트의 메모리를 시간 역순으로 정렬
                for agent_name in memories_data:
                    if "memories" in memories_data[agent_name] and isinstance(memories_data[agent_name]["memories"], dict):
                        # 메모리 항목들을 시간 기준으로 정렬
                        # strptime 포맷을 유연하게 처리하기 위해 여러 포맷 시도
                        def parse_time(time_str):
                            formats_to_try = [
                                "%Y.%m.%d.%H:%M:%S", 
                                "%Y.%m.%d.%H:%M",
                                "%Y-%m-%dT%H:%M:%S.%fZ", # ISO 8601 format
                                "%Y-%m-%d %H:%M:%S" # 다른 일반적인 포맷
                            ]
                            for fmt in formats_to_try:
                                try:
                                    return datetime.strptime(time_str, fmt)
                                except ValueError:
                                    continue
                            # 모든 포맷에 실패하면 None 반환 또는 에러 처리
                            print(f"Warning: Could not parse time string {time_str} for agent {agent_name}")
                            return datetime.min # 정렬에서 가장 오래된 것으로 처리

                        memory_items = []
                        for mem_id, mem_content in memories_data[agent_name]["memories"].items():
                            parsed_time = parse_time(mem_content.get("time", ""))
                            memory_items.append((mem_id, mem_content, parsed_time))

                        # 시간(parsed_time)을 기준으로 내림차순 정렬
                        sorted_memory_items = sorted(
                            memory_items,
                            key=lambda item: item[2], # item[2]는 parsed_time
                            reverse=True
                        )
                        
                        # 정렬된 결과를 새 딕셔너리에 저장
                        ordered_memories = {mem_id: mem_content for mem_id, mem_content, _ in sorted_memory_items}
                        memories_data[agent_name]["memories"] = ordered_memories
            
            return memories_data
        except Exception as e:
            print(f"메모리 로드 중 오류 발생: {e}")
            return {
                "Tom": {
                    "memories": {},
                    "embeddings": {}
                },
                "Jane": {
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
            return {"Tom": {"reflections": []}, "Jane": {"reflections": []}}

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

    def save_memory(self, event_sentence: str, embedding: List[float], event_time: str, agent_name: str, event_role: str = "", importance:int = 0):
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
            "feedback_negative": "",
            "conversation_detail": "",
            "time": event_time,
            "event_type": "",
            "event_location": "", 
        }
        
        # if event_role != "" and event_role != " ":
        #     memory["importance"] = 8
        
        ## 10 이상의 importance -> 10 처리
        if importance > 10 : 
            importance = 10


        ## 디버그용 기본점수
        if importance == 0:
            importance = 3

        ## importance가 디폴트 값이 아니면 메모리에 저장
        if importance != 0 : 
            memory["importance"] = importance

        # 메모리와 임베딩을 별도로 저장
        memories[agent_name]["memories"][memory_id] = memory
        
        # 임베딩 데이터 저장
        embeddings = {
            "event": embedding,
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

        # 특수문자 제거 (공백 제외)
        import re
        cleaned_text = re.sub(r'[^\w\s]', '', text)    

        # 토큰화 및 소문자 변환
        tokens = [w.lower() for w in cleaned_text.split() if w.lower() in self.model]
        
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
            event_sentence = event.get("event_description", "")
            embedding = self.get_embedding(event_sentence)
            event_role = event.get("event_role", "")
            event_time = event.get("time", datetime.now().strftime("%Y.%m.%d.%H:%M"))
            if event.get("importance", 0) != 0:
                memory_id = self.save_memory(event_sentence, embedding, event_time, agent_name, event_role, importance=event.get("importance", 0))
            else:   
                memory_id = self.save_memory(event_sentence, embedding, event_time, agent_name, event_role)
            return True
        except Exception as e:
            print(f"관찰 정보 저장 실패: {e}")
            return False

######################## 위치 저장하는 메소드 라인 ################################

    def overwrite_location_memory(self, event_sentence: str, embedding: List[float], event_location: str, event_type: str, event_time: str, agent_name: str, event_role: str = "", importance:int = 0):
        """기존 메모리 덮어쓰기"""
        memories = self._load_memories(sort_by_time=True)
        
        if agent_name not in memories:
            memories[agent_name] = {
                "memories": {},
                "embeddings": {}
            }
            
        # 현재 시간이 제공되지 않은 경우 현재 시간 사용
        if not event_time:
            event_time = datetime.now().strftime("%Y.%m.%d.%H:%M")
        
        most_recent_match_id = None
        older_duplicate_ids_to_delete = []

        # 기존 메모리에서 event_type과 event_location이 일치하는지 확인
        # _load_memories(sort_by_time=True)로 인해 memories는 최신순으로 정렬되어 있음
        if agent_name in memories and "memories" in memories[agent_name]:
            for mem_id, mem_data in memories[agent_name]["memories"].items():
                if mem_data.get("event_type") == event_type and \
                   mem_data.get("event_location") == event_location:
                    if most_recent_match_id is None: # 첫 번째 일치 항목 (가장 최신)
                        most_recent_match_id = mem_id
                    else: # 이후 일치 항목 (오래된 중복)
                        older_duplicate_ids_to_delete.append(mem_id)
        
        # 오래된 중복 메모리 삭제
        if older_duplicate_ids_to_delete:
            for del_id in older_duplicate_ids_to_delete:
                if del_id in memories[agent_name]["memories"]:
                    del memories[agent_name]["memories"][del_id]
                if del_id in memories[agent_name]["embeddings"]: # 연결된 임베딩도 삭제
                    del memories[agent_name]["embeddings"][del_id]

        # 사용할 메모리 ID 결정
        if most_recent_match_id:
            memory_id = most_recent_match_id
        else:
            memory_id = self._get_next_memory_id(agent_name)

        ## 디버그용 기본점수
        if importance == 0:
            importance = 5

        # 메모리 데이터 저장
        memory = {
            "event_role": event_role,
            "event": event_sentence,
            "action": "",
            "feedback": "",
            "feedback_negative": "",
            "conversation_detail": "",
            "importance": importance,
            "time": event_time,
            "event_type": event_type,  # event_type 저장
            "event_location": event_location  # event_location 저장
        }
        

        print(f"memory: {memory}")
        print(f"memory_id: {memory_id}")
        # if event_role != "" and event_role != " ":
        #     memory["importance"] = 8
        
        ## 10 이상의 importance -> 10 처리
        if importance > 10 : 
            importance = 10

        ## 디버그용 기본점수
        if importance == 0:
            importance = 5

        ## importance가 디폴트 값이 아니면 메모리에 저장
        if importance != 0 : 
            memory["importance"] = importance

        # 메모리와 임베딩을 별도로 저장
        memories[agent_name]["memories"][memory_id] = memory
        
        # 임베딩 데이터 저장
        embeddings = {
            "event": embedding,
            "action": [],
            "feedback": []
        }
        memories[agent_name]["embeddings"][memory_id] = embeddings
        
        self._save_memories(memories)
        
        return memory_id

    def save_location_data(self, event: Dict[str, Any], agent_name: str) -> bool:
        """지역 정보를 메모리에 저장"""
        try:
            event_sentence = event.get("event_description", "")
            embedding = self.get_embedding(event_sentence)
            event_time = event.get("time", datetime.now().strftime("%Y.%m.%d.%H:%M"))
            event_location = event.get("event_location", "")
            event_type = event.get("event_type", "")
            if event.get("importance", 0) != 0:
                memory_id = self.overwrite_location_memory(event_sentence, embedding, event_location, event_type, event_time, agent_name, importance=event.get("importance", 0))
            else:   
                memory_id = self.overwrite_location_memory(event_sentence, embedding, event_location, event_type, event_time, agent_name)
            return True
        except Exception as e:
            print(f"관찰 정보 저장 실패: {e}")
            return False