import subprocess
import time
import sys

MAX_RUNS = 5
SCRIPT_PATH = "plantest.py"  # 실행할 스크립트 경로

for i in range(MAX_RUNS):
    print(f"\n🔁 실행 {i + 1}/{MAX_RUNS} - {SCRIPT_PATH}...\n")

    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH],  # python 대신 현재 실행 중인 인터프리터 사용
            capture_output=True,
            text=True,
            encoding='utf-8',  # UTF-8 강제 인코딩
            errors='replace'   # 인코딩 문제 발생 시 문자 치환
        )

        print("📤 표준 출력:")
        print(result.stdout)

        if result.stderr:
            print(f"⚠️ 오류 출력:\n{result.stderr}")

    except Exception as e:
        print(f"❌ 실행 중 예외 발생: {e}")

    time.sleep(1)
