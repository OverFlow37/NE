// using UnityEngine;
// using UnityEngine.Networking;
// using System.Collections;
// using System.Collections.Generic;
// using System.Text;
// using Newtonsoft.Json;
// using System;

// public class AIConnectionTest : MonoBehaviour
// {
//     [Header("서버 설정")]
//     [SerializeField] private string mServerUrl = "http://127.0.0.1:5000/action";
//     [SerializeField] private float mRequestInterval = 300f; // 요청 간격 (초)
//     [SerializeField] private bool mAutoRequest = true; // 자동 요청 여부
    
//     [Header("디버깅")]
//     [SerializeField] private bool mShowDebugInfo = true;
//     [SerializeField] private bool mTestRequest = false; // 인스펙터에서 테스트 요청을 위한 플래그
    
//     // 내부 참조
//     private AgentController mAgentController;
//     private AgentScheduler mScheduler;
//     private float mLastRequestTime = 0f;
//     private bool mIsRequesting = false;
    
//     // ========== 데이터 구조 ==========
//     [System.Serializable]
//     public class AgentState
//     {
//         public int hunger;
//         public int sleepiness;
//         public int loneliness;
//         public int stress;
//         public int happiness;
//     }

//     [System.Serializable]
//     public class ObjectGroup
//     {
//         public string location;
//         public List<string> objects;
//     }

//     [System.Serializable]
//     public class Agent
//     {
//         public string name;
//         public AgentState state;
//         public string location;
//         public string personality;
//         public ObjectGroup[] visible_objects;
//         public ObjectGroup[] interactable_items;
//         public string[] nearby_agents;
//     }

//     [System.Serializable]
//     public class AgentRequest
//     {
//         public Agent[] agents;
//     }
    
//     // 서버 응답을 위한 데이터 구조
//     [System.Serializable]
//     public class ActionResponse
//     {
//         public string agent_name;
//         public string action;
//         public string location;
//         public string target_object;
//         public string start_time;
//         public string end_time;
//         public int priority;
//         public bool is_flexible;
//     }
    
//     [System.Serializable]
//     public class ServerResponse
//     {
//         public ActionResponse[] actions;
//     }
    
//     private void Awake()
//     {
//         // 필요한 컴포넌트 참조 가져오기
//         mAgentController = GetComponent<AgentController>();
//         if (mAgentController == null)
//         {
//             Debug.LogError("AgentController 컴포넌트를 찾을 수 없습니다.");
//             enabled = false;
//             return;
//         }
        
//         mScheduler = GetComponent<AgentScheduler>();
//         if (mScheduler == null)
//         {
//             Debug.LogError("AgentScheduler 컴포넌트를 찾을 수 없습니다.");
//             enabled = false;
//             return;
//         }
//     }
    
//     private void Start()
//     {
//         if (mAutoRequest)
//         {
//             // 게임 시작 시 첫 요청 수행
//             StartCoroutine(RequestAgentActions());
//         }
//     }
    
//     private void Update()
//     {
//         // 디버그용 테스트 요청
//         if (mTestRequest)
//         {
//             mTestRequest = false;
//             if (!mIsRequesting)
//             {
//                 StartCoroutine(RequestAgentActions());
//             }
//             else
//             {
//                 Debug.LogWarning("이미 요청 진행 중입니다.");
//             }
//         }
        
//         // 자동 요청 모드에서 주기적으로 요청
//         if (mAutoRequest && !mIsRequesting && Time.time - mLastRequestTime >= mRequestInterval)
//         {
//             StartCoroutine(RequestAgentActions());
//         }
//     }
    
//     // AI 서버에 행동 요청 코루틴
//     private IEnumerator RequestAgentActions()
//     {
//         mIsRequesting = true;
        
//         if (mShowDebugInfo)
//         {
//             Debug.Log($"[{mAgentController.AgentName}] AI 서버에 행동 요청 시작");
//         }
        
//         // 에이전트 정보 수집
//         AgentRequest requestData = GatherAgentData();
        
//         // JSON으로 변환
//         string jsonData = JsonConvert.SerializeObject(requestData, Formatting.Indented);
        
//         if (mShowDebugInfo)
//         {
//             Debug.Log($"요청 데이터:\n{jsonData}");
//         }
        
//         // HTTP 요청 설정
//         UnityWebRequest request = new UnityWebRequest(mServerUrl, "POST");
//         byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
//         request.uploadHandler = new UploadHandlerRaw(bodyRaw);
//         request.downloadHandler = new DownloadHandlerBuffer();
//         request.SetRequestHeader("Content-Type", "application/json");
        
