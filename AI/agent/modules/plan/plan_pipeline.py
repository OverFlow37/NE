"""
계획 생성 파이프라인

반성 처리 후 계획을 생성하는 파이프라인을 구현합니다.
"""

import logging
from typing import Dict, Any, Tuple
from .plan_generator import PlanGenerator

# validate_unity_plan.py

from typing import Dict, List, Tuple
from .available_test import (
    VALID_ACTIONS,
    REGION_LOCATION_OBJECTS,
    FINDABLE_ANYWHERE,
    OBJECT_LOCATION_MAP
)

def validate_unity_plan(plan_dict: Dict[str, List], retry_count: int = 0) -> Tuple[bool, str]:
    """
    Unity용 계획의 유효성 검사

    Args:
        plan_dict (Dict): 계획 데이터 (JSON 파싱 결과)
        retry_count (int): 재시도 횟수 (0 또는 1)

    Returns:
        Tuple[bool, str]: (유효성 여부, 실패 메시지 또는 성공 메시지)
    """
    time_slots = plan_dict.get("time_slots", [])
    for i, slot in enumerate(time_slots):
        if len(slot) != 6:
            return False, f"[{i}] 항목 형식 오류: 6개의 요소가 필요합니다."

        action, location, target, start_time, end_time, importance = slot

        # 1. 액션 유효성
        if action not in VALID_ACTIONS:
            return False, f"[{i}] 유효하지 않은 액션: '{action}'"

        # 2. 로케이션 유효성
        if location not in REGION_LOCATION_OBJECTS:
            return False, f"[{i}] 존재하지 않는 위치: '{location}'"

        # 3. 타겟 유효성
        # location_objects = REGION_LOCATION_OBJECTS[location]
        # if target not in location_objects and action != "find":
        #     return False, f"[{i}] '{location}'에 '{target}' 없음"

        # 4. importance 타입 확인
        if not isinstance(importance, str) or not importance.isdigit():
            return False, f"[{i}] 중요도 값 오류: 반드시 숫자 형태의 문자열이어야 함 (예: '3')"

        # 5. 액션에 따른 타겟 유효성 검사
        # if action == "find":
        #     if target not in FINDABLE_ANYWHERE:
        #         valid_locations = OBJECT_LOCATION_MAP.get(target, [])
        #         if location not in valid_locations:
        #             return False, f"[{i}] '{target}'는 '{location}'에서 발견 불가"

        # 대소문자 판별별
        if not (target[0].isupper() and target[1:].islower()):
            return False, f"[{i}] 타겟 대소문자 오류: '{target}'는 첫 글자만 대문자여야 함"

    # 모두 통과
    return True, "✅ 유효한 계획입니다." if retry_count == 0 else "✅ 재생성된 계획이 유효합니다."

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PlanPipeline")

async def process_plan_request(request_data: Dict[str, Any], ollama_client) -> Tuple[bool, Dict]:
    """
    계획 생성 요청 처리
    
    Args:
        request_data: 요청 데이터
        ollama_client: Ollama API 클라이언트 인스턴스
    
    Returns:
        Tuple[bool, Dict]: (성공 여부, Unity용 계획 객체)
    """
    try:
        # 요청 데이터 로깅
        logger.info(f"계획 생성 요청: {request_data}")
        
        # 필수 필드 확인
        if not request_data or 'agent' not in request_data:
            logger.error("필수 필드 누락")
            return False, {}
        
        # 에이전트 데이터 추출
        agent_data = request_data.get('agent', {})
        agent_name = agent_data.get('name', 'John')
        
        # 날짜 추출
        date = agent_data.get('time', '')
        if not date:
            logger.error("날짜 정보 누락")
            return False, {}
        
        # 계획 생성기 초기화
        plan_generator = PlanGenerator(
            plan_file_path="agent/data/plans.json",
            reflection_file_path="agent/data/reflections.json",
            ollama_client=ollama_client
        )
        
        # 1단계: 계획 JSON 생성
        plans = await plan_generator.generate_plans(agent_name, date)
        
        if not plans:
            logger.error("계획 생성 실패")
            return False, {}
        
        logger.info(f"1단계 계획 생성 성공: {plans}")
        
        # 2단계: Unity용 계획 객체 생성
        unity_plan = await plan_generator.generate_unity_plan(plans)
        
        # 3단계 : 유효성 검사 (맵과 오브젝트, 액션 까지 모두 유효한지 검사) 
        # 만약 유효성 검사 실패 또는 출력 형식에 맞지 않는 결과가 나올 경우 재생성

        # 3단계: 유효성 검사
        valid, message = validate_unity_plan(unity_plan, retry_count=0)
        if not valid:
            logger.warning(f"유효성 검사 실패: {message} → 1회 재시도 시도 중...")

            # 재시도: 1단계, 2단계 다시 실행
            retry_plans = await plan_generator.generate_plans(agent_name, date)
            retry_unity_plan = await plan_generator.generate_unity_plan(retry_plans)

            if not retry_unity_plan:
                logger.error("재생성된 Unity 계획도 실패")
                return False, {}

            # 재검사
            valid, message = validate_unity_plan(retry_unity_plan, retry_count=1)
            if not valid:
                logger.error(f"재생성된 계획도 유효하지 않음: {message}")
                return False, {}
            
            logger.info(f"✅ 재생성된 계획이 유효함: {message}")
            return True, retry_unity_plan

        logger.info(f"✅ 계획 유효성 검사 통과: {message}")
        return True, unity_plan

    except Exception as e:
        logger.error(f"계획 생성 중 오류 발생: {str(e)}")
        return False, {}