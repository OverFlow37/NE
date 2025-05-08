"""
    batch_reflection_generator를 외부 스크립트에서 사용하는 간소화된 예제
    - generate_daily_reflections 함수만 사용
"""

import os
from batch_reflection_generator import generate_daily_reflections

def main():
    # 현재 스크립트 파일의 디렉토리 경로 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 파일 경로 설정
    agent_name = "John"
    memory_file_path = os.path.join(current_dir, "memories.json")
    reflection_file_path = os.path.join(current_dir, "./reflect/reflections.json")
    results_folder = os.path.join(current_dir, "reflection_results")
    date_str = "2025.05.04"  # 특정 날짜 지정
    
    print(f"에이전트 '{agent_name}'의 {date_str} 반성 생성을 시작합니다.")
    
    # generate_daily_reflections 함수 직접 사용
    result = generate_daily_reflections(
        agent_name=agent_name,
        memory_file_path=memory_file_path,
        reflection_file_path=reflection_file_path,
        results_folder=results_folder,
        date_str=date_str
    )
    
    # 결과에 대한 추가 분석이나 처리가 필요한 경우
    print(f"\n===== 성능 결과 요약 =====")
    print(f"생성된 반성 수: {result.get('count', 0)}")
    print(f"총 처리 시간: {result.get('total_time', 0):.2f}초")
    print(f"API 호출 시간: {result.get('api_time', 0):.2f}초")
    
    """
    # BatchMemoryReflectionSystem 클래스를 직접 사용하는 코드 (주석 처리)
    # 방법 2: BatchMemoryReflectionSystem 클래스 직접 사용
    print("\n=== 방법 2: BatchMemoryReflectionSystem 클래스 사용 ===")
    
    # 시스템 초기화
    reflection_system = BatchMemoryReflectionSystem(
        memory_file_path=memory_file_path,
        reflection_file_path=reflection_file_path,
        results_folder=results_folder
    )
    
    # 특정 날짜의 메모리 가져오기
    todays_memories = reflection_system.get_todays_memories(agent_name, date_str)
    print(f"해당 날짜의 메모리 수: {len(todays_memories)}")
    
    # 중요 메모리 필터링
    important_memories = reflection_system.get_important_memories(todays_memories, top_k=3)
    print(f"중요 메모리 수: {len(important_memories)}")
    
    # 중요 메모리 출력
    for i, memory in enumerate(important_memories):
        print(f"\n중요 메모리 #{i+1}:")
        print(f"  이벤트: {memory.get('event', '')}")
        print(f"  행동: {memory.get('action', '')}")
        print(f"  중요도: {memory.get('importance', 0)}")
    
    # 배치 반성 생성
    batch_result = reflection_system.generate_batch_reflections(agent_name, date_str)
    
    # 결과 출력
    if "error" not in batch_result:
        print("\n생성된 반성 목록:")
        for i, reflection in enumerate(batch_result.get("reflections", [])):
            print(f"\n반성 #{i+1}:")
            print(f"  이벤트: {reflection.get('event', '')}")
            print(f"  행동: {reflection.get('action', '')}")
            print(f"  생각: {reflection.get('thought', '')}")
            print(f"  중요도: {reflection.get('importance', 0)}")
    """

# 메인 함수 실행
if __name__ == "__main__":
    main()