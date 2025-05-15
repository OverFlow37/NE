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

class ReactionDecider:
    def __init__(self, memory_utils, ollama_client, word2vec_model, similarity_threshold: float = 0.6):
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
        agent_name: str, 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        유사한 메모리 검색
        
        Args:
            event_embedding: 현재 이벤트의 임베딩
            agent_name: 에이전트 이름
            top_k: 반환할 메모리 개수
            
        Returns:
            List[Dict[str, Any]]: 유사한 메모리 리스트
        """
        memories = self.memory_utils._load_memories()
        
        if agent_name not in memories or not memories[agent_name]["memories"]:
            return []
        
        agent_memories = memories[agent_name]["memories"]
        
        # 유사도 계산 및 정렬
        memory_similarities = []
        for memory_id, memory in agent_memories.items():
            memory_embedding = memory.get("embeddings", [])
            if not memory_embedding:
                continue
                
            # 코사인 유사도 계산
            similarity = np.dot(event_embedding, memory_embedding) / (
                np.linalg.norm(event_embedding) * np.linalg.norm(memory_embedding)
            )
            
            if similarity >= self.similarity_threshold:
                memory['memory_id'] = memory_id
                memory_similarities.append((memory, similarity))
        
        # 유사도 기준으로 정렬
        memory_similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 k개 반환
        return [memory for memory, _ in memory_similarities[:top_k]]
    
    def _format_similar_memories(self, similar_memories: List[Dict[str, Any]]) -> str:
        """
        유사한 메모리를 문자열로 포맷팅 (영어로 변경)
        
        Args:
            similar_memories: 유사한 메모리 리스트
            
        Returns:
            str: 포맷팅된 메모리 문자열
        """
        if not similar_memories:
            return "No similar events found in the past."
        
        formatted_memories = []
        for memory in similar_memories:
            # 새 구조에서 이벤트와 액션 가져오기
            event = memory.get("event", "")
            action = memory.get("action", "")
            feedback = memory.get("feedback", "")
            event_role = memory.get("event_role", "")
            time = memory.get("time", "")
            importance = memory.get("importance", "N/A")
            memory_id = memory.get("memory_id", "")
            
            # 어떤 필드에 내용이 있는지 확인하고 표시
            content = ""
            if event:
                if event_role == "God say":
                    content = f"Event: God said, {event}"
                content = f"Event: {event}"
            elif action:
                content = f"Action: {action}"
            elif feedback:
                content = f"Feedback: {feedback}"
            
            if content and time:
                formatted_memories.append(f"- {content} (time: {time}, importance: {importance}, id: {memory_id})")
        
        return "\n".join(formatted_memories)
    
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
        
        # 유사한 메모리 검색
        similar_memories = self._find_similar_memories(event_embedding, agent_name)
        
        # 유사한 메모리 포맷팅
        similar_memories_str = self._format_similar_memories(similar_memories)
        
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