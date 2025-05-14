using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using System;
using System.Linq;
using OhMAIGod.Agent;
using Unity.VisualScripting;
using OhMAIGod.Perceive;

// 관찰 정보 AI로 전송
// 임계치에 따라 반응 판단과 관찰 정보 전송으로 나뉨
// find로 시작할때 agentController에서 연결할것
public class AIBridge_Perceive : MonoBehaviour
{    
    // ========== AI에게 전송하는 데이터 구조체들 ==========
    // 에이전트가 인식할 수 있는 오브젝트 그룹 정의
    [System.Serializable]
    public struct ObjectGroup
    {
        public string location;        // 오브젝트가 있는 위치
        public List<string> interactables;   // 해당 위치의 오브젝트 목록
    }

    // AI에게 전송할 에이전트 정보 구조체
    [System.Serializable]
    public struct Agent
    {
        public string name;                         // 에이전트 이름
        public AgentNeeds state;                    // 에이전트의 욕구
        public string current_location;             // 현재 위치
        public string personality;                  // 성격 특성
        public TimeSpan time;                       // 요청 보낸 시각
        public ObjectGroup[] visible_interactables;       // 볼 수 있는 오브젝트들
        public PerceiveEvent perceive_event;         // 관찰 이벤트
    }

    // AI 서버에 보낼 요청 데이터 구조체
    [System.Serializable]
    public struct AgentRequest
    {
        public Agent agent;  // 에이전트 정보
    }

    private bool mIsRequesting = false;

    // ========== AI에게서 응답받을 데이터 구조체들 ==========
    [System.Serializable]
    public struct ResponseReactJudge
    {
        public bool success;
        public bool should_react;
        public int event_id;
    }


     // 싱글톤
    private static AIBridge_Perceive mInstance;
    
    public static AIBridge_Perceive Instance
    {
        get
        {
            if (mInstance == null)
            {
                GameObject obj = new GameObject("AIBridge");
                mInstance = obj.AddComponent<AIBridge_Perceive>();
                DontDestroyOnLoad(obj);
            }
            return mInstance;
        }
    }

        private void Awake()
    {
        // 싱글톤 인스턴스 설정
        if (mInstance != null && mInstance != this)
        {
            Destroy(gameObject);
            return;
        }

        mInstance = this;
        DontDestroyOnLoad(gameObject);
    }


