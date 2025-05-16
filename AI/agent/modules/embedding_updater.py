"""
임베딩 업데이트 모듈

메모리와 반성 데이터의 임베딩을 업데이트하는 기능을 제공합니다.
"""

import json
import os
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
import numpy as np
from .memory_utils import MemoryUtils

class EmbeddingUpdater:
    def __init__(self, word2vec_model):
        """
        임베딩 업데이트 초기화
        
        Args:
            word2vec_model: Word2Vec 모델
        """
        self.memory_utils = MemoryUtils(word2vec_model)
        self.word2vec_model = word2vec_model
        
        # 현재 파일의 절대 경로를 기준으로 상위 디렉토리 찾기
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent.parent  # AI 디렉토리
        agent_dir = root_dir / "agent"
        data_dir = agent_dir / "data"
        object_dict_dir = data_dir / "object_dict"
        
        self.object_dictionary_path = str(object_dict_dir / "object_dictionary.json")
        self.object_embeddings_path = str(object_dict_dir / "object_embeddings.json")
        
    def create_object_embeddings(self) -> Dict[str, Dict[str, List[float]]]:
        """
        오브젝트 사전에서 오브젝트 이름과 설명을 추출하여 임베딩 생성
        
        Returns:
            Dict[str, Dict[str, List[float]]]: 오브젝트 임베딩 데이터
        """
        print("오브젝트 임베딩 생성 중...")
        
        # JSON 파일에서 오브젝트 이름과 설명 추출
        with open(self.object_dictionary_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        objects = data.get("objects", {})
        print(f"🔍 총 오브젝트 수: {len(objects)}")

        embeddings = {}
        
        for name, desc in objects.items():
            # 이름만 사용한 임베딩
            name_words = name.lower().split()
            try:
                name_embedding = np.mean([self.word2vec_model[word] for word in name_words if word in self.word2vec_model], axis=0)
                name_embedding = name_embedding.tolist()  # numpy array를 list로 변환
                
                # 이름과 설명을 합친 임베딩
                combined_text = f"{name} {desc}".lower()
                combined_words = combined_text.split()
                combined_embedding = np.mean([self.word2vec_model[word] for word in combined_words if word in self.word2vec_model], axis=0)
                combined_embedding = combined_embedding.tolist()  # numpy array를 list로 변환
                
                embeddings[name] = {
                    "name_only": name_embedding,
                    "name_and_info": combined_embedding
                }
            except:
                continue
        
        # 임베딩 데이터 저장
        os.makedirs(os.path.dirname(self.object_embeddings_path), exist_ok=True)
        with open(self.object_embeddings_path, "w", encoding="utf-8") as f:
            json.dump(embeddings, f, ensure_ascii=False, indent=2)
        print("✅ 오브젝트 임베딩 데이터 저장 완료!")
        
        return embeddings
        
    def update_embeddings(self) -> Dict[str, int]:
        """
        모든 메모리와 반성의 임베딩을 업데이트
        
        Returns:
            Dict[str, int]: 업데이트된 항목 수 {"memories": n, "reflections": m, "objects": o}
        """
        update_counts = {"memories": 0, "reflections": 0, "objects": 0}
        
        # 오브젝트 임베딩 확인 및 생성
        if not os.path.exists(self.object_embeddings_path):
            print("오브젝트 임베딩 파일이 없습니다. 생성합니다...")
            self.create_object_embeddings()
            update_counts["objects"] = 1
        
        # 메모리 업데이트
        memories = self.memory_utils._load_memories()
        for agent_name in memories:
            for memory_id, memory in memories[agent_name]["memories"].items():
                embeddings_list = []
                
                # event 임베딩
                event = memory.get("event", "")
                if event:
                    embeddings_list.append(self.memory_utils.get_embedding(event))
                
                # action 임베딩
                action = memory.get("action", "")
                if action:
                    embeddings_list.append(self.memory_utils.get_embedding(action))
                
                # feedback 임베딩
                feedback = memory.get("feedback", "")
                if feedback:
                    embeddings_list.append(self.memory_utils.get_embedding(feedback))
                
                if embeddings_list:
                    memory["embeddings"] = embeddings_list
                    update_counts["memories"] += 1
        
        self.memory_utils._save_memories(memories)
        
        # 반성 업데이트
        reflections = self.memory_utils._load_reflections()
        for agent_name in reflections:
            for reflection in reflections[agent_name]["reflections"]:
                event = reflection.get("event", "")
                if event:
                    # 시간 필드가 없는 경우 현재 시간 추가
                    current_time = datetime.now().strftime("%Y.%m.%d.%H:%M")
                    if "time" not in reflection:
                        reflection["time"] = current_time
                    if "created" not in reflection:
                        reflection["created"] = current_time
                    reflection["embeddings"] = self.memory_utils.get_embedding(event)
                    update_counts["reflections"] += 1
        
        self.memory_utils._save_reflections(reflections)
        
        return update_counts 