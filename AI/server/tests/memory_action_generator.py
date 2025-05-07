"""
OLLAMA를 사용하지 않고 임베딩 -> 임베딩 파일 생성 -> 유사 메모리 검색 -> 액션 생성
"""

import os
import json
import time
import numpy as np
import gensim.downloader as api
from numpy import dot
from numpy.linalg import norm
from typing import List, Dict, Any, Tuple
import datetime
import random
import re

class MemoryActionGenerator:
    def __init__(self, memory_file_path: str, prompt_folder: str, model_name: str = "word2vec-google-news-300"):
        """
        메모리 기반 액션 생성기 초기화
        
        Parameters:
        - memory_file_path: 메모리 JSON 파일 경로
        - prompt_folder: 프롬프트 파일이 있는 폴더 경로
        - model_name: 사용할 Word2Vec 모델 이름
        """
        self.memory_file_path = memory_file_path  # 메모리 파일 경로 저장
        
        # 시간 측정 시작
        start_time = time.time()
        print(f"로딩 시작: Word2Vec 모델 '{model_name}'...")
        
        # Word2Vec 모델 로드
        self.model = api.load(model_name)
        
        # 모델 로딩 시간 출력
        model_load_time = time.time() - start_time
        print(f"모델 로딩 완료 (소요 시간: {model_load_time:.2f}초)")
        
        # 메모리 로드
        start_time = time.time()
        print(f"메모리 로딩 중: {memory_file_path}...")
        self.memory_data = self._load_memory(memory_file_path)
        
        # 메모리 로딩 시간 출력
        memory_load_time = time.time() - start_time
        print(f"메모리 로드 완료 (소요 시간: {memory_load_time:.2f}초)")
        
        # 메모리 중복 제거
        self._remove_duplicates()
        
        # 메모리에 임베딩 추가
        start_time = time.time()
        print("메모리 임베딩 생성 중...")
        self._add_embeddings_to_memories()
        
        # 임베딩 생성 시간 출력
        embedding_time = time.time() - start_time
        print(f"임베딩 생성 완료 (소요 시간: {embedding_time:.2f}초)")
        
        # 임베딩이 추가된 메모리 저장 - 이 부분이 추가됨
        output_path = os.path.splitext(memory_file_path)[0] + "_with_embeddings.json"
        self._save_memory_with_embeddings(output_path)
        
        # 프롬프트 폴더 저장
        self.prompt_folder = prompt_folder
        
        # 결과 저장용 폴더 생성
        self.results_folder = "action_results"
        os.makedirs(self.results_folder, exist_ok=True)

    def _load_memory(self, memory_file_path: str) -> Dict:
        """
        메모리 파일 로드
        
        Parameters:
        - memory_file_path: 메모리 JSON 파일 경로
        
        Returns:
        - 메모리 데이터
        """
        try:
            with open(memory_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"메모리 파일 로드 오류: {e}")
            return {}
    
    def _remove_duplicates(self):
        """메모리에서 중복된 이벤트-액션 쌍 제거"""
        for agent_name, agent_data in self.memory_data.items():
            # 중복 체크를 위한 집합
            seen_events = set()
            unique_memories = []
            
            for memory in agent_data["memories"]:
                # 이벤트와 액션을 결합하여 중복 체크
                event_action_pair = (memory["event"], memory["action"])
                
                if event_action_pair not in seen_events:
                    seen_events.add(event_action_pair)
                    unique_memories.append(memory)
            
            # 중복이 제거된 메모리로 업데이트
            self.memory_data[agent_name]["memories"] = unique_memories
            
            print(f"중복 제거: {len(agent_data['memories']) - len(unique_memories)}개 중복 메모리 제거됨")

    def _get_sentence_vector(self, sentence: str) -> np.ndarray:
        """
        문장을 임베딩 벡터로 변환
        
        Parameters:
        - sentence: 임베딩할 문장
        
        Returns:
        - 문장 임베딩 벡터
        """
        tokens = [w.lower() for w in sentence.split() if w.lower() in self.model]
        if not tokens:
            return np.zeros(self.model.vector_size)
        
        # 단어 벡터의 평균을 문장 벡터로 사용
        return np.mean([self.model[w] for w in tokens], axis=0)

    def _calculate_cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """
        두 벡터 간의 코사인 유사도 계산
        
        Parameters:
        - v1: 첫 번째 벡터
        - v2: 두 번째 벡터
        
        Returns:
        - 코사인 유사도 (0~1 사이 값)
        """
        if np.all(v1 == 0) or np.all(v2 == 0):
            return 0.0
        return float(dot(v1, v2) / (norm(v1) * norm(v2)))

    def _add_embeddings_to_memories(self):
        """
        모든 메모리에 임베딩 추가
        """
        total_memories = 0
        
        for agent_name, agent_data in self.memory_data.items():
            memories = agent_data["memories"]
            total_memories += len(memories)
            
            for i, memory in enumerate(memories):
                # event와 action을 합쳐서 임베딩 생성
                combined_text = f"{memory['event']} {memory['action']}"
                
                # 임베딩 벡터 생성 - 실제 계산이 일어나는 부분
                embedding_vector = self._get_sentence_vector(combined_text)
                
                # 메모리에 임베딩 벡터 추가
                self.memory_data[agent_name]["memories"][i]["embedding_vector"] = embedding_vector
                
                # 진행 상황 출력 (10개마다)
                if (i + 1) % 10 == 0 or i + 1 == len(memories):
                    print(f"임베딩 생성 진행 중: {i + 1}/{len(memories)}")

    def find_similar_memories(self, query: str, top_k: int = 20, similarity_threshold: float = 0.5) -> List[Tuple[Dict, float]]:
        """
        쿼리와 유사한 메모리 검색
        
        Parameters:
        - query: 검색 쿼리
        - top_k: 반환할 최대 메모리 수
        - similarity_threshold: 유사도 임계값 (이보다 낮은 유사도는 제외)
        
        Returns:
        - 유사도 순으로 정렬된 (메모리, 유사도) 튜플 리스트
        """
        start_time = time.time()
        
        # 쿼리 임베딩 생성
        query_vector = self._get_sentence_vector(query)
        query_embedding_time = time.time() - start_time
        print(f"쿼리 임베딩 생성 완료 (소요 시간: {query_embedding_time:.4f}초)")
        
        similarities = []
        
        # 모든 에이전트의 메모리에 대해 유사도 계산
        similarity_start_time = time.time()
        for agent_name, agent_data in self.memory_data.items():
            for memory in agent_data["memories"]:
                # 메모리 임베딩 벡터 가져오기
                memory_vector = memory.get("embedding_vector")
                
                if memory_vector is not None:
                    # 코사인 유사도 계산
                    similarity = self._calculate_cosine_similarity(query_vector, memory_vector)
                    if similarity >= similarity_threshold:
                        similarities.append((memory, similarity))
        
        similarity_time = time.time() - similarity_start_time
        print(f"유사도 계산 완료 (소요 시간: {similarity_time:.4f}초)")
        
        # 유사도 기준 내림차순 정렬
        sort_start_time = time.time()
        sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)
        sort_time = time.time() - sort_start_time
        print(f"정렬 완료 (소요 시간: {sort_time:.4f}초)")
        
        # 상위 k개 반환
        total_time = time.time() - start_time
        print(f"전체 검색 완료 (소요 시간: {total_time:.4f}초)")
        
        # 유사도가 임계값 이상인 결과만 반환
        return sorted_similarities[:top_k]

    def load_prompt_file(self, file_path: str) -> str:
        """
        프롬프트 파일 로드
        
        Parameters:
        - file_path: 프롬프트 파일 경로
        
        Returns:
        - 프롬프트 내용
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (FileNotFoundError, UnicodeDecodeError) as e:
            print(f"프롬프트 파일 로드 오류: {e}")
            return ""

    def extract_agent_info(self, prompt_text: str) -> Dict[str, Any]:
        """
        프롬프트에서 에이전트 정보 추출
        
        Parameters:
        - prompt_text: 프롬프트 텍스트
        
        Returns:
        - 에이전트 정보 (이름, 상태, 위치 등)
        """
        agent_info = {}
        
        # 정규 표현식으로 에이전트 정보 추출
        agent_match = re.search(r'([\w]+): ([\w\s,]+), at ([\w\s]+)', prompt_text)
        if agent_match:
            agent_info["name"] = agent_match.group(1)
            agent_info["state"] = agent_match.group(2)
            agent_info["location"] = agent_match.group(3)
        
        # 상태 분석
        if "state" in agent_info:
            state_text = agent_info["state"].lower()
            agent_info["is_hungry"] = "hungry" in state_text and "not hungry" not in state_text
            agent_info["is_sleepy"] = "sleepy" in state_text and "not sleepy" not in state_text
            agent_info["is_lonely"] = "lonely" in state_text and "not lonely" not in state_text
        
        # 가시적 객체와 상호작용 가능 항목 추출
        visible_match = re.search(r'Visible: ([\w\s,]+)', prompt_text)
        if visible_match:
            agent_info["visible_objects"] = visible_match.group(1).split(", ")
        
        interact_match = re.search(r'Can interact with: ([\w\s,]+)', prompt_text)
        if interact_match:
            agent_info["interactable_items"] = interact_match.group(1).split(", ")
        
        return agent_info

    def generate_action(self, prompt_text: str, relevant_memories: List[Tuple[Dict, float]]) -> Dict[str, Any]:
        """
        프롬프트와 관련 메모리를 기반으로 액션 생성
        
        Parameters:
        - prompt_text: 프롬프트 텍스트
        - relevant_memories: 관련 메모리 리스트 (메모리, 유사도)
        
        Returns:
        - 생성된 액션
        """
        # 에이전트 정보 추출
        agent_info = self.extract_agent_info(prompt_text)
        
        # 액션 결정 로직
        action_type = "idle"  # 기본 액션
        target = ""
        location = agent_info.get("location", "house").lower()
        message = ""
        using = None
        reason = "No specific reason"
        memory_action = ""
        importance = 1  # 기본 중요도
        
        # 배고픔 상태 확인
        if agent_info.get("is_hungry", False):
            action_type = "eat"
            
            # Kitchen이 상호작용 가능하면 집에서 식사
            if any("Kitchen" in item for item in agent_info.get("interactable_items", [])):
                target = "Kitchen"
                location = "house"
                message = "I'm hungry, I should eat something."
                memory_action = f"Had a meal at home"
                reason = "I'm feeling very hungry and need to eat to satisfy my hunger."
                importance = random.randint(1, 3)  # 혼자 식사는 중요도 낮음
                
            # 아니면 카페테리아 방문
            elif any("Cafeteria" in item for item in agent_info.get("interactable_items", [])):
                target = "Cafeteria"
                location = "cafeteria"
                message = "I'm heading to the cafeteria to get some food."
                memory_action = f"Had a meal at the cafeteria"
                reason = "I'm very hungry and want to eat at the cafeteria."
                
                # 카페테리아는 사회적 공간이므로 다른 사람과 함께할 가능성이 있음
                if random.random() < 0.7:  # 70% 확률로 다른 사람과 함께 식사
                    people = ["Alice", "Bob", "Charlie", "Diana", "Eva", "Frank"]
                    companion = random.choice(people)
                    memory_action = f"Had a meal with {companion} at the cafeteria"
                    importance = random.randint(4, 7)  # 함께하는 활동은 중요도 중간
                    reason = f"I'm very hungry and decided to eat with {companion} at the cafeteria."
                else:
                    importance = random.randint(2, 3)  # 혼자 카페테리아에서 식사
                
        # 졸음 상태 확인
        elif agent_info.get("is_sleepy", False):
            action_type = "sleep"
            
            # Bedroom이 상호작용 가능하면 침실에서 수면
            if any("Bedroom" in item for item in agent_info.get("interactable_items", [])):
                target = "Bedroom"
                location = "house"
                message = "I'm really tired, time to get some sleep."
                memory_action = f"Slept in bedroom"
                reason = "I'm feeling very sleepy and need to rest in my bedroom."
                importance = random.randint(1, 3)  # 일상적 수면은 중요도 낮음
                
                # 간혹 중요한 꿈을 꾸는 경우 (10% 확률)
                if random.random() < 0.1:
                    memory_action = f"Had a very important dream about future"
                    importance = random.randint(8, 10)  # 중요한 사건
                    reason = "I had a sleep that gave me an important revelation that will affect my future."
            
            # 아니면 LivingRoom에서 휴식
            elif any("LivingRoom" in item for item in agent_info.get("interactable_items", [])):
                target = "LivingRoom"
                location = "house"
                message = "I need to rest for a while."
                memory_action = f"Took a nap in the living room"
                reason = "I'm sleepy but there's no bedroom available, so I'll rest in the living room."
                importance = random.randint(1, 3)  # 혼자 하는 일상적 활동
                
        # 외로움 상태 확인
        elif agent_info.get("is_lonely", False):
            action_type = "move"
            
            # 카페테리아로 이동
            if any("Cafeteria" in item for item in agent_info.get("interactable_items", [])):
                target = "Cafeteria"
                location = "cafeteria"
                message = "I feel lonely, I should go where people gather."
                
                # 사람들을 만나는 경우
                people = ["Alice", "Bob", "Charlie", "Diana", "Eva", "Frank"]
                num_people = random.randint(1, 3)
                companions = random.sample(people, num_people)
                
                if num_people == 1:
                    memory_action = f"Met {companions[0]} at the cafeteria"
                    importance = random.randint(4, 7)  # 함께하는 활동
                    reason = f"I was feeling lonely and went to meet {companions[0]} at the cafeteria."
                else:
                    memory_action = f"Socialized with {', '.join(companions)} at the cafeteria"
                    importance = random.randint(4, 7)  # 함께하는 활동
                    reason = f"I was feeling lonely and socialized with friends at the cafeteria."
                
                # 특별한 이벤트가 있는 경우 (15% 확률)
                if random.random() < 0.15:
                    events = [
                        "celebrated a birthday", 
                        "had an important conversation about future", 
                        "discussed a project collaboration",
                        "resolved a misunderstanding"
                    ]
                    special_event = random.choice(events)
                    memory_action = f"{special_event} with {', '.join(companions)} at the cafeteria"
                    importance = random.randint(8, 10)  # 중요한 이벤트
                    reason = f"I went to the cafeteria and {special_event} with friends, which will impact my future."
            
            # 아니면 LivingRoom에서 대기
            elif any("LivingRoom" in item for item in agent_info.get("interactable_items", [])):
                target = "LivingRoom"
                location = "house"
                message = "I'll wait in the living room for someone to talk to."
                memory_action = f"Waited in the living room for company"
                reason = "I feel lonely, so I'm going to the living room where I might meet someone."
                importance = random.randint(1, 3)  # 혼자 하는 활동
                
        # 기본 상태(특별한 필요 없음)
        else:
            # 다양한 일상 액션 중 랜덤 선택
            daily_actions = [
                ("interact", "Desk", "house", "Worked on some documents", 
                 "I need to catch up on some work.", random.randint(1, 3)),
                
                ("interact", "Kitchen", "house", "Cleaned the kitchen", 
                 "The kitchen could use some cleaning.", random.randint(1, 3)),
                
                ("move", "LivingRoom", "house", "Relaxed in the living room", 
                 "I feel like relaxing for a bit.", random.randint(1, 3)),
                
                ("move", "Cafeteria", "cafeteria", "Went to cafeteria to see what's happening", 
                 "I wonder what's going on at the cafeteria.", random.randint(1, 3))
            ]
            
            # 랜덤 선택
            action_choice = random.choice(daily_actions)
            action_type = action_choice[0]
            target = action_choice[1]
            location = action_choice[2]
            memory_action = action_choice[3]
            reason = action_choice[4]
            importance = action_choice[5]
            message = f"I think I'll {action_type} at the {target}."
            
            # 일정 확률(30%)로 다른 사람과 함께하는 활동으로 변경
            if random.random() < 0.3:
                people = ["Alice", "Bob", "Charlie", "Diana", "Eva", "Frank"]
                companion = random.choice(people)
                
                social_activities = [
                    f"Chatted with {companion} at {location}",
                    f"Had a nice conversation with {companion} at {location}",
                    f"Spent time with {companion} at {location}",
                    f"Met {companion} at {location}"
                ]
                
                memory_action = random.choice(social_activities)
                reason = f"I decided to spend some time with {companion}."
                importance = random.randint(4, 7)  # 함께하는 활동은 중요도 중간
                message = f"I'll talk with {companion}."
                action_type = "talk"
                
                # 특별한 사건이 있는 경우 (10% 확률)
                if random.random() < 0.1:
                    major_events = [
                        f"Made an important decision with {companion}",
                        f"Resolved a conflict with {companion}",
                        f"Planned a big project with {companion}",
                        f"Learned an important life lesson from {companion}"
                    ]
                    
                    memory_action = random.choice(major_events)
                    reason = f"I had a significant interaction with {companion} that will affect my future."
                    importance = random.randint(8, 10)  # 중요한 사건은 중요도 높음
        
        # 관련 메모리가 있으면 참고하여 행동 보완 (액션 타입 등은 유지)
        if relevant_memories:
            for memory, similarity in relevant_memories[:3]:  # 상위 3개만 고려
                # 높은 유사도의 메모리에서 참고사항 획득
                if similarity > 0.7:
                    # 메모리의 액션 세부사항 활용
                    memory_action_parts = memory["action"].split()
                    if len(memory_action_parts) >= 2:
                        # 메시지에 과거 경험 참조 추가
                        message += f" (I recall doing something similar before.)"
                        # 이유에 과거 경험 참조 추가
                        reason += f" I've done something similar in the past."
                        break
        
        # 현재 시간 가져오기
        current_time = datetime.datetime.now().strftime("%H:%M, Day %d")
        
        # 액션 결과 생성
        result = {
            "actions": {
                "agent": agent_info.get("name", "unknown"),
                "action": action_type,
                "details": {
                    "location": location,
                    "target": target,
                    "using": using,
                    "message": message
                },
                "memory_update": {
                    "action": memory_action if memory_action else f"{action_type} at {location}",
                    "time": current_time,
                    "importance": importance
                },
                "reason": reason
            }
        }
        
        return result

    def process_prompt_files(self):
        """
        프롬프트 폴더의 모든 파일 처리
        """
        # 프롬프트 폴더 내 모든 텍스트 파일 검색
        prompt_files = [f for f in os.listdir(self.prompt_folder) if f.endswith('.txt')]
        
        if not prompt_files:
            print(f"경고: {self.prompt_folder} 폴더에 텍스트 파일이 없습니다.")
            return
        
        print(f"{len(prompt_files)}개의 프롬프트 파일을 처리합니다.")
        
        for file_name in prompt_files:
            file_path = os.path.join(self.prompt_folder, file_name)
            print(f"\n파일 처리 중: {file_name}")
            
            # 프롬프트 로드
            prompt_text = self.load_prompt_file(file_path)
            if not prompt_text:
                print(f"경고: {file_name} 파일이 비어있거나 로드할 수 없습니다.")
                continue
            
            # 프롬프트를 쿼리로 사용하여 유사 메모리 검색
            similar_memories = self.find_similar_memories(prompt_text, top_k=20)
            
            # 각 k 값(1, 5, 10, 15, 20)에 대해 액션 생성
            k_values = [1, 5, 10, 15, 20]
            
            for k in k_values:
                if k <= len(similar_memories):
                    print(f"\n상위 {k}개 메모리 사용하여 액션 생성:")
                    
                    # 액션 생성
                    action_result = self.generate_action(prompt_text, similar_memories[:k])
                    
                    # 결과 출력
                    print(json.dumps(action_result, ensure_ascii=False, indent=2))
                    
                    # 결과 파일 저장
                    output_filename = f"{os.path.splitext(file_name)[0]}_top{k}.json"
                    output_path = os.path.join(self.results_folder, output_filename)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(action_result, f, ensure_ascii=False, indent=2)
                    
                    print(f"결과 저장 완료: {output_path}")

    def _save_memory_with_embeddings(self, output_path: str):
        """
        임베딩이 추가된 메모리 저장
        
        Parameters:
        - output_path: 저장할 파일 경로
        """
        try:
            # 임베딩 벡터는 ndarray이므로 JSON으로 직접 저장할 수 없음
            # 벡터를 리스트로 변환하여 저장 (개발 단계에서는 편의성 우선)
            serializable_data = {}
            
            for agent_name, agent_data in self.memory_data.items():
                serializable_data[agent_name] = {"memories": []}
                
                for memory in agent_data["memories"]:
                    memory_copy = memory.copy()
                    # 임베딩 벡터를 리스트로 변환
                    if "embedding_vector" in memory_copy:
                        memory_copy["embedding"] = memory_copy["embedding_vector"].tolist()
                        del memory_copy["embedding_vector"]
                    serializable_data[agent_name]["memories"].append(memory_copy)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            
            print(f"임베딩이 추가된 메모리 저장 완료: {output_path}")
        except Exception as e:
            print(f"메모리 저장 오류: {e}")

def main():
    """
    메인 함수
    """
    # 메모리 파일 경로
    memory_file_path = "memories.json"
    
    # 프롬프트 폴더 경로
    prompt_folder = "temp_prompt"
    
    # 폴더가 없으면 생성
    os.makedirs(prompt_folder, exist_ok=True)
    
    # 샘플 프롬프트 생성 (폴더가 비어있을 경우)
    if not os.listdir(prompt_folder):
        print(f"프롬프트 폴더 '{prompt_folder}'가 비어있습니다. 샘플 프롬프트를 생성합니다.")
        
        hungry_prompt = """
