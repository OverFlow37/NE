using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json;

public class AIBridge : MonoBehaviour
{
    private static AIBridge mInstance;

    // 싱글톤
    public static AIBridge Instance
    {
        get
        {
            if (mInstance == null)
            {
                GameObject go = new GameObject("AIBridge");
                mInstance = go.AddComponent<AIBridge>();
                DontDestroyOnLoad(go);
            }
            return mInstance;
        }
    }

    private void Awake()
    {
        if (mInstance == null)
        {
            mInstance = this;
            DontDestroyOnLoad(gameObject);
        }
        else if (mInstance != this)
        {
            Destroy(gameObject);
            return;
        }

        // 초기화
        InitializeRequestQueue();
    }

    public enum RequestType
    {
        GetSchedule,     // 일정 요청
        GetActionPlan,   // 행동 계획 요청
        ProcessEvent,    // 이벤트 처리 요청
        GetDialogue      // 대화 내용 요청
    }

    private class AIRequest
    {
        public RequestType Type;
        public string AgentId;
        public string Data;
        public float Timestamp;
        public Action<string> Callback;
    }

    // AI에 전송할 에이전트 상태 데이터
    [Serializable]
    public class AgentStateData
    {
        public string AgentId;
        public string AgentName;
        public string CurrentState;
        public string CurrentActivity;
        public string CurrentLocation;
        public string GameDate;
        public string GameTime;
        public List<MemoryData> RecentMemories;
    }

    // 메모리 데이터
    [Serializable]
    public class MemoryData
    {
        public string Description;
        public string Timestamp;
        public int Importance;
    }

    // AI로부터 받은 스케줄 데이터
    [Serializable]
    public class ScheduleData
    {
        public List<ScheduleItemData> Items;
    }

    // 스케줄 항목 데이터
    [Serializable]
    public class ScheduleItemData
    {
        public string Id;
        public string ActivityName;
        public string LocationName;
        public string StartTime;
        public string EndTime;
        public int Priority;
        public bool IsFlexible;
        public string ActivityDetails;
    }

    [Header("서버 설정")]
    [SerializeField] private string mApiUrl = "http://localhost:5000/api/agent"; // API 엔드포인트
    [SerializeField] private float mRequestInterval = 5.0f; // 요청 간격 (초)
    [SerializeField] private int mMaxQueueSize = 10; // 최대 큐 크기

    [Header("인증")]
    [SerializeField] private string mApiKey = ""; // API 키

    [Header("디버깅")]
    [SerializeField] private bool mUseLocalFallback = true; // 로컬 폴백 사용 여부
    [SerializeField] private bool mShowDebugInfo = true; // 디버그 정보 표시 여부

    // 요청 큐
    private Queue<AIRequest> mRequestQueue;
    private bool mIsProcessingQueue = false;

    // 등록된 에이전트
    private Dictionary<string, AgentController> mRegisteredAgents = new Dictionary<string, AgentController>();

    public void RegisterAgent(string _agentId, AgentController _controller)
    {
        if (!mRegisteredAgents.ContainsKey(_agentId))
        {
            mRegisteredAgents.Add(_agentId, _controller);
            
            if (mShowDebugInfo)
            {
                Debug.Log($"AIBridge: 에이전트 등록됨 - {_agentId} ({_controller.AgentName})");
            }
        }
    }

    public void UnregisterAgent(string _agentId)
    {
        if (mRegisteredAgents.ContainsKey(_agentId))
        {
            mRegisteredAgents.Remove(_agentId);
            
            if (mShowDebugInfo)
            {
                Debug.Log($"AIBridge: 에이전트 등록 해제됨 - {_agentId}");
            }
        }
    }

    public void RequestSchedule(string _agentId, Action<List<AgentScheduler.ScheduleItem>> _callback)
    {
        if (!mRegisteredAgents.ContainsKey(_agentId))
        {
            Debug.LogWarning($"AIBridge: 등록되지 않은 에이전트의 스케줄 요청 - {_agentId}");
            return;
        }
        
        // 에이전트 상태 데이터 수집
        AgentStateData stateData = CollectAgentState(_agentId);
        string jsonData = JsonConvert.SerializeObject(stateData);
        
        // 콜백 래핑
        Action<string> wrappedCallback = (response) => 
        {
            var scheduleItems = ParseScheduleResponse(response);
            _callback?.Invoke(scheduleItems);
        };
        
        // 요청 큐에 추가
        EnqueueRequest(new AIRequest
        {
            Type = RequestType.GetSchedule,
            AgentId = _agentId,
            Data = jsonData,
            Timestamp = Time.time,
            Callback = wrappedCallback
        });
    }

