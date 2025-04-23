import urllib.request
import json
import time
import re

# ==============================
#  서버 호출 함수
# ==============================
def get_response(prompt: str, api_url: str) -> str:
    """
    prompt 문자열을 LLM 서버에 보내고,
    JSON 응답에서 'response' 필드를 꺼내 출력 후 반환합니다.
    """
    payload = {
        "model": "gemma3",
        "prompt": prompt,
        "stream": False  # 스트리밍 모드를 꺼서 단일 JSON 응답을 받습니다
    }
    # HTTP 요청 준비
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        api_url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    # 요청-응답 시간 측정 시작
    start_time = time.time()
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
    elapsed = time.time() - start_time

    # 받은 바이트를 디코딩하고 JSON 파싱
    result = json.loads(raw.decode('utf-8'))
    answer = result.get("response", "")

    # 개행 문자 및 백슬래시 제거: 실제 newline, JSON 이스케이프된 "\n" 모두 처리
    answer = answer.replace("\\n", " ")
    answer = answer.replace("\n", " ")
    # 모든 백슬래시 제거
    answer = answer.replace("\\", "")
    # 코드 펜스(markdown) 제거
    answer = answer.replace("```json", "")
    answer = answer.replace("```", "")
    # 중복 공백 정리
    answer = re.sub(r'\s+', ' ', answer).strip()

    # 결과 출력
    print("🧠 응답:", answer)
    print(f"⏱ 응답시간: {elapsed:.3f}초")

    return answer

# ==============================
#  프롬프트 조립 함수
# ==============================
def format_prompt(instruction: str, state_obj: dict) -> str:
    """
    1) instruction: 자연어 지침 문자열
    2) state_obj: 에이전트 상태가 담긴 dict

    state_obj['agents'] 내부의 각 agent['state'] 필드를
    hunger, sleepiness, loneliness 수치를 기반해
    'very/not' 표현으로 변환한 후,
    지침과 JSON dump를 합쳐서 반환합니다.
    """
    # 수치 → 형용사 매핑 테이블
    metric_adj = {
        "hunger": "hungry",
        "sleepiness": "sleepy",
        "loneliness": "lonely"
    }

    def describe(level: int, adj: str) -> str:
        if level <= 3:
            return f"not {adj}"
        elif level <= 6:
            return adj
        else:
            return f"very {adj}"  

    # 에이전트 state 변환
    for agent in state_obj.get("agents", []):
        st = agent.get("state", {})
        parts = []
        for key in ("hunger", "sleepiness", "loneliness"):
            if key in st:
                parts.append(describe(st[key], metric_adj[key]))
        agent["state"] = ", ".join(parts)

    # 최종 프롬프트 조립
    prompt = instruction.strip() + "\n\n" + json.dumps(state_obj, ensure_ascii=False, indent=2)
    return prompt

# 이 모듈을 import 해서 사용하세요:
#
# from api_client import get_response, format_prompt
#
# 예시:
# instruction = open('prompt.txt', encoding='utf-8').read()
# state_data = json.loads(external_json_string)
# prompt = format_prompt(instruction, state_data)
# answer = get_response(prompt, 'http://localhost:11434/api/generate')
