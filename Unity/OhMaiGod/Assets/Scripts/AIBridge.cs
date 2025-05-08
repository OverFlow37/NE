using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System;
using System.Linq;
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
    public AgentNeeds state;                    // 에이전트의 욕구
    public string section;                      // 현재 구역
    public string location;                     // 현재 위치
    public string personality;                  // 성격 특성
    public ObjectGroup[] visible_objects;       // 볼 수 있는 오브젝트들
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
    public string target;      // 행동의 대상
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

public class AIBridge : MonoBehaviour
{
    [Header("에이전트 참조")]
    [SerializeField] private AgentController[] mAgentControllers;

    private bool mIsRequesting = false;  // AI에게 응답 보내고 있는지 확인하는 변수

    private void Update(){
        if (Input.GetKeyDown(KeyCode.D))
        {
            send_test();
        }
    }
    // 게임 시작시 자동으로 첫 요청 보내기(임시)
    public void send_test()
    {
        // 게임 시작시 자동으로 첫 요청 보내기
        SendAgent(mAgentControllers[0]);

        // 목적지 도착 이벤트 구독
        // if (mAgentControllers[0] != null)
        // {
        //     mAgentControllers[0].OnDestinationReached += HandleDestinationReached;
        // }
    }

    // Interactable 목록을 ObjectGroup 배열로 변환
    private ObjectGroup[] ConvertToObjectGroups(List<Interactable> interactables)
    {
        // 위치별로 오브젝트들을 그룹화
        Dictionary<string, List<string>> locationGroups = new Dictionary<string, List<string>>();

        foreach (Interactable interactable in interactables)
        {
            if (interactable == null || interactable.mInteractableData == null) continue;

            string location = interactable.CurrentLocation;
            if (string.IsNullOrEmpty(location)) continue;

            if (!locationGroups.ContainsKey(location))
            {
                locationGroups[location] = new List<string>();
            }
            locationGroups[location].Add(interactable.InteractableName);
        }

        // Dictionary를 ObjectGroup 배열로 변환
        return locationGroups.Select(group => new ObjectGroup
        {
            location = group.Key,
            objects = group.Value
        }).ToArray();
    }

    // AI 서버에게 특정 에이전트의 Agent Data 보내는 함수
    public void SendAgent(AgentController agent)
    {
        if (mIsRequesting)
        {
            LogManager.Log("AI", $"요청 진행 중입니다. 기다려주세요. (에이전트: {agent.AgentName})", 1);
            return;
        }
        agent.ChangeState(AgentState.WAIT_FOR_AI_RESPONSE);
        StartCoroutine(SendAgentData(agent));
    }

