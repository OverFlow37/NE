# server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import re
import asyncio
import sys
from pathlib import Path
import os

# 현재 파일의 절대 경로를 기준으로 상위 디렉토리 찾기
CURRENT_DIR = Path(__file__).parent
ROOT_DIR = CURRENT_DIR.parent  # AI 디렉토리

# AI 디렉토리를 Python 경로에 추가
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from agent.modules.ollama_client import OllamaClient
from agent.modules.memory_utils import MemoryUtils
from agent.modules.retrieve import Retrieve
import prompts.json_to_prompt as jp

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모듈 인스턴스 생성
client = OllamaClient()
memory_utils = MemoryUtils()
retrieve = Retrieve()

@app.get("/hello")
async def hello():
    return "Hello from Python!"

@app.post("/action")
async def receive_data(payload: dict):
    print("Unity로부터 받은 데이터:", payload)

    # 프롬프트 생성
    prompt = jp.format_prompt(payload)
    
    # Future를 사용하여 응답 대기
    future = asyncio.Future()
    
    async def handle_response(response):
        try:
            answer = response.get("response", "")
            
            # 1) 펜스 제거
            cleaned = answer.replace("```json", "").replace("```", "").strip()

            # 2) JSON 텍스트만 추출 (가장 바깥 중괄호 영역)
            match = re.search(r'\{.*\}', cleaned, flags=re.DOTALL)
            if not match:
                future.set_exception(HTTPException(status_code=500, detail="응답에서 JSON을 찾을 수 없습니다."))
                return
            json_text = match.group(0)

            # 3) 파싱
            try:
                action_obj = json.loads(json_text)
                future.set_result(action_obj)
            except json.JSONDecodeError as e:
                future.set_exception(HTTPException(status_code=500, detail=f"JSON 파싱 실패: {e}"))
        except Exception as e:
            future.set_exception(HTTPException(status_code=500, detail=str(e)))

    async def handle_error(error):
        future.set_exception(HTTPException(status_code=500, detail=str(error)))

    # 프롬프트 처리 요청
    await client.process_prompt(
        prompt=prompt,
        system_prompt="You are a helpful AI assistant that responds in JSON format.",
        model_name="gemma3",
        callback=handle_response,
        error_callback=handle_error
    )

    try:
        # 응답 대기
        action_obj = await future
        return {
            "action": action_obj
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/react")
async def react_to_event(payload: dict):
    try:
        # 1. 이벤트 추출 (필요한 경우 JSON 파싱)
        event_obj = payload.get("event", {})
        agent_name = payload.get("agent_name", "default")
        
        # 2. 이벤트 문장화
        event_sentence = memory_utils.event_to_sentence(event_obj)
        
        # 3. 이벤트 임베딩 추출
        event_embedding = memory_utils.get_embedding(event_sentence)
        
        # 4. 메모리 저장
        current_time = payload.get("time", "")  # 시간 정보는 클라이언트에서 전달받음
        memory_utils.save_memory(
            event_sentence=event_sentence,
            embedding=event_embedding,
            event_time=current_time
        )
        
        # 5. 반응 여부 결정 및 프롬프트 생성
        prompt = retrieve.create_reaction_prompt(
            event_obj=event_obj,
            event_embedding=event_embedding,
            agent_name=agent_name
        )
        
        if not prompt:
            return {"reaction": None, "reason": "No reaction needed"}
        
        # 6. Ollama API 호출
        future = asyncio.Future()
        
        async def handle_response(response):
            try:
                answer = response.get("response", "")
                cleaned = answer.replace("```json", "").replace("```", "").strip()
                match = re.search(r'\{.*\}', cleaned, flags=re.DOTALL)
                if not match:
                    future.set_exception(HTTPException(status_code=500, detail="응답에서 JSON을 찾을 수 없습니다."))
                    return
                json_text = match.group(0)
                reaction_obj = json.loads(json_text)
                future.set_result(reaction_obj)
            except Exception as e:
                future.set_exception(HTTPException(status_code=500, detail=str(e)))

        async def handle_error(error):
            future.set_exception(HTTPException(status_code=500, detail=str(error)))

        await client.process_prompt(
            prompt=prompt,
            system_prompt="You are an AI agent that decides how to react to events based on past memories.",
            model_name="gemma3",
            callback=handle_response,
            error_callback=handle_error
        )

        # 7. 응답 반환
        reaction = await future
        return {
            "reaction": reaction
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
