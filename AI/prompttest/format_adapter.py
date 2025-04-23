"""
유니티<->AI 간 JSON 형식 변환 유틸리티
"""
import json
import time
from pathlib import Path
from datetime import datetime

def unity_to_ai_format(unity_json, current_time=None, environment_state=None):
    """
    유니티 형식의 JSON을 AI 프롬프트용 형식으로 변환
    
    Args:
        unity_json: 유니티에서 전송한 JSON 문자열 또는 객체
        current_time: (선택) 현재 시간 문자열 (없으면 현재 시간 사용)
        environment_state: (선택) 환경 상태 문자열
    
    Returns:
        AI 프롬프트용 형식의 딕셔너리
    """
    # JSON 파싱 (문자열인 경우)
    if isinstance(unity_json, str):
        try:
            unity_data = json.loads(unity_json)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format from Unity")
    else:
        unity_data = unity_json
    
    # 시간 정보 설정
    if current_time is None:
        current_time = datetime.now().strftime("%Y.%m.%d.%H:%M")
    
    # 환경 정보 설정
    if environment_state is None:
        # 시간대에 따른 기본 환경 상태 생성
        hour = int(current_time.split(".")[-1].split(":")[0])
        if 6 <= hour < 12:
            environment_state = "Morning, clear sky"
        elif 12 <= hour < 18:
            environment_state = "Afternoon, bright day"
        elif 18 <= hour < 22:
            environment_state = "Evening, getting dark"
        else:
            environment_state = "Night time, dark and quiet"
    
    # AI 프롬프트용 데이터 구조 생성
    ai_format = {
        "current_time": current_time,
        "environment_state": environment_state
    }
    
    # 에이전트 정보 복사
    if "agents" in unity_data and isinstance(unity_data["agents"], list):
        ai_format["agents"] = unity_data["agents"]
        
        # 처리할 에이전트 이름 추출 (첫 번째 에이전트만 사용)
        if unity_data["agents"]:
            ai_format["agents_to_process"] = [unity_data["agents"][0]["name"]]
    
    return ai_format

def ai_to_unity_format(ai_json):
    """
    AI 응답 JSON을 유니티용 형식으로 변환 (memory_update와 reason 필드 제외)
    
    Args:
        ai_json: AI에서 반환한 JSON 문자열 또는 객체
    
    Returns:
        유니티용 형식의 JSON 문자열
    """
    # JSON 파싱 (문자열인 경우)
    if isinstance(ai_json, str):
        try:
            ai_data = json.loads(ai_json)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format from AI")
    else:
        ai_data = ai_json
    
    # 유니티용 데이터 구조 생성
    unity_format = {"actions": []}
    
    # 액션 정보 추출
    if "actions" in ai_data and isinstance(ai_data["actions"], list):
        for action in ai_data["actions"]:
            # 필수 필드 확인
            if not all(k in action for k in ["agent", "action", "details"]):
                continue
            
            # reason과 memory_update 필드 제외한 액션 복사
            unity_action = {
                "agent": action["agent"],
                "action": action["action"],
                "details": action["details"]
            }
            unity_format["actions"].append(unity_action)
    
    return json.dumps(unity_format, indent=2)

