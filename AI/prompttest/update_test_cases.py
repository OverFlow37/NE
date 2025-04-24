"""
모든 테스트 케이스 파일을 표준 형식으로 변환하는 스크립트
"""
import os
import json
from pathlib import Path

def standardize_test_cases():
    """테스트 케이스 파일을 유니티 표준 형식으로 변환"""
    # 테스트 케이스 디렉토리
    test_cases_dir = Path("test_cases")
    if not test_cases_dir.exists():
        print("테스트 케이스 디렉토리가 없습니다.")
        test_cases_dir.mkdir(exist_ok=True)
        print("테스트 케이스 디렉토리를 생성했습니다.")
    
    # 표준 형식의 테스트 케이스 생성
    test_cases = {
        "agent_hungry": {
            "agent": 
                {
                    "name": "John",
                    "state": {
                        "hunger": 9,
                        "sleepiness": 2,
                        "loneliness": 3,
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
        },
        
        "agent_sleepy": {
            "agent": 
                {
                    "name": "John",
                    "state": {
                        "hunger": 3,
                        "sleepiness": 9,
                        "loneliness": 2,
                        "stress": 4,
                        "happiness": 4
                    },
                    "location": "town hall",
                    "personality": "introverted, practical, punctual",
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
                    "nearby_agents": []
                }
            
        },
        
        "agent_lonely": {
            "agent": 
                {
                    "name": "John",
                    "state": {
                        "hunger": 4,
                        "sleepiness": 2,
                        "loneliness": 7,
                        "stress": 3,
                        "happiness": 3
                    },
                    "location": "John's home",
                    "personality": "introverted, practical, punctual",
                    "visible_objects": [
                        {
                            "location": "John's home",
                            "objects": ["TV", "sofa", "phone", "book", "laptop", "kitchen table"]
                        }
                    ],
                    "interactable_items": [
                        {
                            "location": "John's home",
                            "objects": ["TV", "sofa", "phone", "book", "laptop", "kitchen table"]
                        }
                    ],
                    "nearby_agents": []
                }
            
        },
        
        "agent_stressed": {
            "agent": 
                {
                    "name": "John",
                    "state": {
                        "hunger": 5,
                        "sleepiness": 4,
                        "loneliness": 3,
                        "stress": 8,
                        "happiness": 2
                    },
                    "location": "town hall",
                    "personality": "introverted, practical, punctual",
                    "visible_objects": [
                        {
                            "location": "town hall",
                            "objects": ["computer", "work documents", "coffee mug", "chair", "calendar"]
                        }
                    ],
                    "interactable_items": [
                        {
                            "location": "town hall",
                            "objects": ["computer", "work documents", "coffee mug", "chair"]
                        }
                    ],
                    "nearby_agents": ["Alice"]
                }
            
        },
        
        "agent_balanced": {
            "agent": 
                {
                    "name": "John",
                    "state": {
                        "hunger": 4,
                        "sleepiness": 3,
                        "loneliness": 4,
                        "stress": 3,
                        "happiness": 6
                    },
                    "location": "cafeteria",
                    "personality": "introverted, practical, punctual",
                    "visible_objects": [
                        {
                            "location": "cafeteria",
                            "objects": ["coffee machine", "pastries", "tables", "chairs", "newspaper"]
                        }
                    ],
                    "interactable_items": [
                        {
                            "location": "cafeteria",
                            "objects": ["coffee machine", "pastries", "tables", "chairs", "newspaper"]
                        }
                    ],
                    "nearby_agents": ["Alice", "Tom", "Sarah"]
                }
            
        }
    }
    
    # 파일 생성
    for name, data in test_cases.items():
        file_path = test_cases_dir / f"{name}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"파일 생성 완료: {file_path}")

def update_prompt_template():
    """프롬프트 템플릿을 업데이트"""
    prompts_dir = Path("prompts")
    if not prompts_dir.exists():
        prompts_dir.mkdir(exist_ok=True)
        print("prompts 디렉토리를 생성했습니다.")
    
    # 표준 형식에 맞는 프롬프트 템플릿
    prompt_template = """You are the AI controller for agents in a simulation game.

CURRENT TIME: {current_time}
ENVIRONMENT: {environment_state}

AGENT DATA:
Name: {agents[0].name}
State: {agents[0].state}
Personality: {agents[0].personality}
Location: {agents[0].location}
Visible objects: {agents[0].visible_objects}
Interactable items: {agents[0].interactable_items}
Nearby agents: {agents[0].nearby_agents}

TASK: Determine the next action for this agent based on their current state, personality, and environment.

ACTION OPTIONS:
- move: go to a new location  
- interact: use/manipulate an object  
- eat: consume food  
- talk: speak to another agent  
- wait: remain inactive briefly  
- think: internal thought process  
- idle: remain idle without taking any action  
- sleep: sleep to recover energy
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
- Base decisions on agent's current state and personality traits
- Consider time of day, environment, and location
- Reference specific visible objects or nearby agents where appropriate
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
        "location": "location",
        "target": "object_or_agent",
        "using": "item_if_needed",
        "message": "spoken_text_or_thought"
      },
      "memory_update": {
        "action": "with_whom_and_where_action_took_place",
        "time": "{current_time}", 
        "importance": importance_rating
      },
      "reason": "Detailed explanation of why this action was chosen based on state, personality, etc."
    }
  ]
}
```

IMPORTANT: Provide EXACTLY ONE action. Respond ONLY with JSON. The "reason" field is for internal processing and will not be sent to Unity. The "memory_update" will be saved to the memory database."""
    
    # 파일 저장
    template_path = prompts_dir / "complex_prompt.txt"
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(prompt_template)
    print(f"프롬프트 템플릿 업데이트 완료: {template_path}")

if __name__ == "__main__":
    print("테스트 케이스 표준화 시작...")
    standardize_test_cases()
    update_prompt_template()
    print("모든 파일이 표준 형식으로 업데이트되었습니다.")