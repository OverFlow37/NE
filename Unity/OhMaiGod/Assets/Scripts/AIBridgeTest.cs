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
        public Agent[] agents;
    }

    [System.Serializable]
    public class AgentResponse
    {
        public string activity_name;
        public string location_name;
        public string start_time;
        public string end_time;
        public int priority;
        public bool is_flexible;
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

        // 현재 에이전트의 상태 정보 수집
        AgentState currentState = new AgentState
        {
            hunger = 5, // TODO: 실제 상태값 구현 필요
            sleepiness = 3,
            loneliness = 4,
            stress = 2,
            happiness = 6
        };

        AgentRequest requestData = new AgentRequest
        {
            agents = new Agent[]
            {
                new Agent
                {
                    name = agentController.AgentName,
                    state = currentState,
                    location = movementController.CurrentDestination,
                    personality = "friendly, helpful", // TODO: 에이전트별 성격 구현 필요
                    visible_objects = visibleObjects.ToArray(),
                    interactable_items = interactableItems.ToArray(),
                    nearby_agents = new string[] { } // TODO: 주변 에이전트 감지 구현 필요
                }
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
            
            // 시간 문자열을 TimeSpan으로 변환
            TimeSpan startTime = TimeSpan.Parse(agentResponse.start_time);
            TimeSpan endTime = TimeSpan.Parse(agentResponse.end_time);

            // 스케줄 아이템 생성
            AgentScheduler.ScheduleItem newScheduleItem = new AgentScheduler.ScheduleItem
            {
                Id = System.Guid.NewGuid().ToString(),
                ActivityName = agentResponse.activity_name,
                LocationName = agentResponse.location_name,
                StartTime = startTime,
                EndTime = endTime,
                Priority = agentResponse.priority,
                IsFlexible = agentResponse.is_flexible,
                IsCompleted = false
            };

            // 스케줄에 추가
            bool success = agentScheduler.AddScheduleItem(newScheduleItem);
            
            if (success)
            {
                Debug.Log($"새로운 스케줄 추가됨: {newScheduleItem.ActivityName} @ {newScheduleItem.LocationName}");
            }
            else
            {
                Debug.LogWarning("스케줄 추가 실패");
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"응답 처리 중 오류 발생: {e.Message}");
        }
    }
} 