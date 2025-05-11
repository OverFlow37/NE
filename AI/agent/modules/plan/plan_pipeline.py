"""
계획 생성 파이프라인

반성 처리 후 계획을 생성하는 파이프라인을 구현합니다.
"""

import logging
from typing import Dict, Any
from .plan_generator import PlanGenerator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PlanPipeline")

async def process_plan_request(request_data: Dict[str, Any], ollama_client) -> bool:
    """
    계획 생성 요청 처리
    
    Args:
        request_data: 요청 데이터
        ollama_client: Ollama API 클라이언트 인스턴스
    
    Returns:
        bool: 성공 여부
    """
    try:
        # 요청 데이터 로깅
        logger.info(f"계획 생성 요청: {request_data}")
        
        # 필수 필드 확인
        if not request_data or 'agent' not in request_data:
            logger.error("필수 필드 누락")
            return False
        
        # 에이전트 데이터 추출
        agent_data = request_data.get('agent', {})
        agent_name = agent_data.get('name', 'John')
        
        # 날짜 추출
        date = agent_data.get('time', '')
        if not date:
            logger.error("날짜 정보 누락")
            return False
        
        # 계획 생성기 초기화
        plan_generator = PlanGenerator(
            plan_file_path="agent/data/plans.json",
            reflection_file_path="agent/data/reflections.json",
            ollama_client=ollama_client
        )
        
        # 계획 생성
        plans = await plan_generator.generate_plans(agent_name, date)
        
        if not plans:
            logger.error("계획 생성 실패")
            return False
        
        logger.info(f"계획 생성 성공: {plans}")
        return True
        
    except Exception as e:
        logger.error(f"계획 생성 중 오류 발생: {str(e)}")
        return False 