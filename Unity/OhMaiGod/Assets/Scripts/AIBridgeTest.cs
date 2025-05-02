using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System;
using OhMAIGod.Agent;

// ========== AI에게 전송하는 데이터 구조체들 ==========
// 에이전트가 인식할 수 있는 오브젝트 그룹 정의
[System.Serializable]
public struct ObjectGroup
{
    public string location;        // 오브젝트가 있는 위치
    public List<string> objects;   // 해당 위치의 오브젝트 목록
}

// AI에게 전송할 에이전트 정보 구조체
[System.Serializable]
public struct Agent
{
    public string name;                         // 에이전트 이름
    public AgentNeeds state;   // 에이전트의 감정 상태
    public string location;                     // 현재 위치
    public string personality;                  // 성격 특성
    public ObjectGroup[] visible_objects;       // 볼 수 있는 오브젝트들
    public ObjectGroup[] interactable_items;    // 상호작용 가능한 아이템들
    public string[] nearby_agents;              // 근처에 있는 다른 에이전트들
}

// AI 서버에 보낼 요청 데이터 구조체
[System.Serializable]
public struct AgentRequest
{
    public Agent agent;  // 에이전트 정보
}

// AI가 결정한 행동의 세부 정보
[System.Serializable]
public struct ActionDetails
{
    public string location;    // 행동을 수행할 위치
    public string message;     // 행동과 관련된 메시지
    public string target;      // 행동의 대상
    public string using_item;  // 사용할 아이템 (JSON의 "using"에 매핑)
}

// AI가 결정한 행동 정보
[System.Serializable]
public struct Action
{
    public string action;               // 수행할 행동
    public string agent;                // 행동을 수행할 에이전트
    public ActionDetails details;       // 행동의 세부 정보
    public string reason;               // 행동의 이유
}

// AI 응답 데이터를 감싸는 래퍼 구조체
[System.Serializable]
public struct DataWrapper
{
    public Action action;  // AI가 결정한 행동
}

// AI 서버로부터의 응답 구조체
[System.Serializable]
public struct AgentResponse
{
    public DataWrapper data;    // 응답 데이터 (행동 정보)
    public string status;       // 응답 상태 ("OK" 등)
}

public class AIBridgeTest : MonoBehaviour
{
    [Header("에이전트 참조")]
    [SerializeField] private AgentController mAgentController;
    [SerializeField] private AgentScheduler mAgentScheduler;
    [SerializeField] private MovementController mMovementController;

    [Header("오브젝트 그룹 (인식 가능)")]
    [SerializeField] public List<ObjectGroup> mVisibleObjects = new List<ObjectGroup>();

    [Header("오브젝트 그룹 (상호작용 가능)")]
    [SerializeField] public List<ObjectGroup> mInteractableItems = new List<ObjectGroup>();

    private bool mIsRequesting = false;  // AI에게 응답 보내고 있는지 확인하는 변수

    private void Awake()
    {
        // 컴포넌트 참조 가져오기
        if (mAgentController == null)
            mAgentController = GetComponent<AgentController>();
        if (mAgentScheduler == null)
            mAgentScheduler = GetComponent<AgentScheduler>();
        if (mMovementController == null)
            mMovementController = GetComponent<MovementController>();

        // 컴포넌트 유효성 검사
        if (mAgentController == null || mAgentScheduler == null || mMovementController == null)
        {
            Debug.LogError("필요한 컴포넌트가 없습니다!");
            enabled = false;
            return;
        }
    }

    private void Start()
    {
        // 게임 시작시 자동으로 첫 요청 보내기
        SendAgent();

        // 목적지 도착 이벤트 구독
        if (mMovementController != null)
        {
            mMovementController.OnDestinationReached += HandleDestinationReached;
        }
    }

    private void OnDestroy()
    {
        // 이벤트 구독 해제
        if (mMovementController != null)
        {
            mMovementController.OnDestinationReached -= HandleDestinationReached;
        }
    }

    // 목적지 도착 이벤트 발생 시, AI서버에게 Agent Data 전송
    private void HandleDestinationReached()
    {
        SendAgent();
    }

