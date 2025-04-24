import os
import json
import time
import requests
import re
import asyncio
from pathlib import Path
from datetime import datetime

# Ollama API settings
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3"
MAX_CONCURRENT_REQUESTS = 1  # 동시 요청 제한
DEFAULT_TIMEOUT = 60  # 기본 타임아웃 60초로 설정
FALLBACK_ENABLED = True  # 타임아웃 시 대체 응답 사용

def load_template(template_path):
    """템플릿 파일 로드"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_test_case(test_case_path):
    """테스트 케이스 파일 로드"""
    with open(test_case_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def state_to_phrases(state: dict) -> str:
    """에이전트 상태(state) 딕셔너리를 자연어 표현으로 변환"""
    state_map = {
        'hunger': 'hungry',
        'sleepiness': 'sleepy',
        'loneliness': 'lonely',
        'stress': 'stressed',
        'happiness': 'happy'
    }
    phrases = []
    for key, val in state.items():
        base = state_map.get(key, key)
        if val <= 3:
            prefix = 'not '
        elif val <= 6:
            prefix = ''
        else:
            prefix = 'very '
        phrases.append(f"{prefix}{base}")
    return ", ".join(phrases)


def format_template(template, data):
    """템플릿에 데이터 적용"""
    # 현재 시간 및 랜덤 시드 설정
    import random
    current_time = time.strftime("%Y.%m.%d.%H:%M")
    random_seed = random.randint(1, 10000)
    
    # 템플릿에 기본 정보 추가
    formatted = template.replace("{current_time}", current_time)
    formatted = formatted.replace("{current_timestamp}", current_time)
    formatted = formatted.replace("{random_seed}", str(random_seed))
    
    # data에 시간 정보가 없으면 추가
    if "current_time" not in data:
        data["current_time"] = current_time
    
    # data에 환경 정보가 없으면 시간대에 따라 기본값 설정
    if "environment_state" not in data:
        hour = int(current_time.split(".")[-1].split(":")[0])
        if 6 <= hour < 12:
            data["environment_state"] = "Morning, clear sky"
        elif 12 <= hour < 18:
            data["environment_state"] = "Afternoon, bright day"
        elif 18 <= hour < 22:
            data["environment_state"] = "Evening, getting dark"
        else:
            data["environment_state"] = "Night time, dark and quiet"
    
    # 단일 에이전트 처리 - "agent" 필드가 있으면 처리
    agent_data = None
    if "agent" in data and isinstance(data["agent"], dict):
        agent_data = data["agent"]
        # agents 배열로도 추가 (이전 호환성)
        data["agents"] = [agent_data]
    elif "agents" in data and data["agents"] and isinstance(data["agents"], list):
        agent_data = data["agents"][0]
    
    # 에이전트 데이터가 있으면 템플릿에 적용
    if agent_data:
        # 에이전트 기본 필드 매핑
        formatted = formatted.replace("{agent.name}", str(agent_data.get("name", "Unknown")))
        formatted = formatted.replace("{agent.location}", str(agent_data.get("location", "Unknown")))
        formatted = formatted.replace("{agent.personality}", str(agent_data.get("personality", "Unknown")))
        
        # 에이전트 상태 필드 매핑
        if "state" in agent_data and isinstance(agent_data["state"], dict):
            # 기존 코드 대신 유틸 함수 사용
            state_str = state_to_phrases(agent_data["state"])
            formatted = formatted.replace("{agent.state.phrases}", state_str)
        
        # 복잡한 필드 (리스트/딕셔너리) JSON으로 변환하여 매핑
        formatted = formatted.replace("{agent.visible_objects}", json.dumps(agent_data.get("visible_objects", [])))
        formatted = formatted.replace("{agent.interactable_items}", json.dumps(agent_data.get("interactable_items", [])))
        formatted = formatted.replace("{agent.nearby_agents}", json.dumps(agent_data.get("nearby_agents", [])))
        
        # 에이전트 이름으로 메모리 로드
        agent_name = agent_data.get("name", "")
        memory_str = get_agent_memories(agent_name)
        formatted = formatted.replace("{agent.memories}", memory_str or "No previous memories available.")
    
    # 기존 복잡한 표현식 처리는 유지 (agents[0].name 등)
    pattern = r'{([^{}]+)}'
    matches = re.findall(pattern, formatted)
    
    for match in matches:
        try:
            # agents[0].state.hunger와 같은 복잡한 표현식 평가
            if 'agents[' in match:
                parts = match.split('.')
                base_part = parts[0]
                index_match = re.search(r'agents\[(\d+)\]', base_part)
                
                if index_match:
                    index = int(index_match.group(1))
                    if "agents" in data and len(data["agents"]) > index:
                        agent = data["agents"][index]
                        
                        if len(parts) == 1:  # agents[0]
                            value = agent
                        elif len(parts) == 2:  # agents[0].name
                            attr = parts[1]
                            value = agent.get(attr, f"unknown_{attr}")
                        elif len(parts) == 3:  # agents[0].state.hunger
                            parent_attr = parts[1]
                            child_attr = parts[2]
                            if parent_attr in agent and isinstance(agent[parent_attr], dict):
                                value = agent[parent_attr].get(child_attr, f"unknown_{child_attr}")
                            else:
                                value = f"unknown_{parent_attr}_{child_attr}"
                        else:
                            value = f"unknown_deep_attribute"
                    else:
                        value = f"unknown_agent_{index}"
                else:
                    value = f"unknown_agent_index"
            else:
                # 일반 키 접근
                value = data.get(match, f"{{{match}}}")
            
            # 값을 문자열로 변환
            if isinstance(value, (list, dict)):
                value = json.dumps(value, ensure_ascii=False)
            
            # 템플릿에 적용
            formatted = formatted.replace(f"{{{match}}}", str(value))
        except Exception as e:
            print(f"템플릿 처리 중 오류: {e} (표현식: {match})")
            formatted = formatted.replace(f"{{{match}}}", f"{{오류: {match}}}")
    
    return formatted

def get_agent_memories(agent_name, max_memories=5):
    """에이전트 메모리 로드"""
    memory_path = Path("./memories/agents_memories.json")
    
    if not memory_path.exists():
        return ""
    
    try:
        with open(memory_path, 'r', encoding='utf-8') as f:
            memories = json.load(f)
    except:
        return ""
    
    if agent_name not in memories or not memories[agent_name]:
        return ""
    
    # 최신순 정렬
    sorted_memories = sorted(
        memories[agent_name],
        key=lambda x: datetime.strptime(x.get('time', "2000.01.01.00:00"), "%Y.%m.%d.%H:%M"),
        reverse=True
    )
    
    # 최대 개수 제한
    limited_memories = sorted_memories[:max_memories]
    
    # 메모리 문자열 생성
    memory_text = []
    for memory in limited_memories:
        time = memory.get('time', '')
        action = memory.get('action', '')
        importance = memory.get('importance', 0)
        # memory_text.append(f"- {time}: {action} (importance: {importance})")
        memory_text.append(f"-{action}")
    
    return "\n".join(memory_text)

def update_memories(ai_response):
    """AI 응답에서 메모리 업데이트"""
    try:
        # JSON 파싱
        if isinstance(ai_response, str):
            response_data = json.loads(ai_response)
        else:
            response_data = ai_response
        
        # 메모리 DB 로드
        memory_path = Path("./memories/agents_memories.json")
        Path("./memories").mkdir(exist_ok=True)
        
        if memory_path.exists():
            try:
                with open(memory_path, 'r', encoding='utf-8') as f:
                    memories = json.load(f)
            except:
                memories = {}
        else:
            memories = {}
        
        # 액션별 메모리 업데이트
        update_count = 0
        
        if "actions" in response_data and isinstance(response_data["actions"], list):
            for action in response_data["actions"]:
                if "memory_update" in action and "agent" in action:
                    agent_name = action["agent"]
                    memory_update = action["memory_update"]
                    
                    # 메모리 형식 검증 및 변환
                    if isinstance(memory_update, dict):
                        if "time" not in memory_update:
                            memory_update["time"] = time.strftime("%Y.%m.%d.%H:%M")
                        if "importance" not in memory_update:
                            memory_update["importance"] = 3
                    else:
                        memory_update = {
                            "action": str(memory_update),
                            "time": time.strftime("%Y.%m.%d.%H:%M"),
                            "importance": 3
                        }
                    
                    # 에이전트 메모리 생성 또는 업데이트
                    if agent_name not in memories:
                        memories[agent_name] = []
                    
                    # 메모리 추가
                    memories[agent_name].append(memory_update)
                    update_count += 1
        
        # 메모리 DB 저장
        with open(memory_path, 'w', encoding='utf-8') as f:
            json.dump(memories, f, indent=2)
        
        return update_count
    except Exception as e:
        print(f"메모리 업데이트 중 오류: {e}")
        return 0

def create_unity_json(ai_response):
    """AI 응답에서 Unity용 JSON 생성 (memory_update와 reason 필드 제외)"""
    try:
        # JSON 파싱
        if isinstance(ai_response, str):
            response_data = json.loads(ai_response)
        else:
            response_data = ai_response
        
        # Unity용 JSON 생성
        unity_json = {"actions": []}
        
        if "actions" in response_data and isinstance(response_data["actions"], list):
            for action in response_data["actions"]:
                # 필수 필드 확인
                if not all(k in action for k in ["agent", "action", "details"]):
                    continue
                
                # memory_update와 reason 필드 제외한 액션 복사
                unity_action = {
                    "agent": action["agent"],
                    "action": action["action"],
                    "details": action["details"].copy() if "details" in action else {}
                }
                
                unity_json["actions"].append(unity_action)
        
        return unity_json
    except Exception as e:
        print(f"Unity JSON 생성 중 오류: {e}")
        return {"actions": []}

def call_model(prompt, agent_names, timeout=DEFAULT_TIMEOUT):
    """LLM 호출 (타임아웃 설정 포함)"""
    print(f"타임아웃 설정: {timeout}초")
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,  # 다양성을 위해 온도 증가
            "top_p": 0.9,
            "frequency_penalty": 0.5,  # 반복되는 패턴 감소
            "presence_penalty": 0.5,  # 새로운 요소 증가
            "num_predict": 1024
        }
    }
    
    try:
        start_time = time.time()
        
        # 타임아웃 설정으로 요청
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            response_data = {
                "response": result.get("response", ""),
                "elapsed_time": elapsed_time,
                "status": "success"
            }
            
            return response_data
        else:
            print(f"오류 응답: 상태 코드 {response.status_code}")
            return {
                "response": f"Error: {response.status_code}",
                "elapsed_time": elapsed_time,
                "status": "error"
            }
    except requests.exceptions.Timeout:
        print(f"요청 타임아웃 발생 ({timeout}초 초과)")
        if FALLBACK_ENABLED:
            fallback = create_fallback_response(agent_names)
            print(f"대체 응답 생성: {len(agent_names)}개 에이전트에 대한 기본 행동")
            return fallback
        else:
            return {
                "response": "Error: Request timed out",
                "elapsed_time": timeout,
                "status": "timeout"
            }
    except Exception as e:
        print(f"예외 발생: {str(e)}")
        return {
            "response": f"Exception: {str(e)}",
            "elapsed_time": 0,
            "status": "error"
        }

def create_fallback_response(agent_names):
    """타임아웃 시 사용할 기본 대체 응답 생성"""
    actions = []
    
    for agent_name in agent_names:
        # 각 에이전트에 대한 기본 대체 행동
        action = {
            "agent": agent_name,
            "action": "wait",
            "details": {
                "location": "current_location",
                "target": "none",
                "using": None,
                "message": "I need to think about what to do next."
            },
            "reason": "Fallback reasoning: Agent needed more time to decide on a complex action."
        }
        
        # 메모리 업데이트 필드 추가
        action["memory_update"] = {
            "action": "Paused to consider my next action carefully.",
            "time": time.strftime("%Y.%m.%d.%H:%M"),
            "importance": 2
        }
        
        actions.append(action)
    
    return {
        "response": json.dumps({"actions": actions}, indent=2),
        "elapsed_time": DEFAULT_TIMEOUT,
        "status": "timeout_fallback"
    }

def extract_json(text):
    """텍스트에서 JSON 형식 추출 및 유효성 검사"""
    try:
        # JSON 형식 추출 (중괄호로 둘러싸인 부분 찾기)
        json_pattern = r'({[\s\S]*})'
        match = re.search(json_pattern, text)
        
        if not match:
            print("JSON 형식을 찾을 수 없음")
            return False, None, None
            
        json_str = match.group(1)
        original_json = json_str  # 원본 저장
        
        # 1. 작은따옴표를 큰따옴표로 변환 (JSON 표준)
        json_str = json_str.replace("'", '"')
        
        # 2. 따옴표 없는 속성 이름 수정 시도
        json_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
        
        # 3. null, true, false 값 처리
        json_str = re.sub(r':\s*null([,}])', r': null\1', json_str)
        json_str = re.sub(r':\s*true([,}])', r': true\1', json_str)
        json_str = re.sub(r':\s*false([,}])', r': false\1', json_str)
        
        # 4. 누락된 콤마 수정 시도 - 일반적인 패턴
        # "action": "wait" } 형태를 "action": "wait", } 로 수정
        json_str = re.sub(r'(["}])\s*}', r'\1,}', json_str)
        json_str = re.sub(r',\s*}', r'}', json_str)  # 마지막 속성 이후에 콤마 제거
        
        # JSON 파싱 시도
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"첫 번째 파싱 시도 실패: {e}")
            
            # 추가 교정 시도 - 콤마 오류 수정
            line_info = str(e)
            if "Expecting ',' delimiter" in line_info:
                # 오류 위치 추출
                pos_match = re.search(r'char (\d+)', line_info)
                if pos_match:
                    pos = int(pos_match.group(1))
                    # 오류 위치 앞에 콤마 추가
                    json_str = json_str[:pos] + ',' + json_str[pos:]
                    try:
                        parsed = json.loads(json_str)
                    except json.JSONDecodeError as e2:
                        print(f"두 번째 파싱 시도 실패: {e2}")
                        # 마지막 시도 - 전체 구조 재구성
                        return fix_json_with_regex(original_json)
            else:
                # 다른 유형의 오류 - 정규식으로 고급 수정 시도
                return fix_json_with_regex(original_json)
        
        # 기본 유효성 검사
        if "actions" not in parsed or not isinstance(parsed["actions"], list):
            print("필수 'actions' 배열이 없거나 배열이 아님")
            return False, None, None
            
        if len(parsed["actions"]) == 0:
            print("'actions' 배열이 비어 있음")
            return False, None, None
        
        for action in parsed["actions"]:
            if not all(k in action for k in ["agent", "action", "details"]):
                print(f"필수 필드 누락된 액션 발견: {action}")
                return False, None, None
            
            # reason 필드 검사 추가
            if "reason" not in action:
                print(f"'reason' 필드가 누락됨: {action}")
                # reason 필드 추가 (자동 수정)
                action["reason"] = "Auto-generated reason: Action based on current state and memories."
            
            # memory_update 필드 검사 추가
            if "memory_update" not in action:
                print(f"'memory_update' 필드가 누락됨: {action}")
                # memory_update 필드 추가 (자동 수정)
                action["memory_update"] = {
                    "action": f"{action.get('action', 'unknown action')} at {action.get('details', {}).get('location', 'unknown location')}",
                    "time": time.strftime("%Y.%m.%d.%H:%M"),
                    "importance": 3
                }
            
            # details 필드에 location이 없는 경우 추가
            if "details" in action and "location" not in action["details"]:
                print(f"'location' 필드가 누락됨: {action['details']}")
                action["details"]["location"] = "current_location"
        
        # Unity용 JSON 생성 (memory_update와 reason 필드 제외)
        unity_json = create_unity_json(parsed)
        
        # 검증 통과 - JSON 정상
        return True, parsed, unity_json
    
    except Exception as e:
        print(f"JSON 검증 중 예외 발생: {e}")
        return False, None, None

def fix_json_with_regex(text):
    """정규식을 사용한 고급 JSON 수정 시도"""
    try:
        # 기본 구조 확인
        if not re.search(r'{\s*"actions"\s*:\s*\[', text):
            # actions 배열을 찾을 수 없으면 기본 구조 생성
            actions_match = re.findall(r'"agent"\s*:\s*"([^"]+)"', text)
            if actions_match:
                actions = []
                for agent in actions_match:
                    action_type = "wait"  # 기본값
                    action_match = re.search(r'"action"\s*:\s*"([^"]+)"', text)
                    if action_match:
                        action_type = action_match.group(1)
                    
                    action = {
                        "agent": agent,
                        "action": action_type,
                        "details": {
                            "location": "current_location",
                            "target": "none",
                            "using": None,
                            "message": "Auto-fixed action."
                        },
                        "memory_update": {
                            "action": f"Auto-fixed {action_type} action.",
                            "time": time.strftime("%Y.%m.%d.%H:%M"),
                            "importance": 3
                        },
                        "reason": "Auto-fixed reason: Based on agent's current state."
                    }
                    actions.append(action)
                
                json_obj = {"actions": actions}
                unity_json = create_unity_json(json_obj)
                return True, json_obj, unity_json
            return False, None, None
        
        # actions 배열 추출
        actions_pattern = r'"actions"\s*:\s*\[([\s\S]*?)\]'
        actions_match = re.search(actions_pattern, text)
        if not actions_match:
            return False, None, None

        actions_text = actions_match.group(1)
        
        # 개별 액션 항목 파싱
        action_items = []
        open_braces = 0
        current_item = ""
        
        for char in actions_text:
            current_item += char
            if char == '{':
                open_braces += 1
            elif char == '}':
                open_braces -= 1
                if open_braces == 0:
                    action_items.append(current_item)
                    current_item = ""
        
        # 각 액션 항목 수정
        fixed_actions = []
        for item in action_items:
            if not item.strip():
                continue
                
            # 필드 추출
            agent = re.search(r'"agent"\s*:\s*"([^"]*)"', item)
            action = re.search(r'"action"\s*:\s*"([^"]*)"', item)
            location = re.search(r'"location"\s*:\s*"([^"]*)"', item)
            target = re.search(r'"target"\s*:\s*"([^"]*)"', item)
            using = re.search(r'"using"\s*:\s*(?:"([^"]*)"|(null))', item)
            message = re.search(r'"message"\s*:\s*"([^"]*)"', item)
            memory = re.search(r'"memory_update"\s*:\s*"([^"]*)"', item)
            reason = re.search(r'"reason"\s*:\s*"([^"]*)"', item)
            
            fixed_action = {
                "agent": agent.group(1) if agent else "unknown",
                "action": action.group(1) if action else "wait",
                "details": {
                    "location": location.group(1) if location else "current_location",
                    "target": target.group(1) if target else "none",
                    "using": None if (using and using.group(2) == "null") else (using.group(1) if using else None),
                    "message": message.group(1) if message else "Auto-fixed action."
                },
                "memory_update": {
                    "action": memory.group(1) if memory else f"Auto-fixed action at {location.group(1) if location else 'current_location'}",
                    "time": time.strftime("%Y.%m.%d.%H:%M"),
                    "importance": 3
                },
                "reason": reason.group(1) if reason else "Auto-fixed reason: Based on agent's current state and memories."
            }
            
            fixed_actions.append(fixed_action)
        
        if not fixed_actions:
            return False, None, None
            
        # 최종 JSON 객체 생성
        json_obj = {"actions": fixed_actions}
        unity_json = create_unity_json(json_obj)
        return True, json_obj, unity_json
        
    except Exception as e:
        print(f"고급 JSON 수정 중 오류: {e}")
        return False, None, None

async def process_test_case(template_name, template, case_name, test_case):
    """단일 테스트 케이스 처리 (비동기)"""
    print(f"테스트 실행: {template_name} + {case_name}")
    
    try:
        # 프롬프트 생성
        prompt = format_template(template, test_case)
        
        # 프롬프트 저장 (디버깅용)
        Path("results").mkdir(exist_ok=True) # 디렉토리 확인
        with open(Path("results") / f"{template_name}_{case_name}_prompt.txt", 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        # 프롬프트 길이 계산
        token_estimate = len(prompt.split())  # 단순 추정
        print(f"프롬프트 토큰 수 (추정): {token_estimate}")
        
        # 처리할 에이전트 이름 목록
        agent_names = test_case.get("agents_to_process", [])
        if not agent_names and "agents" in test_case and test_case["agents"]:
            agent_names = [agent.get("name") for agent in test_case["agents"] if "name" in agent]
        
        # 모델 호출
        model_response = call_model(prompt, agent_names, timeout=DEFAULT_TIMEOUT)
        
        # 원본 응답 저장
        original_response = model_response["response"]
        
        # JSON 응답 검증
        is_json, extracted_json, unity_json = extract_json(model_response["response"])
        
        # 메모리 업데이트 (JSON이 유효한 경우)
        memory_updates = 0
        if is_json and extracted_json:
            memory_updates = update_memories(extracted_json)
        
        # 에이전트 수 검증
        expected_agent_count = len(agent_names)
        actual_agent_count = 0
        
        if is_json and extracted_json:
            if "actions" in extracted_json and isinstance(extracted_json["actions"], list):
                # 고유 에이전트 이름 추출
                agents_in_response = set()
                for action in extracted_json["actions"]:
                    if "agent" in action and action["agent"] not in ["unknown", "unknown_agent"]:
                        agents_in_response.add(action["agent"])
                
                actual_agent_count = len(agents_in_response)
                
                # 에이전트 수 검증
                if actual_agent_count != expected_agent_count:
                    print(f"경고: 예상 에이전트 수({expected_agent_count})와 실제 에이전트 수({actual_agent_count}) 불일치")
                    
                    # 비어있는 에이전트 확인
                    missing_agents = set(agent_names) - agents_in_response
                    if missing_agents:
                        print(f"누락된 에이전트: {', '.join(missing_agents)}")
        
        # 결과 저장
        test_result = {
            "template": template_name,
            "test_case": case_name,
            "prompt_tokens": token_estimate,
            "response_time": model_response["elapsed_time"],
            "is_valid_json": is_json,
            "response": original_response,  # 원본 응답 보존
            "status": model_response.get("status", "unknown"),
            "extracted_json": extracted_json if is_json else None,
            "unity_json": unity_json if is_json else None,  # Unity용 JSON 추가
            "memory_updates": memory_updates,  # 메모리 업데이트 수
            "fixed": is_json and json.dumps(extracted_json) != original_response,  # JSON 수정 여부 표시
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),  # 타임스탬프 추가
            "expected_agents": expected_agent_count,
            "actual_agents": actual_agent_count
        }
        
        # 결과 저장
        with open(Path("results") / f"{template_name}_{case_name}_result.json", 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2)
        
        print(f"테스트 완료: {template_name}_{case_name} - 유효한 JSON: {is_json}, 시간: {model_response['elapsed_time']:.2f}초")
        if memory_updates > 0:
            print(f"메모리 업데이트: {memory_updates}개")
        print()
        
        return test_result
    
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def optimize_prompt_tokens(prompt):
    """프롬프트 토큰 수 최적화"""
    # 간단한 최적화만 구현
    # 불필요한 공백 제거
    prompt = re.sub(r'\n\s*\n', '\n\n', prompt)
    
    # 긴 설명 줄이기 (예시)
    prompt = prompt.replace("You are the AI manager for the", "AI manager for")
    
    return prompt

def batch_tests(templates, test_cases, batch_size=2):
    """테스트를 배치로 그룹화"""
    batches = []
    current_batch = []
    
    for template_name, template in templates.items():
        for case_name, test_case in test_cases.items():
            current_batch.append((template_name, template, case_name, test_case))
            
            if len(current_batch) >= batch_size:
                batches.append(current_batch)
                current_batch = []
    
    if current_batch:  # 남은 항목이 있으면 추가
        batches.append(current_batch)
    
    return batches

async def run_test_suite():
    """비동기 테스트 실행"""
    results = []
    
    # Check and create directories
    Path("prompts").mkdir(exist_ok=True)
    Path("test_cases").mkdir(exist_ok=True)
    Path("results").mkdir(exist_ok=True)
    Path("memories").mkdir(exist_ok=True)
    
    # 디버깅 정보 출력
    print("템플릿 파일 찾기...")
    template_files = list(Path("prompts").glob("*.txt"))
    print(f"찾은 템플릿 파일: {[f.name for f in template_files]}")
    
    print("테스트 케이스 파일 찾기...")
    test_case_files = list(Path("test_cases").glob("*.json"))
    print(f"찾은 테스트 케이스 파일: {[f.name for f in test_case_files]}")
    
    if not template_files:
        print("경고: prompts 디렉토리에 템플릿 파일(.txt)이 없습니다.")
        return []
    
    if not test_case_files:
        print("경고: test_cases 디렉토리에 테스트 케이스 파일(.json)이 없습니다.")
        return []
    
    # Load templates
    templates = {}
    for template_file in template_files:
        templates[template_file.stem] = load_template(template_file)
    
    # Load test cases
    test_cases = {}
    for test_file in test_case_files:
        test_cases[test_file.stem] = load_test_case(test_file)
    
    # 배치로 그룹화
    test_batches = batch_tests(templates, test_cases, batch_size=MAX_CONCURRENT_REQUESTS)
    
    # 각 배치 순차 처리, 배치 내에선 병렬 처리
    for batch in test_batches:
        tasks = []
        for template_name, template, case_name, test_case in batch:
            task = process_test_case(template_name, template, case_name, test_case)
            tasks.append(task)
        
        # 현재 배치의 모든 테스트 병렬 실행
        batch_results = await asyncio.gather(*tasks)
        results.extend([r for r in batch_results if r is not None])
        
        # 배치 간 짧은 대기 추가 (Ollama 부하 방지)
        await asyncio.sleep(1)
    
    return results

def check_files():
    """필요한 파일과 디렉토리가 모두 있는지 확인"""
    print("\n===== 파일 구조 확인 =====")
    
    # 필요한 디렉토리 확인
    dirs_to_check = ["prompts", "test_cases", "memories", "results"]
    all_dirs_exist = True
    
    for dir_name in dirs_to_check:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            print(f"✓ 디렉토리 '{dir_name}' 존재함")
            
            # 파일 목록 확인
            files = list(dir_path.glob("*"))
            if files:
                print(f"  파일 목록: {', '.join(f.name for f in files)}")
            else:
                print(f"  ⚠ 디렉토리에 파일 없음")
                if dir_name in ["prompts", "test_cases"]:
                    all_dirs_exist = False
        else:
            print(f"✗ 디렉토리 '{dir_name}' 없음")
            all_dirs_exist = False
            
            # 디렉토리 생성
            dir_path.mkdir(exist_ok=True)
            print(f"  → 디렉토리 '{dir_name}' 생성됨")
    
    return all_dirs_exist

def print_test_summary(results):
    """테스트 결과 요약 출력"""
    if not results:
        print("테스트 결과가 없습니다.")
        return
    
    # 기본 통계
    total_tests = len(results)
    valid_json_count = sum(1 for r in results if r["is_valid_json"])
    fixed_json_count = sum(1 for r in results if r.get("fixed", False))
    memory_updates = sum(r.get("memory_updates", 0) for r in results)
    
    # 응답 시간 통계
    response_times = [r["response_time"] for r in results]
    avg_time = sum(response_times) / len(response_times)
    min_time = min(response_times)
    max_time = max(response_times)
    
    # 에이전트 수 일치
    agent_match_count = sum(1 for r in results if r.get("expected_agents") == r.get("actual_agents", 0))
    
    # 요약 출력
    print("\n===== 테스트 결과 요약 =====")
    print(f"총 테스트: {total_tests}")
    print(f"유효한 JSON: {valid_json_count}/{total_tests} ({valid_json_count/total_tests*100:.1f}%)")
    print(f"자동 수정된 JSON: {fixed_json_count}/{valid_json_count} ({fixed_json_count/valid_json_count*100:.1f}% 유효 응답 중)")
    print(f"메모리 업데이트: 총 {memory_updates}개")
    print(f"에이전트 수 일치: {agent_match_count}/{total_tests} ({agent_match_count/total_tests*100:.1f}%)")
    print(f"응답 시간: 평균 {avg_time:.2f}초 (최소 {min_time:.2f}초, 최대 {max_time:.2f}초)")
    
    # 템플릿별 통계
    print("\n== 템플릿별 통계 ==")
    template_stats = {}
    for result in results:
        template = result["template"]
        if template not in template_stats:
            template_stats[template] = {"count": 0, "valid": 0, "time": []}
        
        template_stats[template]["count"] += 1
        template_stats[template]["valid"] += 1 if result["is_valid_json"] else 0
        template_stats[template]["time"].append(result["response_time"])
    
    for template, stats in template_stats.items():
        avg_template_time = sum(stats["time"]) / len(stats["time"])
        valid_percent = stats["valid"] / stats["count"] * 100
        print(f"{template}: {stats['valid']}/{stats['count']} 성공 ({valid_percent:.1f}%), 평균 {avg_template_time:.2f}초")
    
    # 케이스별 통계
    print("\n== 케이스별 통계 ==")
    case_stats = {}
    for result in results:
        case = result["test_case"]
        if case not in case_stats:
            case_stats[case] = {"count": 0, "valid": 0, "time": []}
        
        case_stats[case]["count"] += 1
        case_stats[case]["valid"] += 1 if result["is_valid_json"] else 0
        case_stats[case]["time"].append(result["response_time"])
    
    for case, stats in case_stats.items():
        avg_case_time = sum(stats["time"]) / len(stats["time"])
        valid_percent = stats["valid"] / stats["count"] * 100
        print(f"{case}: {stats['valid']}/{stats['count']} 성공 ({valid_percent:.1f}%), 평균 {avg_case_time:.2f}초")

if __name__ == "__main__":
    print("프롬프트 테스트 스위트 시작...")
    
    # 파일 구조 확인
    files_ok = check_files()
    if not files_ok:
        print("\n필요한 파일이나 디렉토리가 없습니다.")
        import sys
        sys.exit(1)
    
    # 비동기 이벤트 루프 실행
    import asyncio
    results = asyncio.run(run_test_suite())
    
    # 결과 요약 출력
    print_test_summary(results)
    
    print("\n상세 결과는 'results' 디렉토리에 저장되었습니다.")