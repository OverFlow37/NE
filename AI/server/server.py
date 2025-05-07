# server.py
from flask import Flask, request, jsonify
import json
import prompts.json_to_prompt as jp
import re
import atexit

app = Flask(__name__)

# 서버 시작 시 세션 초기화
def init_app():
    print("서버 시작: Ollama 세션 초기화")
    # 첫 요청 시 모델 로딩을 위해 더미 요청 전송
    try:
        jp.get_response("test")
    except Exception as e:
        print(f"초기 모델 로딩 실패 (무시해도 됨): {e}")

# 서버 종료 시 세션 정리
@atexit.register
def cleanup():
    print("서버 종료: Ollama 세션 정리")
    jp.session.close()

# GET 테스트용 엔드포인트
@app.route("/hello", methods=["GET"])
def hello():
    return "Hello from Python!"

# POST로 JSON 받기
@app.route("/action", methods=["POST"])
def receive_data():
    payload = request.get_json()
    print("Unity로부터 받은 데이터:", payload)

    prompt = jp.format_prompt(payload)
    answer = jp.get_response(prompt)  # API_URL은 기본값 사용

    # 1) 펜스 제거
    cleaned = answer.replace("```json", "").replace("```", "").strip()

    # 2) JSON 텍스트만 추출 (가장 바깥 중괄호 영역)
    match = re.search(r'\{.*\}', cleaned, flags=re.DOTALL)
    if not match:
        return jsonify({"status":"ERROR","message":"응답에서 JSON을 찾을 수 없습니다."}), 500
    json_text = match.group(0)

    # 3) 파싱
    try:
        action_obj = json.loads(json_text)
    except json.JSONDecodeError as e:
        return jsonify({"status":"ERROR","message":f"JSON 파싱 실패: {e}"}), 500

    # 4) dict 그대로 jsonify
    return jsonify({
        "status": "OK",
        "data": {
            "action": action_obj
        }
    })

if __name__ == "__main__":
    # 서버 시작 전 초기화
    init_app()
    # 0.0.0.0 으로 열면 같은 LAN 상 다른 기기에서도 접근 가능
    app.run(host="127.0.0.1", port=5000, debug=True)
