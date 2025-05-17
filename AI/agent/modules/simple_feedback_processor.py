"""
간단한 피드백 처리 모듈

LLM을 사용하지 않고 행동에 대한 피드백을 처리하고 메모리에 저장합니다.
이벤트 정보와 피드백을 합쳐서 저장하는 기능 추가
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
        # 성공/실패 결과 (기본 템플릿)
        if success:
            if action and interactable:
                result_text = f"Successfully {action}ed {interactable}"
                if location:
                    result_text += f" at {location}"
            elif action:
                result_text = f"Successfully {action}ed"
                if location:
                    result_text += f" at {location}"
            elif location:
                result_text = f"Successfully went to {location}"
            else:
                result_text = "Successfully performed an action"
        else:
            # 실패 케이스
            if "Inedible" in feedback_description and action == "eat":
                result_text = f"tried to eat {interactable}"
                if location:
                    result_text += f" at {location}"
                result_text += ", but it was completely inedible"
            elif action and interactable:
                result_text = f"failed to {action} {interactable}"
                if location:
                    result_text += f" at {location}"
            elif action:
                result_text = f"failed to {action}"
                if location:
                    result_text += f" at {location}"
            elif location:
                result_text = f"failed to go to {location}"
            else:
                result_text = "failed to perform an action"
        # 욕구 변화를 자연스러운 문장으로 표현
        effects = []
        
        # 배고픔
        hunger = needs_diff.get("hunger", 0)
        if hunger <= -10:
            effects.append("much less hungry now")
        elif hunger < 0:
            effects.append("a bit less hungry")
        elif hunger > 10:
            effects.append("much more hungry")
        elif hunger > 0:
            effects.append("a bit more hungry")
        
        # 졸림
        sleepiness = needs_diff.get("sleepiness", 0)
        if sleepiness <= -10:
            effects.append("much more awake")
        elif sleepiness < 0:
            effects.append("a bit more awake")
        elif sleepiness > 10:
            effects.append("much more sleepy")
        elif sleepiness > 0:
            effects.append("a bit more sleepy")
        
        # 외로움
        loneliness = needs_diff.get("loneliness", 0)
        if loneliness <= -10:
            effects.append("much less lonely")
        elif loneliness < 0:
            effects.append("a bit less lonely")
        elif loneliness > 10:
            effects.append("much more lonely")
        elif loneliness > 0:
            effects.append("a bit more lonely")
        
        # 스트레스
        stress = needs_diff.get("stress", 0)
        if stress <= -10:
            effects.append("much less stressed")
        elif stress < 0:
            effects.append("a bit less stressed")
        elif stress > 10:
            effects.append("much more stressed")
        elif stress > 0:
            effects.append("a bit more stressed")
        
        # 효과 문장 결합
        if effects:
            if len(effects) == 1:
                result_text += f". feeling {effects[0]}"
            else:
                result_text += f". feeling {', '.join(effects[:-1])} and {effects[-1]}"
        
        return result_text
    
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
        성공 시에는 중복 정보 제거하여 간결하게 생성
        """
        # 이벤트 부분 생성
        event_part = ""
        if action:
            event_part += action
            if interactable:
                event_part += f" {interactable}"
            if location:
                event_part += f" at {location}"
        elif location:
            event_part = f"went to {location}"
        else:
            event_part = "unknown event"
        
        # 피드백 문장 처리 (성공 시 간결하게, 실패 시 상세하게)
        if success:
            # 성공 시 욕구 변화만 표현 (이벤트 정보 + 욕구 변화)
            # 욕구 변화 추출
            needs_effects = ""
            
            # 원본 피드백 문장에서 "feeling" 이후 부분 추출
            feeling_index = feedback_sentence.lower().find("feeling")
            if feeling_index != -1:
                needs_effects = feedback_sentence[feeling_index:]
            
            # 결합된 피드백 (간결한 버전)
            combined_feedback = f"{event_part}. {needs_effects}"
        else:
            # 실패 시 전체 피드백 (이벤트 + 실패 경험 + 욕구 변화)
            # 'I' 시작 패턴 정리
            processed_feedback = feedback_sentence
            i_patterns = ['I tried to', 'I feel', 'I am', 'I was', 'I went', 'I found', 'I failed to']
            for pattern in i_patterns:
                if processed_feedback.startswith(pattern):
                    processed_feedback = processed_feedback[len(pattern):].strip()
            
            # 첫 문자 소문자로 변경
            if processed_feedback and len(processed_feedback) > 0:
                processed_feedback = processed_feedback[0].lower() + processed_feedback[1:]
            
            # 결합된 피드백 (상세 버전)
            combined_feedback = f"{event_part}. {processed_feedback}"
        
        # 피드백 설명 추가 (있는 경우)
        if feedback_description:
            # 이미 마침표로 끝나는지 확인
            if combined_feedback.endswith('.'):
                combined_feedback += f" {feedback_description}"
            else:
                combined_feedback += f". {feedback_description}"
        
        return combined_feedback
    
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
                    
                    # 임베딩 데이터 저장
                    print(f"🔍 임베딩 저장 시작 - agent_name: {agent_name}, memory_id: {memory_id}")
                    if "embeddings" not in memories[agent_name]:
                        print("📁 embeddings 디렉토리 생성")
                        memories[agent_name]["embeddings"] = {}
                    if memory_id not in memories[agent_name]["embeddings"]:
                        print("📝 새로운 memory_id에 대한 임베딩 구조 생성")
                        memories[agent_name]["embeddings"][memory_id] = {
                            "event": [],
                            "action": [],
                            "feedback": []
                        }
                    print(f"💾 임베딩 저장 시도 - embedding 길이: {len(embedding) if embedding else 'None'}")
                    memories[agent_name]["embeddings"][memory_id]["feedback"] = embedding
                    print("✅ 임베딩 저장 완료")
                    
                    # 메모리 저장 확인
                    self.memory_utils._save_memories(memories)
                    print("💾 메모리 파일 저장 완료")

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
                    "importance": 4  # 피드백의 기본 중요도
                }
                memories[agent_name]["embeddings"][memory_id] = {
                    "event": [],
                    "action": self.memory_utils.get_embedding(action) if action else [],
                    "feedback": embedding
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
                    "importance": 4  # 피드백의 기본 중요도
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