def save_memories_from_ai_response(ai_json, memory_db_path=None):
    """
    AI 응답에서 메모리 업데이트 정보를 추출하여 메모리 DB에 저장
    
    Args:
        ai_json: AI에서 반환한 JSON 문자열 또는 객체
        memory_db_path: 메모리 DB 파일 경로 (기본: ./memories/agents_memories.json)
    
    Returns:
        업데이트된 메모리 수
    """
    if memory_db_path is None:
        memory_db_path = Path("./memories/agents_memories.json")
    
    # 디렉토리 생성
    memory_db_path.parent.mkdir(exist_ok=True)
    
    # JSON 파싱 (문자열인 경우)
    if isinstance(ai_json, str):
        try:
            ai_data = json.loads(ai_json)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format from AI")
    else:
        ai_data = ai_json
    
    # 메모리 DB 로드
    if memory_db_path.exists():
        try:
            with open(memory_db_path, 'r', encoding='utf-8') as f:
                memory_db = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            memory_db = {}
    else:
        memory_db = {}
    
    # 메모리 업데이트 카운트
    update_count = 0
    
    # 액션에서 메모리 업데이트 정보 추출
    if "actions" in ai_data and isinstance(ai_data["actions"], list):
        for action in ai_data["actions"]:
            if "memory_update" in action and "agent" in action:
                agent_name = action["agent"]
                memory_update = action["memory_update"]
                
                # 메모리 항목 확인 및 보완
                if isinstance(memory_update, dict):
                    if "time" not in memory_update:
                        memory_update["time"] = datetime.now().strftime("%Y.%m.%d.%H:%M")
                    if "importance" not in memory_update:
                        memory_update["importance"] = 3
                else:
                    memory_update = {
                        "action": str(memory_update),
                        "time": datetime.now().strftime("%Y.%m.%d.%H:%M"),
                        "importance": 3
                    }
                
                # 에이전트 항목 생성
                if agent_name not in memory_db:
                    memory_db[agent_name] = []
                
                # 메모리 추가
                memory_db[agent_name].append(memory_update)
                update_count += 1
    
    # 메모리 DB 저장
    with open(memory_db_path, 'w', encoding='utf-8') as f:
        json.dump(memory_db, f, indent=2)
    
    return update_count

def get_memories_for_prompt(agent_name, memory_db_path=None, max_memories=5):
    """
    프롬프트에 포함할 에이전트 메모리 문자열 생성
    
    Args:
        agent_name: 에이전트 이름
        memory_db_path: 메모리 DB 파일 경로 (기본: ./memories/agents_memories.json)
        max_memories: 최대 반환 메모리 수
    
    Returns:
        프롬프트용 메모리 문자열
    """
    if memory_db_path is None:
        memory_db_path = Path("./memories/agents_memories.json")
    
    # 메모리 DB가 없으면 빈 문자열 반환
    if not memory_db_path.exists():
        return "No previous memories available."
    
    # 메모리 DB 로드
    try:
        with open(memory_db_path, 'r', encoding='utf-8') as f:
            memory_db = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return "No previous memories available."
    
    # 에이전트 메모리가 없으면 빈 문자열 반환
    if agent_name not in memory_db or not memory_db[agent_name]:
        return "No previous memories available."
    
    # 메모리 정렬 (최신순)
    sorted_memories = sorted(
        memory_db[agent_name],
        key=lambda x: datetime.strptime(x.get('time', "2000.01.01.00:00"), "%Y.%m.%d.%H:%M"),
        reverse=True
    )
    
    # 반환할 메모리 선택 (최신 및 중요 메모리 위주)
    # 1. 최신 메모리
    recent_memories = sorted_memories[:max_memories]
    
    # 2. 중요한 메모리 (중요도 기준 정렬)
    important_memories = sorted(
        sorted_memories,
        key=lambda x: x.get('importance', 0),
        reverse=True
    )[:max_memories]
    
    # 3. 중복 제거 및 통합
    selected_memories = []
    memory_ids = set()
    
    # 최신 메모리 추가
    for memory in recent_memories:
        memory_id = memory.get('time', '')
        if memory_id not in memory_ids:
            selected_memories.append(memory)
            memory_ids.add(memory_id)
    
    # 중요 메모리 추가 (중복 제외)
    for memory in important_memories:
        memory_id = memory.get('time', '')
        if memory_id not in memory_ids:
            selected_memories.append(memory)
            memory_ids.add(memory_id)
    
    # 최대 개수 제한
    selected_memories = selected_memories[:max_memories]
    
    # 메모리 문자열 생성
    memory_lines = []
    for memory in selected_memories:
        time_str = memory.get('time', '')
        action_str = memory.get('action', '')
        importance = memory.get('importance', 0)
        memory_lines.append(f"- {time_str}: {action_str} (importance: {importance})")
    
    if not memory_lines:
        return "No previous memories available."
    
    return "\n".join(memory_lines)

