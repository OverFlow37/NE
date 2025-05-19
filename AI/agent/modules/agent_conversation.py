"""
Agent 대화 시스템 모듈

두 Agent 간의 대화를 처리하고 메모리에 저장하는 기능을 제공합니다.
"""

import json
import os
import uuid
import re
from datetime import datetime
from pathlib import Path
import asyncio

class AgentConversationManager:
    def __init__(self, ollama_client, memory_utils, word2vec_model, max_turns=10):
        """
        Agent 대화 관리자 초기화
        
        Args:
            ollama_client: OllamaClient 인스턴스
            memory_utils: MemoryUtils 인스턴스
            word2vec_model: Word2Vec 모델
            max_turns: 최대 대화 턴 수 (기본값: 10)
        """
        self.ollama_client = ollama_client
        self.memory_utils = memory_utils
        self.word2vec_model = word2vec_model
        self.max_turns = max_turns  # 모듈 내부에서 최대 턴 수 설정
        
        # 현재 파일의 절대 경로를 기준으로 상위 디렉토리 찾기
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent.parent  # AI 디렉토리
        agent_dir = root_dir / "agent"
        
        # 대화 저장 디렉토리
        self.conversations_dir = agent_dir / "data" / "conversations"
        os.makedirs(self.conversations_dir, exist_ok=True)
        
        print(f"✅ AgentConversationManager 초기화 완료 (최대 대화 턴 수: {self.max_turns})")
    
    async def process_conversation(self, payload):
        """
        대화 처리 핵심 로직
        
        Args:
            payload: 대화 요청 데이터
            
        Returns:
            dict: 처리 결과
        """
        try:
            # 기본 검증
            if "agents" not in payload or len(payload.get("agents", [])) < 2:
                return {"success": False, "error": "At least two agents are required"}
            
            # 대화 ID 확인
            conversation_id = payload.get("conversation_id")
            is_new_conversation = not conversation_id
            
            # 에이전트 정보 추출
            agents = payload.get("agents", [])
            current_speaker_name = payload.get("current_speaker")
            location = payload.get("location", "")
            context = payload.get("context", "")
            
            # 화자 정보 추출
            current_speaker = next((a for a in agents if a["name"] == current_speaker_name), None)
            other_agent = next((a for a in agents if a["name"] != current_speaker_name), None)
            
            if not current_speaker or not other_agent:
                return {"success": False, "error": "Invalid speaker configuration"}
            
            # 1. 새 대화 또는 기존 대화 로드
            if is_new_conversation:
                conversation = self._initialize_conversation(agents, location, context)
                conversation_id = conversation["conversation_id"]
            else:
                conversation = await self._load_conversation(conversation_id)
                if not conversation:
                    return {"success": False, "error": f"Conversation {conversation_id} not found"}
            
            # 2. 대화 턴 수 확인 - 최대 턴 수에 도달했는지 체크
            current_turns = len(conversation["messages"])
            force_end = False
            
            if current_turns >= self.max_turns - 1:  # 이번 턴이 마지막 턴이 될 경우
                print(f"🔚 최대 대화 턴 수({self.max_turns})에 도달하여 대화를 종료합니다.")
                force_end = True
            
            # 3. 이전 대화 메모리 로드
            previous_conversations = await self._get_previous_conversations(
                current_speaker["name"], 
                other_agent["name"]
            )
            
            # 4. 프롬프트 생성 - 강제 종료 힌트 포함
            prompt = self._create_conversation_prompt(
                conversation=conversation,
                current_speaker=current_speaker,
                other_agent=other_agent,
                previous_conversations=previous_conversations,
                location=location,
                context=context,
                force_end=force_end,
                current_turns=current_turns,
                max_turns=self.max_turns
            )
            
            # 5. 시스템 프롬프트 생성
            system_prompt = self._get_system_prompt(force_end)
            
            # 6. Gemma 모델 호출
            response = await self.ollama_client.process_prompt(
                prompt=prompt,
                system_prompt=system_prompt,
                model_name="gemma3"
            )
            
            # 7. 응답 파싱
            parsed_response = self._parse_conversation_response(
                response.get("response", ""),
                default_next_speaker=other_agent["name"]
            )
            
            # 8. 강제 종료 적용
            if force_end:
                parsed_response["should_continue"] = False
                if not parsed_response.get("reason_to_end"):
                    parsed_response["reason_to_end"] = f"Conversation naturally concluded after {current_turns + 1} exchanges"
            
            # 9. 대화 업데이트
            new_message = {
                "speaker": current_speaker["name"],
                "message": parsed_response["message"],
                "emotion": parsed_response["emotion"],
                "time": current_speaker["time"]
            }
            
            conversation["messages"].append(new_message)
            conversation["last_updated"] = current_speaker["time"]
            
            # 10. 대화 저장
            await self._save_conversation(conversation)
            
            # 11. 대화 종료 처리
            memory_ids = []
            if not parsed_response["should_continue"]:
                # 대화 종료 처리
                conversation["status"] = "completed"
                
                # 종료 이유 (강제 종료 여부에 따라 다름)
                if force_end and not parsed_response.get("reason_to_end"):
                    conversation["end_reason"] = f"Conversation reached the maximum of {self.max_turns} turns"
                else:
                    conversation["end_reason"] = parsed_response.get("reason_to_end", "Natural conclusion")
                
                # 대화 메모리에 저장
                memory_ids = await self._save_conversation_to_memory(
                    conversation, 
                    agents,
                    parsed_response.get("importance", 3)
                )
                
                # 대화 저장 (상태 업데이트)
                await self._save_conversation(conversation)
            
            # 12. 응답 구성
            result = {
                "success": True,
                "conversation_id": conversation_id,
                "message": new_message,
                "should_continue": parsed_response["should_continue"],
                "next_speaker": parsed_response["next_speaker"],
                "turns": current_turns + 1,
                "max_turns": self.max_turns
            }
            
            if memory_ids:
                result["memory_ids"] = memory_ids
            
            if not parsed_response["should_continue"]:
                result["conversation"] = conversation
            
            return result
            
        except Exception as e:
            print(f"Error processing conversation: {e}")
            return {"success": False, "error": str(e)}
    
    def _initialize_conversation(self, agents, location, context):
        """새 대화 초기화"""
        conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        
        return {
            "conversation_id": conversation_id,
            "agents": [a["name"] for a in agents],
            "location": location,
            "context": context,
            "messages": [],
            "status": "active",
            "start_time": agents[0]["time"],  # 첫 번째 에이전트의 시간 사용
            "last_updated": agents[0]["time"],
            "end_reason": ""
        }
    
    async def _load_conversation(self, conversation_id):
        """대화 로드"""
        filepath = self.conversations_dir / f"{conversation_id}.json"
        
        if not os.path.exists(filepath):
            return None
        
        # 파일 로드
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading conversation {conversation_id}: {e}")
            return None
    
    async def _save_conversation(self, conversation):
        """대화 저장"""
        filepath = self.conversations_dir / f"{conversation['conversation_id']}.json"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False
    
    async def _get_previous_conversations(self, agent1_name, agent2_name, max_count=3):
        """이전 대화 메모리 조회"""
        # 메모리에서 두 에이전트 간의 이전 대화 검색
        memories = self.memory_utils._load_memories()
        
        if agent1_name not in memories:
            return []
        
        conversation_memories = []
        for memory in memories[agent1_name]["memories"]:
            if memory.get("event_type") == "conversation":
                details = memory.get("details", {})
                if details.get("with") == agent2_name:
                    conversation_memories.append({
                        "time": memory.get("time", ""),
                        "summary": details.get("summary", ""),
                        "importance": memory.get("importance", 5),
                        "location": details.get("location", "")
                    })
        
        # 최근 대화 순으로 정렬
        conversation_memories.sort(key=lambda x: x["time"], reverse=True)
        return conversation_memories[:max_count]
    
    async def _save_conversation_to_memory(self, conversation, agents, importance=5):
        """대화를 메모리에 저장"""
        memory_ids = []
        
        # 대화 요약 생성
        summaries = await self._generate_conversation_summaries(conversation, agents)
        
        # 각 에이전트에 대해 메모리 저장
        for agent in agents:
            agent_name = agent["name"]
            other_agent = next(a for a in agents if a["name"] != agent_name)
            
            # 이벤트 문장 생성
            event_sentence = f"Conversation with {other_agent['name']} at {conversation['location']}"
            
            # 임베딩 생성
            embedding = self.memory_utils.get_embedding(event_sentence)
            
            # 메모리 저장
            memory = {
                "event": event_sentence,
                "time": agent["time"],
                "embeddings": embedding,
                "event_type": "conversation",
                "importance": summaries.get("importance", importance),
                "details": {
                    "conversation_id": conversation["conversation_id"],
                    "with": other_agent["name"],
                    "location": conversation["location"],
                    "summary": summaries.get(f"{agent_name.lower()}_memory", 
                                          f"Talked with {other_agent['name']} about various topics")
                }
            }
            
            # 메모리에 저장
            memories = self.memory_utils._load_memories()
            
            if agent_name not in memories:
                memories[agent_name] = {"memories": []}
            
            # 메모리 ID 생성
            memory_id = 1
            if memories[agent_name]["memories"]:
                memory_id = max([m.get("event_id", 0) for m in memories[agent_name]["memories"]]) + 1
            
            memory["event_id"] = memory_id
            memories[agent_name]["memories"].append(memory)
            
            # 저장
            self.memory_utils._save_memories(memories)
            memory_ids.append(memory_id)
        
        return memory_ids
    
    async def _generate_conversation_summaries(self, conversation, agents):
        """대화 요약 생성"""
        if not conversation["messages"]:
            return {
                "importance": 3,
                f"{agents[0]['name'].lower()}_memory": f"Brief encounter with {agents[1]['name']}",
                f"{agents[1]['name'].lower()}_memory": f"Brief encounter with {agents[0]['name']}"
            }
        
        # 대화 전체 내용 포맷팅
        conversation_text = "\n".join([f"{msg['speaker']}: {msg['message']}" for msg in conversation["messages"]])
        
        # 요약 생성 프롬프트
        prompt = f"""
Summarize the following conversation between {agents[0]['name']} and {agents[1]['name']}:

{conversation_text}

Create three items:
1. A summary from {agents[0]['name']}'s perspective (what they would remember)
2. A summary from {agents[1]['name']}'s perspective (what they would remember)
3. An importance rating (1-10) indicating how memorable/significant this conversation is

Format your response as JSON:
{{
  "{agents[0]['name'].lower()}_memory": "Summary from {agents[0]['name']}'s perspective",
  "{agents[1]['name'].lower()}_memory": "Summary from {agents[1]['name']}'s perspective",
  "importance": 1-10
}}
"""
        
        # Gemma 모델 호출
        system_prompt = "You are an AI that summarizes conversations. Respond only with the requested JSON format."
        response = await self.ollama_client.process_prompt(
            prompt=prompt,
            system_prompt=system_prompt,
            model_name="gemma3"
        )
        
        # JSON 파싱
        try:
            json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
            matches = re.findall(json_pattern, response.get("response", ""))
            
            if matches:
                for match in matches:
                    try:
                        return json.loads(match)
                    except:
                        continue
            
            # 파싱 실패 시 기본값 반환
            return {
                "importance": 5,
                f"{agents[0]['name'].lower()}_memory": f"Talked with {agents[1]['name']} at {conversation['location']}",
                f"{agents[1]['name'].lower()}_memory": f"Talked with {agents[0]['name']} at {conversation['location']}"
            }
            
        except Exception as e:
            print(f"Error parsing summary response: {e}")
            return {
                "importance": 4,
                f"{agents[0]['name'].lower()}_memory": f"Had a conversation with {agents[1]['name']}",
                f"{agents[1]['name'].lower()}_memory": f"Had a conversation with {agents[0]['name']}"
            }
    
    def _get_system_prompt(self, force_end=False):
        """시스템 프롬프트 생성"""
        base_prompt = """
You are an AI handling a conversation between two game characters. Your task is to generate a natural response for the current speaker and determine if the conversation should continue.

Respond in this exact JSON format:
{
  "message": "Your natural dialogue response here",
  "emotion": "one word describing the emotional state (e.g., happy, curious, concerned)",
  "should_continue": true/false,
  "reason_to_end": "Only provide if should_continue is false, explaining why conversation would naturally end",
  "next_speaker": "Name of the other participant",
  "importance": 1-10 (how memorable/significant this conversation is)
}

Make dialogue natural and reflect the speaker's personality and current state.
"""

        # 강제 종료가 필요한 경우 추가 지침
        if force_end:
            base_prompt += """

IMPORTANT: This conversation has reached its maximum allowed length. You MUST set "should_continue" to false and provide a natural reason to end the conversation in "reason_to_end" field. Make the ending feel natural based on the context.
"""
        
        return base_prompt
    
    def _create_conversation_prompt(self, conversation, current_speaker, other_agent, previous_conversations, location, context, force_end=False, current_turns=0, max_turns=10):
        """대화 프롬프트 생성"""
        # 대화 기록 포맷팅
        conversation_history = self._format_conversation_history(conversation["messages"])
        
        # 이전 대화 메모리 포맷팅
        previous_conversations_text = self._format_previous_conversations(previous_conversations)
        
        # 에이전트 상태 정보 포맷팅
        current_state = self._format_agent_state(current_speaker.get("state", {}))
        
        # 기본 프롬프트
        prompt = f"""
You are {current_speaker["name"]} with personality: {current_speaker["personality"]}
You are talking with {other_agent["name"]} who has personality: {other_agent["personality"]}
Location: {location}
Context: {context}

Your current state:
{current_state}

Previous interactions with {other_agent["name"]}:
{previous_conversations_text}

Current conversation:
{conversation_history}
"""

        # 대화 턴 수에 관한 정보 추가
        if current_turns > 0:
            prompt += f"\nThis is turn {current_turns + 1} of a conversation (maximum {max_turns} turns).\n"
        
        # 강제 종료 필요한 경우 안내문 추가
        if force_end:
            prompt += f"""
IMPORTANT: This conversation needs to end naturally after this response. 
Find a natural way to conclude the conversation based on your personality, state, or the context.
Examples of natural endings:
- You need to go somewhere else
- You've shared what you wanted to say
- You need to attend to your needs (like your hunger if it's high)
- The topic has reached its natural conclusion
"""
        else:
            prompt += """
Generate your next response as yourself and decide if the conversation should naturally continue or end.
Consider your personality, current state, conversation context, and history with the other person.

Base your decision to continue or end the conversation on:
1. Natural conversation flow
2. Your current state (hunger, sleepiness, etc.)
3. Your personality traits
4. Previous history with the other person
5. Current location and context

End the conversation only if it would logically conclude (e.g., you need to leave, conversation reached a natural end, etc.)
"""
        
        return prompt
    
    def _format_conversation_history(self, messages):
        """대화 기록 포맷팅"""
        if not messages:
            return "No messages yet."
        
        formatted = []
        for msg in messages:
            formatted.append(f"{msg['speaker']}: {msg['message']} ({msg['emotion']})")
        
        return "\n".join(formatted)
    
    def _format_previous_conversations(self, previous_conversations):
        """이전 대화 메모리 포맷팅"""
        if not previous_conversations:
            return "No previous interactions."
        
        formatted = []
        for conv in previous_conversations:
            formatted.append(f"- {conv['summary']} ({conv['time']})")
        
        return "\n".join(formatted)
    
    def _format_agent_state(self, state):
        """에이전트 상태 포맷팅"""
        if not state:
            return "No specific state information."
        
        formatted = []
        for key, value in state.items():
            level = "high" if value > 7 else "moderate" if value > 3 else "low"
            formatted.append(f"- {key}: {level} ({value}/10)")
        
        return "\n".join(formatted)
    
    def _parse_conversation_response(self, response, default_next_speaker=None):
        """Gemma 응답 파싱"""
        try:
            # 1. 전체 응답이 유효한 JSON인지 시도
            try:
                result = json.loads(response)
                if "message" in result:
                    return self._validate_response(result, default_next_speaker)
            except json.JSONDecodeError:
                pass
            
            # 2. JSON 패턴 찾기
            json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
            matches = re.findall(json_pattern, response)
            
            if matches:
                for match in matches:
                    try:
                        result = json.loads(match)
                        if "message" in result:
                            return self._validate_response(result, default_next_speaker)
                    except json.JSONDecodeError:
                        continue
            
            # 3. 마크다운 코드 블록에서 JSON 추출
            md_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            md_matches = re.findall(md_pattern, response)
            
            if md_matches:
                for md_match in md_matches:
                    try:
                        result = json.loads(md_match)
                        if "message" in result:
                            return self._validate_response(result, default_next_speaker)
                    except json.JSONDecodeError:
                        continue
            
            # 4. 구조화된 JSON이 없으면 응답에서 메시지 추출
            message = response.strip()
            if '"message":' in response:
                message_match = re.search(r'"message"\s*:\s*"([^"]*)"', response)
                if message_match:
                    message = message_match.group(1)
            
            # 5. should_continue 값 추출 시도
            should_continue = True
            if '"should_continue"' in response:
                if '"should_continue"\s*:\s*false' in response.lower():
                    should_continue = False
            
            # 기본 응답 반환
            return {
                "message": message,
                "emotion": "neutral",
                "should_continue": should_continue,
                "next_speaker": default_next_speaker,
                "reason_to_end": "",
                "importance": 5
            }
            
        except Exception as e:
            print(f"Error parsing response: {e}")
            # 오류 발생 시 기본 응답 반환
            return {
                "message": "I'm not sure how to respond to that.",
                "emotion": "confused",
                "should_continue": True,
                "next_speaker": default_next_speaker,
                "reason_to_end": "",
                "importance": 3
            }
    
    def _validate_response(self, result, default_next_speaker):
        """응답 유효성 검사 및 기본값 설정"""
        # 필수 필드 확인 및 기본값 설정
        if "message" not in result:
            result["message"] = "I'm not sure what to say."
        
        if "emotion" not in result:
            result["emotion"] = "neutral"
        
        if "should_continue" not in result:
            result["should_continue"] = True
        
        if "next_speaker" not in result:
            result["next_speaker"] = default_next_speaker
        
        return result