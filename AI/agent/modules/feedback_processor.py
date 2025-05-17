"""
피드백 처리 모듈

행동에 대한 피드백을 처리하고 메모리에 저장합니다.
이벤트 정보와 피드백을 합쳐서 저장하는 기능 추가
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import numpy as np
from datetime import datetime
import re

class FeedbackProcessor:
    def __init__(self, memory_utils, ollama_client):
        """
        피드백 처리기 초기화
        
        Args:
            memory_utils: MemoryUtils 인스턴스
            ollama_client: OllamaClient 인스턴스
        """
        self.memory_utils = memory_utils
        self.ollama_client = ollama_client
        
        # 현재 파일의 절대 경로를 기준으로 상위 디렉토리 찾기
        current_dir = Path(__file__).parent
        root_dir = current_dir.parent.parent  # AI 디렉토리
        agent_dir = root_dir / "agent"
        prompts_dir = agent_dir / "prompts" / "feedback"
        
        # 피드백 프롬프트 파일 경로
        self.system_prompt_path = str(prompts_dir / "feedback_system.txt")
        self.feedback_prompt_path = str(prompts_dir / "feedback_prompt.txt")
        
        # 기본 프롬프트 템플릿 (영어로 변경)
        self.default_system_prompt = """
You are an AI assistant that helps NPCs process feedback about their actions. 
Your task is to create a natural language summary of the feedback that describes how an action affected the NPC.
You will analyze the action details, success/failure information, and how the action affected the NPC's needs.

Respond with a concise, first-person perspective description of the experience.
"""
        
        self.default_feedback_prompt = """
I am {AGENT_NAME}, and I just tried to {ACTION} {INTERACTABLE} at {LOCATION}.

Result: {SUCCESS_STATUS}
{FEEDBACK_DESCRIPTION}

Changes in my needs:
- Hunger: {HUNGER_DIFF} {HUNGER_FEELING}
- Sleepiness: {SLEEPINESS_DIFF} {SLEEPINESS_FEELING}
- Loneliness: {LONELINESS_DIFF} {LONELINESS_FEELING}
- Stress: {STRESS_DIFF} {STRESS_FEELING}

