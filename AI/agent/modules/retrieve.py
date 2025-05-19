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
        state_embedding: List[float],
        object_embeddings: Dict[str, Dict[str, List[float]]],
        top_k: int = 10,
        similarity_threshold: float = 0.01
    ) -> List[Tuple[str, float]]:
        """
        이벤트와 관련된 상위 k개의 오브젝트를 찾습니다.
        
        Args:
            event_embedding: 이벤트 임베딩
            state_embedding: 상태 임베딩
            object_embeddings: 오브젝트 임베딩 딕셔너리
            top_k: 반환할 오브젝트 개수
            similarity_threshold: 유사도 임계값
            
        Returns:
            List[Tuple[str, float]]: (오브젝트 이름, 유사도) 튜플 리스트
        """
        
        event_embedding_np = np.array(event_embedding)
        state_embedding_np = np.array(state_embedding)

        is_event_embedding_zero = np.all(event_embedding_np == 0)
        is_state_embedding_zero = np.all(state_embedding_np == 0)
        
        object_similarities = []
        
        for obj_name, obj_data in object_embeddings.items():
            obj_embedding_np = np.array(obj_data.get("name_only", []))
            
            if np.all(obj_embedding_np == 0): # Object embedding이 0이면 건너뛰기
                continue

            if obj_embedding_np.shape == event_embedding_np.shape:
                event_similarity = 0.01
                if not is_event_embedding_zero:
                    norm_event = np.linalg.norm(event_embedding_np)
                    norm_obj = np.linalg.norm(obj_embedding_np)
                    if norm_event > 0 and norm_obj > 0:
                        event_similarity = np.dot(event_embedding_np, obj_embedding_np) / (norm_event * norm_obj)
                
                state_similarity = 0.01
                if not is_state_embedding_zero:
                    norm_state = np.linalg.norm(state_embedding_np)
                    norm_obj = np.linalg.norm(obj_embedding_np) # norm_obj는 위에서 이미 계산되었을 수 있으나, 명확성을 위해 다시 계산
                    if norm_state > 0 and norm_obj > 0:
                        state_similarity = np.dot(state_embedding_np, obj_embedding_np) / (norm_state * norm_obj)
                
                avg_similarity = (event_similarity + state_similarity) / 2
                max_similarity = max(event_similarity, state_similarity)
                
                if avg_similarity >= similarity_threshold or max_similarity >= similarity_threshold:
                    object_similarities.append((obj_name, float(event_similarity), float(state_similarity), float(avg_similarity), float(max_similarity)))
        
        avg_sorted = sorted(object_similarities, key=lambda x: x[3], reverse=True)
        max_sorted = sorted(object_similarities, key=lambda x: x[4], reverse=True)
        
        return [(obj_name, event_sim) for obj_name, event_sim, _, _, _ in max_sorted[:top_k]]

    def _get_object_description(self, object_name: str) -> str:
        """
        오브젝트의 설명을 찾습니다.
        
        Args:
            object_name: 오브젝트 이름
            
        Returns:
            str: 오브젝트 설명
        """
        objects = self.object_dictionary.get("objects", {})
        return objects.get(object_name, f"Description not found for {object_name}")

    def _create_interactable_objects_list(
        self,
        event_embedding: List[float],
        state_embedding: List[float],
        object_embeddings: Dict[str, Dict[str, List[float]]],
        visible_interactables: List[Dict[str, Any]] = None
    ) -> List[str]:
        """
        상호작용 가능한 오브젝트 리스트를 생성합니다.
        
        Args:
            event_embedding: 이벤트 임베딩
            state_embedding: 상태 임베딩
            object_embeddings: 오브젝트 임베딩 딕셔너리
            visible_interactables: 현재 보이는 상호작용 가능한 객체 목록
            
        Returns:
            List[str]: 상호작용 가능한 오브젝트 이름 리스트
        """
        # 중복 제거를 위한 set 사용
        interactable_objects = set()
        
        # visible_interactables에서 오브젝트 이름 추가
        if visible_interactables:
            for location_data in visible_interactables:
                interactables = location_data.get("interactables", [])
                if isinstance(interactables, list):
                    interactable_objects.update(interactables)
        
        # object_embeddings에서 관련 오브젝트 추가
        if object_embeddings:
            relevant_objects = self._find_relevant_objects(event_embedding, state_embedding, object_embeddings)
            for obj_name, _ in relevant_objects:
                interactable_objects.add(obj_name)
        
        return list(interactable_objects)

    def _create_interactable_objects_string(self, interactable_objects: List[str]) -> str:
        """
        상호작용 가능한 오브젝트 리스트를 문자열로 변환합니다.
        
        Args:
            interactable_objects: 상호작용 가능한 오브젝트 이름 리스트
            
        Returns:
            str: 오브젝트 문자열
        """
        if not interactable_objects:
            return "No interactable objects found."
        
        object_strings = []
        for obj_name in interactable_objects:
            description = self._get_object_description(obj_name)
            if description:
                object_strings.append(f"- {obj_name}: {description}")
        
        return "\n".join(object_strings)

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
        state_embedding: List[float],
        agent_name: str,
        top_k: int = 3,
        similarity_threshold: float = 0.1
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        유사한 메모리 검색
        
        Args:
            event_embedding: 현재 이벤트의 임베딩
            state_embedding: 현재 상태의 임베딩
            agent_name: 에이전트 이름
            top_k: 반환할 메모리 개수
            similarity_threshold: 유사도 임계값
            
        Returns:
            List[Tuple[Dict[str, Any], float]]: (메모리, 유사도) 튜플 리스트
        """
        memories = self.memory_utils._load_memories(sort_by_time=True)
        reflections = self.memory_utils._load_reflections()
        
        if agent_name not in memories or not memories[agent_name]["memories"]:
            return []
        
        memory_items = []
        reflection_items = []
        current_event_embedding_np = np.array(event_embedding)
        current_state_embedding_np = np.array(state_embedding)

        is_current_event_embedding_zero = np.all(current_event_embedding_np == 0)
        is_current_state_embedding_zero = np.all(current_state_embedding_np == 0)
        
        for memory_id, memory in memories[agent_name]["memories"].items():
            if memory.get("event") == "" and memory.get("feedback") == "":
                continue
            memory_embeddings = memories[agent_name]["embeddings"].get(str(memory_id), {})
            memory_with_id = memory.copy()
            memory_with_id["memory_id"] = memory_id
            # 기본 유사도를 0.01로 설정
            calculated_event_similarity = 0.01
            calculated_state_similarity = 0.01

            if memory_embeddings:
                # feedback 우선 확인
                if memory_embeddings.get("feedback"):
                    mem_feedback_embedding_np = np.array(memory_embeddings["feedback"])
                    if not np.all(mem_feedback_embedding_np == 0): # 메모리의 feedback 임베딩이 0이 아닐 때
                        if not is_current_event_embedding_zero: # 현재 이벤트 임베딩이 0이 아닐 때
                            norm_current_event = np.linalg.norm(current_event_embedding_np)
                            norm_mem_feedback = np.linalg.norm(mem_feedback_embedding_np)
                            if norm_current_event > 0 and norm_mem_feedback > 0:
                                calculated_event_similarity = np.dot(current_event_embedding_np, mem_feedback_embedding_np) / (norm_current_event * norm_mem_feedback)
                        
                        if not is_current_state_embedding_zero: # 현재 상태 임베딩이 0이 아닐 때
                            norm_current_state = np.linalg.norm(current_state_embedding_np)
                            norm_mem_feedback = np.linalg.norm(mem_feedback_embedding_np) # 위에서 계산되었을 수 있음
                            if norm_current_state > 0 and norm_mem_feedback > 0:
                                calculated_state_similarity = np.dot(current_state_embedding_np, mem_feedback_embedding_np) / (norm_current_state * norm_mem_feedback)
                
                # feedback이 없는 경우에만 event 확인
                elif memory_embeddings.get("event"):
                    mem_event_embedding_np = np.array(memory_embeddings["event"])
                    if not np.all(mem_event_embedding_np == 0): # 메모리의 event 임베딩이 0이 아닐 때
                        if not is_current_event_embedding_zero: # 현재 이벤트 임베딩이 0이 아닐 때
                            norm_current_event = np.linalg.norm(current_event_embedding_np)
                            norm_mem_event = np.linalg.norm(mem_event_embedding_np)
                            if norm_current_event > 0 and norm_mem_event > 0:
                                calculated_event_similarity = np.dot(current_event_embedding_np, mem_event_embedding_np) / (norm_current_event * norm_mem_event)

                        if not is_current_state_embedding_zero: # 현재 상태 임베딩이 0이 아닐 때
                            norm_current_state = np.linalg.norm(current_state_embedding_np)
                            norm_mem_event = np.linalg.norm(mem_event_embedding_np) # 위에서 계산되었을 수 있음
                            if norm_current_state > 0 and norm_mem_event > 0:
                                calculated_state_similarity = np.dot(current_state_embedding_np, mem_event_embedding_np) / (norm_current_state * norm_mem_event)
                
            avg_similarity = (calculated_event_similarity + calculated_state_similarity) / 2
            max_similarity_val = max(calculated_event_similarity, calculated_state_similarity) # 변수명 변경 max_similarity -> max_similarity_val
            
            if avg_similarity >= similarity_threshold or max_similarity_val >= similarity_threshold:
                memory_items.append((memory_with_id, float(calculated_event_similarity), float(calculated_state_similarity), float(avg_similarity), float(max_similarity_val)))
            else: # 임베딩이 없거나, 계산된 유사도가 낮아도 기본 점수로 추가 (추후 개선 가능)
                memory_items.append((memory_with_id, 0.01, 0.01, 0.01, 0.01))


        # ### 반성 데이터 불안정성, 추후 개선 필요
        
        # # 반성 추가 로직 (유사하게 0 임베딩 체크 및 기본 유사도 0.01 적용 필요)
        # if agent_name in reflections:
        #     for reflection in reflections[agent_name]["reflections"]:
        #         reflection_embedding = reflection.get("embedding", [])
        #         if reflection_embedding:
        #             max_event_similarity = 0.01
        #             max_state_similarity = 0.01
                
        #             reflection_embedding = np.array(reflection_embedding)
        #             if not np.all(reflection_embedding == 0):  # 임베딩이 0이 아닐 때만 계산
        #                 if not is_current_event_embedding_zero:  # 현재 이벤트 임베딩이 0이 아닐 때
        #                     norm_current_event = np.linalg.norm(current_event_embedding_np)
        #                     norm_reflection = np.linalg.norm(reflection_embedding)
        #                     if norm_current_event > 0 and norm_reflection > 0:
        #                         event_similarity = np.dot(current_event_embedding_np, reflection_embedding) / (norm_current_event * norm_reflection)
        #                         max_event_similarity = max(max_event_similarity, float(event_similarity))
                        
        #                 if not is_current_state_embedding_zero:  # 현재 상태 임베딩이 0이 아닐 때
        #                     norm_current_state = np.linalg.norm(current_state_embedding_np)
        #                     norm_reflection = np.linalg.norm(reflection_embedding)  # 위에서 계산되었을 수 있음
        #                     if norm_current_state > 0 and norm_reflection > 0:
        #                         state_similarity = np.dot(current_state_embedding_np, reflection_embedding) / (norm_current_state * norm_reflection)
        #                         max_state_similarity = max(max_state_similarity, float(state_similarity))
                
        #             avg_similarity = (max_event_similarity + max_state_similarity) / 2
        #             max_similarity = max(max_event_similarity, max_state_similarity)
                    
        #             if avg_similarity >= similarity_threshold or max_similarity >= similarity_threshold:
        #                 reflection_items.append((reflection, max_event_similarity, max_state_similarity, avg_similarity, max_similarity))
        
        # 시간순으로 정렬하여 가중치 계산
        def get_time(item):
            return item.get("time", "")
            
        memory_items.sort(key=lambda x: get_time(x[0]), reverse=True)
        reflection_items.sort(key=lambda x: get_time(x[0]), reverse=True)
        
        # -------------------------------------------------------------------
        # 1) 파라미터: 선형 가중합 계수
        memory_alpha, memory_beta, memory_gamma = 0.5, 0.2, 0.3
        K = 20  # 포물선형 시간 가중치 계산용

        valued_items = []
        to_print_items = []

        ## 메모리 
        for i, (item, event_sim, state_sim, avg_sim, max_sim) in enumerate(memory_items):
        
            # (1) 시간 가중치
            t = min(i, K) / K
            time_weight = max(1.0 - t**2, 0.01)

            # (2) 중요도 정규화
            importance = float(item.get("importance", 3))
            imp_norm = importance / 10.0

            # (3) 유사도 최고치
            sim_max = max(event_sim, state_sim)

            # (4) 최종 점수 계산
            final_score = (
                memory_alpha * sim_max
            + memory_beta  * imp_norm
            + memory_gamma * time_weight
            )

            valued_items.append((item, final_score, False))
            to_print_items.append((item, final_score, sim_max, imp_norm, time_weight, event_sim, state_sim))

        ## 반성
        
        # reflection_alpha, reflection_beta, reflection_gamma = 0.7, 0.1, 0.1


        # for i, (item, event_sim, state_sim, avg_sim, max_sim) in enumerate(reflection_items):
        #     # (1) 시간 가중치
        #     t = min(i, K) / K
        #     time_weight = max(1.0 - t**2, 0.01)

        #     # (2) 중요도 정규화
        #     importance = float(item.get("importance", 3))
        #     imp_norm = importance / 10.0

        #     # (3) 유사도 최고치
        #     sim_max = max(event_sim, state_sim)

        #     # (4) 최종 점수 계산
        #     final_score = (
        #         reflection_alpha * sim_max
        #     + reflection_beta  * imp_norm
        #     + reflection_gamma * time_weight
        #     )

        #     valued_items.append((item, final_score, True))
        #     to_print_items.append((item, final_score, sim_max, imp_norm, time_weight, event_sim, state_sim))

        # final_score 기준 내림차순 정렬
        valued_items.sort(key=lambda x: x[1], reverse=True)
        to_print_items.sort(key=lambda x: x[1], reverse=True)

        # 인자로 넘어온 top_k 사용
        result = valued_items[:top_k]

        for mem, score, sim_avg, imp_norm, tw, e_sim, s_sim in to_print_items[:top_k]:
            print(f"=== 메모리 ID: {mem.get('memory_id')} ===")
            print(f"  Final Score : {score:.4f}")
            print(f"    sim_max   : {sim_avg:.4f}  (event_sim={e_sim:.4f}, state_sim={s_sim:.4f})")
            print(f"    importance: {imp_norm:.4f}")
            print(f"    time_weight: {tw:.4f}")
            print()
        
        # # 결과가 부족한 경우 최근 메모리로 채우기
        # if len(result) < top_k:
        #     # 이미 선택된 메모리 ID 수집
        #     selected_memory_ids = {item.get("memory_id") for item, _ in result}
            
        #     # 추가로 필요한 메모리 개수 계산
        #     needed_count = top_k - len(result)
            
        #     # 최근 메모리 가져오기
        #     recent_memories = self._get_recent_memories(
        #         agent_name,
        #         top_k=needed_count,
        #         exclude_memory_ids=selected_memory_ids
        #     )
            
        #     # 최근 메모리 추가
        #     result.extend(recent_memories)
        
        return result

    def _create_event_string(self, memory: Dict[str, Any], is_reflection: bool) -> str:
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
        if is_reflection:
            if thought and thought != "":
                content = f"Thought: {thought}\n"
        else:
            if event and event != "":
                if event_role != "" and event_role != " ":
                    content = f"Event: {event_role}, {event}\n"
                else:
                    content = f"Event: {event}\n"
            if feedback and feedback != "":
                content = f"Feedback: {feedback}\n"
        
        return f"- {content}\n"
        

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
            interactable_strings.append(f"- (Objects: ({', '.join(sorted_objects)}) in Location: {location})")
        
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
            if hunger >= 90:
                state_strings.append("EXTREMELY HUNGRY")
            elif hunger >= 70:
                state_strings.append("extremely hungry")
            elif hunger >= 40:
                state_strings.append("very hungry")
            elif hunger >= 20:
                state_strings.append("slightly hungry")
            elif hunger < -70:
                state_strings.append("You can't eat anymore")
                
        if "loneliness" in state:
            loneliness = state["loneliness"]
            if loneliness >= 70:
                state_strings.append("very lonely")
            elif loneliness >= 40:
                state_strings.append("lonely")
            elif loneliness >= 20:
                state_strings.append("slightly lonely")
            elif loneliness < -70:
                state_strings.append("you want to be alone")
                
        if "sleepiness" in state and state["sleepiness"] > 0:
            sleepiness = state["sleepiness"]
            if sleepiness >= 90:
                state_strings.append("EXTREMELY SLEEPY")
            elif sleepiness >= 70:
                state_strings.append("very sleepy")
            elif sleepiness >= 40:
                state_strings.append("sleepy")
            elif sleepiness >= 20:
                state_strings.append("slightly sleepy")
            elif sleepiness <= -70:
                state_strings.append("you feel completely awake")
                
        if "stress" in state and state["stress"] > 0:
            stress = state["stress"]
            if stress >= 70:
                state_strings.append("very stressed")
            elif stress >= 40:
                state_strings.append("stressed")
            elif stress >= 10:
                state_strings.append("slightly stressed")
        
        ## 빈 배열일 경우 문자열 추가
        if not state_strings:
            state_strings.append("completely fine")

        return ", ".join(state_strings) if state_strings else ""

    def create_reaction_prompt(
        self,
        event_sentence: str,
        event_embedding: List[float],
        state_embedding: List[float],
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
            state_embedding: 현재 상태의 임베딩
            event_role: 이벤트 역할
            agent_name: 에이전트 이름
            prompt_template: 프롬프트 템플릿
            agent_data: 에이전트 데이터 (성격, 위치, 상호작용 가능한 객체 등)
            similar_data_cnt: 유사한 이벤트 개수
            similarity_threshold: 유사도 임계값
            object_embeddings: 오브젝트 임베딩 리스트
            
        Returns:
            Optional[str]: 생성된 프롬프트
        """
        
        # 유사한 메모리 검색
        similar_memories = self._find_similar_memories(
            event_embedding,
            state_embedding,
            agent_name,
            top_k=similar_data_cnt,
            similarity_threshold=similarity_threshold
        )
        
        # 중복 제거를 위한 Set 사용
        processed_events = set()
        similar_events = []
        
        for memory, _, is_reflection in similar_memories:
            # 메모리 문자열 생성
            event_str = self._create_event_string(memory, is_reflection)
            if event_str not in processed_events:
                similar_events.append(event_str)
                processed_events.add(event_str)
        
        similar_event_str = "\n".join(similar_events) if similar_events else "No similar past events found."
        
        # 상태 정보 처리
        state_str = ""
        if agent_data and "state" in agent_data:
            state_str = self._format_state(agent_data["state"])
        

        
        # 상호작용 가능한 객체 정보 처리
        visible_interactables_str = ""
        if agent_data and "visible_interactables" in agent_data:
            visible_interactables_str = self._format_visible_interactables(agent_data["visible_interactables"])
        
        # 상호작용 가능한 오브젝트 리스트 생성
        interactable_objects = self._create_interactable_objects_list(
            event_embedding,
            state_embedding,
            object_embeddings,
            agent_data.get("visible_interactables") if agent_data else None
        )
        
        # 상호작용 가능한 오브젝트 문자열 생성
        interactable_objects_str = self._create_interactable_objects_string(interactable_objects)
        
        # 에이전트 정보 문자열 생성
        agent_data_str = f"Your Name: {agent_name}\n"

        agent_data_str += f"Your Current Location: {agent_data['current_location']}\n"
        
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
                EVENT_CONTENT=f"{event_role} {event_sentence}",
                RELEVANT_MEMORIES=similar_event_str,
                RELEVANT_OBJECTS=interactable_objects_str
            )
            return prompt
        except Exception as e:
            print(f"프롬프트 생성 중 오류 발생: {e}")
            return None

    def _get_recent_memories(
        self,
        agent_name: str,
        top_k: int = 3,
        exclude_memory_ids: Set[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        최근 메모리를 가져옵니다.
        
        Args:
            agent_name: 에이전트 이름
            top_k: 반환할 메모리 개수
            exclude_memory_ids: 제외할 메모리 ID 집합
            
        Returns:
            List[Tuple[Dict[str, Any], float]]: (메모리, 기본 유사도) 튜플 리스트
        """
        memories = self.memory_utils._load_memories()
        
        if agent_name not in memories:
            return []
            
        # 메모리를 시간순으로 정렬
        memory_list = []
        for memory_id, memory in memories[agent_name]["memories"].items():
            if exclude_memory_ids and memory_id in exclude_memory_ids:
                continue
                
            memory_with_id = memory.copy()
            memory_with_id["memory_id"] = memory_id
            memory_list.append(memory_with_id)
            
        # 시간 기준으로 정렬 (최신순)
        memory_list.sort(key=lambda x: x.get("time", ""), reverse=True)
        
        # 상위 k개 메모리 반환 (기본 유사도 0.5 부여)
        return [(memory, 0.5) for memory in memory_list[:top_k]]