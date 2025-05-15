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
        for memory_id, memory in memories[agent_name]["memories"].items():
            memory_embedding = memory.get("embeddings", [])
            if memory_embedding:
                similarity = np.dot(event_embedding, memory_embedding) / (
                    np.linalg.norm(event_embedding) * np.linalg.norm(memory_embedding)
                )
                if similarity >= similarity_threshold:
                    # memory_id 추가
                    memory_with_id = memory.copy()
                    memory_with_id["memory_id"] = memory_id
                    all_items.append((memory_with_id, similarity, False))  # False는 메모리임을 나타냄
        
        # 반성 추가 (반성 데이터는 기존 구조 유지)
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

    def _create_event_string(self, memory: Dict[str, Any]) -> str:
        """
        메모리를 이벤트 문자열로 변환
        
        Args:
            memory: 메모리 데이터
            
        Returns:
            str: 포맷된 이벤트 문자열
        """
        memory_id = memory.get("memory_id", "")
        time = memory.get("time", "")
        
        # 새 구조에서 어떤 필드에 내용이 있는지 확인
        event = memory.get("event", "")
        action = memory.get("action", "")
        feedback = memory.get("feedback", "")
        thought = memory.get("thought", "")  # 반성 데이터 호환성
        event_role = memory.get("event_role", "")
        print(f"🔍 ##이벤트 주체##: {event_role}")
        
        content = ""
        if event:
            if event_role == "God say":
                content = f"Event: God said, {event}"
            else:
                content = f"Event: {event}"
        elif action:
            content = f"Action: {action}"
        elif feedback:
            content = f"Feedback: {feedback}"
        
        # if thought:
        #     return f"- {content} (time: {time}, id: {memory_id})\n  thought: {thought}"
        # return f"- {content} (time: {time}, id: {memory_id})"
        if thought:
            return f"- {content}\n  thought: {thought}"
        return f"- {content}"
        

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
        
        # 각 위치별로 고유한 객체 목록을 저장할 딕셔너리
        location_objects = {}
        
        # 각 위치별로 고유한 객체 목록 생성
        for location_data in visible_interactables:
            location = location_data.get("location", "")
            interactables = location_data.get("interactables", [])
            
            if location and interactables:
                if location not in location_objects:
                    location_objects[location] = set()
                
                # 중복 제거를 위해 set 사용
                location_objects[location].update(interactables)
        
        # 결과 문자열 생성
        interactable_strings = []
        for location, objects in location_objects.items():
            # 객체 목록을 정렬된 리스트로 변환
            sorted_objects = sorted(list(objects))
            interactable_strings.append(f"- Location: {location}, Objects: {', '.join(sorted_objects)}")
        
        return "\n".join(interactable_strings) if interactable_strings else "Nothing visible nearby."

    def _format_state(self, state: Dict[str, int]) -> str:
        """
        상태 정보를 문자열로 변환
        
        Args:
            state: 상태 정보 딕셔너리
            
        Returns:
            str: 포맷된 상태 문자열
        """
        if not state:
            return ""
            
        state_strings = []
        
        # hunger와 loneliness는 양수일 때 해당 욕구가 높음
        if "hunger" in state:
            hunger = state["hunger"]
            if hunger >= 70:
                state_strings.append("very hungry")
            elif hunger >= 40:
                state_strings.append("hungry")
            elif hunger >= 10:
                state_strings.append("slightly hungry")
            elif hunger >= -10:
                state_strings.append("not hungry")
            else:
                state_strings.append("not hungry at all")
                
        if "loneliness" in state:
            loneliness = state["loneliness"]
            if loneliness >= 70:
                state_strings.append("very lonely")
            elif loneliness >= 40:
                state_strings.append("lonely")
            elif loneliness >= 10:
                state_strings.append("slightly lonely")
            elif loneliness >= -10:
                state_strings.append("not lonely")
            else:
                state_strings.append("want to be alone")
                
        # sleepiness와 stress는 0 이하일 때 표시하지 않음
        if "sleepiness" in state and state["sleepiness"] > 0:
            sleepiness = state["sleepiness"]
            if sleepiness >= 70:
                state_strings.append("very sleepy")
            elif sleepiness >= 40:
                state_strings.append("sleepy")
            elif sleepiness >= 1:
                state_strings.append("slightly sleepy")
                
        if "stress" in state and state["stress"] > 0:
            stress = state["stress"]
            if stress >= 70:
                state_strings.append("very stressed")
            elif stress >= 40:
                state_strings.append("stressed")
            elif stress >= 1:
                state_strings.append("slightly stressed")
        
        return ", ".join(state_strings) if state_strings else ""

    def create_reaction_prompt(
        self,
        event_sentence: str,
        event_embedding: List[float],
        event_role: str,
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
        processed_events = set()
        similar_events = []
        
        for memory, _ in similar_memories:
            # 메모리 문자열 생성
            event_str = self._create_event_string(memory)
            if event_str not in processed_events:
                similar_events.append(event_str)
                processed_events.add(event_str)
        
        similar_event_str = "\n".join(similar_events) if similar_events else "No similar past events found."
        
        # 에이전트 정보 처리
        agent_info = f"{agent_name} in {agent_data.get('current_location', '')}" if agent_data else agent_name
        
        # 상태 정보 처리
        state_str = ""
        if agent_data and "state" in agent_data:
            state_str = self._format_state(agent_data["state"])
        
        # 상호작용 가능한 객체 정보 처리
        visible_interactables_str = ""
        if agent_data and "visible_interactables" in agent_data:
            visible_interactables_str = self._format_visible_interactables(agent_data["visible_interactables"])
        
        # 에이전트 정보 문자열 생성
        agent_data_str = f"Name and Location: {agent_info}\n"
        
        # 성격 정보 추가
        if agent_data and "personality" in agent_data:
            agent_data_str += f"Personality: {agent_data['personality']}\n"
            
        # 상태 정보 추가
        if state_str:
            agent_data_str += f"Current State: {state_str}\n"
            
        # 상호작용 가능한 객체 정보 추가
        if visible_interactables_str:
            agent_data_str += f"Visible and can interact with:\n{visible_interactables_str}\n"

        # 프롬프트 생성
        try:
            prompt = prompt_template.format(
                AGENT_NAME=agent_name,
                AGENT_DATA=agent_data_str,
                EVENT_CONTENT=f"{'God say: ' if event_role == 'God say' else ''}{event_sentence}",
                RELEVANT_MEMORIES=similar_event_str
            )
            return prompt
        except Exception as e:
            print(f"프롬프트 생성 중 오류 발생: {e}")
            return None