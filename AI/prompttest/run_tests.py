import os
import json
import time
import requests
import re
import asyncio
import json
from pathlib import Path


### 메모리 우선도 정렬 코드
from datetime import datetime

def sort_by_time_desc(data):
    return sorted(data, key=lambda x: datetime.strptime(x['time'], "%Y.%m.%d.%H:%M"), reverse=True)

def sort_by_importance(data):
    return sorted(data, key=lambda x: x['importance'], reverse=True)

def compute_weighted_importance(data):
    # 최신순으로 0.02씩 페널티
    sorted_by_time = sort_by_time_desc(data)
    weighted_data = []
    for i, item in enumerate(sorted_by_time):
        weight = max(1.0 - i * 0.02, 0)
        score = round(weight * item['importance'], 4)
        weighted_data.append({ **item, 'score': score })
    # 최종 스코어 기준 내림차순
    return sorted(weighted_data, key=lambda x: x['score'], reverse=True)



# Ollama API settings
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3"
MAX_CONCURRENT_REQUESTS = 1  # 동시 요청 제한

# 캐싱 관련 설정
ENABLE_CACHING = False

# 타임아웃 및 성능 설정
DEFAULT_TIMEOUT = 60  # 기본 타임아웃 60초로 설정
FALLBACK_ENABLED = True  # 타임아웃 시 대체 응답 사용


def get_cache_key(template_name, test_case_name, prompt):
    """캐시 키 생성"""
    # 프롬프트 해싱 (간단한 해시)
    import hashlib
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    return f"{template_name}_{test_case_name}_{prompt_hash[:8]}"

