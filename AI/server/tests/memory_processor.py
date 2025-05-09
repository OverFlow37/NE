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
            with open(self.memory_file_path, 'w', encoding='utf-8') as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
            logger.info(f"메모리 파일 저장 완료: {self.memory_file_path}")
            return True
        except Exception as e:
            logger.error(f"메모리 파일 저장 오류: {e}")
            return False
    
    def filter_todays_memories(self, agent_name: str, date_str: str = None) -> List[Dict]:
        """
        오늘 날짜(또는 지정한 날짜)의 메모리 필터링
        
        Parameters:
        - agent_name: 에이전트 이름
        - date_str: 날짜 문자열 (None인 경우 최신 메모리 날짜 사용)
        
        Returns:
        - 필터링된 메모리 리스트
        """
        if date_str is None:
            # 날짜가 제공되지 않은 경우, 메모리에서 최신 날짜 찾기
            date_str = self._find_latest_memory_date()
            if not date_str:
                date_str = self.today_str
        
        # 메모리 로드
        memories = self.load_memories()
        
        # 특정 날짜 메모리 필터링
        filtered_memories = []
        
        if agent_name in memories and "memories" in memories[agent_name]:
            for memory in memories[agent_name]["memories"]:
                time_str = memory.get("time", "")
                # 날짜가 일치하는 메모리만 추가
                if time_str.startswith(date_str):
                    filtered_memories.append(memory)
        
        logger.info(f"에이전트 '{agent_name}'의 {date_str} 날짜 메모리 {len(filtered_memories)}개를 필터링했습니다.")
        return filtered_memories
    
    def _find_latest_memory_date(self) -> str:
        """
        메모리 데이터에서 가장 최근 날짜 찾기
        
        Returns:
        - 최신 날짜 (YYYY.MM.DD 형식) 또는 빈 문자열
        """
        memory_data = self.load_memories()
        latest_date = ""
        latest_datetime = datetime.datetime.min
        
        for agent_name in memory_data:
            if "memories" in memory_data[agent_name]:
                for memory in memory_data[agent_name]["memories"]:
                    time_str = memory.get("time", "")
                    if time_str:
                        # 날짜 부분 추출 (YYYY.MM.DD)
                        match = re.match(r'(\d{4}\.\d{2}\.\d{2})', time_str)
                        if match:
                            date_str = match.group(1)
                            try:
                                # datetime 객체로 변환하여 비교
                                date_obj = datetime.datetime.strptime(date_str, "%Y.%m.%d")
                                if date_obj > latest_datetime:
                                    latest_datetime = date_obj
                                    latest_date = date_str
                            except:
                                pass
        
        return latest_date

    def select_important_memories(self, memories: Dict, agent_name: str, date_str: str = None, top_k: int = 3) -> List[Dict]:
        """
        중요한 메모리 선택
        
        Parameters:
        - memories: 메모리 데이터
        - agent_name: 에이전트 이름
        - date_str: 날짜 문자열 (None인 경우 오늘 날짜)
        - top_k: 선택할 상위 메모리 개수
        
        Returns:
        - 중요도 순으로 정렬된 상위 k개 메모리
        """
        if date_str is None:
            date_str = self.today_str
        
        # 해당 날짜의 메모리만 필터링
        todays_memories = []
        if agent_name in memories and "memories" in memories[agent_name]:
            for memory in memories[agent_name]["memories"]:
                time_str = memory.get("time", "")
                if time_str.startswith(date_str):
                    todays_memories.append(memory)
        
        # 중요도 필드가 있는 메모리만 필터링
        memories_with_importance = [m for m in todays_memories if "importance" in m]
        
        if not memories_with_importance:
            logger.warning(f"에이전트 '{agent_name}'의 메모리 중 중요도가 있는 메모리가 없습니다.")
            return []
        
        # 중요도 기준 내림차순 정렬
        sorted_memories = sorted(
            memories_with_importance, 
            key=lambda x: x.get("importance", 0), 
            reverse=True
        )
        
        # 상위 k개 반환
        selected_memories = sorted_memories[:top_k]
        logger.info(f"중요도 기준 상위 {len(selected_memories)}개 메모리를 선택했습니다.")
        
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