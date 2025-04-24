"""
파일 구조 확인 및 필요한 파일 생성
"""
import os
from pathlib import Path
import json
import shutil

def check_file_structure():
    """파일 구조 확인 및 디버깅 정보 출력"""
    print("\n===== 파일 구조 확인 =====")
    
    # 필요한 디렉토리 확인
    dirs_to_check = ["prompts", "test_cases", "memories", "results"]
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
        else:
            print(f"✗ 디렉토리 '{dir_name}' 없음")
            
            # 디렉토리 생성
            dir_path.mkdir(exist_ok=True)
            print(f"  → 디렉토리 '{dir_name}' 생성됨")
    
    # 필수 파일 확인
    required_files = [
        "prompts/complex_prompt.txt",
        "test_cases/agent_hungry.json",
        "test_cases/agent_sleepy.json",
        "test_cases/agent_lonely.json",
        "test_cases/agent_stressed.json",
        "test_cases/agent_balanced.json",
        "memories/agents_memories.json"
    ]
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ 파일 '{file_path}' 존재함")
            
            # 파일 내용이 비어있는지 확인
            if path.stat().st_size == 0:
                print(f"  ⚠ 파일이 비어있음")
        else:
            print(f"✗ 파일 '{file_path}' 없음")

def copy_templates_to_project():
    """템플릿 파일들을 프로젝트 디렉토리로 복사"""
    # 필요한 디렉토리 생성
    dirs_to_create = ["prompts", "test_cases", "memories", "results"]
    for dir_name in dirs_to_create:
        Path(dir_name).mkdir(exist_ok=True)
    
    print("\n===== 템플릿 파일 복사 =====")
    
    # complex_prompt.txt 복사
    complex_prompt = """You are the AI controller for agents in a simulation game '{game_name}'.

GAME INFO:
- Time: {current_time}
- Environment: {environment_state}

AGENTS TO CONTROL: {agents_to_process}

AGENT DATA:
{agents[0].name}: state: {agents[0].state}, personality: {agents[0].personality}, at {agents[0].location}, goal: {agents[0].goal}
Visible: {agents[0].visible_objects}
Can interact with: {agents[0].interactable_items}
Nearby agents: {agents[0].nearby_agents}
Memories: {agents[0].memory}

TASK: For each agent, determine ONE NEXT ACTION based on their current state, goals, memories, and personality.

ACTION OPTIONS:
- move: go to a new location  
- interact: use/manipulate an object  
- eat: consume food  
- talk: speak to another agent  
- wait: remain inactive briefly  
- think: internal thought process  
- idle: remain idle without taking any action  
- sleep: sleep to recover energy (agent becomes inactive for a longer period)  
- die: be removed from the simulation  

LOCATION OPTIONS:
- John's home: the private residence of John  
- town hall: central community building where agents gather for meetings  
- cafeteria: communal dining area where agents can eat and socialize  

MEMORY RATING RULES:
On a scale of 1 to 10, where  
1 = purely mundane (e.g., brushing teeth, making bed)  
3 = minor daily event (e.g., short conversation, shopping)
5 = moderately significant (e.g., playing games with friends)
7 = important event (e.g., having dinner with friends)
10 = extremely poignant (e.g., a breakup, college acceptance)  
rate the poignancy of any newly generated memory.

REASONING GUIDELINES:
- Base decisions on agent's current state, goals, past memories, and personality traits
- Consider time of day, environment, and location
- Prioritize higher importance memories that are recent when making decisions
- Show causality between memories, current state, and chosen action
- If agent is hungry (hunger > 6), prioritize finding food
- If agent is sleepy (sleepiness > 7), prioritize rest
- If agent is lonely (loneliness > 5), prioritize social interaction
- If agent is stressed (stress > 6), prioritize relaxation
- Account for personality traits in decision making (e.g., introverted agents may prefer solitary activities)

RESPONSE FORMAT (provide ONLY valid JSON):
```json
{
  "actions": [
    {
      "agent": "agent_name",
      "action": "action_type",
      "details": {
        "target": "object_or_location",
        "using": "item_if_needed",
        "message": "spoken_text_or_thought"
      },
      "memory_update": {
        "action": "with_whom_and_where_action_took_place",
        "time": "{current_time}", 
        "importance": importance_rating
      },
      "reason": "Detailed explanation of why this action was chosen based on memories, state, goals, personality, etc."
    }
  ]
}
```

IMPORTANT: Provide EXACTLY ONE action per character. Respond ONLY with JSON. Ensure the reason field explains how memories and personality influenced the decision."""
    
    with open(Path("prompts") / "complex_prompt.txt", 'w', encoding='utf-8') as f:
        f.write(complex_prompt)
    print("✓ complex_prompt.txt 생성됨")
    
    # agent_hungry.json 복사
    agent_hungry = {
        "game_name": "Life Simulation",
        "current_time": "2025.04.23.12:30",
        "environment_state": "Sunny day, lunchtime",
        "agents_to_process": ["John"],
        "agents": [
            {
                "name": "John",
                "location": "town hall",
                "goal": "Find something to eat",
                "personality": "introverted, practical, punctual",
                "state": {
                    "hunger": 9,
                    "sleepiness": 2,
                    "loneliness": 3,
                    "stress": 5,
                    "happiness": 4
                },
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
                "nearby_agents": ["Alice", "Tom"],
                "memory": "Recent memories of John talking with Alice and Sarah at town hall, previously having coffee with Tom and Alice at cafeteria."
            }
        ]
    }
    
    with open(Path("test_cases") / "agent_hungry.json", 'w', encoding='utf-8') as f:
        json.dump(agent_hungry, f, indent=2)
    print("✓ agent_hungry.json 생성됨")
    
    # agent_sleepy.json 복사
    agent_sleepy = {
        "game_name": "Life Simulation",
        "current_time": "2025.04.23.22:45",
        "environment_state": "Night time, quiet",
        "agents_to_process": ["John"],
        "agents": [
            {
                "name": "John",
                "location": "town hall",
                "goal": "Get some rest",
                "personality": "introverted, practical, punctual",
                "state": {
                    "hunger": 3,
                    "sleepiness": 9,
                    "loneliness": 2,
                    "stress": 4,
                    "happiness": 4
                },
                "visible_objects": [
                    {
                        "location": "town hall",
                        "objects": ["chair", "desk", "computer", "lamp", "couch"]
                    }
                ],
                "interactable_items": [
                    {
                        "location": "town hall",
                        "objects": ["chair", "desk", "computer", "lamp", "couch"]
                    }
                ],
                "nearby_agents": [],
                "memory": "John remembers having drinks with Alice and Sarah earlier at cafeteria. He also recalls his comfortable bed at home."
            }
        ]
    }
    
    with open(Path("test_cases") / "agent_sleepy.json", 'w', encoding='utf-8') as f:
        json.dump(agent_sleepy, f, indent=2)
    print("✓ agent_sleepy.json 생성됨")
    
    # 간단한 memories 파일 생성
    memories = {
        "John": [
            {
                "action": "Had coffee with Tom at cafeteria.",
                "time": "2025.04.22.13:00",
                "importance": 3
            },
            {
                "action": "Had dinner with Alice at cafeteria.",
                "time": "2025.04.22.19:00",
                "importance": 7
            }
        ]
    }
    
    with open(Path("memories") / "agents_memories.json", 'w', encoding='utf-8') as f:
        json.dump(memories, f, indent=2)
    print("✓ agents_memories.json 생성됨")
    
    # run_tests.py 확인
    run_tests_path = Path("run_tests.py")
    if not run_tests_path.exists():
        print("✗ run_tests.py 파일이 없습니다. 이 파일을 제공해주세요.")

if __name__ == "__main__":
    check_file_structure()
    
    choice = input("\n필요한 파일을 생성하시겠습니까? (y/n): ")
    if choice.lower() == 'y':
        copy_templates_to_project()
        print("\n모든 필요한 파일이 생성되었습니다. 이제 run_tests.py를 실행해보세요.")
    else:
        print("\n기존 파일을 유지합니다.")