def load_template(template_path):
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_test_case(test_case_path):
    with open(test_case_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_prompt(template, test_case):
    """Apply test case data to the template."""
    # 랜덤 요소 추가
    import random
    import time
    current_time = time.strftime("%H:%M:%S")
    random_seed = random.randint(1, 10000)
    
    # 템플릿에 랜덤 요소 추가
    modified_template = template.replace("{current_timestamp}", current_time)
    modified_template = modified_template.replace("{random_seed}", str(random_seed))
    
    # memory db에서 값 가져오기
    mem_path = Path("./memories/agents_memories.json")
    if mem_path.exists():
        with open(mem_path, 'r', encoding='utf-8') as mf:
            memory_db = json.load(mf)
    else:
        memory_db = {}


    # 동적 에이전트 데이터 섹션 생성
    if 'agents_to_process' in test_case and 'agents' in test_case:
        # 동적 에이전트 데이터 부분 찾기
        agent_data_pattern = r'AGENT DATA:[\s\S]*?(?=TASK:|$)'
        agent_data_match = re.search(agent_data_pattern, modified_template)
        
        if agent_data_match:
            original_agent_data_section = agent_data_match.group(0)
            
            # 새로운 동적 에이전트 데이터 섹션 생성
            new_agent_data = "AGENT DATA:\n"
            for agent_name in test_case['agents_to_process']:
                # 해당 에이전트 찾기
                agent_data = next((a for a in test_case['agents'] if a['name'] == agent_name), None)
                if not agent_data:
                    continue

                # 1. state → 자연어로 변환
                state_map = {
                    'hunger': 'hungry',
                    'sleepiness': 'sleepy',
                    'loneliness': 'lonely',
                    'stress': 'stressed',
                    'happiness': 'happy'
                }
                state_phrases = []
                for key, val in agent_data.get('state', {}).items():
                    base = state_map.get(key, key)
                    if val <= 3:
                        prefix = 'not '
                    elif val <= 6:
                        prefix = ''
                    else:
                        prefix = 'very '
                    state_phrases.append(f"{prefix}{base}")
                state_str = ", ".join(state_phrases)

                # 2. visible_objects → “{location}에 있는 {object}” 형식으로
                vis = agent_data.get('visible_objects', [])
                vis_phrases = []
                if isinstance(vis, list):
                    for group in vis:
                        location = group.get('location')
                        for obj in group.get('objects', []):
                            vis_phrases.append(f"{obj} located in {location}")
                else:
                    # fallback: comma-separated string
                    for obj in str(vis).split(','):
                        vis_phrases.append(f"{obj.strip()} located in {agent_data.get('location')}")
                visible_str = ", ".join(vis_phrases)

                # 3. interactable_items → same approach
                it = agent_data.get('interactable_items', [])
                it_phrases = []
                if isinstance(it, list):
                    for group in it:
                        location = group.get('location')
                        for obj in group.get('objects', []):
                            it_phrases.append(f"{obj} located in {location}")
                else:
                    for obj in str(it).split(','):
                        it_phrases.append(f"{obj.strip()} located in {agent_data.get('location')}")
                interact_str = ", ".join(it_phrases)


                # 에이전트 데이터 추가
                new_agent_data += (
                    f"{agent_name}: state: {state_str}, "
                    f"at {agent_data.get('location', 'unknown')}\n"
                    f"Visible: {visible_str}\n"
                    f"Can interact with: {interact_str}\n"
                )
                
                # 메모리 정보 추가 (complex_prompt용)
                mem_list = memory_db.get(agent_name, [])
                if mem_list and isinstance(mem_list[0], list):
                    mem_list = mem_list[0]
                if mem_list:
                    sorted_mem = compute_weighted_importance(mem_list)
                    new_agent_data += "Memories:\n"
                    for m_item in sorted_mem:
                        new_agent_data += f"- {m_item['action']}\n"
                        # new_agent_data += f"- At {m_item['time']}, {m_item['action']} (importance {m_item['importance']})\n"
                    new_agent_data += "\n"

            # 원본 에이전트 데이터 섹션을 새 섹션으로 교체
            modified_template = modified_template.replace(original_agent_data_section, new_agent_data)

    
    # Process complex expressions (agents[0].name, etc.) - 기존 처리 방식 유지
    agent_pattern = r'{agents\[(\d+)\]\.(\w+)}'
    matches = re.findall(agent_pattern, modified_template)
    
    for match in matches:
        index, attribute = match
        index = int(index)
        
        # Original pattern
        original = f"{{agents[{index}].{attribute}}}"
        
        # Get corresponding value from test case
        if 'agents' in test_case and len(test_case['agents']) > index:
            if attribute in test_case['agents'][index]:
                value = test_case['agents'][index][attribute]
                # Replace pattern with actual value in template
                modified_template = modified_template.replace(original, str(value))
            else:
                modified_template = modified_template.replace(original, f"unknown_{attribute}")
        else:
            modified_template = modified_template.replace(original, f"unknown_agent_{index}")
    
    # 중첩된 속성 처리 (agents[0].state.hunger 등)
    nested_pattern = r'{agents\[(\d+)\]\.(\w+)\.(\w+)}'
    nested_matches = re.findall(nested_pattern, modified_template)
    
    for match in nested_matches:
        index, parent_attr, child_attr = match
        index = int(index)
        
        # Original pattern
        original = f"{{agents[{index}].{parent_attr}.{child_attr}}}"
        
        # Get corresponding value from test case
        if 'agents' in test_case and len(test_case['agents']) > index:
            if parent_attr in test_case['agents'][index]:
                parent_obj = test_case['agents'][index][parent_attr]
                if isinstance(parent_obj, dict) and child_attr in parent_obj:
                    value = parent_obj[child_attr]
                    modified_template = modified_template.replace(original, str(value))
                else:
                    modified_template = modified_template.replace(original, f"unknown_{child_attr}")
            else:
                modified_template = modified_template.replace(original, f"unknown_{parent_attr}")
        else:
            modified_template = modified_template.replace(original, f"unknown_agent_{index}")
    
    modified_template = optimize_prompt_tokens(modified_template)
    
    # 에이전트 수 강조 (모든 에이전트에 대한 응답 생성 유도)
    num_agents = len(test_case.get('agents_to_process', []))
    agent_names = ', '.join(test_case.get('agents_to_process', []))
    
    # IMPORTANT 섹션 찾기 및 업데이트
    important_pattern = r'IMPORTANT:.*?(?=\n\n|\Z)'
    important_match = re.search(important_pattern, modified_template, re.DOTALL)
    
    if important_match:
        important_text = important_match.group(0)
        new_important = f"{important_text}\nMUST generate EXACTLY {num_agents} actions for EACH of these agents: {agent_names}."
        modified_template = modified_template.replace(important_text, new_important)
    
    # 기본 형식 적용
    try:
        return modified_template.format(**test_case)
    except KeyError as e:
        print(f"Warning: Missing key in test case: {e}")
        missing_key = str(e.args[0])
        return modified_template.replace(f"{{{missing_key}}}", f"unknown_{missing_key}")

def load_cache():
    """캐시 파일 로드 (캐싱이 비활성화됨)"""
    pass

def save_cache():
    """캐시 파일 저장 (캐싱이 비활성화됨)"""
    pass

def optimize_agent_context(template, test_case):
    """에이전트 관련 컨텍스트 최적화"""
    # 실제 처리할 에이전트만 상세 정보 유지
    if 'agents_to_process' not in test_case or 'agents' not in test_case:
        return template
    
    return template

def create_fallback_response(agent_names):
    """타임아웃 시 사용할 기본 대체 응답 생성"""
    actions = []
    
    for agent_name in agent_names:
        # 각 에이전트에 대한 기본 대체 행동
        action = {
            "agent": agent_name,
            "action": "wait",
            "details": {
                "target": "current_location",
                "using": None,
                "message": "I need to think about what to do next."
            }
        }
        
        # complex_prompt인 경우 memory_update 필드 추가
        if len(agent_names) > 1:  # 간단한 휴리스틱: 에이전트가 여러 개면 complex_prompt 가정
            action["memory_update"] = "Paused to consider my next action carefully."
        
        actions.append(action)
    
    return {
        "response": json.dumps({"actions": actions}, indent=2),
        "elapsed_time": DEFAULT_TIMEOUT,
        "status": "timeout_fallback"
    }

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


def is_valid_json(text):
    """텍스트에서 JSON 형식 추출 및 유효성 검사 (개선된 버전)"""
    try:
        # JSON 형식 추출 (중괄호로 둘러싸인 부분 찾기)
        json_pattern = r'({[\s\S]*})'
        match = re.search(json_pattern, text)
        
        if not match:
            print("JSON 형식을 찾을 수 없음")
            return False, None
            
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
            return False, None
            
        if len(parsed["actions"]) == 0:
            print("'actions' 배열이 비어 있음")
            return False, None
        
        for action in parsed["actions"]:
            if not all(k in action for k in ["agent", "action", "details"]):
                print(f"필수 필드 누락된 액션 발견: {action}")
                return False, None
        
        # 검증 통과 - JSON 정상
        return True, json_str
    
    except Exception as e:
        print(f"JSON 검증 중 예외 발생: {e}")
        return False, None

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
                            "target": "current_location",
                            "using": None,
                            "message": "Auto-fixed action."
                        }
                    }
                    actions.append(action)
                
                json_obj = {"actions": actions}
                return True, json.dumps(json_obj)
            return False, None
        
        # actions 배열 추출
        actions_pattern = r'"actions"\s*:\s*\[([\s\S]*?)\]'
        actions_match = re.search(actions_pattern, text)
        if not actions_match:
            return False, None
        
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
            target = re.search(r'"target"\s*:\s*"([^"]*)"', item)
            using = re.search(r'"using"\s*:\s*(?:"([^"]*)"|(null))', item)
            message = re.search(r'"message"\s*:\s*"([^"]*)"', item)
            memory = re.search(r'"memory_update"\s*:\s*"([^"]*)"', item)
            
            fixed_action = {
                "agent": agent.group(1) if agent else "unknown",
                "action": action.group(1) if action else "wait",
                "details": {
                    "target": target.group(1) if target else "current_location",
                    "using": None if (using and using.group(2) == "null") else (using.group(1) if using else None),
                    "message": message.group(1) if message else "Auto-fixed action."
                }
            }
            
            if memory:
                fixed_action["memory_update"] = memory.group(1)
                
            fixed_actions.append(fixed_action)
        
        if not fixed_actions:
            return False, None
            
        # 최종 JSON 객체 생성
        json_obj = {"actions": fixed_actions}
        fixed_json = json.dumps(json_obj, indent=2)
        return True, fixed_json
        
    except Exception as e:
        print(f"고급 JSON 수정 중 오류: {e}")
        return False, None