//         var stopwatch = new System.Diagnostics.Stopwatch();
//         stopwatch.Start();
        
//         // 요청 전송
//         yield return request.SendWebRequest();
        
//         stopwatch.Stop();
//         mLastRequestTime = Time.time;
        
//         if (request.result == UnityWebRequest.Result.Success)
//         {
//             if (mShowDebugInfo)
//             {
//                 Debug.Log($"응답 성공 (소요시간: {stopwatch.ElapsedMilliseconds}ms):\n{request.downloadHandler.text}");
//             }
            
//             // 응답 처리
//             ProcessResponse(request.downloadHandler.text);
//         }
//         else
//         {
//             Debug.LogError($"요청 실패: {request.error}");
//         }
        
//         mIsRequesting = false;
//     }
    
//     // 에이전트 데이터 수집
//     private AgentRequest GatherAgentData()
//     {
//         // 에이전트 상태 설정 (기본값 설정, 실제로는 AgentController에서 상태를 가져오도록 구현)
//         AgentState state = new AgentState
//         {
//             hunger = 5,
//             sleepiness = 3,
//             loneliness = 4,
//             stress = 2,
//             happiness = 6
//         };
        
//         // 현재 위치 가져오기
//         string currentLocation = mAgentController.GetCurrentLocationName();
//         if (string.IsNullOrEmpty(currentLocation))
//         {
//             currentLocation = "Unknown";
//         }
        
//         // 가시 오브젝트 및 상호작용 가능 오브젝트 수집 (예시)
//         List<ObjectGroup> visibleObjects = GetVisibleObjects();
//         List<ObjectGroup> interactableItems = GetInteractableItems();
        
//         // 근처 에이전트 수집 (예시)
//         string[] nearbyAgents = GetNearbyAgents();
        
//         // 에이전트 데이터 구성
//         Agent agent = new Agent
//         {
//             name = mAgentController.AgentName,
//             state = state,
//             location = currentLocation,
//             personality = mAgentController.GetPersonality(),
//             visible_objects = visibleObjects.ToArray(),
//             interactable_items = interactableItems.ToArray(),
//             nearby_agents = nearbyAgents
//         };
        
//         return new AgentRequest
//         {
//             agents = new Agent[] { agent }
//         };
//     }
    
//     // 서버 응답 처리
//     private void ProcessResponse(string jsonResponse)
//     {
//         try
//         {
//             // JSON 응답 파싱
//             ServerResponse response = JsonConvert.DeserializeObject<ServerResponse>(jsonResponse);
            
//             if (response == null || response.actions == null || response.actions.Length == 0)
//             {
//                 Debug.LogWarning("응답에 유효한 행동이 없습니다.");
//                 return;
//             }
            
//             // 기존 스케줄 지우기 (필요에 따라 조정)
//             if (mScheduler.HasCurrentActivity())
//             {
//                 // 현재 진행 중인 활동이 있으면 유지
//                 mScheduler.ClearFutureSchedule();
//             }
//             else
//             {
//                 // 현재 진행 중인 활동이 없으면 모두 지우기
//                 mScheduler.ClearSchedule();
//             }
            
//             // 응답의 각 행동을 일정에 추가
//             foreach (ActionResponse action in response.actions)
//             {
//                 AddActionToSchedule(action);
//             }
            
//             if (mShowDebugInfo)
//             {
//                 Debug.Log($"[{mAgentController.AgentName}] 일정 업데이트 완료. {response.actions.Length}개의 행동이 추가됨.");
//             }
//         }
//         catch (Exception ex)
//         {
//             Debug.LogError($"응답 처리 중 오류 발생: {ex.Message}\n{ex.StackTrace}");
//         }
//     }
    
//     // 행동을 일정에 추가
//     private void AddActionToSchedule(ActionResponse action)
//     {
//         // 활동 이름 생성
//         string activityName = !string.IsNullOrEmpty(action.target_object)
//             ? $"{action.action} ({action.target_object})"
//             : action.action;
        
//         // 시간 처리
//         TimeSpan startTime;
//         TimeSpan endTime;
        
//         // 시간이 지정되지 않은 경우 현재 시간 기준으로 설정
//         if (string.IsNullOrEmpty(action.start_time) || string.IsNullOrEmpty(action.end_time))
//         {
//             TimeSpan currentTime = mScheduler.GetCurrentGameTime();
//             startTime = currentTime;
            