    // Interactable 목록을 ObjectGroup 배열로 변환
    private ObjectGroup[] ConvertToObjectGroups(List<Interactable> _interactables)
    {
        // 위치별로 오브젝트들을 그룹화
        Dictionary<string, List<string>> locationGroups = new Dictionary<string, List<string>>();

        foreach (Interactable interactable in _interactables)
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
            interactables = group.Value
        }).ToArray();
    }
    
    // 관찰 이벤트 전송(응답없음)
    public void SendPerceiveEvent(AgentController _agent, PerceiveEvent _perceiveEvent)
    {
        LogManager.Log("AI", $"[AIBridge_Perceive] SendPerceiveEvent: {_perceiveEvent.event_type}, {_perceiveEvent.event_location}, {_perceiveEvent.event_description}", 3);
        // TODO: 관찰 이벤트 전송 엔드포인트 구현 후 주석 해제
        StartCoroutine(SendPerceiveEventData(_agent, _perceiveEvent));
    }

    IEnumerator SendPerceiveEventData(AgentController _agent, PerceiveEvent _perceiveEvent){
        mIsRequesting = true;

        // ---- 에이전트 정보 ----
        // 현재 에이전트의 상태 정보 가져오기
        AgentNeeds currentNeeds = _agent.AgnetNeeds;
        var movement = _agent.mMovement;
        var scheduler = _agent.mScheduler;

        // AI 서버에 보낼 요청 데이터 생성
        var visibleObjectGroups = ConvertToObjectGroups(_agent.mVisibleInteractables);

        // 에이전트의 현재 위치 가져오기 (CurrentAction이 null일 경우 대비)
        string agentLocation = "Unknown"; // 기본값
        Interactable agentInteractable = _agent.GetComponent<Interactable>();
        if (agentInteractable != null && !string.IsNullOrEmpty(agentInteractable.CurrentLocation))
        {
            agentLocation = agentInteractable.CurrentLocation;
        }
        else if (_agent.CurrentAction != null && !string.IsNullOrEmpty(_agent.CurrentAction.LocationName))
        {
            // CurrentAction이 있고 LocationName이 유효하면 해당 위치 사용
            agentLocation = _agent.CurrentAction.LocationName;
        }

        for (int i = 0; i < visibleObjectGroups.Length; i++)
        {
            //LogManager.Log("AI", $"[AIBridge_Perceive] ObjectGroup {i}: location={visibleObjectGroups[i].location}, objects=[{string.Join(",", visibleObjectGroups[i].objects)}]", 3);
        }

        AgentRequest requestData = new AgentRequest
        {
            agent = new Agent
            {
                name = _agent.AgentName,
                state = currentNeeds,
                current_location = agentLocation,
                personality = "friendly, helpful", // TODO: 에이전트별 성격 구현 필요
                time = TimeManager.Instance.GetCurrentGameTime(),
                visible_interactables = visibleObjectGroups,
                perceive_event = _perceiveEvent,          
            }
        };
        // ---- 이벤트 정보 ----
        // perceiveEvent를 JSON으로 변환
        string requestJson = JsonUtility.ToJson(requestData);
        LogManager.Log("AI", $"[AIBridge_Perceive] perceiveEvent JSON: {requestData}", 3);

        // HTTP 요청 설정 (임시 주소)
        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:5000/perceive", "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(requestJson);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        mIsRequesting = false;

        if (request.result == UnityWebRequest.Result.Success)
        {
            LogManager.Log("AI", $"✅ perceiveEvent 전송 성공: " + request.downloadHandler.text, 2);
        }
        else
        {
            LogManager.Log("AI", $"❌ perceiveEvent 전송 실패: " + request.error, 0);
        }
    }

    // 반응 판단 이벤트 전송(반환값 true, false)
    public void SendReactJudgeEvent(AgentController _agent, PerceiveEvent _perceiveEvent)
    {
        LogManager.Log("AI", $"[AIBridge_Perceive] SendReactJudgeEvent: {_perceiveEvent.event_type}, {_perceiveEvent.event_location}, {_perceiveEvent.event_description}", 3);
        // TODO: 관찰 이벤트 전송 엔드포인트 구현 후 주석 해제
        StartCoroutine(SendReactJudgeEventData(_agent, _perceiveEvent));
    }

    IEnumerator SendReactJudgeEventData(AgentController _agent, PerceiveEvent _perceiveEvent){
        mIsRequesting = true;

        // ---- 에이전트 정보 ----
        // 현재 에이전트의 상태 정보 가져오기
        AgentNeeds currentNeeds = _agent.AgnetNeeds;
        var movement = _agent.mMovement;
        var scheduler = _agent.mScheduler;

        // AI 서버에 보낼 요청 데이터 생성
        var visibleObjectGroups = ConvertToObjectGroups(_agent.mVisibleInteractables);

        // 에이전트의 현재 위치 가져오기 (CurrentAction이 null일 경우 대비)
        string agentLocation = "Unknown"; // 기본값
        Interactable agentInteractable = _agent.GetComponent<Interactable>();
        if (agentInteractable != null && !string.IsNullOrEmpty(agentInteractable.CurrentLocation))
        {
            agentLocation = agentInteractable.CurrentLocation;
        }
        else if (_agent.CurrentAction != null && !string.IsNullOrEmpty(_agent.CurrentAction.LocationName))
        {
            // CurrentAction이 있고 LocationName이 유효하면 해당 위치 사용
            agentLocation = _agent.CurrentAction.LocationName;
        }

        for (int i = 0; i < visibleObjectGroups.Length; i++)
        {
            //LogManager.Log("AI", $"[AIBridge_Perceive] ObjectGroup {i}: location={visibleObjectGroups[i].location}, objects=[{string.Join(",", visibleObjectGroups[i].objects)}]", 3);
        }

        AgentRequest requestData = new AgentRequest
        {
            agent = new Agent
            {
                name = _agent.AgentName,
                state = currentNeeds,
                current_location = agentLocation,
                personality = "friendly, helpful", // TODO: 에이전트별 성격 구현 필요
                time = TimeManager.Instance.GetCurrentGameTime(),
                visible_interactables = visibleObjectGroups,
                perceive_event = _perceiveEvent,          
            }
        };
        // ---- 이벤트 정보 ----
        // perceiveEvent를 JSON으로 변환
        string requestJson = JsonUtility.ToJson(requestData);
        LogManager.Log("AI", $"[AIBridge_Perceive] perceiveEvent JSON: {requestData}", 3);

        // HTTP 요청 설정 (임시 주소)
        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:5000/react", "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(requestJson);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        ResponseReactJudge response = JsonUtility.FromJson<ResponseReactJudge>(request.downloadHandler.text);
        Debug.Log(response.should_react);
        
        mIsRequesting = false;

        if (request.result == UnityWebRequest.Result.Success)
        {
            LogManager.Log("AI", $"✅ 반응 판단 응답받음: " + request.downloadHandler.text, 2);
        }
        else
        {
            LogManager.Log("AI", $"❌ 반응 행동 응답실패: " + request.error, 0);
        }

        // 반응 판단 결과 처리
        if(response.should_react){
            LogManager.Log("AI", "반응 판단 결과: 반응함", 2);           
        }
        else{
            LogManager.Log("AI", "반응 판단 결과: 반응하지 않음", 2);
        }
        _agent.ReactToResponse(response.should_react, _perceiveEvent);
    }

    // 반응 행동 이벤트 전송(반환값 true, false)
    public void SendReactActionEvent(AgentController _agent, PerceiveEvent _perceiveEvent)
    {
        LogManager.Log("AI", $"[AIBridge_Perceive] SendReactActionEvent: {_perceiveEvent.event_type}, {_perceiveEvent.event_location}, {_perceiveEvent.event_description}", 3);
        // TODO: 관찰 이벤트 전송 엔드포인트 구현 후 주석 해제
        StartCoroutine(SendReactActionEventData(_agent, _perceiveEvent));
    }

    IEnumerator SendReactActionEventData(AgentController _agent, PerceiveEvent _perceiveEvent){
        mIsRequesting = true;

        // ---- 에이전트 정보 ----
        // 현재 에이전트의 상태 정보 가져오기
        AgentNeeds currentNeeds = _agent.AgnetNeeds;
        var movement = _agent.mMovement;
        var scheduler = _agent.mScheduler;

        // AI 서버에 보낼 요청 데이터 생성
        var visibleObjectGroups = ConvertToObjectGroups(_agent.mVisibleInteractables);

        // 에이전트의 현재 위치 가져오기 (CurrentAction이 null일 경우 대비)
        string agentLocation = "Unknown"; // 기본값
        Interactable agentInteractable = _agent.GetComponent<Interactable>();
        if (agentInteractable != null && !string.IsNullOrEmpty(agentInteractable.CurrentLocation))
        {
            agentLocation = agentInteractable.CurrentLocation;
        }
        else if (_agent.CurrentAction != null && !string.IsNullOrEmpty(_agent.CurrentAction.LocationName))
        {
            // CurrentAction이 있고 LocationName이 유효하면 해당 위치 사용
            agentLocation = _agent.CurrentAction.LocationName;
        }

        for (int i = 0; i < visibleObjectGroups.Length; i++)
        {
            //LogManager.Log("AI", $"[AIBridge_Perceive] ObjectGroup {i}: location={visibleObjectGroups[i].location}, objects=[{string.Join(",", visibleObjectGroups[i].objects)}]", 3);
        }

        AgentRequest requestData = new AgentRequest
        {
            agent = new Agent
            {
                name = _agent.AgentName,
                state = currentNeeds,
                current_location = agentLocation,
                personality = "friendly, helpful", // TODO: 에이전트별 성격 구현 필요
                time = TimeManager.Instance.GetCurrentGameTime(),
                visible_interactables = visibleObjectGroups,
                perceive_event = _perceiveEvent,          
            }
        };
        // ---- 이벤트 정보 ----
        // perceiveEvent를 JSON으로 변환
        string requestJson = JsonUtility.ToJson(requestData);
        LogManager.Log("AI", $"[AIBridge_Perceive] perceiveEvent JSON: {requestData}", 3);

        // HTTP 요청 설정 (임시 주소)
        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:5000/make_reaction", "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(requestJson);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        mIsRequesting = false;

        if (request.result == UnityWebRequest.Result.Success)
        {
            LogManager.Log("AI", $"✅ 반응 행동 응답받음: " + request.downloadHandler.text, 2);
        }
        else
        {
            LogManager.Log("AI", $"❌ 반응 행동 응답실패: " + request.error, 0);
        }
    }

} 