    // AI 서버와 통신하는 코루틴 (에이전트별)
    IEnumerator SendAgentData(AgentController agent)
    {
        mIsRequesting = true;

        // 현재 에이전트의 상태 정보 가져오기
        AgentNeeds currentNeeds = agent.AgnetNeeds;
        var movement = agent.mMovement;
        var scheduler = agent.mScheduler;

        // AI 서버에 보낼 요청 데이터 생성
        var visibleObjectGroups = ConvertToObjectGroups(agent.mVisibleInteractables);
        
        // 에이전트의 현재 위치 가져오기 (CurrentAction이 null일 경우 대비)
        string agentLocation = "Unknown"; // 기본값
        Interactable agentInteractable = agent.GetComponent<Interactable>();
        if (agentInteractable != null && !string.IsNullOrEmpty(agentInteractable.CurrentLocation))
        {
            agentLocation = agentInteractable.CurrentLocation;
        }
        else if (agent.CurrentAction != null && !string.IsNullOrEmpty(agent.CurrentAction.LocationName))
        {
            // CurrentAction이 있고 LocationName이 유효하면 해당 위치 사용
            agentLocation = agent.CurrentAction.LocationName;
        }

        for (int i = 0; i < visibleObjectGroups.Length; i++)
        {
            LogManager.Log("AI", $"[AIBridge] ObjectGroup {i}: location={visibleObjectGroups[i].location}, objects=[{string.Join(",", visibleObjectGroups[i].objects)}]", 3);
        }

        AgentRequest requestData = new AgentRequest
        {
            agent = new Agent
            {
                name = agent.AgentName,
                state = currentNeeds,
                location = agentLocation,
                personality = "friendly, helpful", // TODO: 에이전트별 성격 구현 필요
                visible_objects = visibleObjectGroups
            }
        };

        // requestData 전체 구조를 JSON으로 출력
        LogManager.Log("AI", $"[AIBridge] requestData 전체: {JsonUtility.ToJson(requestData, true)}", 3);

        // 요청 데이터를 JSON으로 변환
        string jsonData = JsonUtility.ToJson(requestData, true);
        LogManager.Log("AI", $"보낼 JSON (에이전트: {agent.AgentName}):\n" + jsonData, 3);

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
            LogManager.Log("AI", $"✅ 응답 (에이전트: {agent.AgentName}): " + request.downloadHandler.text, 2);
            LogManager.Log("AI", $"⏱️ 요청 소요 시간: {elapsedMs} ms", 2);

            // AI 응답 처리
            ProcessResponse(request.downloadHandler.text, agent);
        }
        else
        {
            LogManager.Log("AI", $"❌ 실패 (에이전트: {agent.AgentName}): " + request.error, 0);
        }
    }

    // AI 서버로부터 받은 응답을 처리하는 함수 (에이전트별)
    private void ProcessResponse(string response, AgentController agent)
    {
        try
        {
            // JSON 응답을 객체로 변환
            AgentResponse agentResponse = JsonUtility.FromJson<AgentResponse>(response);
            LogManager.Log("AI", $"응답: {agentResponse}", 3);
            // 응답 유효성 검사
            if (agentResponse.status != "OK" || string.IsNullOrEmpty(agentResponse.data.action.action))
            {
                LogManager.Log("AI", $"Invalid response format or status is not OK (에이전트: {agent.AgentName})", 0);
                return;
            }
            Action action = agentResponse.data.action;
            // 현재 시간 가져오기 및 활동 지속 시간 설정
            TimeSpan currentTime = TimeManager.Instance.GetCurrentGameTime();
            TimeSpan duration = TimeSpan.FromMinutes(30); // 기본 30분으로 설정
            string location = action.details.location;
            if (!TileManager.Instance.GetLocationNames().Contains(location))
            {
                SendAgent(agent);
                return;
            }
            // 새로운 일정 아이템 생성
            ScheduleItem newScheduleItem = new ScheduleItem
            {
                ID = System.Guid.NewGuid().ToString(),
                ActionName = action.action,
                LocationName = location,
                TargetName = action.details.target,
                StartTime = currentTime,
                EndTime = currentTime.Add(duration),
                Priority = 1, // 최우선순위로 설정
                IsFlexible = true,
                IsCompleted = false,
                ActionDetails = JsonUtility.ToJson(action.details),
                Reason = action.reason
            };
            // 스케줄러에 새 일정 추가 (기존 일정은 자동으로 취소됨)
            bool success = agent.mScheduler.AddScheduleItem(newScheduleItem);
            // 일정 추가 결과 로깅
            if (!success)
            {
                LogManager.Log("AI", $"Failed to add schedule item: {newScheduleItem.ActionName} @ {newScheduleItem.LocationName} (에이전트: {agent.AgentName})", 0);
            }
            else
            {
                LogManager.Log("AI", $"Successfully added and started new Action: {newScheduleItem.ActionName} @ {newScheduleItem.LocationName} (에이전트: {agent.AgentName})", 2);
            }
        }
        catch (Exception ex)
        {
            LogManager.Log("AI", $"Error processing response (에이전트: {agent.AgentName}): {ex.Message}\n{ex.StackTrace}", 0);
        }
    }
} 