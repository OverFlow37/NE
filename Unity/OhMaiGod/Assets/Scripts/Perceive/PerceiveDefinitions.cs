using UnityEngine;
using System.Collections;
using System.Text;
using UnityEngine.Networking;

namespace OhMAIGod.Perceive{
    // 반응인지 관찰인지 여부
    public enum RequestType
    {
        REACTION,
        PERCEIVE,
    }
    // 반응 또는 관찰을 유발한 Event 타입
    public enum PerceiveEventType
    {
        INTERACTABLE_DISCOVER,          // 오브젝트 발견
        INTERACTABLE_STATE_CHANGE,      // 오브젝트 상태 변화 감지
        POWER_OBSERVE,                  // 권능 목격
        OTHER_AGENT_REQUEST,            // 다른 에이전트의 상호작용 요청
        AGENT_LOCATION_CHANGE,          // 에이전트 지역 이동
        AGENT_NEED_LIMIT,               // 에이전트 욕구 한계치 도달
        AGENT_NO_TASK,                  // 현재 에이전트에 할당된 작업 없음
        TARGET_NOT_IN_LOCATION          // 현재 위치에 목표가 없음
    }

    // 반응 또는 관찰을 유발한 Event에 대한 정보 구조화
    [System.Serializable]
    public struct PerceiveEvent
    {
        public PerceiveEventType event_type; // 이벤트 타입
        public string event_location;        // 이벤트 발생 위치
        public string event_description;     // 이벤트 설명
        public bool event_is_save;           // 이벤트 메모리 저장 여부
        public string event_role;            // 이벤트 발생 주체(GOD says, Tom Thougt)
    }

    // 피드백 구조체
    [System.Serializable]
    public struct needs_diff
    {
        public int hunger;
        public int sleepiness;
        public int loneliness;
        public int stress;
    }
    [System.Serializable]
    public struct feedback
    {
        public string memory_id;
        public string feedback_description;
        public needs_diff needs_diff;
    }

    [System.Serializable]
    public struct PerceiveFeedback
    {
        public string agent_name;   
        public string current_location_name;  
        public string time;     
        public string interactable_name;
        public string action_name;
        public bool success;
        public feedback feedback;
    }
}
