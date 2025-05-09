"""
서버 경로에서 파이프라인을 테스트하는 파일
"""

# test_reflection_pipeline.py
import sys
import os

# tests 폴더를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
tests_dir = os.path.join(current_dir, "tests")
sys.path.append(tests_dir)

# 이제 reflection_pipeline을 직접 임포트할 수 있음
from tests.reflection_pipeline import process_reflection_request

def test_reflection_process():
    # 테스트 요청 데이터
    test_request = {
        "agent": {
            "name": "John",
            "time": "2025.05.07"
        }
    }
    
    print("반성 파이프라인 테스트 시작")
    print(f"요청 데이터: {test_request}")
    
    # 반성 처리 함수 호출
    result = process_reflection_request(test_request)
    
    print(f"처리 결과: {result}")
    return result

if __name__ == "__main__":
    test_reflection_process()