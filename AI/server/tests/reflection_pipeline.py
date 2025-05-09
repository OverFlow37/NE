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
from typing import Dict, Any

# 각 단계별 처리 모듈 가져오기
from .memory_processor import MemoryProcessor 
import importance_rater
from .reflection_generator import ReflectionGenerator

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

def process_reflection_request(request_data: Dict[str, Any]) -> bool:
    """
    AI 브릿지의 반성 요청 처리 파이프라인
    
    Parameters:
    - request_data: AI 브릿지로부터의 요청 데이터
    
    Returns:
    - 성공 여부 (True/False)
    """
    try:
        # 현재 디렉토리 경로
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 파일 경로 설정
        memory_file_path = os.path.join(base_dir, "memories.json")
        reflection_file_path = os.path.join(base_dir, "./reflect/reflections.json")
        results_folder = os.path.join(base_dir, "reflection_results")
        
        # 폴더 생성
        os.makedirs(results_folder, exist_ok=True)
        os.makedirs(os.path.dirname(reflection_file_path), exist_ok=True)
        
        # 에이전트 이름과 날짜 추출
        agent_data = request_data.get("agent", {})
        agent_name = agent_data.get("name", "")
        agent_date = agent_data.get("time", "")
        
        if not agent_name:
            logger.error("요청에 유효한 에이전트 이름이 없습니다.")
            return False
        
        logger.info(f"에이전트 '{agent_name}'에 대한 반성 처리 시작 (날짜: {agent_date})")
        
        # 1. 메모리 처리기 초기화 및 메모리 로드
        memory_processor = MemoryProcessor(memory_file_path)
        memories = memory_processor.load_memories()
        
        if not memories or agent_name not in memories:
            logger.error(f"에이전트 '{agent_name}'의 메모리를 찾을 수 없습니다.")
            return False
        
        # 2. 특정 날짜의 메모리 필터링 (날짜가 제공된 경우)
        if agent_date:
            filtered_memories = memory_processor.filter_todays_memories(agent_name, date_str=agent_date)
            logger.info(f"날짜 '{agent_date}'로 특정된 메모리를 필터링합니다.")
        else:
            # 날짜가 제공되지 않은 경우 최신 날짜 사용
            filtered_memories = memory_processor.filter_todays_memories(agent_name)
            logger.info(f"날짜가 제공되지 않아 최신 메모리를 사용합니다.")
        
        if not filtered_memories:
            # 해당 날짜에 메모리가 없는 경우
            if agent_date:
                logger.warning(f"에이전트 '{agent_name}'의 {agent_date} 날짜 메모리가 없습니다.")
            else:
                logger.warning(f"에이전트 '{agent_name}'의 오늘 메모리가 없습니다.")
            return False
        
        logger.info(f"{len(filtered_memories)}개의 필터링된 메모리를 찾았습니다.")
        
        # 3. 메모리 중요도 평가
        importance_rater_instance = importance_rater.ImportanceRater()
        rated_memories = importance_rater_instance.add_importance_to_memories(memories, agent_name, filtered_memories)
        
        # 4. 업데이트된 메모리 저장
        memory_processor.save_memories(rated_memories)
        logger.info("중요도가 추가된 메모리가 저장되었습니다.")
        
        # 5. 중요한 메모리 선택 (특정 날짜에 맞게)
        important_memories = memory_processor.select_important_memories(
            rated_memories, 
            agent_name, 
            date_str=agent_date
        )
        
        if not important_memories:
            logger.warning(f"에이전트 '{agent_name}'의 중요한 메모리를 찾을 수 없습니다.")
            return False
        
        logger.info(f"{len(important_memories)}개의 중요한 메모리를 선택했습니다.")
        
        # 6. 반성 생성기 초기화
        reflection_generator = ReflectionGenerator(reflection_file_path)
        
        # 7. 이전 반성 가져오기
        previous_reflections = reflection_generator.get_previous_reflections(agent_name)
        
        # 8. 반성 생성
        reflections = reflection_generator.generate_reflections(agent_name, important_memories, previous_reflections)
        
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