Please create a concise, first-person perspective description of my experience that I can remember.
"""
        self._ensure_prompt_files_exist()
    
    def _ensure_prompt_files_exist(self):
        """프롬프트 파일이 존재하는지 확인하고, 없다면 기본 템플릿으로 생성"""
        os.makedirs(os.path.dirname(self.system_prompt_path), exist_ok=True)
        
        if not os.path.exists(self.system_prompt_path):
            with open(self.system_prompt_path, 'w', encoding='utf-8') as f:
                f.write(self.default_system_prompt)
        
        if not os.path.exists(self.feedback_prompt_path):
            with open(self.feedback_prompt_path, 'w', encoding='utf-8') as f:
                f.write(self.default_feedback_prompt)
    
    def _load_prompt(self, file_path: str, default_template: str) -> str:
        """프롬프트 파일 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"프롬프트 파일 로드 실패: {e}, 기본 템플릿 사용")
            return default_template
    
    def _interpret_needs_diff(self, needs_diff: Dict[str, int]) -> Dict[str, str]:
        """
        욕구 변화량에 대한 해석 생성
        
        Args:
            needs_diff: 욕구 변화량 딕셔너리
            
        Returns:
            Dict[str, str]: 각 욕구에 대한 해석
        """
        interpretations = {}
        
        # 배고픔 해석 (음수면 좋음 - 배고픔 감소)
        hunger = needs_diff.get("hunger", 0)
        if hunger <= -10:
            interpretations["hunger"] = "I feel much less hungry now."
        elif hunger < 0:
            interpretations["hunger"] = "I feel a bit less hungry."
        elif hunger == 0:
            interpretations["hunger"] = "My hunger didn't change."
        elif hunger < 10:
            interpretations["hunger"] = "I feel a bit more hungry."
        else:
            interpretations["hunger"] = "I feel much more hungry now."
        
        # 졸림 해석 (음수면 좋음 - 졸림 감소)
        sleepiness = needs_diff.get("sleepiness", 0)
        if sleepiness <= -10:
            interpretations["sleepiness"] = "I feel much more awake now."
        elif sleepiness < 0:
            interpretations["sleepiness"] = "I feel a bit more awake."
        elif sleepiness == 0:
            interpretations["sleepiness"] = "My sleepiness didn't change."
        elif sleepiness < 10:
            interpretations["sleepiness"] = "I feel a bit more sleepy."
        else:
            interpretations["sleepiness"] = "I feel much more sleepy now."
        
        # 외로움 해석 (음수면 좋음 - 외로움 감소)
        loneliness = needs_diff.get("loneliness", 0)
        if loneliness <= -10:
            interpretations["loneliness"] = "I feel much less lonely now."
        elif loneliness < 0:
            interpretations["loneliness"] = "I feel a bit less lonely."
        elif loneliness == 0:
            interpretations["loneliness"] = "My loneliness didn't change."
        elif loneliness < 10:
            interpretations["loneliness"] = "I feel a bit more lonely."
        else:
            interpretations["loneliness"] = "I feel much more lonely now."
        
        # 스트레스 해석 (음수면 좋음 - 스트레스 감소)
        stress = needs_diff.get("stress", 0)
        if stress <= -10:
            interpretations["stress"] = "I feel much less stressed now."
        elif stress < 0:
            interpretations["stress"] = "I feel a bit less stressed."
        elif stress == 0:
            interpretations["stress"] = "My stress level didn't change."
        elif stress < 10:
            interpretations["stress"] = "I feel a bit more stressed."
        else:
            interpretations["stress"] = "I feel much more stressed now."
        
        return interpretations
    
    def _create_event_text(self, action: str, interactable: str, location: str) -> str:
        """
        안전한 이벤트 텍스트 생성
        
        Args:
            action: 행동 이름
            interactable: 상호작용 대상
            location: 위치
            
        Returns:
            str: 생성된 이벤트 텍스트
        """
        event_str = ""
        
        if action:
            event_str += action
            
            if interactable:
                event_str += f" {interactable}"
                
            if location:
                event_str += f" at {location}"
        elif location:
            event_str = f"went to {location}"
        else:
            event_str = "unknown event"
            
        return event_str
    
    def _create_combined_feedback(self, action: str, interactable: str, location: str, 
                              success: bool, feedback_sentence: str, 
                              feedback_description: str = "") -> str:
        """
        이벤트 정보와 피드백을 결합한 통합 피드백 생성
        
        Args:
            action: 행동 이름
            interactable: 상호작용 대상
            location: 위치
            success: 성공 여부
            feedback_sentence: 생성된 피드백 문장
            feedback_description: 피드백 설명
            
        Returns:
            str: 결합된 피드백 문장
        """
        # 이벤트 정보 구성
        event_info = "Event: "
        
        if action:
            event_info += action
            
            if interactable:
                event_info += f" {interactable}"
                
            if location:
                event_info += f" at {location}"
        elif location:
            event_info += f"went to {location}"
        else:
            event_info += "unknown action"
            
        event_info += ". "
        
        # 성공/실패 상태
        status_info = f"Result: {'Success' if success else 'Failed'}"
        if feedback_description:
            status_info += f" ({feedback_description})"
        status_info += ". "
        
        # 통합 피드백 생성
        combined_feedback = f"{event_info}{status_info}Feedback: {feedback_sentence}"
        
        return combined_feedback
    
    async def process_feedback(self, feedback_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        피드백 데이터를 처리하여 메모리에 저장
        
        Args:
            feedback_data: 피드백 데이터
            
        Returns:
            Optional[Dict[str, Any]]: 처리 결과
        """
        try:
            # 필수 데이터 추출
            agent_data = feedback_data.get('agent', {})
            # 'agent_name'과 'name' 필드 모두 확인
            agent_name = agent_data.get('agent_name', agent_data.get('name', ''))
            
            # agent_name이 비어있는지 확인
            if not agent_name:
                print("⚠️ agent_name이 비어있습니다.")
                return {"success": False, "error": "agent_name is required"}
            
            current_location = agent_data.get('current_location_name', '')
            interactable = agent_data.get('interactable_name', '')
            action = agent_data.get('action_name', '')
            success = agent_data.get('success', False)
            time = agent_data.get('time', datetime.now().strftime("%Y.%m.%d.%H:%M"))
            
            feedback = agent_data.get('feedback', {})
            feedback_description = feedback.get('feedback_description', '')
            
            # memory_id 처리 - 문자열로 변환하여 확인
            memory_id = str(feedback.get('memory_id', '')) if feedback.get('memory_id') is not None else ''
            
            print(f"👉 처리할 메모리 ID: {memory_id}, 에이전트: {agent_name}")
            
            needs_diff = feedback.get('needs_diff', {})
            
            # 욕구 변화량 해석
            needs_interpretations = self._interpret_needs_diff(needs_diff)
            
            # 성공/실패 상태
            success_status = "Success" if success else "Failed"
            
            # 프롬프트 템플릿 로드
            system_prompt = self._load_prompt(self.system_prompt_path, self.default_system_prompt)
            feedback_prompt = self._load_prompt(self.feedback_prompt_path, self.default_feedback_prompt)
            
            # 프롬프트 생성
            formatted_prompt = feedback_prompt.format(
                AGENT_NAME=agent_name,
                ACTION=action if action else "",
                INTERACTABLE=interactable if interactable else "",
                LOCATION=current_location if current_location else "",
                SUCCESS_STATUS=success_status,
                FEEDBACK_DESCRIPTION=feedback_description if feedback_description else "",
                HUNGER_DIFF=needs_diff.get("hunger", 0),
                HUNGER_FEELING=needs_interpretations.get("hunger", ""),
                SLEEPINESS_DIFF=needs_diff.get("sleepiness", 0),
                SLEEPINESS_FEELING=needs_interpretations.get("sleepiness", ""),
                LONELINESS_DIFF=needs_diff.get("loneliness", 0),
                LONELINESS_FEELING=needs_interpretations.get("loneliness", ""),
                STRESS_DIFF=needs_diff.get("stress", 0),
                STRESS_FEELING=needs_interpretations.get("stress", "")
            )
            
            # Ollama API 호출
            response = await self.ollama_client.process_prompt(
                prompt=formatted_prompt,
                system_prompt=system_prompt,
                model_name="gemma3"
            )
            
            if response.get("status") != "success":
                print(f"🚫 API 응답 실패: {response}")
                return None
            
            # 피드백 문장 생성
            feedback_sentence = response.get("response", "").strip()
            
            # 따옴표 제거 로직 향상
            # 전체 문장이 따옴표로 감싸져 있는 경우
            if (feedback_sentence.startswith('"') and feedback_sentence.endswith('"')) or \
            (feedback_sentence.startswith("'") and feedback_sentence.endswith("'")):
                feedback_sentence = feedback_sentence[1:-1]
            
            # 따옴표로 감싸진 텍스트 패턴 확인 (예: "text" 또는 'text')
            quote_pattern = r'^["\'](.*)["\']$'
            match = re.match(quote_pattern, feedback_sentence)
            if match:
                feedback_sentence = match.group(1)
            
            # 줄바꿈 및 여러 공백 정리
            feedback_sentence = re.sub(r'\s+', ' ', feedback_sentence).strip()
            
            print(f"📝 생성된 피드백: {feedback_sentence}")
            
            # 이벤트 정보와 피드백 결합
            combined_feedback = self._create_combined_feedback(
                action=action,
                interactable=interactable,
                location=current_location,
                success=success,
                feedback_sentence=feedback_sentence,
                feedback_description=feedback_description
            )
            
            print(f"📝 통합 피드백: {combined_feedback}")
            
            # 임베딩 생성 (통합 피드백 기반)
            embedding = self.memory_utils.get_embedding(combined_feedback)
            
            # 메모리 데이터 로드
            memories = self.memory_utils._load_memories()
            
            # 에이전트가 존재하는지 확인
            if agent_name not in memories:
                memories[agent_name] = {"memories": {}}
            
            if "memories" not in memories[agent_name]:
                memories[agent_name]["memories"] = {}
            
            # 이벤트 텍스트 생성
            event_text = self._create_event_text(action, interactable, current_location)
            
            # 메모리 ID가 있으면 해당 메모리에 피드백 저장
            if memory_id:
                agent_memories = memories[agent_name]["memories"]
                
                # 메모리 ID가 존재하는지 확인
                if memory_id in agent_memories:
                    # 기존 메모리에 통합 피드백 추가
                    agent_memories[memory_id]["feedback"] = combined_feedback
                    print(f"✅ 메모리 ID {memory_id}에 통합 피드백 저장")
                    self.memory_utils._save_memories(memories)
                    
                    return {
                        "success": True,
                        "message": f"Combined feedback added to memory_id {memory_id}",
                        "memory_id": memory_id,
                        "feedback": combined_feedback
                    }
                else:
                    print(f"⚠️ 메모리 ID {memory_id}를 찾을 수 없습니다. 해당 ID로 새 메모리를 생성합니다.")
            
            # 새 메모리 생성 (기존 ID 유지)
            if memory_id:
                # 기존 ID로 새 메모리 생성
                memories[agent_name]["memories"][memory_id] = {
                    "event_role": "",
                    "event": event_text,  # 안전하게 생성된 이벤트 텍스트
                    "action": action if action else "",
                    "feedback": combined_feedback,  # 통합 피드백 저장
                    "conversation_detail": "",
                    "time": time,
                    "embeddings": embedding,
                    "importance": 3  # 피드백의 기본 중요도
                }
                print(f"✅ 메모리 ID {memory_id}로 새 메모리 생성 및 통합 피드백 저장")
                self.memory_utils._save_memories(memories)
                
                return {
                    "success": True,
                    "message": f"New memory created with ID {memory_id}",
                    "memory_id": memory_id,
                    "feedback": combined_feedback
                }
            else:
                # 새 ID로 메모리 생성
                new_memory_id = self.memory_utils._get_next_memory_id(agent_name)
                memories[agent_name]["memories"][new_memory_id] = {
                    "event_role": "",
                    "event": event_text,  # 안전하게 생성된 이벤트 텍스트
                    "action": action if action else "",
                    "feedback": combined_feedback,  # 통합 피드백 저장
                    "conversation_detail": "",
                    "time": time,
                    "embeddings": embedding,
                    "importance": 3  # 피드백의 기본 중요도
                }
                print(f"✅ 새 메모리 ID {new_memory_id}에 통합 피드백 저장")
                self.memory_utils._save_memories(memories)
                
                return {
                    "success": True,
                    "message": "New memory created with combined feedback",
                    "memory_id": new_memory_id,
                    "feedback": combined_feedback
                }
            
        except Exception as e:
            print(f"❌ 피드백 처리 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}