def process_unity_request(unity_json_str, current_time=None, environment_state=None):
    """
    유니티 요청 처리 통합 함수
    
    Args:
        unity_json_str: 유니티에서 전송한 JSON 문자열
        current_time: 현재 시간 (기본: 현재 시간 사용)
        environment_state: 환경 상태 (기본: 시간대에 따라 자동 생성)
    
    Returns:
        ai_format: AI 프롬프트용 형식 (딕셔너리)
    """
    # 유니티 JSON 파싱
    try:
        unity_data = json.loads(unity_json_str)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format from Unity")
    
    # 단일 에이전트 형식 처리
    if "agent" in unity_data and isinstance(unity_data["agent"], dict):
        unity_data["agents"] = [unity_data["agent"]]
    
    # AI 형식으로 변환
    ai_format = unity_to_ai_format(unity_data, current_time, environment_state)
    
    # 에이전트가 없으면 오류
    if "agents" not in ai_format or not ai_format["agents"]:
        raise ValueError("No agents found in Unity data")
    
    # 첫 번째 에이전트 이름 가져오기
    agent_name = ai_format["agents"][0]["name"]
    
    # 메모리 로드 및 추가
    memories = get_memories_for_prompt(agent_name)
    
    # 메모리가 있으면 프롬프트에 추가
    if memories and memories != "No previous memories available.":
        ai_format["memories"] = memories
    
    return ai_format

def process_ai_response(ai_json_str):
    """
    AI 응답 처리 통합 함수
    
    Args:
        ai_json_str: AI에서 반환한 JSON 문자열
    
    Returns:
        unity_json: 유니티용 JSON 문자열
        memory_count: 저장된 메모리 수
    """
    # 메모리 업데이트
    memory_count = save_memories_from_ai_response(ai_json_str)
    
    # 유니티용 JSON 생성
    unity_json = ai_to_unity_format(ai_json_str)
    
    return unity_json, memory_count

# 테스트 코드
if __name__ == "__main__":
    # 유니티 요청 예제
    unity_request = """
    {
        "agents": [
            {
                "name": "John",
                "state": {
                    "hunger": 8,
                    "sleepiness": 3,
                    "loneliness": 4,
                    "stress": 5,
                    "happiness": 4
                },
                "location": "town hall",
                "personality": "introverted, practical, punctual",
                "visible_objects": [
                    {
                        "location": "town hall",
                        "objects": ["book", "chair", "table", "clock", "newspaper"]
                    }
                ],
                "interactable_items": [
                    {
                        "location": "town hall",
                        "objects": ["book", "chair", "table", "newspaper"]
                    }
                ],
                "nearby_agents": ["Alice", "Tom"]
            }
        ]
    }
    """
    
    # 유니티 요청 처리
    try:
        ai_format = process_unity_request(
            unity_request,
            current_time="2025.04.23.12:30",
            environment_state="Sunny day, lunchtime"
        )
        print("유니티 요청을 AI 형식으로 변환:")
        print(json.dumps(ai_format, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"오류 발생: {e}")
    
    print("\n" + "-" * 40 + "\n")
    
    # AI 응답 예제
    ai_response = """
    {
        "actions": [
            {
                "agent": "John",
                "action": "move",
                "details": {
                    "location": "cafeteria",
                    "target": "cafeteria",
                    "using": null,
                    "message": "I need to find something to eat."
                },
                "memory_update": {
                    "action": "Decided to go to cafeteria because I was very hungry.",
                    "time": "2025.04.23.12:35",
                    "importance": 4
                },
                "reason": "John's hunger level is high (8) and it's lunchtime. Being practical, he decides to go to the cafeteria where food is available."
            }
        ]
    }
    """
    
    # AI 응답 처리
    try:
        unity_json, memory_count = process_ai_response(ai_response)
        print("AI 응답을 유니티 형식으로 변환:")
        print(unity_json)
        print(f"\n저장된 메모리 수: {memory_count}")
        
        # 저장된 메모리 확인
        print("\n저장된 메모리:")
        memories = get_memories_for_prompt("John")
        print(memories)
    except Exception as e:
        print(f"오류 발생: {e}")