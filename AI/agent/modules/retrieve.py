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
        self.object_dictionary = self._load_object_dictionary()

    def _load_object_dictionary(self) -> Dict[str, Any]:
        """
        오브젝트 사전을 로드합니다.
        
        Returns:
            Dict[str, Any]: 오브젝트 사전 데이터
        """
        dictionary_path = os.path.join(os.path.dirname(__file__), "../data/object_dict/object_dictionary.json")
        try:
            with open(dictionary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"오브젝트 사전 로드 중 오류 발생: {e}")
            return {}

    def _find_relevant_objects(
        self,
        event_embedding: List[float],
        object_embeddings: Dict[str, Dict[str, List[float]]],
        top_k: int = 10,
        similarity_threshold: float = 0.1
    ) -> List[Tuple[str, float]]:
        """
        이벤트와 관련된 상위 k개의 오브젝트를 찾습니다.
        
        Args:
            event_embedding: 이벤트 임베딩
            object_embeddings: 오브젝트 임베딩 딕셔너리
            top_k: 반환할 오브젝트 개수
            similarity_threshold: 유사도 임계값
            
        Returns:
            List[Tuple[str, float]]: (오브젝트 이름, 유사도) 튜플 리스트
        """
        
        event_embedding = np.array(event_embedding)
        object_similarities = []
        
        for obj_name, obj_data in object_embeddings.items():
            obj_embedding = np.array(obj_data.get("name_only", []))
            
            if obj_embedding.shape == event_embedding.shape:
                similarity = np.dot(event_embedding, obj_embedding) / (
                    np.linalg.norm(event_embedding) * np.linalg.norm(obj_embedding)
                )
                if similarity >= similarity_threshold:
                    object_similarities.append((obj_name, float(similarity)))
        
        # 유사도 기준으로 정렬하고 상위 k개 반환
        object_similarities.sort(key=lambda x: x[1], reverse=True)
        return object_similarities[:top_k]

    def _get_object_description(self, object_name: str) -> str:
        """
        오브젝트의 설명을 찾습니다.
        
        Args:
            object_name: 오브젝트 이름
            
        Returns:
            str: 오브젝트 설명
        """
        objects = self.object_dictionary.get("objects", {})
        
        # 각 카테고리에서 오브젝트 검색
        for category in objects.values():
            if isinstance(category, dict):
                for subcategory in category.values():
                    if isinstance(subcategory, dict) and object_name in subcategory:
                        return subcategory[object_name]
        
        return f"Description not found for {object_name}"

    def _create_interactable_objects_string(
        self,
        event_embedding: List[float],
        object_embeddings: Dict[str, Dict[str, List[float]]]
    ) -> str:
        """
        상호작용 가능한 오브젝트 문자열을 생성합니다.
        
        Args:
            event_embedding: 이벤트 임베딩
            object_embeddings: 오브젝트 임베딩 딕셔너리
            
        Returns:
            str: 오브젝트 문자열
        """
        relevant_objects = self._find_relevant_objects(event_embedding, object_embeddings)
        
        if not relevant_objects:
            return "No interactable objects found."
        
        object_strings = []
        for obj_name, similarity in relevant_objects:
            # object_dictionary에서 오브젝트 설명 찾기
            description = self._get_object_description(obj_name)
            if description:
                object_strings.append(f"- {obj_name}: {description}")
        
        return "\n".join(object_strings)

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
            event_embedding: 현재 이벤트의 임베딩 (단일 벡터)
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
        
        # event_embedding을 numpy 배열로 변환
        event_embedding = np.array(event_embedding)
        
        # 메모리 추가
        for memory_id, memory in memories[agent_name]["memories"].items():
            memory_embeddings = memory.get("embeddings", [])
            if memory_embeddings:
                # 여러 임베딩 중 가장 높은 유사도 계산
                max_similarity = 0
                for memory_embedding in memory_embeddings:
                    memory_embedding = np.array(memory_embedding)
                    if memory_embedding.shape == event_embedding.shape:
                        similarity = np.dot(event_embedding, memory_embedding) / (
                            np.linalg.norm(event_embedding) * np.linalg.norm(memory_embedding)
                        )
                        max_similarity = max(max_similarity, float(similarity))
                
                if max_similarity >= similarity_threshold:
                    # memory_id 추가
                    memory_with_id = memory.copy()
                    memory_with_id["memory_id"] = memory_id
                    all_items.append((memory_with_id, max_similarity, False))  # False는 메모리임을 나타냄
        
        # 반성 추가 (반성 데이터는 기존 구조 유지)
        if agent_name in reflections:
            for reflection in reflections[agent_name]["reflections"]:
                reflection_embeddings = reflection.get("embeddings", [])
                if reflection_embeddings:
                    # 여러 임베딩 중 가장 높은 유사도 계산
                    max_similarity = 0
                    for reflection_embedding in reflection_embeddings:
                        reflection_embedding = np.array(reflection_embedding)
                        if reflection_embedding.shape == event_embedding.shape:
                            similarity = np.dot(event_embedding, reflection_embedding) / (
                                np.linalg.norm(event_embedding) * np.linalg.norm(reflection_embedding)
                            )
                            max_similarity = max(max_similarity, float(similarity))
                    
                    if max_similarity >= similarity_threshold:
                        all_items.append((reflection, max_similarity, True))  # True는 반성임을 나타냄
        
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
        # memory_id = memory.get("memory_id", "")
        # time = memory.get("time", "")
        
        # 새 구조에서 어떤 필드에 내용이 있는지 확인
        event = memory.get("event", "")
        action = memory.get("action", "")
        feedback = memory.get("feedback", "")
        thought = memory.get("thought", "")  # 반성 데이터 호환성
        event_role = memory.get("event_role", "")
        
        content = ""
        if event:
            if event_role == "God say":
                content = f"Event: God said, {event}\n"
            else:
                content = f"Event: {event}\n"
        if action:
            content += f"Action: {action}\n"
        if feedback:
            content += f"Feedback: {feedback}\n"
        
        # if thought:
        #     return f"- {content} (time: {time}, id: {memory_id})\n  thought: {thought}"
        # return f"- {content} (time: {time}, id: {memory_id})"
        if thought:
            return f"- {content}\n  thought: {thought}\n"
        return f"- {content}\n"
        

    def _format_visible_interactables(self, visible_interactables: List[Dict[str, Any]]) -> str:
        """
        상호작용 가능한 객체 목록을 (location, object) 쌍 문자열로 변환합니다.

        Args:
            visible_interactables: 상호작용 가능한 객체 목록
                                    형식: [{"location": "...", "interactables": ["...", "..."]}, ...]

        Returns:
            str: (location, object) 쌍의 줄바꿈으로 구분된 문자열.
                예: "- (outdoor, Flower)\n- (outdoor, Jewel)\n- (temple, Grape)"
        """
        if not visible_interactables:
            return "Nothing visible nearby."

        formatted_lines = []

        # 입력받은 visible_interactables 리스트를 순회합니다.
        # 이 리스트의 각 요소는 {"location": "위치 이름", "interactables": ["객체1", "객체2", ...]} 형태입니다.
        for location_data in visible_interactables:
            location = location_data.get("location")
            interactables = location_data.get("interactables", []) # 해당 위치의 객체 목록 (리스트)

            # 위치 정보가 유효하고, interactables가 리스트이며 비어있지 않은 경우 처리
            if location and isinstance(interactables, list) and interactables:
                # 해당 위치(location)에 속한 각 객체(obj)에 대해 새로운 포맷의 문자열을 만듭니다.
                for obj in interactables:
                    # 각 (위치, 객체) 쌍을 "- (location, object)" 형태로 포맷하여 리스트에 추가
                    formatted_lines.append(f"- ({location}, {obj})")

        # 모든 포맷된 라인을 줄바꿈 문자로 연결하여 최종 문자열을 생성합니다.
        # 만약 visible_interactables 데이터는 있었지만 유효한 location/interactables 엔트리가 하나도 없었다면
        # formatted_lines는 비어있을 것이므로 "Nothing visible nearby."를 반환합니다.
        return "\n".join(formatted_lines) if formatted_lines else "Nothing visible nearby."


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
            if hunger >= 90:
                state_strings.append("You are so hungry that you need to eat something right away!")
            elif hunger >= 70:
                state_strings.append("extremely hungry")
            elif hunger >= 40:
                state_strings.append("very hungry")
            elif hunger >= 20:
                state_strings.append("slightly hungry")
            elif hunger >= -70:
                state_strings.append("")
            else:
                state_strings.append("You can't eat anymore")
                
        if "loneliness" in state:
            loneliness = state["loneliness"]
            if loneliness >= 70:
                state_strings.append("very lonely")
            elif loneliness >= 40:
                state_strings.append("lonely")
            elif loneliness >= 20:
                state_strings.append("slightly lonely")
            elif loneliness >= -70:
                state_strings.append("")
            else:
                state_strings.append("want to be alone")
                
        # sleepiness와 stress는 0 이하일 때 표시하지 않음
        if "sleepiness" in state and state["sleepiness"] > 0:
            sleepiness = state["sleepiness"]
            if sleepiness >= 90:
                state_strings.append("You are so sleepy that you are on the verge of fainting, you should use a bed.")
            elif sleepiness >= 70:
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
        similarity_threshold: float = 0.5,
        object_embeddings: List[Dict[str, Any]] = None
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
            object_embeddings: 오브젝트 임베딩 리스트
            
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
        #agent_info = f"{agent_name} in {agent_data.get('current_location', '')}" if agent_data else agent_name
        
        # 상태 정보 처리
        state_str = ""
        if agent_data and "state" in agent_data:
            state_str = self._format_state(agent_data["state"])
        
        # 상호작용 가능한 객체 정보 처리
        visible_interactables_str = ""
        if agent_data and "visible_interactables" in agent_data:
            visible_interactables_str = self._format_visible_interactables(agent_data["visible_interactables"])
        
        # 관련 오브젝트 문자열 생성
        interactable_objects_str = json.dumps({"interactable_objects": []})  # 기본값으로 빈 객체 리스트
        if object_embeddings:
            interactable_objects_str = self._create_interactable_objects_string(event_embedding, object_embeddings)
        # 에이전트 정보 문자열 생성
        agent_data_str = f"Your Name: {agent_name}\n"
        #agent_data_str += f"Your Location: {agent_data.get('current_location', '')}\n"
        
        # 성격 정보 추가
        if agent_data and "personality" in agent_data:
            agent_data_str += f"Personality: {agent_data['personality']}\n"
            
        # 상태 정보 추가
        if state_str:
            agent_data_str += f"Current State: {state_str}\n"
            
        # 상호작용 가능한 객체 정보 추가
        if visible_interactables_str:
            agent_data_str += f"Visible objects (location, object pairs):\n{visible_interactables_str}\n"

        # 프롬프트 생성
        try:
            prompt = prompt_template.format(
                AGENT_NAME=agent_name,
                AGENT_DATA=agent_data_str,
                EVENT_CONTENT=f"{'God say: ' if event_role == 'God say' else ''}{event_sentence}",
                RELEVANT_MEMORIES=similar_event_str,
                RELEVANT_OBJECTS=interactable_objects_str  # 키 이름을 INTERACTABLE_OBJECT로 수정
            )
            return prompt
        except Exception as e:
            print(f"프롬프트 생성 중 오류 발생: {e}")
            return None