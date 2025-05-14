# server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import re
import asyncio
import sys
from pathlib import Path
import os
from datetime import datetime, timedelta
import time
import gensim.downloader as api
from typing import Dict, Any
import numpy as np

print("\n=== 서버 초기화 시작 ===")
start_time = time.time()

# 현재 파일의 절대 경로를 기준으로 상위 디렉토리 찾기
CURRENT_DIR = Path(__file__).parent
ROOT_DIR = CURRENT_DIR.parent  # AI 디렉토리
print(f"📁 작업 디렉토리: {ROOT_DIR}")

# AI 디렉토리를 Python 경로에 추가
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
    print(f"📌 Python 경로에 추가됨: {ROOT_DIR}")

print("\n=== 모듈 임포트 시작 ===")
import_start = time.time()

try:
    from agent.modules.ollama_client import OllamaClient
    print("✅ OllamaClient 임포트 완료")
except Exception as e:
    print(f"❌ OllamaClient 임포트 실패: {e}")

try:
    from agent.modules.memory_utils import MemoryUtils
    print("✅ MemoryUtils 임포트 완료")
except Exception as e:
    print(f"❌ MemoryUtils 임포트 실패: {e}")

try:
    from agent.modules.retrieve import MemoryRetriever
    print("✅ MemoryRetriever 임포트 완료")
except Exception as e:
    print(f"❌ MemoryRetriever 임포트 실패: {e}")

try:
    from agent.modules.embedding_updater import EmbeddingUpdater
    print("✅ EmbeddingUpdater 임포트 완료")
except Exception as e:
    print(f"❌ EmbeddingUpdater 임포트 실패: {e}")

from agent.modules.event_id_manager import EventIdManager
from agent.modules.reaction_decider import ReactionDecider

from agent.modules.npc_conversation import NPCConversationManager

print(f"⏱ 모듈 임포트 시간: {time.time() - import_start:.2f}초")

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("\n=== 모듈 인스턴스 생성 시작 ===")
instance_start = time.time()

# Word2Vec 모델 로드
print("🤖 Word2Vec 모델 로딩 중...")
word2vec_model = api.load('word2vec-google-news-300')
print("✅ Word2Vec 모델 로딩 완료")

try:
    client = OllamaClient()
    print("✅ OllamaClient 인스턴스 생성 완료")
except Exception as e:
    print(f"❌ OllamaClient 인스턴스 생성 실패: {e}")

try:
    memory_utils = MemoryUtils(word2vec_model)
    print("✅ MemoryUtils 인스턴스 생성 완료")
except Exception as e:
    print(f"❌ MemoryUtils 인스턴스 생성 실패: {e}")

try:
    retrieve = MemoryRetriever(memory_file_path="agent/data/memories.json", word2vec_model=word2vec_model)
    print("✅ MemoryRetriever 인스턴스 생성 완료")
except Exception as e:
    print(f"❌ MemoryRetriever 인스턴스 생성 실패: {e}")

try:
    embedding_updater = EmbeddingUpdater(word2vec_model)
    print("✅ EmbeddingUpdater 인스턴스 생성 완료")
except Exception as e:
    print(f"❌ EmbeddingUpdater 인스턴스 생성 실패: {e}")

try:
    event_id_manager = EventIdManager(memory_utils=memory_utils)
    print("✅ EventIdManager 인스턴스 생성 완료")
except Exception as e:
    print(f"❌ EventIdManager 인스턴스 생성 실패: {e}")

try:
    reaction_decider = ReactionDecider(
        memory_utils=memory_utils,
        ollama_client=client,
        word2vec_model=word2vec_model
    )
    print("✅ ReactionDecider 인스턴스 생성 완료")
except Exception as e:
    print(f"❌ ReactionDecider 인스턴스 생성 실패: {e}")

try:
    conversation_manager = NPCConversationManager(
        ollama_client=client,
        memory_utils=memory_utils,
        word2vec_model=word2vec_model,
        max_turns=4  # 모듈 내부에서 최대 턴 수 설정 (필요에 따라 변경 가능)
    )
    print("✅ NPCConversationManager 인스턴스 생성 완료")