    public void RequestActionPlan(string _agentId, string _activityName, Action<string> _callback)
    {
        if (!mRegisteredAgents.ContainsKey(_agentId))
        {
            Debug.LogWarning($"AIBridge: 등록되지 않은 에이전트의 행동 계획 요청 - {_agentId}");
            return;
        }
        
        // 에이전트 상태와 활동 정보 결합
        AgentStateData stateData = CollectAgentState(_agentId);
        stateData.CurrentActivity = _activityName;
        string jsonData = JsonConvert.SerializeObject(stateData);
        
        // 요청 큐에 추가
        EnqueueRequest(new AIRequest
        {
            Type = RequestType.GetActionPlan,
            AgentId = _agentId,
            Data = jsonData,
            Timestamp = Time.time,
            Callback = _callback
        });
    }

    public void ProcessEvent(string _agentId, string _eventDescription, Action<string> _callback)
    {
        if (!mRegisteredAgents.ContainsKey(_agentId))
        {
            Debug.LogWarning($"AIBridge: 등록되지 않은 에이전트의 이벤트 처리 요청 - {_agentId}");
            return;
        }
        
        // 에이전트 상태와 이벤트 정보 결합
        var requestData = new Dictionary<string, object>
        {
            ["agentState"] = CollectAgentState(_agentId),
            ["eventDescription"] = _eventDescription
        };
        
        string jsonData = JsonConvert.SerializeObject(requestData);
        
        // 요청 큐에 추가
        EnqueueRequest(new AIRequest
        {
            Type = RequestType.ProcessEvent,
            AgentId = _agentId,
            Data = jsonData,
            Timestamp = Time.time,
            Callback = _callback
        });
    }

    public void RequestDialogue(string _agentId, string _targetAgentId, string _context, Action<string> _callback)
    {
        if (!mRegisteredAgents.ContainsKey(_agentId))
        {
            Debug.LogWarning($"AIBridge: 등록되지 않은 에이전트의 대화 요청 - {_agentId}");
            return;
        }
        
        // 두 에이전트 상태와 대화 컨텍스트 결합
        var requestData = new Dictionary<string, object>
        {
            ["speakerState"] = CollectAgentState(_agentId),
            ["listenerState"] = mRegisteredAgents.ContainsKey(_targetAgentId) 
                ? CollectAgentState(_targetAgentId) 
                : null,
            ["context"] = _context
        };
        
        string jsonData = JsonConvert.SerializeObject(requestData);
        
        // 요청 큐에 추가
        EnqueueRequest(new AIRequest
        {
            Type = RequestType.GetDialogue,
            AgentId = _agentId,
            Data = jsonData,
            Timestamp = Time.time,
            Callback = _callback
        });
    }

    private void InitializeRequestQueue()
    {
        mRequestQueue = new Queue<AIRequest>();
        mIsProcessingQueue = false;
    }

    private void EnqueueRequest(AIRequest _request)
    {
        // 큐 크기 제한 확인
        if (mRequestQueue.Count >= mMaxQueueSize)
        {
            Debug.LogWarning($"AIBridge: 요청 큐가 가득 참 (크기: {mRequestQueue.Count})");
            return;
        }
        
        // 요청 큐에 추가
        mRequestQueue.Enqueue(_request);
        
        if (mShowDebugInfo)
        {
            Debug.Log($"AIBridge: 요청 큐에 추가됨 - {_request.Type} for {_request.AgentId} (큐 크기: {mRequestQueue.Count})");
        }
        
        // 큐 처리 시작 (아직 처리 중이 아니면)
        if (!mIsProcessingQueue)
        {
            StartCoroutine(ProcessRequestQueue());
        }
    }

    private IEnumerator ProcessRequestQueue()
    {
        mIsProcessingQueue = true;
        
        while (mRequestQueue.Count > 0)
        {
            // 큐에서 다음 요청 가져오기
            AIRequest request = mRequestQueue.Dequeue();
            
            if (mShowDebugInfo)
            {
                Debug.Log($"AIBridge: 요청 처리 중 - {request.Type} for {request.AgentId}");
            }
            
            // 요청 처리
            yield return StartCoroutine(SendRequest(request));
            
            // 요청 간격 대기
            yield return new WaitForSeconds(mRequestInterval);
        }
        
        mIsProcessingQueue = false;
    }