AGENT DATA:
Tom: very hungry, not sleepy, not lonely, at House
Visible: Kitchen located in House, Bedroom located in House, Desk located in House, Cafeteria located in Cafeteria
Can interact with: Kitchen located in House, LivingRoom located in House, Bedroom located in House, Desk located in House, Cafeteria located in Cafeteria
        """
        
        sleepy_prompt = """
AGENT DATA:
Tom: not hungry, very sleepy, not lonely, at House
Visible: Kitchen located in House, Bedroom located in House, Desk located in House, Cafeteria located in Cafeteria
Can interact with: Kitchen located in House, LivingRoom located in House, Bedroom located in House, Desk located in House, Cafeteria located in Cafeteria
        """
        
        with open(os.path.join(prompt_folder, "hungry.txt"), 'w', encoding='utf-8') as f:
            f.write(hungry_prompt)
        
        with open(os.path.join(prompt_folder, "sleepy.txt"), 'w', encoding='utf-8') as f:
            f.write(sleepy_prompt)
        
        print("샘플 프롬프트 생성 완료: hungry.txt, sleepy.txt")
    
    # 메모리 임베딩 시스템 초기화
    action_generator = MemoryActionGenerator(memory_file_path, prompt_folder)
    
    # 프롬프트 파일 처리
    action_generator.process_prompt_files()


if __name__ == "__main__":
    main()