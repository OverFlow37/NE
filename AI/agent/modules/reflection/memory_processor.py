"""
메모리 처리 모듈

메모리 파일을 로드하고, 필터링하며, 저장하는 기능을 제공합니다.
반성 파이프라인에서 메모리 관련 처리를 담당합니다.
"""

import os
import json
import re
import datetime
import logging
from typing import Dict, List, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MemoryProcessor")

class MemoryProcessor:
    def __init__(self, memory_file_path: str):
        """
        메모리 처리기 초기화
        
        Parameters:
        - memory_file_path: 메모리 JSON 파일 경로
        """
        self.memory_file_path = memory_file_path

        # 테스트를 위해 오늘 날짜를 메모리에 있는 날짜로 고정
        # self.today_str = "2025.05.07"  # memories.json에 있는 최신 날짜로 설정
        
        # logger.info(f"메모리 처리기 초기화 (파일: {memory_file_path})")

        self.today_str = datetime.datetime.now().strftime("%Y.%m.%d")
        
        logger.info(f"메모리 처리기 초기화 (파일: {memory_file_path})")
    
    def load_memories(self) -> Dict:
        """
        메모리 JSON 파일 로드
        
        Returns:
        - 로드된 메모리 데이터
        """
        try:
            with open(self.memory_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"메모리 파일 로드 완료: {self.memory_file_path}")
            return data
        except Exception as e:
            logger.error(f"메모리 파일 로드 오류: {e}")
            return {}
    
    def save_memories(self, memories: Dict) -> bool:
        """
        메모리 JSON 파일 저장
        
        Parameters:
        - memories: 저장할 메모리 데이터
        
        Returns:
        - 저장 성공 여부
        """
        try:
            # 임베딩 구조 변환
            for agent_name in memories:
                if "memories" in memories[agent_name]:
                    for memory_id, memory in memories[agent_name]["memories"].items():
                        # embeddings 필드 처리
                        if "embeddings" in memory:
                            # 최대 3개의 임베딩만 유지
                            memory["embeddings"] = memory["embeddings"][:3]
                        else:
                            memory["embeddings"] = []
                        
                        # 다른 임베딩 필드들은 제거
                        for field in ["event_embeddings", "action_embeddings", "feedback_embeddings"]:
                            if field in memory:
                                del memory[field]
            
            with open(self.memory_file_path, 'w', encoding='utf-8') as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
            logger.info(f"메모리 파일 저장 완료: {self.memory_file_path}")
            return True
        except Exception as e:
            logger.error(f"메모리 파일 저장 오류: {e}")
            return False
    
    def filter_todays_memories(self, agent_name: str, date_str: str = None) -> List[Dict]:
        """
        특정 날짜의 메모리 필터링
        
        Args:
            agent_name: 에이전트 이름
            date_str: 날짜 문자열 (YYYY.MM.DD 형식)
            
        Returns:
            List[Dict]: 필터링된 메모리 목록
        """
        memories = self.load_memories()
        
        if agent_name not in memories or "memories" not in memories[agent_name]:
            return []
        
        filtered_memories = []
        
        # 날짜가 제공되지 않은 경우 최신 날짜 사용
        if not date_str:
            # 모든 메모리의 날짜를 확인하여 최신 날짜 찾기
            latest_date = None
            for memory_id, memory in memories[agent_name]["memories"].items():
                time_str = memory.get("time", "")
                if time_str:
                    date_part = time_str.split(".")[:3]  # YYYY.MM.DD 부분만 추출
                    date = ".".join(date_part)
                    if not latest_date or date > latest_date:
                        latest_date = date
            date_str = latest_date
        
        # 해당 날짜의 메모리 필터링
        for memory_id, memory in memories[agent_name]["memories"].items():
            time_str = memory.get("time", "")
            if time_str:
                date_part = time_str.split(".")[:3]  # YYYY.MM.DD 부분만 추출
                date = ".".join(date_part)
                if date == date_str:
                    # memory_id 추가
                    memory_with_id = memory.copy()
                    memory_with_id["memory_id"] = memory_id
                    
                    # event, action, feedback 필드 확인 및 추가
                    for field in ["event", "action", "feedback"]:
                        if field not in memory_with_id:
                            memory_with_id[field] = ""
                    
                    filtered_memories.append(memory_with_id)
        
        logger.info(f"에이전트 '{agent_name}'의 {date_str} 날짜 메모리 {len(filtered_memories)}개 필터링됨")
        return filtered_memories
    
    def select_important_memories(self, memories: Dict, agent_name: str, date_str: str = None, k: int = 3) -> List[Dict]:
        """
        중요한 메모리 선택
        
        Args:
            memories: 전체 메모리 데이터
            agent_name: 에이전트 이름
            date_str: 날짜 문자열 (YYYY.MM.DD 형식)
            k: 선택할 메모리 개수
            
        Returns:
            List[Dict]: 선택된 중요한 메모리 목록
        """
        if agent_name not in memories or "memories" not in memories[agent_name]:
            return []
        
        # 해당 날짜의 메모리 필터링
        filtered_memories = []
        for memory_id, memory in memories[agent_name]["memories"].items():
            if "importance" not in memory:
                continue
                
            time_str = memory.get("time", "")
            if time_str:
                date_part = time_str.split(".")[:3]  # YYYY.MM.DD 부분만 추출
                date = ".".join(date_part)
                if not date_str or date == date_str:
                    # memory_id 추가
                    memory_with_id = memory.copy()
                    memory_with_id["memory_id"] = memory_id
                    
                    # event, action, feedback 필드 확인 및 추가
                    for field in ["event", "action", "feedback"]:
                        if field not in memory_with_id:
                            memory_with_id[field] = ""
                    
                    filtered_memories.append(memory_with_id)
        
        # importance 기준으로 정렬
        filtered_memories.sort(key=lambda x: x.get("importance", 0), reverse=True)
        
        # 상위 k개 선택
        selected_memories = filtered_memories[:k]
        logger.info(f"에이전트 '{agent_name}'의 중요한 메모리 {len(selected_memories)}개 선택됨")
        return selected_memories

# 테스트 코드
if __name__ == "__main__":
    # 현재 디렉토리 기준 메모리 파일 경로
    current_dir = os.path.dirname(os.path.abspath(__file__))
    memory_file_path = os.path.join(current_dir, "memories.json")
    
    # 메모리 처리기 초기화
    processor = MemoryProcessor(memory_file_path)
    
    # 메모리 로드
    memories = processor.load_memories()
    print(f"로드된 메모리: {bool(memories)}")
    
    # 오늘 메모리 필터링
    today_memories = processor.filter_todays_memories("John")
    print(f"오늘 메모리 개수: {len(today_memories)}")
    
    # 중요한 메모리 선택
    important_memories = processor.select_important_memories(memories, "John")
    print(f"중요한 메모리 개수: {len(important_memories)}")
    
    # 중요한 메모리 출력
    for i, memory in enumerate(important_memories):
        print(f"중요 메모리 #{i+1}: {memory.get('event', '')} (중요도: {memory.get('importance', 0)})")