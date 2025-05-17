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

    [System.Serializable]
    public struct ResponseActionData
    {
        public string action;
        public string target_location;
        public string target_object; // AI 프롬프트 혼동을 막기 위해 여기서만 object로 명명
        public string duration;
        public string thought;
        public string memory_id;
    }

    [System.Serializable]
    public struct ResponseActionRoot
    {
        public bool success;
        public ResponseActionData data;
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
                personality = _agent.mPersonality, // TODO: 에이전트별 성격 구현 필요
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
        if(_agent.mIsReactJudge || _agent.CurrentState == AgentState.WAITING_FOR_AI_RESPONSE) {
            LogManager.Log("AI", $"[AIBridge_Perceive] 이미 반응 판단 중입니다.", 2);
            return;
        }
        LogManager.Log("AI", $"[AIBridge_Perceive] SendReactJudgeEvent: {_perceiveEvent.event_type}, {_perceiveEvent.event_location}, {_perceiveEvent.event_description}", 3);
        _agent.mIsReactJudge = true;
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
                personality = _agent.mPersonality,
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
        if(_agent.CurrentState == AgentState.WAITING_FOR_AI_RESPONSE) {
            LogManager.Log("AI", $"[AIBridge_Perceive] 반응행동 응답 대기중입니다.", 2);
            return;
        }
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
                personality = _agent.mPersonality, // TODO: 에이전트별 성격 구현 필요
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
            _agent.AllowStateChange = true;
            ProcessResponseScheduleItem(request.downloadHandler.text, _agent);
        }
        else
        {
            LogManager.Log("AI", $"❌ 반응 행동 응답실패: " + request.error, 0);
        }
    }

    // AI 서버로부터 받은 응답을 처리하는 함수 (에이전트별)
    private void ProcessResponseScheduleItem(string _response, AgentController _agent)
    {
        try
        {
            // JSON 응답을 객체로 변환
            ResponseActionRoot responseRoot = JsonUtility.FromJson<ResponseActionRoot>(_response);
            LogManager.Log("AI", $"응답: {_response}", 3);
            // 응답 유효성 검사
            if (!responseRoot.success || string.IsNullOrEmpty(responseRoot.data.action))
            {
                LogManager.Log("AI", $"Invalid response format or success is false (에이전트: {_agent.AgentName})", 0);
                return;
            }
            ResponseActionData actionData = responseRoot.data;
            // 현재 시간 가져오기 및 활동 지속 시간 설정
            TimeSpan currentTime = TimeManager.Instance.GetCurrentGameTime();
            int durationMinutes = 30;
            //int.TryParse(details.duration, out durationMinutes);
            TimeSpan duration = TimeSpan.FromMinutes(durationMinutes);
            TimeSpan endTime = currentTime.Add(duration);
            // 새로운 일정 아이템 생성
            ScheduleItem newScheduleItem = new ScheduleItem
            (
                actionData.action,
                actionData.target_location.ToLower(),
                actionData.target_object,
                currentTime,
                endTime,
                1, 
                actionData.thought,
                actionData.memory_id
            );
            // 스케줄러에 새 일정 추가
            bool success = _agent.mScheduler.AddScheduleItem(newScheduleItem);
            // 일정 추가 결과 로깅
            if (!success)
            {
                LogManager.Log("AI", $"Failed to add schedule item: {newScheduleItem.ActionName} @ {newScheduleItem.LocationName} (에이전트: {_agent.AgentName})", 0);
            }
            else
            {
                LogManager.Log("AI", $"Successfully added and started new Action: {newScheduleItem.ActionName} @ {newScheduleItem.LocationName} (에이전트: {_agent.AgentName})", 2);
            }
        }
        catch (Exception ex)
        {
            LogManager.Log("AI", $"Error processing response (에이전트: {_agent.AgentName}): {ex.Message}\n{ex.StackTrace}", 0);
        }
    }

    public void SendFeedbackToAI(PerceiveFeedback _feedback){
        LogManager.Log("AI", $"[AIBridge_Perceive] SendFeedbackToAI: {_feedback}", 3);
        // TODO: 피드백 전송 엔드포인트 구현 후 주석 해제
        StartCoroutine(SendFeedbackToAIData(_feedback));
    }

    IEnumerator SendFeedbackToAIData(PerceiveFeedback _feedback){
        mIsRequesting = true;

        // ---- 피드백 정보 ----
        // feedback를 JSON으로 변환 후 agent로 감싸기
        string feedbackJson = JsonUtility.ToJson(_feedback);
        string requestJson = $"{{\"agent\":{feedbackJson}}}";
        LogManager.Log("AI", $"[AIBridge_Perceive] feedback JSON: {requestJson}", 3);

        // HTTP 요청 설정 (임시 주소)
        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:5000/simple_action_feedback", "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(requestJson);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        mIsRequesting = false;

        if (request.result == UnityWebRequest.Result.Success)
        {
            LogManager.Log("AI", $"✅ 피드백 전송 성공: " + request.downloadHandler.text, 2);
        }
        else
        {
            LogManager.Log("AI", $"❌ 피드백 전송 실패: " + request.error, 0);
        }
    }

    // 기억 리셋
    public void ResetMemoryAllAgent(){
        StartCoroutine(ResetMemoryAllAgentCoroutine());
    }

    IEnumerator ResetMemoryAllAgentCoroutine(){
        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:5000/data/clear", "POST");
        request.uploadHandler = new UploadHandlerRaw(new byte[0]);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            LogManager.Log("AI", $"✅ 기억 리셋 성공: " + request.downloadHandler.text, 2);
        }
        else
        {
            LogManager.Log("AI", $"❌ 기억 리셋 실패: " + request.error, 0);
        }
    }

} 