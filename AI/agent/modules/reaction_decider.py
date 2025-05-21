"""
반응 판단 모듈

이벤트에 대해 반응해야 하는지 여부를 판단합니다.
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pathlib import Path
from datetime import datetime
from .retrieve import MemoryRetriever

class ReactionDecider:
    def __init__(self, memory_utils, ollama_client, word2vec_model, similarity_threshold: float = 0.1):
        """
        반응 판단기 초기화
        
        Args:
            memory_utils: MemoryUtils 인스턴스
            ollama_client: OllamaClient 인스턴스
            word2vec_model: Word2Vec 모델
            similarity_threshold: 유사 메모리 검색을 위한 유사도 임계값
        """
        self.memory_utils = memory_utils
        self.ollama_client = ollama_client
        self.word2vec_model = word2vec_model
        self.similarity_threshold = similarity_threshold
        
        # 현재 파일의 절대 경로를 기준으로 상위 디렉토리 찾기
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent.parent  # AI 디렉토리
        agent_dir = root_dir / "agent"
        prompts_dir = agent_dir / "prompts" / "reaction"
        
        # 시스템 프롬프트와 반응 판단 프롬프트 파일 경로
        self.system_prompt_path = str(prompts_dir / "reaction_system.txt")
        self.reaction_prompt_path = str(prompts_dir / "reaction_prompt.txt")
        
        # 기본 프롬프트 템플릿 (영어로 변경)
        self.default_system_prompt = """
You are an AI decision-maker that determines whether an agent should react to a given event.
Your task is to analyze the event context and return ONLY a valid JSON object with a clear True or False decision.

IMPORTANT: Your entire response must be ONLY A SINGLE VALID JSON OBJECT with the format:
{
    "should_react": true/false,
    "reason": "brief explanation"
}

Do not include any additional text, explanations, or markdown formatting outside this JSON object.
"""
        
        self.default_reaction_prompt = """
You are {AGENT_NAME}. You need to decide whether to react to the following event.

Current event:
{EVENT_CONTENT}

Similar past events:
{SIMILAR_EVENT}

{AGENT_NAME}'s personality:
{PERSONALITY}

Situation analysis:
1. Is this event important to {AGENT_NAME}?
2. Given {AGENT_NAME}'s personality, would they be interested in this event?
3. Has {AGENT_NAME} reacted to similar events in the past?
4. Does this event directly impact {AGENT_NAME}'s current state or activities?

IMPORTANT: You must respond with ONLY a JSON object in the following format:
{{
    "should_react": true/false,
    "reason": "reason for reacting/not reacting"
}}

Keep your explanation concise and provide ONLY this JSON with NO additional text.
"""
        self._ensure_prompt_files_exist()
    
    def _ensure_prompt_files_exist(self):
        """프롬프트 파일이 존재하는지 확인하고, 없다면 기본 템플릿으로 생성"""
        os.makedirs(os.path.dirname(self.system_prompt_path), exist_ok=True)
        
        if not os.path.exists(self.system_prompt_path):
            with open(self.system_prompt_path, 'w', encoding='utf-8') as f:
                f.write(self.default_system_prompt)
        
        if not os.path.exists(self.reaction_prompt_path):
            with open(self.reaction_prompt_path, 'w', encoding='utf-8') as f:
                f.write(self.default_reaction_prompt)
    
    def _load_prompt(self, file_path: str, default_template: str) -> str:
        """프롬프트 파일 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"프롬프트 파일 로드 실패: {e}, 기본 템플릿 사용")
            return default_template
    
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
            # to_print_items.append((item, final_score, sim_max, imp_norm, time_weight, event_sim, state_sim))

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
                state_strings.append("want to be alone")
                
        # sleepiness와 stress는 0 이하일 때 표시하지 않음
        if "sleepiness" in state and state["sleepiness"] > 0:
            sleepiness = state["sleepiness"]
            if sleepiness >= 90:
                state_strings.append("EXTREMELY SLEEPY")
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
        
        ## 빈 배열일 경우 문자열 추가
        if not state_strings:
            state_strings.append("completely fine")

        return ", ".join(state_strings) if state_strings else ""

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
        feedback_negative = memory.get("feedback_negative", "")
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
                content = f"Feedback: {feedback + feedback_negative}\n"
        
        return f"- {content}\n"
    
    async def should_react_to_event(self, event: Dict[str, Any], agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        이벤트에 반응해야 하는지 판단
        
        Args:
            event: 이벤트 데이터
            agent_data: 에이전트 데이터
            
        Returns:
            Dict[str, Any]: 반응 여부와 이유
        """
        agent_name = agent_data.get("name", "Unknown")
        
        # 이벤트를 문장으로 변환
        event_sentence = self.memory_utils.event_to_sentence(event)
        
        # 임베딩 생성
        event_embedding = self.memory_utils.get_embedding(event_sentence)


        need_sentence = self._format_state(agent_data.get("state", {}))
        

        need_state_embedding = self.memory_utils.get_embedding(need_sentence)

        # 유사한 메모리 검색
        similar_memories = self._find_similar_memories(event_embedding, need_state_embedding, agent_name, 3, 0.1)
        
        # 중복 제거를 위한 Set 사용
        processed_events = set()
        similar_events = []
        
        for memory, _, is_reflection in similar_memories:
            # 메모리 문자열 생성
            event_str = self._create_event_string(memory, is_reflection)
            if event_str not in processed_events:
                similar_events.append(event_str)
                processed_events.add(event_str)

        # 유사한 메모리 포맷팅
        similar_memories_str = "\n".join(similar_events) if similar_events else "No similar past events found."
        
        # 프롬프트 템플릿 로드
        system_prompt = self._load_prompt(self.system_prompt_path, self.default_system_prompt)
        reaction_prompt = self._load_prompt(self.reaction_prompt_path, self.default_reaction_prompt)

        # 에이전트 성격 추출 (영어로 설명 필요시 번역)
        personality = agent_data.get("personality", "No specific personality information available.")
        
        # 프롬프트 생성
        prompt = reaction_prompt.format(
            AGENT_NAME=agent_name,
            EVENT_CONTENT=event_sentence,
            SIMILAR_EVENT=similar_memories_str,
            PERSONALITY=personality
        )
        
        try:
            # Ollama API 호출
            response = await self.ollama_client.process_prompt(
                prompt=prompt,
                system_prompt=system_prompt,
                model_name="gemma3"
            )
            
            if response.get("status") != "success":
                print(f"🚫 API 응답 실패: {response}")
                return {
                    "should_react": True,  # 오류 발생 시 기본적으로 반응
                    "reason": "Error occurred during decision. Defaulting to react for safety."
                }
            
            # 응답 가져오기
            answer = response.get("response", "").strip()
            print(f"📝 모델 응답: {answer}")
            
            # JSON 파싱
            import re
            import json
            
            # JSON 형식 추출
            json_match = re.search(r'\{[\s\S]*\}', answer)
            if json_match:
                json_str = json_match.group(0)
                try:
                    result = json.loads(json_str)
                    print(f"🤔 결정: {'반응' if result.get('should_react', True) else '무시'}, 이유: {result.get('reason', '')}")
                    return result
                except json.JSONDecodeError:
                    print(f"❌ JSON 파싱 실패: {json_str}")
            
            # 기본값 반환
            return {
                "should_react": True,
                "reason": "Failed to parse response. Defaulting to react for safety."
            }
                
        except Exception as e:
            print(f"❌ API 호출 중 오류 발생: {e}")
            return {
                "should_react": True,
                "reason": f"Error: {e}. Defaulting to react for safety."
            }