async def process_test_case(template_name, template, case_name, test_case):
    """단일 테스트 케이스 처리 (비동기)"""
    print(f"테스트 실행: {template_name} + {case_name}")
    
    try:
        # 프롬프트 생성
        prompt = format_prompt(template, test_case)
        
        # 프롬프트 저장 (디버깅용)
        Path("results").mkdir(exist_ok=True) # 디렉토리 확인
        with open(Path("results") / f"{template_name}_{case_name}_prompt.txt", 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        # 프롬프트 길이 계산
        token_estimate = len(prompt.split())  # 단순 추정
        print(f"프롬프트 토큰 수 (추정): {token_estimate}")
        
        # 캐시 키 생성
        cache_key = get_cache_key(template_name, case_name, prompt)
        
        # 처리할 에이전트 이름 목록
        agent_names = test_case.get("agents_to_process", [])
        
        # 모델 호출
        model_response = call_model(prompt, agent_names, timeout=DEFAULT_TIMEOUT)
        
        # 원본 응답 저장
        original_response = model_response["response"]
        
        # JSON 응답 검증
        is_json, extracted_json = is_valid_json(model_response["response"])
        
        # 에이전트 수 검증
        expected_agent_count = len(agent_names)
        actual_agent_count = 0
        
        if is_json and extracted_json:
            try:
                parsed = json.loads(extracted_json)
                if "actions" in parsed and isinstance(parsed["actions"], list):
                    # 고유 에이전트 이름 추출
                    agents_in_response = set()
                    for action in parsed["actions"]:
                        if "agent" in action and action["agent"] not in ["unknown", "unknown_agent_1"]:
                            agents_in_response.add(action["agent"])
                    
                    actual_agent_count = len(agents_in_response)
                    
                    # 에이전트 수 검증
                    if actual_agent_count != expected_agent_count:
                        print(f"경고: 예상 에이전트 수({expected_agent_count})와 실제 에이전트 수({actual_agent_count}) 불일치")
                        
                        # 비어있는 에이전트 확인
                        missing_agents = set(agent_names) - agents_in_response
                        if missing_agents:
                            print(f"누락된 에이전트: {', '.join(missing_agents)}")
            except Exception as e:
                print(f"에이전트 수 검증 중 오류: {e}")
        
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
            "fixed": extracted_json != original_response if is_json else False,  # JSON 수정 여부 표시
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),  # 타임스탬프 추가
            "expected_agents": expected_agent_count,
            "actual_agents": actual_agent_count
        }
        
        # 결과 저장
        with open(Path("results") / f"{template_name}_{case_name}_result.json", 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2)
        
        print(f"테스트 완료: {template_name}_{case_name} - 유효한 JSON: {is_json}, 시간: {model_response['elapsed_time']:.2f}초")
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
    
    # 캐시 로드
    load_cache()
    
    # Check and create directories
    Path("prompts").mkdir(exist_ok=True)
    Path("test_cases").mkdir(exist_ok=True)
    Path("results").mkdir(exist_ok=True)
    
    # Load templates
    templates = {}
    for template_file in Path("prompts").glob("*.txt"):
        templates[template_file.stem] = load_template(template_file)
    
    # Load test cases
    test_cases = {}
    for test_file in Path("test_cases").glob("*.json"):
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
    
    # 캐시 저장
    save_cache()
    
    return results

