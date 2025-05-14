"""
메모리 검색 모듈

메모리를 검색하고 관련된 메모리를 찾는 기능을 제공합니다.
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
from datetime import datetime
from pathlib import Path
from .memory_utils import MemoryUtils

class MemoryRetriever:
    def __init__(self, memory_file_path: str, word2vec_model):
        """
        메모리 검색기 초기화
        
        Args:
            memory_file_path: 메모리 JSON 파일 경로
            word2vec_model: Word2Vec 모델
        """
        self.memory_utils = MemoryUtils(word2vec_model)
        self.memory_file_path = memory_file_path

    def should_react(self, event: Dict[str, Any]) -> bool:
        """
        이벤트에 반응해야 하는지 결정
        
        Args:
            event: 이벤트 데이터
            
        Returns:
            bool: 반응 여부
        """
        # 현재는 모든 이벤트에 반응
        return True

    def _calculate_value(
        self,
        memory: Dict[str, Any],
        similarity: float,
        time_weight: float,
        is_reflection: bool = False
    ) -> float:
        """
        메모리의 가치 계산
        
        Args:
            memory: 메모리 데이터
            similarity: 유사도
            time_weight: 시간 가중치
            is_reflection: 반성 데이터 여부
            
        Returns:
            float: 계산된 가치
        """
        # importance 값 가져오기 (기본값: 5)
        importance = float(memory.get("importance", 5))
        
        # 반성인 경우 importance에 1.5를 곱함
        if is_reflection:
            importance *= 1.5
            
        # importance를 10으로 나누어 0~1 사이의 값으로 정규화
        importance = importance / 10
        
        # 시간 가중치와 importance를 곱한 값
        time_importance = time_weight * importance
        
        # 최종 가치 = 시간 가중치 * importance + 유사도
        return time_importance + similarity

    def _find_similar_memories(
        self,
        event_embedding: List[float],
        agent_name: str,
        top_k: int = 3,
        similarity_threshold: float = 0.5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        유사한 메모리 검색
        
        Args:
            event_embedding: 현재 이벤트의 임베딩
            agent_name: 에이전트 이름
            top_k: 반환할 메모리 개수
            similarity_threshold: 유사도 임계값
            
        Returns:
            List[Tuple[Dict[str, Any], float]]: (메모리, 유사도) 튜플 리스트
        """
        memories = self.memory_utils._load_memories()
        reflections = self.memory_utils._load_reflections()
        
        if agent_name not in memories or not memories[agent_name]["memories"]:
            return []
        
        # 모든 메모리와 반성을 하나의 리스트로 합치기
        all_items = []
        
        # 메모리 추가
        for memory in memories[agent_name]["memories"]:
            memory_embedding = memory.get("embeddings", [])
            if memory_embedding:
                similarity = np.dot(event_embedding, memory_embedding) / (
                    np.linalg.norm(event_embedding) * np.linalg.norm(memory_embedding)
                )
                if similarity >= similarity_threshold:
                    all_items.append((memory, similarity, False))  # False는 메모리임을 나타냄
        
        # 반성 추가
        if agent_name in reflections:
            for reflection in reflections[agent_name]["reflections"]:
                reflection_embedding = reflection.get("embeddings", [])
                if reflection_embedding:
                    similarity = np.dot(event_embedding, reflection_embedding) / (
                        np.linalg.norm(event_embedding) * np.linalg.norm(reflection_embedding)
                    )
                    if similarity >= similarity_threshold:
                        all_items.append((reflection, similarity, True))  # True는 반성임을 나타냄
        
        # 시간순으로 정렬하여 가중치 계산
        def get_time(item):
            return item.get("time", "")
            
        all_items.sort(key=lambda x: get_time(x[0]), reverse=True)
        
        # 각 항목의 가치 계산
        valued_items = []
        for i, (item, similarity, is_reflection) in enumerate(all_items):
            # 시간 가중치 계산 (0.99부터 0.01씩 감소)
            time_weight = max(0.99 - (i * 0.01), 0.01)
            
            # 가치 계산
            value = self._calculate_value(item, similarity, time_weight, is_reflection)
            valued_items.append((item, value, is_reflection))
        
        # 가치 기준으로 정렬
        valued_items.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 k개 반환
        return [(item, value) for item, value, _ in valued_items[:top_k]]

    def _find_group_memories(self, memory: Dict[str, Any], agent_name: str) -> List[Dict[str, Any]]:
        """
        같은 그룹의 메모리 검색
        
        Args:
            memory: 기준 메모리
            agent_name: 에이전트 이름
            
        Returns:
            List[Dict[str, Any]]: 같은 그룹의 메모리 리스트
        """
        memories = self.memory_utils._load_memories()
        if agent_name not in memories:
            return []
        
        group_id = memory.get("groupId")
        if not group_id:
            return []
        
        # 같은 그룹의 메모리 검색
        group_memories = []
        for m in memories[agent_name]["memories"]:
            if m.get("groupId") == group_id and m != memory:
                group_memories.append(m)
        
        return group_memories

    def _create_event_string(self, event: str, time: str, thought: str = None) -> str:
        """
        이벤트 문자열 생성
        
        Args:
            event: 이벤트 내용
            time: 이벤트 시간
            thought: 반성 내용 (선택적)
            
        Returns:
            str: 포맷된 이벤트 문자열
        """
        if thought:
            return f"- {event}\n  thought: {thought}"
        return f"- {event}"

    def _create_cause_effect_string(
        self,
        effect: str,
        cause: str,
        effect_time: str,
        cause_time: str,
        effect_thought: str = None,
        cause_thought: str = None
    ) -> str:
        """
        원인-결과 관계 문자열 생성
        
        Args:
            effect: 결과 이벤트
            cause: 원인 이벤트
            effect_time: 결과 시간
            cause_time: 원인 시간
            effect_thought: 결과에 대한 반성 (선택적)
            cause_thought: 원인에 대한 반성 (선택적)
            
        Returns:
            str: 포맷된 원인-결과 관계 문자열
        """
        effect_str = f"{effect} (time: {effect_time})"
        if effect_thought:
            effect_str += f"\n  thought: {effect_thought}"
            
        cause_str = f"{cause} (time: {cause_time})"
        if cause_thought:
            cause_str += f"\n  thought: {cause_thought}"
            
        return f"- {effect_str} because {cause_str}"
    
    def _format_visible_interactables(self, visible_interactables: List[Dict[str, Any]]) -> str:
        """
        상호작용 가능한 객체 목록을 문자열로 변환
        
        Args:
            visible_interactables: 상호작용 가능한 객체 목록
            
        Returns:
            str: 포맷된 객체 목록 문자열
        """
        if not visible_interactables:
            return "Nothing visible nearby."
        
        interactable_strings = []
        for location_data in visible_interactables:
            location = location_data.get("location", "")
            interactables = location_data.get("interactables", [])
            
            if location and interactables:
                interactable_str = ", ".join(interactables)
                interactable_strings.append(f"In {location}: {interactable_str}")
        
        return "\n".join(interactable_strings) if interactable_strings else "Nothing visible nearby."
    
    def create_reaction_prompt(
        self,
        event_sentence: str,
        event_embedding: List[float],
        agent_name: str,
        prompt_template: str,
        agent_data: Dict[str, Any] = None,
        similar_data_cnt: int = 3,
        similarity_threshold: float = 0.5
    ) -> Optional[str]:
        """
        이벤트에 대한 반응을 결정하기 위한 프롬프트 생성
        
        Args:
            event_sentence: 현재 이벤트 문장
            event_embedding: 현재 이벤트의 임베딩
            agent_name: 에이전트 이름
            prompt_template: 프롬프트 템플릿
            agent_data: 에이전트 데이터 (성격, 위치, 상호작용 가능한 객체 등)
            similar_data_cnt: 유사한 이벤트 개수
            similarity_threshold: 유사도 임계값
            
        Returns:
            Optional[str]: 생성된 프롬프트
        """
        # 반응 여부 결정
        if not self.should_react({"event": event_sentence}):
            return None
        
        # 유사한 메모리 검색
        similar_memories = self._find_similar_memories(
            event_embedding,
            agent_name,
            top_k=similar_data_cnt,
            similarity_threshold=similarity_threshold
        )
        
        # 중복 제거를 위한 Set 사용
        processed_events: Set[str] = set()
        similar_events = []
        
        for memory, _ in similar_memories:
            event = memory.get("event", "")
            time = memory.get("time", "")
            thought = memory.get("thought")  # 반성의 경우 thought가 있을 수 있음
            
            if not event or not time:
                continue
                
            # 기본 이벤트 문자열 생성
            event_str = self._create_event_string(event, time, thought)
            if event_str not in processed_events:
                similar_events.append(event_str)
                processed_events.add(event_str)
            
            # 같은 그룹의 메모리 검색
            group_memories = self._find_group_memories(memory, agent_name)
            for group_memory in group_memories:
                group_event = group_memory.get("event", "")
                group_time = group_memory.get("time", "")
                group_thought = group_memory.get("thought")
                
                if not group_event or not group_time:
                    continue
                
                # 시간 순서에 따라 원인-결과 관계 결정
                if group_time < time:
                    cause_effect_str = self._create_cause_effect_string(
                        event, group_event, time, group_time,
                        thought, group_thought
                    )
                else:
                    cause_effect_str = self._create_cause_effect_string(
                        group_event, event, group_time, time,
                        group_thought, thought
                    )
                
                if cause_effect_str not in processed_events:
                    similar_events.append(cause_effect_str)
                    processed_events.add(cause_effect_str)
        
        similar_event_str = "\n".join(similar_events) if similar_events else "No similar past events found."
        
        # 에이전트 정보 처리
        agent_info = "Name: " + agent_name
        personality = ""
        current_location = ""
        visible_interactables = []
        
        if agent_data:
            if "personality" in agent_data:
                personality = agent_data["personality"]
            
            if "current_location" in agent_data:
                current_location = agent_data["current_location"]
            
            # 상호작용 가능한 객체 정보 추출
            if "visible_interactables" in agent_data:
                for location_data in agent_data["visible_interactables"]:
                    location = location_data.get("location", "")
                    interactables = location_data.get("interactables", [])
                    
                    if location and interactables:
                        visible_interactables.append({
                            "location": location,
                            "interactables": interactables
                        })
        
        # 상호작용 가능한 객체 문자열 생성
        visible_interactables_str = ""
        if visible_interactables:
            visible_interactables_str = "Visible and can interact with:\n"
            for loc_obj in visible_interactables:
                location = loc_obj["location"]
                interactables = ", ".join(loc_obj["interactables"])
                visible_interactables_str += f"- Location: {location}, Interactables: {interactables}\n"
        
        # 에이전트 정보 문자열 생성
        agent_data_str = f"Name: {agent_name}\n"
        if personality:
            agent_data_str += f"Personality: {personality}\n"
        if current_location:
            agent_data_str += f"Current Location: {current_location}\n"
        if visible_interactables_str:
            agent_data_str += visible_interactables_str
        

        # 프롬프트 생성
        try:
            prompt = prompt_template.format(
                AGENT_NAME=agent_name,
                AGENT_DATA=agent_data_str,
                EVENT_CONTENT=event_sentence,
                SIMILAR_EVENT=similar_event_str
            )
            return prompt
        except Exception as e:
            print(f"프롬프트 생성 중 오류 발생: {e}")
            return None 