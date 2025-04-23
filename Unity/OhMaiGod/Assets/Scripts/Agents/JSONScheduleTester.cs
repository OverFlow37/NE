using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Newtonsoft.Json;

public class JSONScheduleTester : MonoBehaviour
{
    [Header("에이전트 참조")]
    [SerializeField] private AgentController mTargetAgent;

    [Header("현재 시간 정보")]
    [SerializeField] private float mTimeScale = 60f; // 분/초
    [SerializeField] private string mCurrentTime = "00:00";
    [SerializeField] private string mCurrentActivity = "없음";

    [Header("JSON 입력")]
    [TextArea(5, 10)]
    [SerializeField] private string mJsonInput = @"{
  ""who"": ""test_npc_1"",
  ""where"": ""Kitchen"",
  ""what"": ""Fridge"",
  ""action"": ""Open fridge and get food"",
  ""startTime"": ""08:00"",
  ""endTime"": ""08:15"",
  ""priority"": 5,
  ""isFlexible"": false
}";

    [Header("액션")]
    [SerializeField] private bool mProcessJson = false;
    [SerializeField] private bool mCompleteCurrentActivity = false;
    [SerializeField] private bool mClearAllSchedule = false;
    [SerializeField] private bool mApplyTimeScale = false;

    // 내부 참조
    private AgentScheduler mScheduler;

    // JSON 데이터 구조
    [Serializable]
    private class AgentActionData
    {
        public string who;         // 에이전트 이름
        public string where;       // 위치
        public string what;        // 대상 객체 (선택적)
        public string action;      // 행동 설명
        public string startTime;   // 시작 시간 (선택적)
        public string endTime;     // 종료 시간 (선택적)
        public int priority = 5;   // 우선순위 (기본값 5)
        public bool isFlexible = false; // 유연한 일정 여부
    }

    private void Start()
    {
        if (mTargetAgent != null)
        {
            mScheduler = mTargetAgent.GetComponent<AgentScheduler>();
        }
        else
        {
            Debug.LogError("대상 에이전트가 설정되지 않았습니다.");
        }

        // 매 프레임 업데이트가 아닌 주기적 업데이트 시작
        StartCoroutine(UpdateInfoRoutine());
    }

    private void Update()
    {
        // 인스펙터에서 버튼 액션 처리
        if (mProcessJson)
        {
            mProcessJson = false;
            ProcessJsonInput();
        }

        if (mCompleteCurrentActivity)
        {
            mCompleteCurrentActivity = false;
            CompleteCurrentActivity();
        }

        if (mClearAllSchedule)
        {
            mClearAllSchedule = false;
            ClearAllSchedule();
        }

        if (mApplyTimeScale)
        {
            mApplyTimeScale = false;
            ApplyTimeScale();
        }
    }


    // 현재 정보 업데이트 코루틴
    private IEnumerator UpdateInfoRoutine()
    {
        while (true)
        {
            if (mScheduler != null)
            {
                // 현재 시간 정보 업데이트
                TimeSpan currentTime = mScheduler.GetCurrentGameTime();
                mCurrentTime = $"{currentTime.Hours:D2}:{currentTime.Minutes:D2}";
                
                // 현재 활동 정보 업데이트
                string activity = mScheduler.GetCurrentActivityName();
                string location = mScheduler.GetCurrentDestination();
                
                if (!string.IsNullOrEmpty(location))
                {
                    mCurrentActivity = $"{activity} @ {location}";
                }
                else
                {
                    mCurrentActivity = activity;
                }
            }

            yield return new WaitForSeconds(0.5f);
        }
    }

    // JSON 입력 처리
    public void ProcessJsonInput()
    {
        if (mScheduler == null)
        {
            Debug.LogError("스케줄러 참조가 없습니다.");
            return;
        }

        try
        {
            // JSON 파싱
            AgentActionData actionData = JsonConvert.DeserializeObject<AgentActionData>(mJsonInput);
            
            if (actionData == null)
            {
                Debug.LogError("JSON 파싱 실패");
                return;
            }

            // 기본 유효성 검사
            if (string.IsNullOrEmpty(actionData.who) || 
                string.IsNullOrEmpty(actionData.where) ||
                string.IsNullOrEmpty(actionData.action))
            {
                Debug.LogError("필수 필드(who, where, action)가 누락되었습니다.");
                return;
            }

            // 에이전트 이름 확인
            if (actionData.who != mTargetAgent.AgentName)
            {
                Debug.LogWarning($"JSON의 에이전트 ID({actionData.who})가 현재 타겟 에이전트({mTargetAgent.AgentName})와 다릅니다. 계속 진행합니다.");
            }

            // 활동 이름 생성
            string activityName = !string.IsNullOrEmpty(actionData.what)
                ? $"{actionData.action} ({actionData.what})"
                : actionData.action;

            // 시간 처리
            TimeSpan startTime;
            TimeSpan endTime;
            
            // 시간이 지정되지 않은 경우 현재 시간 기준으로 설정
            if (string.IsNullOrEmpty(actionData.startTime) || string.IsNullOrEmpty(actionData.endTime))
            {
                TimeSpan currentTime = mScheduler.GetCurrentGameTime();
                startTime = currentTime;
                
                // 기본 활동 시간은 15분으로 설정
                endTime = currentTime.Add(TimeSpan.FromMinutes(15));
            }
            else
            {
                // 지정된 시간 파싱
                startTime = ParseTimeInput(actionData.startTime);
                endTime = ParseTimeInput(actionData.endTime);
            }

            if (endTime <= startTime)
            {
                Debug.LogError("종료 시간은 시작 시간보다 나중이어야 합니다.");
                return;
            }

            // 스케줄 아이템 생성
            AgentScheduler.ScheduleItem item = new AgentScheduler.ScheduleItem
            {
                Id = $"json_{System.Guid.NewGuid().ToString().Substring(0, 8)}",
                ActivityName = activityName,
                LocationName = actionData.where,
                StartTime = startTime,
                EndTime = endTime,
                Priority = actionData.priority,
                IsFlexible = actionData.isFlexible
            };

            // 스케줄에 추가
            bool success = mScheduler.AddScheduleItem(item);
            
            if (success)
            {
                Debug.Log($"JSON에서 새 활동 추가됨: {activityName} @ {actionData.where} ({startTime}-{endTime})");
            }
            else
            {
                Debug.LogWarning("JSON 활동 추가 실패. 기존 활동과 충돌이 있을 수 있습니다.");
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"JSON 처리 실패: {ex.Message}");
        }
    }

    // 시간 문자열 파싱 (시:분 또는 시:분:초 형식)
    private TimeSpan ParseTimeInput(string timeString)
    {
        // 시:분 형식 확인
        if (timeString.Split(':').Length == 2)
        {
            timeString += ":00"; // 초 추가
        }

        return TimeSpan.Parse(timeString);
    }

    // 현재 활동 완료 처리
    public void CompleteCurrentActivity()
    {
        if (mScheduler != null)
        {
            mScheduler.CompleteCurrentActivity();
            Debug.Log("현재 활동 완료 처리됨");
        }
    }

    // 모든 스케줄 지우기
    public void ClearAllSchedule()
    {
        if (mScheduler != null)
        {
            mScheduler.ClearSchedule();
            Debug.Log("모든 스케줄 지움");
        }
    }

    // 시간 속도 적용
    public void ApplyTimeScale()
    {
        if (mScheduler != null)
        {
            mScheduler.SetTimeScale(mTimeScale);
            Debug.Log($"시간 속도 변경: {mTimeScale}분/초");
        }
    }

    // 테스트용 JSON 샘플 생성
    [ContextMenu("Generate Sample JSON")]
    public void GenerateSampleJSON()
    {
        if (mScheduler == null) return;

        // 현재 시간 가져오기
        TimeSpan currentTime = mScheduler.GetCurrentGameTime();
        string startTime = $"{currentTime.Hours:D2}:{(currentTime.Minutes + 5) % 60:D2}";
        string endTime = $"{currentTime.Hours:D2}:{(currentTime.Minutes + 20) % 60:D2}";
        
        // 샘플 JSON 생성
        AgentActionData sample = new AgentActionData
        {
            who = mTargetAgent != null ? mTargetAgent.AgentName : "agent_name",
            where = "Kitchen",
            what = "Fridge",
            action = "Get food and cook meal",
            startTime = startTime,
            endTime = endTime,
            priority = 8,
            isFlexible = false
        };
        
        // JSON 문자열로 변환
        mJsonInput = JsonConvert.SerializeObject(sample, Formatting.Indented);
        Debug.Log("샘플 JSON 생성됨");
    }

    // 여러 테스트 시나리오 JSON 준비
    [ContextMenu("Load Scenario 1")]
    public void LoadScenario1()
    {
        TimeSpan currentTime = mScheduler != null 
            ? mScheduler.GetCurrentGameTime() 
            : new TimeSpan(8, 0, 0);
            
        int hour = currentTime.Hours;
        
        // 아침 식사 시나리오
        AgentActionData scenario = new AgentActionData
        {
            who = mTargetAgent != null ? mTargetAgent.AgentName : "agent_name",
            where = "Kitchen",
            what = "Fridge",
            action = "Prepare breakfast",
            startTime = $"{hour:D2}:00",
            endTime = $"{hour:D2}:30",
            priority = 6,
            isFlexible = false
        };
        
        mJsonInput = JsonConvert.SerializeObject(scenario, Formatting.Indented);
        Debug.Log("시나리오 1 로드됨: 아침 식사");
    }
    
    [ContextMenu("Load Scenario 2")]
    public void LoadScenario2()
    {
        TimeSpan currentTime = mScheduler != null 
            ? mScheduler.GetCurrentGameTime() 
            : new TimeSpan(9, 0, 0);
            
        int hour = currentTime.Hours;
        
        // 업무 시나리오
        AgentActionData scenario = new AgentActionData
        {
            who = mTargetAgent != null ? mTargetAgent.AgentName : "agent_name",
            where = "Desk",
            what = "Computer",
            action = "Work on project",
            startTime = $"{hour:D2}:00",
            endTime = $"{(hour+3) % 24:D2}:00",
            priority = 8,
            isFlexible = false
        };
        
        mJsonInput = JsonConvert.SerializeObject(scenario, Formatting.Indented);
        Debug.Log("시나리오 2 로드됨: 업무");
    }
    
    [ContextMenu("Load Scenario 3")]
    public void LoadScenario3()
    {
        // 긴급 이벤트 시나리오
        AgentActionData scenario = new AgentActionData
        {
            who = mTargetAgent != null ? mTargetAgent.AgentName : "agent_name",
            where = "LivingRoom",
            what = "Phone",
            action = "Answer emergency call",
            startTime = "",  // 현재 시간 자동 사용
            endTime = "",    // 현재 시간 + 15분 자동 사용
            priority = 10,   // 높은 우선순위
            isFlexible = false
        };
        
        mJsonInput = JsonConvert.SerializeObject(scenario, Formatting.Indented);
        Debug.Log("시나리오 3 로드됨: 긴급 이벤트");
    }
}