def calculate_baseline_time():
    """이전 테스트 결과에서 기준 응답 시간 계산"""
    baseline = 34.62  # 기본값
    
    try:
        # results 디렉토리에서 이전 결과 파일 찾기
        result_files = list(Path("results").glob("*_result.json"))
        if result_files:
            response_times = []
            for file_path in result_files:
                with open(file_path, 'r') as f:
                    result = json.load(f)
                    if "response_time" in result:
                        response_times.append(result["response_time"])
            
            if response_times:
                baseline = sum(response_times) / len(response_times)
    except Exception as e:
        print(f"기준 시간 계산 중 오류: {e}")
    
    return baseline

if __name__ == "__main__":
    print("프롬프트 테스트 스위트 시작...")
    
    # 비동기 이벤트 루프 실행
    import asyncio
    results = asyncio.run(run_test_suite())
    
    # 결과가 있는 경우만 요약 통계 출력
    if results:
        # 기준 응답 시간 계산
        baseline_time = calculate_baseline_time()
        
        # 요약 통계 출력
        success_count = sum(1 for r in results if r["is_valid_json"])
        print(f"\n테스트 요약: {success_count}/{len(results)} 테스트가 유효한 JSON 생성")
        
        # 에이전트 카운트 검증
        agent_count_match = sum(1 for r in results if r.get("expected_agents") == r.get("actual_agents", 0))
        print(f"에이전트 수 일치: {agent_count_match}/{len(results)} 테스트")
        
        # JSON 수정이 필요했던 케이스 확인
        fixed_count = sum(1 for r in results if r.get("fixed", False))
        if fixed_count > 0:
            print(f"자동 JSON 수정 적용: {fixed_count}/{success_count} 성공 케이스")
        
        avg_time = sum(r["response_time"] for r in results) / len(results) if results else 0
        print(f"평균 응답 시간: {avg_time:.2f}초")
        
        # 개선율 계산
        improvement = (1 - avg_time/baseline_time) * 100
        print(f"응답 시간 최적화: 기준 대비 {improvement:.1f}% 개선 (기준: {baseline_time:.2f}초)")
        
        # 캐시 히트 수
        cache_hits = sum(1 for r in results if r.get("status") == "cache_hit")
        if cache_hits > 0:
            print(f"캐시 적중: {cache_hits}/{len(results)} ({cache_hits/len(results)*100:.1f}%)")
        
        # 타임아웃 수
        timeouts = sum(1 for r in results if r.get("status") in ["timeout", "timeout_fallback"])
        if timeouts > 0:
            print(f"타임아웃 발생: {timeouts}/{len(results)} ({timeouts/len(results)*100:.1f}%)")
        
        print("\n상세 결과는 'results' 디렉토리에 저장되었습니다.")
    else:
        print("\n생성된 테스트 결과가 없습니다. 설정 오류를 확인하세요.")