except Exception as e:
    print(f"❌ NPCConversationManager 인스턴스 생성 실패: {e}")


print(f"⏱ 인스턴스 생성 시간: {time.time() - instance_start:.2f}초")

# 프롬프트 템플릿
RETRIEVE_PROMPT_TEMPLATE = """
당신은 {AGENT_NAME}입니다. 현재 상황에 대해 반응해야 합니다.

현재 이벤트:
{EVENT_CONTENT}

유사한 과거 이벤트:
{SIMILAR_EVENT}

다음과 같은 형식으로 JSON 응답을 해주세요:
{{
    "action": "이벤트에 대한 반응",
    "emotion": "감정 상태",
    "reason": "반응 이유"
}}
"""

RETRIEVE_SYSTEM_TEMPLATE = """
You are a helpful AI assistant that responds in JSON format.
Your responses should be natural and contextual.
"""

# 프롬프트 파일 경로
PROMPT_DIR = ROOT_DIR / "agent" / "prompts" / "retrieve"
RETRIEVE_PROMPT_PATH = PROMPT_DIR / "retrieve_prompt.txt"
RETRIEVE_SYSTEM_PATH = PROMPT_DIR / "retrieve_system.txt"

print("\n=== 프롬프트 파일 확인 ===")
print(f"📂 프롬프트 디렉토리: {PROMPT_DIR}")
print(f"📄 프롬프트 파일: {RETRIEVE_PROMPT_PATH}")
print(f"📄 시스템 파일: {RETRIEVE_SYSTEM_PATH}")

