"""
임베딩 업데이트 모듈

메모리와 반성 데이터의 임베딩을 업데이트하는 기능을 제공합니다.
"""

import json
import os
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
from .memory_utils import MemoryUtils

class EmbeddingUpdater:
    def __init__(self, word2vec_model):
        """
        임베딩 업데이트 초기화
        
        Args:
            word2vec_model: Word2Vec 모델
        """
        self.memory_utils = MemoryUtils(word2vec_model)
        
    def update_embeddings(self) -> Dict[str, int]:
        """
        모든 메모리와 반성의 임베딩을 업데이트
        
        Returns:
            Dict[str, int]: 업데이트된 항목 수 {"memories": n, "reflections": m}
        """
        update_counts = {"memories": 0, "reflections": 0}
        
        # 메모리 업데이트
        memories = self.memory_utils._load_memories()
        for agent_name in memories:
            for memory in memories[agent_name]["memories"]:
                event = memory.get("event", "")
                if event:
                    # 시간 필드가 없는 경우 현재 시간 추가
                    current_time = datetime.now().strftime("%Y.%m.%d.%H:%M")
                    if "time" not in memory:
                        memory["time"] = current_time
                    memory["embeddings"] = self.memory_utils.get_embedding(event)
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