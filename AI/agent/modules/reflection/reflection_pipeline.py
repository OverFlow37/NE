"""
반성 처리 파이프라인

이 모듈은 반성 처리의 전체 워크플로우를 관리합니다:
1. 당일 메모리에 importance 추가
2. 중요한 메모리 선택
3. 이전 반성 참조
4. 반성 생성 및 저장
5. 결과 반환

AI 브릿지로부터 요청을 받아 처리하고 결과를 반환합니다.
"""

import os
import logging
import traceback
import re
from typing import Dict, Any
from pathlib import Path

# 각 단계별 처리 모듈 가져오기
from .memory_processor import MemoryProcessor 
from .importance_rater import ImportanceRater
from .reflection_generator import ReflectionGenerator
from ..ollama_client import OllamaClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("reflection_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ReflectionPipeline")

def _extract_date_from_time(time_str: str) -> str:
    """
    시간 문자열에서 날짜 부분만 추출
    
    Parameters:
    - time_str: 시간 문자열 (YYYY.MM.DD.HH:MM 형식)
    
    Returns:
    - 날짜 문자열 (YYYY.MM.DD 형식)
    """
    match = re.match(r'(\d{4}\.\d{2}\.\d{2})', time_str)
    if match:
        return match.group(1)
    return ""

async def process_reflection_request(request_data: Dict[str, Any], ollama_client: OllamaClient, word2vec_model=None) -> bool:
    """
    AI 브릿지의 반성 요청 처리 파이프라인
    
    Parameters:
    - request_data: AI 브릿지로부터의 요청 데이터
    - ollama_client: Ollama API 클라이언트 인스턴스
    - word2vec_model: word2vec 임베딩 모델 (선택적)
    
    Returns:
    - 성공 여부 (True/False)
    """
    try:
        # 현재 디렉토리 경로
        base_dir = Path(__file__).parent.parent.parent
        data_dir = base_dir / "data"
        
        # 파일 경로 설정
        memory_file_path = data_dir / "memories.json"
        reflection_file_path = data_dir / "reflections.json"
        
        # 폴더 생성
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 에이전트 이름과 날짜 추출
        agent_data = request_data.get("agent", {})
        agent_name = agent_data.get("name", "")
        agent_date = agent_data.get("time", "")
        
        if not agent_name:
            logger.error("요청에 유효한 에이전트 이름이 없습니다.")
            return False
        
        logger.info(f"에이전트 '{agent_name}'에 대한 반성 처리 시작 (날짜: {agent_date})")
        logger.info(f"임베딩 모델 상태: {'사용 가능' if word2vec_model else '사용 불가'}")
        
        # 1. 메모리 처리기 초기화 및 메모리 로드
        memory_processor = MemoryProcessor(str(memory_file_path))
        memories = memory_processor.load_memories()
        
        if not memories or agent_name not in memories:
            logger.error(f"에이전트 '{agent_name}'의 메모리를 찾을 수 없습니다.")
            return False
        
        # 2. 특정 날짜의 메모리 필터링 (날짜가 제공된 경우)
        if agent_date:
            # 날짜 부분만 추출
            date_str = _extract_date_from_time(agent_date)
            if not date_str:
                logger.error(f"유효하지 않은 날짜 형식: {agent_date}")
                return False
            filtered_memories = memory_processor.filter_todays_memories(agent_name, date_str=date_str)
            logger.info(f"날짜 '{date_str}'로 특정된 메모리를 필터링합니다.")
        else:
            # 날짜가 제공되지 않은 경우 최신 날짜 사용
            filtered_memories = memory_processor.filter_todays_memories(agent_name)
            logger.info(f"날짜가 제공되지 않아 최신 메모리를 사용합니다.")
        
        if not filtered_memories:
            # 해당 날짜에 메모리가 없는 경우
            if agent_date:
                logger.warning(f"에이전트 '{agent_name}'의 {date_str} 날짜 메모리가 없습니다.")
            else:
                logger.warning(f"에이전트 '{agent_name}'의 오늘 메모리가 없습니다.")
            return False
        
        logger.info(f"{len(filtered_memories)}개의 필터링된 메모리를 찾았습니다.")
        
        # 3. 메모리 중요도 평가
        importance_rater = ImportanceRater(ollama_client)
        rated_memories = await importance_rater.add_importance_to_memories(memories, agent_name, filtered_memories)
        
        # 4. 업데이트된 메모리 저장
        memory_processor.save_memories(rated_memories)
        logger.info("중요도가 추가된 메모리가 저장되었습니다.")
        
        # 5. 중요한 메모리 선택 (특정 날짜에 맞게)
        important_memories = memory_processor.select_important_memories(
            rated_memories, 
            agent_name, 
            date_str=date_str if agent_date else None
        )
        
        if not important_memories:
            logger.warning(f"에이전트 '{agent_name}'의 중요한 메모리를 찾을 수 없습니다.")
            return False
        
        logger.info(f"{len(important_memories)}개의 중요한 메모리를 선택했습니다.")
        
        # 6. 반성 생성기 초기화 (word2vec 모델 직접 전달)
        reflection_generator = ReflectionGenerator(str(reflection_file_path), ollama_client, embedding_model=word2vec_model)
        logger.info(f"반성 생성기 초기화 완료 (임베딩 모델: {'사용' if word2vec_model else '미사용'})")
        
        # 7. 이전 반성 가져오기
        previous_reflections = reflection_generator.get_previous_reflections(agent_name, agent_date)
        
        # 8. 반성 생성
        reflections = await reflection_generator.generate_reflections(agent_name, important_memories, previous_reflections, time=agent_date)
        
        if not reflections:
            logger.error("반성 생성에 실패했습니다.")
            return False
        
        logger.info(f"{len(reflections)}개의 반성이 생성되었습니다.")
        
        # 9. 반성 저장
        success = reflection_generator.save_reflections(agent_name, reflections)
        
        if not success:
            logger.error("반성 저장에 실패했습니다.")
            return False
        
        logger.info("반성이 성공적으로 생성되고 저장되었습니다.")
        
        # 성공적으로 모든 단계 완료
        return True
        
    except Exception as e:
        logger.error(f"반성 처리 파이프라인 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# 테스트용 코드
if __name__ == "__main__":
    # 테스트 요청 데이터
    test_request = {
        "agent": {
            "name": "John"
        }
    }
    
    print("반성 파이프라인 테스트")
    print(f"요청 데이터: {test_request}")
    
    # 요청 처리
    result = process_reflection_request(test_request)
    
    print(f"처리 결과: {result}")