    // AI 서버에게 Agent Data 보내는 함수
    public void SendAgent()
    {
        // 이미 요청 중이면 중복 요청 방지
        if (mIsRequesting)
        {
            Debug.LogWarning("요청 진행 중입니다. 기다려주세요.");
            return;
        }

        StartCoroutine(SendAgentData());
    }

    // AI 서버와 통신하는 코루틴
    IEnumerator SendAgentData()
    {
        mIsRequesting = true;

        // 현재 에이전트의 상태 정보 가져오기
        AgentNeeds currentState = mAgentController.GetAgentNeeds();

        // AI 서버에 보낼 요청 데이터 생성
        AgentRequest requestData = new AgentRequest
        {
            agent = new Agent
            {
                name = mAgentController.AgentName,
                state = currentState,
                location = string.IsNullOrEmpty(mMovementController.TargetName) ? "Bedroom" : mMovementController.TargetName,
                personality = "friendly, helpful", // TODO: 에이전트별 성격 구현 필요
                visible_objects = mVisibleObjects.ToArray(),
                interactable_items = mInteractableItems.ToArray(),
                nearby_agents = new string[] { } // TODO: 주변 에이전트 감지 구현 필요
            }
        };

        // 요청 데이터를 JSON으로 변환
        string jsonData = JsonUtility.ToJson(requestData, true);
        Debug.Log("보낼 JSON:\n" + jsonData);

        // HTTP 요청 설정
        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:5000/action", "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        // 요청 시간 측정 시작
        var stopwatch = new System.Diagnostics.Stopwatch();
        stopwatch.Start();

        // 요청 전송 및 응답 대기
        yield return request.SendWebRequest();

        // 요청 시간 측정 종료
        stopwatch.Stop();
        long elapsedMs = stopwatch.ElapsedMilliseconds;

        mIsRequesting = false;

        // 응답 처리
        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("✅ 응답: " + request.downloadHandler.text);
            Debug.Log($"⏱️ 요청 소요 시간: {elapsedMs} ms");

            // AI 응답 처리
            ProcessResponse(request.downloadHandler.text);
        }
        else
        {
            Debug.LogError("❌ 실패: " + request.error);
        }
    }

    // AI 서버로부터 받은 응답을 처리하는 함수
    private void ProcessResponse(string response)
    {
        try
        {
            // JSON 응답을 객체로 변환
            AgentResponse agentResponse = JsonUtility.FromJson<AgentResponse>(response);
            
            // 응답 유효성 검사
            if (agentResponse.status != "OK" || string.IsNullOrEmpty(agentResponse.data.action.action))
            {
                Debug.LogError("Invalid response format or status is not OK");
                return;
            }

            Action action = agentResponse.data.action;
            
            // 현재 시간 가져오기 및 활동 지속 시간 설정
            TimeSpan currentTime = TimeManager.Instance.GetCurrentGameTime();
            TimeSpan duration = TimeSpan.FromMinutes(30); // 기본 30분으로 설정
            
            // 새로운 일정 아이템 생성
            ScheduleItem newScheduleItem = new ScheduleItem
            {
                ID = System.Guid.NewGuid().ToString(),
                ActionName = action.action,
                LocationName = action.details.target,
                StartTime = currentTime,
                EndTime = currentTime.Add(duration),
                Priority = 1, // 최우선순위로 설정
                IsFlexible = true,
                IsCompleted = false,
                ActionDetails = JsonUtility.ToJson(action.details),
                Reason = action.reason
            };

            // 스케줄러에 새 일정 추가 (기존 일정은 자동으로 취소됨)
            bool success = mAgentScheduler.AddScheduleItem(newScheduleItem);
            
            // 일정 추가 결과 로깅
            if (!success)
            {
                Debug.LogError($"Failed to add schedule item: {newScheduleItem.ActionName} @ {newScheduleItem.LocationName}");
            }
            else
            {
                Debug.Log($"Successfully added and started new Action: {newScheduleItem.ActionName} @ {newScheduleItem.LocationName}");
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"Error processing response: {ex.Message}\n{ex.StackTrace}");
        }
    }
} 