    private IEnumerator SendRequest(AIRequest _request)
    {
        // API 엔드포인트 생성
        string endpoint = $"{mApiUrl}/{GetEndpointForRequestType(_request.Type)}";
        
        if (mUseLocalFallback)
        {
            // 로컬 폴백 사용 시
            string response = GenerateLocalFallbackResponse(_request);
            _request.Callback?.Invoke(response);
            yield break;
        }
        
        // UnityWebRequest 생성
        using (UnityWebRequest webRequest = new UnityWebRequest(endpoint, "POST"))
        {
            // 요청 데이터 설정
            byte[] jsonToSend = new UTF8Encoding().GetBytes(_request.Data);
            webRequest.uploadHandler = new UploadHandlerRaw(jsonToSend);
            webRequest.downloadHandler = new DownloadHandlerBuffer();
            webRequest.SetRequestHeader("Content-Type", "application/json");
            
            // API 키가 있으면 인증 헤더 추가
            if (!string.IsNullOrEmpty(mApiKey))
            {
                webRequest.SetRequestHeader("Authorization", $"Bearer {mApiKey}");
            }
            
            // 요청 전송
            yield return webRequest.SendWebRequest();
            
            // 응답 처리
            if (webRequest.result == UnityWebRequest.Result.Success)
            {
                string response = webRequest.downloadHandler.text;
                
                if (mShowDebugInfo)
                {
                    Debug.Log($"AIBridge: 응답 수신 완료 - {_request.Type} for {_request.AgentId}");
                }
                
                // 콜백 호출
                _request.Callback?.Invoke(response);
            }
            else
            {
                Debug.LogError($"AIBridge: 요청 실패 - {webRequest.error}\n" +
                               $"URL: {endpoint}\n" +
                               $"Request Type: {_request.Type}\n" +
                               $"Agent ID: {_request.AgentId}");
                
                // 오류 시 로컬 폴백 사용
                string fallbackResponse = GenerateLocalFallbackResponse(_request);
                _request.Callback?.Invoke(fallbackResponse);
            }
        }
    }

    private string GetEndpointForRequestType(RequestType _type)
    {
        switch (_type)
        {
            case RequestType.GetSchedule:
                return "schedule";
            case RequestType.GetActionPlan:
                return "action";
            case RequestType.ProcessEvent:
                return "event";
            case RequestType.GetDialogue:
                return "dialogue";
            default:
                return string.Empty;
        }
    }

    private AgentStateData CollectAgentState(string _agentId)
    {
        if (!mRegisteredAgents.TryGetValue(_agentId, out AgentController agent))
        {
            Debug.LogWarning($"AIBridge: 등록되지 않은 에이전트 상태 수집 시도 - {_agentId}");
            return new AgentStateData { AgentId = _agentId };
        }
        
        // 에이전트 컴포넌트 참조 가져오기
        AgentScheduler scheduler = agent.GetComponent<AgentScheduler>();
        
        // 상태 데이터 생성
        AgentStateData stateData = new AgentStateData
        {
            AgentId = _agentId,
            AgentName = agent.AgentName,
            CurrentState = agent.CurrentState.ToString(),
            CurrentActivity = scheduler != null ? scheduler.GetCurrentActivityName() : "Unknown",
            CurrentLocation = agent.GetComponent<MovementController>()?.CurrentDestination ?? "Unknown",
            GameDate = scheduler != null ? scheduler.GetCurrentGameDate().ToString("yyyy-MM-dd") : DateTime.Now.ToString("yyyy-MM-dd"),
            GameTime = scheduler != null ? scheduler.GetCurrentGameTime().ToString() : "00:00:00",
            RecentMemories = new List<MemoryData>() // TODO: 메모리 시스템 연동
        };
        
        return stateData;
    }

    private string GenerateLocalFallbackResponse(AIRequest _request)
    {
        switch (_request.Type)
        {
            case RequestType.GetSchedule:
                return GenerateDummySchedule(_request.AgentId);
                
            case RequestType.GetActionPlan:
                return "{ \"action\": \"NPC는 책상에 앉아 컴퓨터 작업을 하고 있습니다.\" }";
                
            case RequestType.ProcessEvent:
                return "{ \"reaction\": \"놀란 표정으로 주변을 둘러봅니다.\" }";
                
            case RequestType.GetDialogue:
                return "{ \"dialogue\": \"안녕하세요, 오늘 날씨가 정말 좋네요.\" }";
                
            default:
                return "{ \"error\": \"Unknown request type\" }";
        }
    }

