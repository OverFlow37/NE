using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System;

public class AIBridgeTest : MonoBehaviour
{
    [Header("에이전트 참조")]
    [SerializeField] private AgentController agentController;
    [SerializeField] private AgentScheduler agentScheduler;
    [SerializeField] private MovementController movementController;

    [Header("오브젝트 그룹 (인식 가능)")]
    [SerializeField]
    public List<ObjectGroup> visibleObjects = new List<ObjectGroup>();

    [Header("오브젝트 그룹 (상호작용 가능)")]
    [SerializeField]
    public List<ObjectGroup> interactableItems = new List<ObjectGroup>();

    [Header("UI")]
    public Button sendButton;

    private bool isRequesting = false;

    // ========== 데이터 구조 ==========
    [System.Serializable]
    public class AgentState
    {
        public int hunger;
        public int sleepiness;
        public int loneliness;
        public int stress;
        public int happiness;
    }

    [System.Serializable]
    public class ObjectGroup
    {
        public string location;
        public List<string> objects;
    }

    [System.Serializable]
    public class Agent
    {
        public string name;
        public AgentState state;
        public string location;
        public string personality;
        public ObjectGroup[] visible_objects;
        public ObjectGroup[] interactable_items;
        public string[] nearby_agents;
    }

    [System.Serializable]
    public class AgentRequest
    {
        public Agent agent;
    }

    [System.Serializable]
    public class ActionDetails
    {
        public string location;
        public string message;
        public string target;
        public string using_item;  // JSON의 "using"에 매핑
    }

    [System.Serializable]
    public class Action
    {
        public string action;
        public string agent;
        public ActionDetails details;
    }

    [System.Serializable]
    public class DataWrapper
    {
        public Action action;
    }

    [System.Serializable]
    public class AgentResponse
    {
        public DataWrapper data;
        public string status;
    }

    private void Awake()
    {
        // 컴포넌트 참조 가져오기
        if (agentController == null)
            agentController = GetComponent<AgentController>();
        if (agentScheduler == null)
            agentScheduler = GetComponent<AgentScheduler>();
        if (movementController == null)
            movementController = GetComponent<MovementController>();

        // 컴포넌트 유효성 검사
        if (agentController == null || agentScheduler == null || movementController == null)
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
        if (movementController != null)
        {
            movementController.OnDestinationReached += HandleDestinationReached;
        }
    }

    private void OnDestroy()
    {
        // 이벤트 구독 해제
        if (movementController != null)
        {
            movementController.OnDestinationReached -= HandleDestinationReached;
        }
    }

    private void HandleDestinationReached()
    {
        SendAgent();
    }

    public void SendAgent()
    {
        if (isRequesting)
        {
            Debug.LogWarning("요청 진행 중입니다. 기다려주세요.");
            return;
        }

        StartCoroutine(SendAgentData());
    }

    IEnumerator SendAgentData()
    {
        isRequesting = true;
        if (sendButton != null) sendButton.interactable = false;

        // 현재 에이전트의 상태 정보 수집 (1~10 사이의 랜덤값)
        System.Random random = new System.Random();
        AgentState currentState = new AgentState
        {
            hunger = random.Next(1, 11),
            sleepiness = random.Next(1, 11),
            loneliness = random.Next(1, 11),
            stress = random.Next(1, 11),
            happiness = random.Next(1, 11)
        };

        AgentRequest requestData = new AgentRequest
        {
            agent = new Agent
            {
                name = agentController.AgentName,
                state = currentState,
                location = string.IsNullOrEmpty(movementController.CurrentDestination) ? "Bedroom" : movementController.CurrentDestination,
                personality = "friendly, helpful", // TODO: 에이전트별 성격 구현 필요
                visible_objects = visibleObjects.ToArray(),
                interactable_items = interactableItems.ToArray(),
                nearby_agents = new string[] { } // TODO: 주변 에이전트 감지 구현 필요
            }
        };

        string jsonData = JsonUtility.ToJson(requestData, true);
        Debug.Log("보낼 JSON:\n" + jsonData);

        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:5000/action", "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        var stopwatch = new System.Diagnostics.Stopwatch();
        stopwatch.Start();

        yield return request.SendWebRequest();

        stopwatch.Stop();
        long elapsedMs = stopwatch.ElapsedMilliseconds;

        isRequesting = false;
        if (sendButton != null) sendButton.interactable = true;

        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("✅ 응답: " + request.downloadHandler.text);
            Debug.Log($"⏱️ 요청 소요 시간: {elapsedMs} ms");

            // 응답 처리
            ProcessResponse(request.downloadHandler.text);
        }
        else
        {
            Debug.LogError("❌ 실패: " + request.error);
        }
    }

    private void ProcessResponse(string response)
    {
        try
        {
            AgentResponse agentResponse = JsonUtility.FromJson<AgentResponse>(response);
            
            if (agentResponse.status != "OK" || agentResponse.data?.action == null)
            {
                Debug.LogError("Invalid response format or status is not OK");
                return;
            }

            Action action = agentResponse.data.action;
            
            // Get current time and calculate duration
            TimeSpan currentTime = agentScheduler.GetCurrentGameTime();
            TimeSpan duration = TimeSpan.FromMinutes(30); // 기본 30분으로 설정
            
            // Create schedule item with improved parameters
            AgentScheduler.ScheduleItem newScheduleItem = new AgentScheduler.ScheduleItem
            {
                Id = System.Guid.NewGuid().ToString(),
                ActivityName = action.action,
                LocationName = action.details.target,
                StartTime = currentTime,
                EndTime = currentTime.Add(duration),
                Priority = 1, // 최우선순위로 설정
                IsFlexible = true,
                IsCompleted = false,
                ActivityDetails = JsonUtility.ToJson(action.details)
            };

            // 새 일정 추가 (기존 일정은 자동으로 취소됨)
            bool success = agentScheduler.AddScheduleItem(newScheduleItem);
            
            if (!success)
            {
                Debug.LogError($"Failed to add schedule item: {newScheduleItem.ActivityName} @ {newScheduleItem.LocationName}");
            }
            else
            {
                Debug.Log($"Successfully added and started new activity: {newScheduleItem.ActivityName} @ {newScheduleItem.LocationName}");
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"Error processing response: {ex.Message}\n{ex.StackTrace}");
        }
    }
} 