//             // 기본 활동 시간은 15분으로 설정
//             endTime = currentTime.Add(TimeSpan.FromMinutes(15));
//         }
//         else
//         {
//             // 지정된 시간 파싱
//             startTime = ParseTimeInput(action.start_time);
//             endTime = ParseTimeInput(action.end_time);
//         }
        
//         // 스케줄 아이템 생성
//         AgentScheduler.ScheduleItem item = new AgentScheduler.ScheduleItem
//         {
//             Id = $"ai_{Guid.NewGuid().ToString().Substring(0, 8)}",
//             ActivityName = activityName,
//             LocationName = action.location,
//             StartTime = startTime,
//             EndTime = endTime,
//             Priority = action.priority,
//             IsFlexible = action.is_flexible,
//             ActivityDetails = JsonConvert.SerializeObject(action)
//         };
        
//         // 스케줄에 추가
//         bool success = mScheduler.AddScheduleItem(item);
        
//         if (mShowDebugInfo)
//         {
//             if (success)
//             {
//                 Debug.Log($"일정 추가됨: {activityName} @ {action.location} ({startTime}-{endTime})");
//             }
//             else
//             {
//                 Debug.LogWarning($"일정 추가 실패: {activityName} @ {action.location}. 기존 일정과 충돌이 있을 수 있습니다.");
//             }
//         }
//     }
    
//     // 시간 문자열 파싱 (시:분 또는 시:분:초 형식)
//     private TimeSpan ParseTimeInput(string timeString)
//     {
//         // 시:분 형식 확인
//         if (timeString.Split(':').Length == 2)
//         {
//             timeString += ":00"; // 초 추가
//         }
        
//         return TimeSpan.Parse(timeString);
//     }
    
//     // 시뮬레이션을 위한 가시 오브젝트 수집 (실제 구현 필요)
//     private List<ObjectGroup> GetVisibleObjects()
//     {
//         // 여기에 실제 구현 필요
//         // 에이전트의 시야 범위 내의 오브젝트를 수집
        
//         List<ObjectGroup> visibleObjects = new List<ObjectGroup>();
        
//         // 예시: 현재 위치에 있는 가시 오브젝트 추가
//         string currentLocation = mAgentController.GetCurrentLocationName();
//         if (!string.IsNullOrEmpty(currentLocation))
//         {
//             // 예시 데이터
//             ObjectGroup group = new ObjectGroup
//             {
//                 location = currentLocation,
//                 objects = new List<string> { "Table", "Chair", "Window" }
//             };
            
//             visibleObjects.Add(group);
//         }
        
//         return visibleObjects;
//     }
    
//     // 시뮬레이션을 위한 상호작용 가능 오브젝트 수집 (실제 구현 필요)
//     private List<ObjectGroup> GetInteractableItems()
//     {
//         // 여기에 실제 구현 필요
//         // 에이전트가 상호작용할 수 있는 오브젝트를 수집
        
//         List<ObjectGroup> interactableItems = new List<ObjectGroup>();
        
//         // 예시: 현재 위치에 있는 상호작용 가능 오브젝트 추가
//         string currentLocation = mAgentController.GetCurrentLocationName();
//         if (!string.IsNullOrEmpty(currentLocation))
//         {
//             // 예시 데이터
//             ObjectGroup group = new ObjectGroup
//             {
//                 location = currentLocation,
//                 objects = new List<string> { "Computer", "Book", "Coffee Machine" }
//             };
            
//             interactableItems.Add(group);
//         }
        
//         return interactableItems;
//     }
    
//     // 시뮬레이션을 위한 근처 에이전트 수집 (실제 구현 필요)
//     private string[] GetNearbyAgents()
//     {
//         // 여기에 실제 구현 필요
//         // 에이전트 주변의 다른 에이전트를 수집
        
//         // 예시 데이터
//         return new string[] { "Agent2", "Agent3" };
//     }
    
//     // 테스트 요청 명령 (인스펙터에서 사용)
//     [ContextMenu("테스트 요청 보내기")]
//     public void SendTestRequest()
//     {
//         if (!mIsRequesting)
//         {
//             StartCoroutine(RequestAgentActions());
//         }
//         else
//         {
//             Debug.LogWarning("이미 요청 진행 중입니다.");
//         }
//     }
// }