    private string GenerateDummySchedule(string _agentId)
    {
        // 현재 시간 기준으로 더미 스케줄 생성 (에이전트 ID에 따라 다르게)
        int agentSeed = _agentId.GetHashCode(); // ID로부터 시드 생성
        System.Random random = new System.Random(agentSeed);
        
        List<ScheduleItemData> items = new List<ScheduleItemData>();
        
        // 아침 활동
        items.Add(new ScheduleItemData
        {
            Id = "morning_1",
            ActivityName = "아침 식사",
            LocationName = "Kitchen",
            StartTime = "08:00:00",
            EndTime = "08:30:00",
            Priority = 5,
            IsFlexible = false
        });
        
        // 업무 활동
        items.Add(new ScheduleItemData
        {
            Id = "work_1",
            ActivityName = "업무 처리",
            LocationName = "Desk",
            StartTime = "09:00:00",
            EndTime = "12:00:00",
            Priority = 8,
            IsFlexible = false
        });
        
        // 점심 활동
        items.Add(new ScheduleItemData
        {
            Id = "lunch",
            ActivityName = "점심 식사",
            LocationName = random.Next(2) == 0 ? "Kitchen" : "Cafeteria",
            StartTime = "12:00:00",
            EndTime = "13:00:00",
            Priority = 5,
            IsFlexible = true
        });
        
        // 오후 활동
        items.Add(new ScheduleItemData
        {
            Id = "afternoon_1",
            ActivityName = random.Next(3) == 0 ? "회의 참석" : "업무 처리",
            LocationName = random.Next(3) == 0 ? "MeetingRoom" : "Desk",
            StartTime = "13:00:00",
            EndTime = "17:00:00",
            Priority = 8,
            IsFlexible = false
        });
        
        // 저녁 활동
        items.Add(new ScheduleItemData
        {
            Id = "evening_1",
            ActivityName = "저녁 식사",
            LocationName = "Kitchen",
            StartTime = "18:00:00",
            EndTime = "19:00:00",
            Priority = 5,
            IsFlexible = true
        });
        
        // 휴식 활동
        items.Add(new ScheduleItemData
        {
            Id = "leisure",
            ActivityName = random.Next(3) == 0 ? "TV 시청" : (random.Next(2) == 0 ? "독서" : "휴식"),
            LocationName = "LivingRoom",
            StartTime = "19:30:00",
            EndTime = "21:30:00",
            Priority = 3,
            IsFlexible = true
        });
        
        // 취침 전 활동
        items.Add(new ScheduleItemData
        {
            Id = "bedtime",
            ActivityName = "취침 준비",
            LocationName = "Bedroom",
            StartTime = "22:00:00",
            EndTime = "23:00:00",
            Priority = 4,
            IsFlexible = true
        });
        
        // JSON 생성
        ScheduleData scheduleData = new ScheduleData { Items = items };
        return JsonConvert.SerializeObject(scheduleData);
    }

    private List<AgentScheduler.ScheduleItem> ParseScheduleResponse(string _response)
    {
        List<AgentScheduler.ScheduleItem> result = new List<AgentScheduler.ScheduleItem>();
        
        try
        {
            // JSON 파싱
            ScheduleData scheduleData = JsonConvert.DeserializeObject<ScheduleData>(_response);
            
            if (scheduleData == null || scheduleData.Items == null)
            {
                Debug.LogError($"AIBridge: 잘못된 스케줄 응답 - {_response}");
                return result;
            }
            
            // 각 항목 변환
            foreach (var item in scheduleData.Items)
            {
                try
                {
                    // 시간 파싱
                    TimeSpan startTime = TimeSpan.Parse(item.StartTime);
                    TimeSpan endTime = TimeSpan.Parse(item.EndTime);
                    
                    // 스케줄 항목 생성
                    AgentScheduler.ScheduleItem scheduleItem = new AgentScheduler.ScheduleItem
                    {
                        Id = item.Id,
                        ActivityName = item.ActivityName,
                        LocationName = item.LocationName,
                        StartTime = startTime,
                        EndTime = endTime,
                        Priority = item.Priority,
                        IsFlexible = item.IsFlexible,
                        ActivityDetails = item.ActivityDetails,
                        IsCompleted = false
                    };
                    
                    result.Add(scheduleItem);
                }
                catch (Exception ex)
                {
                    Debug.LogError($"AIBridge: 스케줄 항목 파싱 오류 - {ex.Message}");
                }
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"AIBridge: 스케줄 응답 파싱 오류 - {ex.Message}");
        }
        
        return result;
    }
}