def load_prompt_file(file_path: Path) -> str:
    """
    프롬프트 파일을 로드하거나 기본 템플릿을 반환
    
    Args:
        file_path: 프롬프트 파일 경로
    
    Returns:
        str: 프롬프트 내용
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 프롬프트 파일 로드 중 오류 발생: {e}")
        # 파일이 없는 경우 기본 템플릿 반환
        if file_path == RETRIEVE_PROMPT_PATH:
            return RETRIEVE_PROMPT_TEMPLATE
        elif file_path == RETRIEVE_SYSTEM_PATH:
            return RETRIEVE_SYSTEM_TEMPLATE
        return ""

@app.get("/hello")
async def hello():
    return "Hello from Python!"

@app.post("/perceive")
async def perceive_event(payload: dict):
    """관찰 정보를 저장하는 엔드포인트"""
    try:
        if not payload or 'agent' not in payload:
            return {"success": False, "error": "agent field is required"}
            
        agent_data = payload.get('agent', {})
        agent_name = agent_data.get('name', 'John')
        event_data = agent_data.get('event', {})
        
        # 게임 시간 가져오기
        game_time = agent_data.get('time', None)
        
        # 시간 정보가 없으면 추가
        if game_time and "time" not in event_data:
            event_data["time"] = game_time
        
        # 이벤트 ID 할당 (게임 시간 전달)
        event_id = event_id_manager.get_event_id(event_data, agent_name, game_time)
        
        # 이벤트 데이터에 event_id 추가
        event_data["event_id"] = event_id
        
        # 메모리 저장
        success = memory_utils.save_perception(event_data, agent_name)
        return {
            "success": success,
            "event_id": event_id
        }
        
    except Exception as e:
        print(f"❌ 관찰 정보 저장 중 오류 발생: {str(e)}")
        return {"success": False, "error": str(e)}


@app.post("/react")
async def should_react(payload: dict):
    """관찰된 이벤트에 반응할지 여부를 결정하는 엔드포인트"""
    try:
        # 전체 처리 시작 시간 기록
        react_start_time = time.time()
        print("\n=== /react 엔드포인트 호출 ===")
        print("📥 요청 데이터:", json.dumps(payload, indent=2, ensure_ascii=False))
        
        if not payload or 'agent' not in payload:
            return {"success": False, "error": "agent field is required"}
            
        agent_data = payload.get('agent', {})
        agent_name = agent_data.get('name', 'John')
        event_data = agent_data.get('event', {})
        
        # 게임 시간 가져오기
        game_time = agent_data.get('time', None)
        
        # 이벤트 ID 할당 (게임 시간 전달)
        event_id = event_id_manager.get_event_id(event_data, agent_name, game_time)
        
        # 이벤트 데이터에 event_id와 time 추가
        event_data["event_id"] = event_id
        if game_time and "time" not in event_data:
            event_data["time"] = game_time
        
        # 반응 여부 판단
        print("🤔 반응 여부 판단 중...")
        decision_start = time.time()
        reaction_decision = await reaction_decider.should_react_to_event(event_data, agent_data)
        decision_time = time.time() - decision_start
        print(f"⏱ 반응 판단 시간: {decision_time:.2f}초")
        
        # 결과 추출 - 단순 불리언 값과 이유
        should_react = reaction_decision.get("should_react", True)
        reason = reaction_decision.get("reason", "")
        
        # 메모리 저장 (판단 결과와 무관하게 저장)
        print("💾 메모리 저장 중...")
        memory_start = time.time()
        success = memory_utils.save_perception(event_data, agent_name)
        memory_time = time.time() - memory_start
        print(f"⏱ 메모리 저장 시간: {memory_time:.2f}초")
        
        # 전체 처리 시간 계산
        total_time = time.time() - react_start_time
        print(f"⏱ 전체 처리 시간: {total_time:.2f}초")
        
        # 응답 - 단순 형식으로 반환
        return {
            "success": success,
            "should_react": should_react,  # True 또는 False
            "event_id": event_id,
        }
        
    except Exception as e:
        print(f"❌ 반응 결정 중 오류 발생: {str(e)}")
        return {"success": False, "error": str(e)}


@app.post("/make_reaction")
async def react_to_event(payload: dict):
    """이벤트에 대한 반응을 생성하는 엔드포인트"""
    try:
        # 전체 처리 시작 시간 기록
        total_start_time = time.time()
        
        # 요청 데이터 로깅
        print("\n=== /make_reaction 엔드포인트 호출 ===")
        print("📥 요청 데이터:", json.dumps(payload, indent=2, ensure_ascii=False))
        
        # 필수 필드 확인
        if not payload or 'agent' not in payload:
            print("❌ 필수 필드 누락")
            return {"error": "agent field is required"}, 400
            
        # 에이전트 데이터 추출
        agent_data = payload.get('agent', {})
        agent_name = agent_data.get('name', 'John')
        
        # 이벤트 데이터 추출
        event_data = agent_data.get('event', {})
        event_type = event_data.get('event_type', '')
        event_location = event_data.get('event_location', '')
        object_name = event_data.get('object', '')
        
        # 에이전트의 현재 시간 추출
        agent_time = agent_data.get('time', '')
        if not agent_time:
            agent_time = datetime.now().strftime("%Y.%m.%d.%H:%M")
        
        # 시간 정보가 없으면 추가
        if "time" not in event_data:
            event_data["time"] = agent_time
        
        print(f"👤 에이전트 이름: {agent_name}")
        print(f"🔍 이벤트 타입: {event_type}")
        print(f"📍 이벤트 위치: {event_location}")
        print(f"🎯 이벤트 대상: {object_name}")
        print(f"⏰ 에이전트 시간: {agent_time}")
        print(f"🧩 성격: {agent_data.get('personality', 'None')}")
        print(f"📍 현재 위치: {agent_data.get('current_location', 'None')}")
        
        visible_interactables = agent_data.get('visible_interactables', [])
        if visible_interactables:
            print("👁️ 상호작용 가능한 객체:")
            for loc_data in visible_interactables:
                loc = loc_data.get('location', '')
                objects = loc_data.get('interactable', [])
                print(f"  - {loc}: {', '.join(objects)}")

        # 이벤트 ID 할당 (게임 시간 전달)
        event_id = event_id_manager.get_event_id(event_data, agent_name, agent_time)
        
        # 이벤트 데이터에 event_id 추가
        event_data["event_id"] = event_id
        
        # 이벤트 객체 생성
        event = {
            "event_type": event_type,
            "event_location": event_location,
            "object": object_name,
            "time": agent_time,  # 시간 정보 추가
            "event_id": event_id  # 이벤트 ID 추가
        }
        
        # 이벤트를 문장으로 변환
        event_sentence = memory_utils.event_to_sentence(event)
        print(f"📝 이벤트 문장: {event_sentence}")
        
        # 임베딩 생성
        embedding = memory_utils.get_embedding(event_sentence)
        print(f"🔢 임베딩 생성 완료 (차원: {len(embedding)})")
        
        # 프롬프트 생성
        prompt = retrieve.create_reaction_prompt(
            event_sentence=event_sentence,
            event_embedding=embedding,
            agent_name=agent_name,
            prompt_template=load_prompt_file(RETRIEVE_PROMPT_PATH),
            agent_data=agent_data,
            similar_data_cnt=3,  # 유사한 이벤트 3개 포함
            similarity_threshold=0.5  # 유사도 0.5 이상인 이벤트만 포함
        )
        print(f"📋 생성된 프롬프트:\n{prompt}")
        
        # Ollama API 호출
        print("🤖 Ollama API 호출 중...")
        
        # Ollama 호출 시작 시간 기록
        ollama_start_time = time.time()
        
        try:
            # Ollama API 호출
            response = await client.process_prompt(
                prompt=prompt,
                system_prompt=load_prompt_file(RETRIEVE_SYSTEM_PATH),
                model_name="gemma3",
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "frequency_penalty": 0.1,
                    "presence_penalty": 0.1
                }
            )
            
            # Ollama 응답 시간 계산
            ollama_response_time = time.time() - ollama_start_time
            
            if response.get("status") != "success":
                raise HTTPException(status_code=500, detail=f"Ollama API 호출 실패: {response.get('status')}")
            
            answer = response.get("response", "")
            print(f"📥 Ollama 응답: {answer}")
            
            # 1) 펜스 제거
            cleaned = answer.replace("```json", "").replace("```", "").strip()
            print(f"🧹 정제된 응답: {cleaned}")
            
            # 2) JSON 텍스트 추출 (더 유연한 패턴)
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if not match:
                print("❌ JSON 형식이 아닙니다.")
                raise HTTPException(status_code=500, detail="응답에서 JSON을 찾을 수 없습니다.")
            
            json_text = match.group(0)
            print(f"📄 추출된 JSON: {json_text}")

            # 3) 파싱
            reaction_obj = json.loads(json_text)
            print(f"✅ JSON 파싱 성공: {reaction_obj}")
            
            # 필수 필드 확인
            if "action" not in reaction_obj or "details" not in reaction_obj:
                print("⚠️ 응답에 필수 필드가 없습니다. 기본값으로 대체합니다.")
                if "action" not in reaction_obj:
                    reaction_obj["action"] = "use"
                if "details" not in reaction_obj:
                    reaction_obj["details"] = {
                        "location": event_location,
                        "target": object_name,
                        "duration": "60",
                        "reason": "Default action due to incomplete response"
                    }
                
            # 메모리 저장 (프롬프트 생성 및 API 응답 이후)
            memory_utils.save_memory(
                event_sentence=event_sentence,
                embedding=embedding,
                event_time=agent_time,  # 에이전트의 시간 사용
                agent_name=agent_name,
                event_id=event_id  # 이벤트 ID 추가
            )
            print(f"💾 메모리 저장 완료 (시간: {agent_time}, 이벤트 ID: {event_id})")
            
            # 전체 처리 시간 계산
            total_response_time = time.time() - total_start_time
            
            # 시간 측정 결과 출력
            print(f"\n⏱ 시간 측정 결과:")
            print(f"  - Ollama 응답 시간: {ollama_response_time:.2f}초")
            print(f"  - 전체 처리 시간: {total_response_time:.2f}초")
            
            # 이벤트 ID를 응답에 포함
            reaction_obj["event_id"] = event_id
            
            return {
                "success": True,
                "data": reaction_obj
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            raise HTTPException(status_code=500, detail=f"JSON 파싱 실패: {e}")
        except Exception as e:
            print(f"❌ 응답 처리 중 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return {"success": False, "error": str(e)}, 500

@app.post("/agent_action")
async def save_agent_action(payload: dict):
    """에이전트의 행동을 저장하는 엔드포인트"""
    try:
        if not payload or 'agent' not in payload:
            return {"success": False, "error": "agent field is required"}
            
        agent_data = payload.get('agent', {})
        agent_name = agent_data.get('name', 'John')
        action_data = agent_data.get('action', {})
        
        # 행동 데이터에 시간 정보 추가
        action_data['time'] = agent_data.get('time', datetime.now().strftime("%Y.%m.%d.%H:%M"))
        
        # 행동 데이터를 영어 문장으로 변환
        action_sentence = f"{action_data.get('action', '')} {action_data.get('target', '')} at {agent_data.get('current_location', '')}"
        
        # 임베딩 생성
        embedding = memory_utils.get_embedding(action_sentence)
        
        # 메모리 저장 (event_id 포함)
        success = memory_utils.save_memory(
            event_sentence=action_sentence,
            embedding=embedding,
            event_time=action_data['time'],
            agent_name=agent_name,
            event_id=action_data.get('event_id', '')  # event_id 추가
        )
        
        return {"success": success}
        
    except Exception as e:
        print(f"❌ 에이전트 행동 저장 중 오류 발생: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/action_feedback")
async def save_action_feedback(payload: dict):
    """행동에 대한 피드백을 저장하는 엔드포인트"""
    try:
        if not payload or 'agent' not in payload:
            return {"success": False, "error": "agent field is required"}
            
        agent_data = payload.get('agent', {})
        agent_name = agent_data.get('name', 'John')
        feedback_data = agent_data.get('feedback', {})
        
        # 피드백 데이터에 시간 정보 추가
        feedback_data['time'] = agent_data.get('time', datetime.now().strftime("%Y.%m.%d.%H:%M"))
        
        # 피드백 문장 추출
        feedback_sentence = feedback_data.get('feedback_description', '')
        
        # 임베딩 생성
        embedding = memory_utils.get_embedding(feedback_sentence)
        
        # 메모리 저장 (event_id 포함)
        success = memory_utils.save_memory(
            event_sentence=feedback_sentence,
            embedding=embedding,
            event_time=feedback_data['time'],
            agent_name=agent_name,
            event_id=feedback_data.get('event_id', '')  # event_id 추가
        )
        
        return {"success": success}
        
    except Exception as e:
        print(f"❌ 피드백 저장 중 오류 발생: {str(e)}")
        return {"success": False, "error": str(e)}

try:
    from agent.modules.reflection.importance_rater import ImportanceRater
    from agent.modules.reflection.reflection_pipeline import process_reflection_request
    from agent.modules.plan.plan_pipeline import process_plan_request
    print("✅ reflection 및 plan 모듈 임포트 완료")
except Exception as e:
    print(f"❌ reflection 및 plan 모듈 임포트 실패: {e}")

@app.post("/reflect-and-plan")
async def reflection_and_plan(payload: Dict[str, Any]):
    """반성 및 계획 생성 엔드포인트"""
    try:
        # 전체 처리 시작 시간 기록
        total_start_time = time.time()
        print(f"\n=== /reflect-and-plan 엔드포인트 호출 ===")
        print(f"📥 요청 데이터: {payload}")
        
        # 필수 필드 확인
        if "agent" not in payload or "name" not in payload["agent"]:
            return {"success": False, "error": "agent.name이 필요합니다."}
        
        # 날짜 확인
        agent_time = payload.get("agent", {}).get("time", "")
        if not agent_time:
            return {"success": False, "error": "agent.time이 필요합니다."}
        
        # # Ollama 클라이언트 초기화
        # client = OllamaClient()
        # 반성 처리 시작 시간
        reflection_start_time = time.time()
        reflection_success = await process_reflection_request(payload, client, word2vec_model=word2vec_model)
        reflection_time = time.time() - reflection_start_time
        print(f"⏱ 반성 처리 시간: {reflection_time:.2f}초")
        
        # 계획 처리 시작 시간
        plan_start_time = time.time()
        plan_success = await process_plan_request(payload, client)
        plan_time = time.time() - plan_start_time
        print(f"⏱ 계획 처리 시간: {plan_time:.2f}초")
        
        # 다음날 계획 가져오기
        next_day_plan = {}
        if plan_success:
            try:
                plan_file_path = os.path.join(ROOT_DIR, "agent", "data", "plans.json")
                with open(plan_file_path, "r", encoding="utf-8") as f:
                    plan_data = json.load(f)
                    agent_name = payload["agent"]["name"]
                    current_date = datetime.strptime(agent_time, "%Y.%m.%d.%H:%M")
                    next_day = (current_date + timedelta(days=1)).strftime("%Y.%m.%d")
                    next_day_plan = plan_data.get(agent_name, {}).get("plans", {}).get(next_day, {})
            except Exception as e:
                print(f"다음날 계획 로드 실패: {str(e)}")
        
        # 전체 처리 시간 계산
        total_time = time.time() - total_start_time
        print(f"\n⏱ 시간 측정 결과:")
        print(f"  - 반성 처리 시간: {reflection_time:.2f}초")
        print(f"  - 계획 처리 시간: {plan_time:.2f}초")
        print(f"  - 전체 처리 시간: {total_time:.2f}초")
        
        return {
            "success": reflection_success and plan_success,
            "next_day_plan": next_day_plan,
            "performance_metrics": {
                "total_time": total_time,
                "reflection_time": reflection_time,
                "plan_time": plan_time
            }
        }
        
    except Exception as e:
        print(f"❌ 반성 및 계획 처리 중 오류 발생: {str(e)}")
        return {"success": False, "error": str(e)}

######################################################################################
###                                     계획                                       ###
######################################################################################

@app.post("/update_embeddings")
async def update_embeddings():
    """
    모든 메모리와 반성의 임베딩을 업데이트하는 엔드포인트
    """
    try:
        print("\n=== 임베딩 업데이트 시작 ===")
        update_counts = embedding_updater.update_embeddings()
        print(f"✅ 임베딩 업데이트 완료: {update_counts}")
        return {
            "success": True,
            "updated": update_counts
        }
    except Exception as e:
        print(f"❌ 임베딩 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation")
async def handle_conversation(payload: dict):
    """
    NPC 간 대화를 처리하는 엔드포인트
    
    새 대화 시작, 대화 진행, 대화 종료 및 메모리 저장을 모두 처리합니다.
    최대 대화 턴 수는 NPCConversationManager 내부에서 설정됩니다.
    """
    try:
        # 전체 처리 시작 시간 기록
        start_time = time.time()
        print("\n=== /conversation 엔드포인트 호출 ===")
        print("📥 요청 데이터:", json.dumps(payload, indent=2, ensure_ascii=False))
        
        # 대화 처리
        result = await conversation_manager.process_conversation(payload)
        
        # 처리 시간 계산
        total_time = time.time() - start_time
        print(f"⏱ 대화 처리 시간: {total_time:.2f}초")
        
        # 현재 턴 수 출력
        if result.get("success"):
            current_turns = result.get("turns", 0)
            max_turns = result.get("max_turns", 10)
            print(f"🔄 현재 대화 턴: {current_turns}/{max_turns}")
        
        # 결과에 대화가 종료되었는지 여부 출력
        if result.get("success") and not result.get("should_continue", True):
            print("🔚 대화가 종료되었습니다. 이유:", result.get("conversation", {}).get("end_reason", ""))
            
            # 메모리 ID 출력
            memory_ids = result.get("memory_ids", [])
            if memory_ids:
                print(f"💾 메모리 저장 완료: {memory_ids}")
        
        return result
        
    except Exception as e:
        print(f"❌ 대화 처리 중 오류 발생: {str(e)}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print(f"\n=== 서버 초기화 완료 (총 소요시간: {time.time() - start_time:.2f}초) ===")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
