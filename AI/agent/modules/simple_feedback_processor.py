"""
간단한 피드백 처리 모듈

LLM을 사용하지 않고 행동에 대한 피드백을 처리하고 메모리에 저장합니다.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import numpy as np
from datetime import datetime

class SimpleFeedbackProcessor:
    def __init__(self, memory_utils):
        """
        간단한 피드백 처리기 초기화
        
        Args:
            memory_utils: MemoryUtils 인스턴스
        """
        self.memory_utils = memory_utils
    
    def _create_feedback_text(self, action: str, interactable: str, location: str, 
                             success: bool, needs_diff: Dict[str, int], 
                             feedback_description: str = "") -> str:
        """
        간단한 피드백 문장 생성
        
        Args:
            action: 행동 이름
            interactable: 상호작용 대상
            location: 위치
            success: 성공 여부
            needs_diff: 욕구 변화량
            feedback_description: 피드백 설명
            
        Returns:
            str: 생성된 피드백 문장
        """
        # 성공/실패 결과
        result_text = ""
        if success:
            result_text = f"I {action}ed {interactable if interactable else ''} at {location} successfully."
        else:
            if feedback_description:
                result_text = f"I failed to {action} {interactable if interactable else ''} at {location}. {feedback_description}"
            else:
                result_text = f"I failed to {action} {interactable if interactable else ''} at {location}."
        
        # 욕구 변화 설명
        needs_text = []
        
        # 배고픔
        hunger = needs_diff.get("hunger", 0)
        if hunger <= -10:
            needs_text.append("I'm much less hungry now")
        elif hunger < 0:
            needs_text.append("I'm a bit less hungry")
        elif hunger > 10:
            needs_text.append("I'm much more hungry now")
        elif hunger > 0:
            needs_text.append("I'm a bit more hungry")
        
        # 졸림
        sleepiness = needs_diff.get("sleepiness", 0)
        if sleepiness <= -10:
            needs_text.append("I feel much more awake")
        elif sleepiness < 0:
            needs_text.append("I feel a bit more awake")
        elif sleepiness > 10:
            needs_text.append("I feel much more sleepy")
        elif sleepiness > 0:
            needs_text.append("I feel a bit more sleepy")
        
        # 외로움
        loneliness = needs_diff.get("loneliness", 0)
        if loneliness <= -10:
            needs_text.append("I feel much less lonely")
        elif loneliness < 0:
            needs_text.append("I feel a bit less lonely")
        elif loneliness > 10:
            needs_text.append("I feel much more lonely")
        elif loneliness > 0:
            needs_text.append("I feel a bit more lonely")
        
        # 스트레스
        stress = needs_diff.get("stress", 0)
        if stress <= -10:
            needs_text.append("I feel much less stressed")
        elif stress < 0:
            needs_text.append("I feel a bit less stressed")
        elif stress > 10:
            needs_text.append("I feel much more stressed")
        elif stress > 0:
            needs_text.append("I feel a bit more stressed")
        
        # 최종 문장 생성
        if needs_text:
            result_text += " After that, " + ", and ".join(needs_text) + "."
        
        return result_text
    
    def process_simple_feedback(self, feedback_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        피드백 데이터를 처리하여 메모리에 저장 (LLM 사용하지 않음)
        
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
            
            # 피드백 문장 생성 (LLM 사용하지 않음)
            feedback_sentence = self._create_feedback_text(
                action=action,
                interactable=interactable,
                location=current_location,
                success=success,
                needs_diff=needs_diff,
                feedback_description=feedback_description
            )
            
            print(f"📝 생성된 피드백: {feedback_sentence}")
            
            # 임베딩 생성
            embedding = self.memory_utils.get_embedding(feedback_sentence)
            
            # 메모리 데이터 로드
            memories = self.memory_utils._load_memories()
            
            # 에이전트가 존재하는지 확인
            if agent_name not in memories:
                memories[agent_name] = {"memories": {}}
            
            if "memories" not in memories[agent_name]:
                memories[agent_name]["memories"] = {}
            
            # 메모리 ID가 있으면 해당 메모리에 피드백 저장
            if memory_id:
                agent_memories = memories[agent_name]["memories"]
                
                # 메모리 ID가 존재하는지 확인
                if memory_id in agent_memories:
                    # 기존 메모리에 피드백 추가
                    agent_memories[memory_id]["feedback"] = feedback_sentence
                    print(f"✅ 메모리 ID {memory_id}에 피드백 저장")
                    self.memory_utils._save_memories(memories)
                    
                    return {
                        "success": True,
                        "message": f"Feedback added to memory_id {memory_id}",
                        "memory_id": memory_id,
                        "feedback": feedback_sentence
                    }
                else:
                    print(f"⚠️ 메모리 ID {memory_id}를 찾을 수 없습니다. 해당 ID로 새 메모리를 생성합니다.")
            
            # 새 메모리 생성 (기존 ID 유지)
            if memory_id:
                # 기존 ID로 새 메모리 생성
                memories[agent_name]["memories"][memory_id] = {
                    "event_role": "",
                    "event": "",
                    "action": action if action else "",
                    "feedback": feedback_sentence,
                    "conversation_detail": "",
                    "time": time,
                    "embeddings": embedding,
                    "importance": 4  # 피드백의 기본 중요도
                }
                print(f"✅ 메모리 ID {memory_id}로 새 메모리 생성 및 피드백 저장")
                self.memory_utils._save_memories(memories)
                
                return {
                    "success": True,
                    "message": f"New memory created with ID {memory_id}",
                    "memory_id": memory_id,
                    "feedback": feedback_sentence
                }
            else:
                # 새 ID로 메모리 생성
                new_memory_id = self.memory_utils._get_next_memory_id(agent_name)
                memories[agent_name]["memories"][new_memory_id] = {
                    "event_role": "",
                    "event": "",
                    "action": action if action else "",
                    "feedback": feedback_sentence,
                    "conversation_detail": "",
                    "time": time,
                    "embeddings": embedding,
                    "importance": 4  # 피드백의 기본 중요도
                }
                print(f"✅ 새 메모리 ID {new_memory_id}에 피드백 저장")
                self.memory_utils._save_memories(memories)
                
                return {
                    "success": True,
                    "message": "New memory created with feedback",
                    "memory_id": new_memory_id,
                    "feedback": feedback_sentence
                }
            
        except Exception as e:
            print(f"❌ 피드백 처리 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}