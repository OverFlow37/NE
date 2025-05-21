using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Linq;

using OhMAIGod.Agent;
using OhMAIGod.Perceive;
public class AgentController : MonoBehaviour, ISaveable
{
    [SerializeField] public AgentUI mAgentUI;
    [SerializeField] private AgentVision agentVision;  // AgentVision 컴포넌트 참조 추가

    [Header("Agent States")]
    [SerializeField] private AgentNeeds mAgentNeeds;                // 현재 Agent의 욕구 수치
    
    // Needs 수정을 위한 메서드들
    public void ModifyNeed(AgentNeedsType _needType, int _amount)
    {
        switch (_needType)
        {
            case AgentNeedsType.Hunger:
                mAgentNeeds.Hunger = Mathf.Clamp(mAgentNeeds.Hunger + _amount, -100, 100);
                break;
            
            case AgentNeedsType.Sleepiness:
                mAgentNeeds.Sleepiness = Mathf.Clamp(mAgentNeeds.Sleepiness + _amount, -100, 100);
                break;
            
            case AgentNeedsType.Loneliness:
                mAgentNeeds.Loneliness = Mathf.Clamp(mAgentNeeds.Loneliness + _amount, -100, 100);
                break;
            
            case AgentNeedsType.Stress:
                mAgentNeeds.Stress = Mathf.Clamp(mAgentNeeds.Stress + _amount, -100, 100);
                break;
        }
    }

    [Header("Base Profile")]
    [SerializeField] private int mID;                               // 에이전트 고유 식별자
    [SerializeField] private string mName;                          // 이름
    [SerializeField] private string mDescription;                   // 초기 설명
    [SerializeField] public string mPersonality;                    // 성격
    [SerializeField] private float mVisualRange;                    // 시야 범위
    [SerializeField] private Transform mSpawnPoint;                 // 스폰 위치
    [SerializeField] private bool mAutoStart = true;                // 자동 시작 여부
    [SerializeField] [Tooltip("감정 상태 자동 증가 간격 (분)")] private int mNeedIntervalMinutes = 30;
    private TimeSpan mLastNeedsIncreaseTime; // 마지막 감정 상태 자동 증가 시각

    [Header("디버깅")]
    [SerializeField] private bool mShowDebugInfo = true;            // 디버그 정보 표시 여부
    [SerializeField, ReadOnly] private AgentState mCurrentState; // 현재 상태 Inspector 디버그용
    [SerializeField, ReadOnly] private string mCurrentLocation = "house";  // 현재 위치 Inspector 디버그용
    [SerializeField, ReadOnly] private Interactable mCurrentTargetInteractable;    // 현재 타겟 Inspector 디버그용
    private ScheduleItem mCurrentAction = null;                     // 현재 활동 정보
    private float mWaitTime = 0f;                                   // 대기 시간 (다음 활동까지)

    public AgentState CurrentState => mStateMachine.CurrentStateType;       // 에이전트 현재 상태
    public string AgentName => mName;                                       // 에이전트 이름
    public int AgentID => mID;                                              // 에이전트 ID
    public AgentNeeds AgnetNeeds => mAgentNeeds;
    public ScheduleItem CurrentAction => mCurrentAction;
    public string CurrentLocation => mCurrentLocation;
    public Interactable CurrentTargetInteractable => mCurrentTargetInteractable;
    public bool AllowStateChange {get {return mStateMachine.AllowStateChange;} set {mStateMachine.AllowStateChange = value;}}
    
    public Animator animator;  // 애니메이터
    // AIBridge에서 Agent만 가져오면 나머지도 가져올 수 있게 public으로 변경
    [SerializeField] public AgentScheduler mScheduler;
    [SerializeField] public MovementController mMovement;
    [SerializeField] public Interactable mInteractable;
    private AgentStateMachine mStateMachine;

    // 시야 내의 오브젝트 목록
    public List<Interactable> mVisibleInteractables = new List<Interactable>();

    private Coroutine mInteractionCoroutine;
    public float mInteractionProgress = 0f; // 상호작용 진행도(0~1)

    public bool mIsReactJudge = false;

    public TimeSpan mWaitTIme;

    public bool isSuccessForFeedback = false;
    public string mActionNameForFeedback = ""; // 피드백 디버그용
    public string mCurrentMemoryID = "";
    public PerceiveFeedback mCurrentFeedback; // 현재 체크 중인 피드백
    private int mInteractCountForFeedback = 0; // 상호작용 발생 횟수

    private Interactable mInteractableAgentSelf;

    public string mPreviousAction = ""; // 직전에 한 행동 기록

    private void Awake()
    {
        // 참조 가져오기
        if (mScheduler == null)
            mScheduler = GetComponent<AgentScheduler>();
            
        if (mMovement == null)
            mMovement = GetComponent<MovementController>();

        if (agentVision == null)
            agentVision = GetComponent<AgentVision>();

        // MovementController의 목적지 도착 이벤트 구독
        if (mMovement != null)
        {
            mMovement.OnDestinationReached += HandleDestinationReached;
            mMovement.OnMovementBlocked += HandleMovementBlocked;
        }

        // AgentVision의 이벤트 구독
        if (agentVision != null)
        {
            agentVision.OnVisionChanged += HandleVisionChanged;
            // 초기 시야 범위 내 오브젝트들 추가
            var initialInteractables = agentVision.GetVisibleInteractables();
            if (initialInteractables != null)
            {
                mVisibleInteractables.AddRange(initialInteractables);
            }
        }

        // 감정 상태 초기화
        mAgentNeeds.Hunger = 0;
        mAgentNeeds.Sleepiness = 0;
        mAgentNeeds.Loneliness = 0;
        mAgentNeeds.Stress = 0;

        // 감정 상태 자동 증가 시간 초기화 (분 단위까지만 저장)
        mLastNeedsIncreaseTime = new TimeSpan(7, 0, 0);

        // 애니메이션 참조
        animator = GetComponent<Animator>();

        // FSM 초기화
        mStateMachine = new AgentStateMachine(this);
        mCurrentState = CurrentState;

        // 자신의 Interactable 컴포넌트 구독
        mInteractable = GetComponent<Interactable>();
        if (mInteractable != null)
        {
            mInteractable.OnLocationChanged += HandleMyLocationChanged;
        }
        // 대기시간 초기화
        mWaitTIme = TimeManager.Instance.GetCurrentGameTime();

        mInteractableAgentSelf = GetComponent<Interactable>();
        mInteractableAgentSelf.mInteractableData.mName = mName;

        // 데일리 일정 가져와서 적용
        mScheduler.ApplyDailySchedule();
    }

    private void OnDestroy()
    {
        // 이벤트 구독 해제
        if (mMovement != null)
        {
            mMovement.OnDestinationReached -= HandleDestinationReached;
            mMovement.OnMovementBlocked -= HandleMovementBlocked;
        }

        if (agentVision != null)
        {
            agentVision.OnVisionChanged -= HandleVisionChanged;
        }

        // 자신의 Interactable 위치 변경 이벤트 구독 해제
        if (mInteractable != null)
        {
            mInteractable.OnLocationChanged -= HandleMyLocationChanged;
        }
    }

    // AgentNeeds를 JSON 파일로 저장
    public void SaveData(string _savePath)
    {
        // AgentNeeds를 JSON 문자열로 변환
        string json = JsonUtility.ToJson(mAgentNeeds);
        // 저장 경로 설정 (persistentDataPath/Agent.json)
        string path = System.IO.Path.Combine(_savePath, "agent.json");
        try
        {
            System.IO.File.WriteAllText(path, json);
            LogManager.Log("Agent", $"AgentNeeds가 {path}에 저장되었습니다.", 2);
        }
        catch (System.Exception e)
        {
            LogManager.Log("Agent", $"AgentNeeds 저장 실패: {e.Message}", 0);
        }
    }

    // AgentNeeds를 JSON 파일에서 불러오기
    public void LoadData(string _loadPath)
    {
        string path = System.IO.Path.Combine(_loadPath, "agent.json");
        if (!System.IO.File.Exists(path)) return;
        
        try
        {
            string json = System.IO.File.ReadAllText(path);
            var loadedNeeds = JsonUtility.FromJson<OhMAIGod.Agent.AgentNeeds>(json);
            // 각 필드를 명시적으로 할당하여 Inspector에도 즉시 반영되도록 함
            mAgentNeeds.Hunger = loadedNeeds.Hunger;
            mAgentNeeds.Sleepiness = loadedNeeds.Sleepiness;
            mAgentNeeds.Loneliness = loadedNeeds.Loneliness;
            mAgentNeeds.Stress = loadedNeeds.Stress;
            LogManager.Log("Agent", $"AgentNeeds가 {path}에서 불러와졌습니다.", 2);
        }
        catch (System.Exception e)
        {
            LogManager.Log("Agent", $"AgentNeeds 불러오기 실패: {e.Message}", 0);
        }
    }

    // 목적지(오브젝트만) 도착 이벤트 발생 시 호출되는 함수
    // 애니메이션 업데이트, Status 업데이트, 활동 시작
    // movementController의 이벤트로 호출
    private void HandleDestinationReached()
    {
        if (mShowDebugInfo)
        {
            LogManager.Log("Agent", $"{mName}: 목적지 도착 - {mCurrentAction.TargetName}", 2);
        }

        // 이동 애니메이션 정지
        //animator.SetBool("isMoving", false);
        if (mStateMachine.CurrentStateType == AgentState.MOVING_TO_LOCATION)
            mStateMachine.ChangeState(AgentState.MOVING_TO_INTERACTABLE); // 상태 INTERACTION으로 전환
        else if (mStateMachine.CurrentStateType == AgentState.MOVING_TO_INTERACTABLE)
            mStateMachine.ChangeState(AgentState.INTERACTING); // 상태 INTERACTION으로 전환
    }

    // 이동 불가능 이벤트 핸들러
    private void HandleMovementBlocked()
    {
        // 현재 상태에 따라 처리 (기본적으로 WAIT 상태로 전환)
        switch (CurrentState)
        {
            case AgentState.MOVING_TO_LOCATION:
                // TODO: 로케이션으로 이동할 수 없는 경우 반응
                LogManager.Log("Agent", $"{mName}: 로케이션으로 이동할 수 없습니다.", 1);
                ChangeState(AgentState.WAITING);
                break;
            case AgentState.MOVING_TO_INTERACTABLE:
                ChangeState(AgentState.WAITING);
                FindMovableInteractable(TileManager.Instance.GetTileController(mCurrentAction.LocationName));
                if (mCurrentTargetInteractable == null)
                {
                    // TODO: 이동 가능한 새로운 오브젝트를 찾을 수 없을 때
                    LogManager.Log("Agent", $"{mName}: 이동 가능한 오브젝트를 찾을 수 없습니다.", 1);
                    ChangeState(AgentState.WAITING);
                }
                else
                {
                    ChangeState(AgentState.MOVING_TO_INTERACTABLE);  // 이동 재개
                }
                break;
            default:
                // TODO: 기타 이동 불가능 상황 반응
                ChangeState(AgentState.WAITING);
                break;
        }
    }

    // 시야 범위 변경 이벤트 처리
    private void HandleVisionChanged(Interactable _interactable, bool _entered)
    {
        if (_entered)
        {
            if (!mVisibleInteractables.Contains(_interactable))
            {
                mVisibleInteractables.Add(_interactable);
                if (mShowDebugInfo)
                {
                    LogManager.Log("Agent", $"{mName}이(가) {_interactable.name}을(를) 발견했습니다.", 2);
                }
            }
        }
        else
        {
            mVisibleInteractables.Remove(_interactable);
            if (mShowDebugInfo)
            {
                LogManager.Log("Agent", $"{mName}이(가) {_interactable.name}을(를) 시야에서 놓쳤습니다.", 2);
            }
        }
    }

    // 자신의 Interactable 위치 변경 이벤트 핸들러
    // Interactable의 이벤트를 구독하여 위치 변경 시 호출
    private void HandleMyLocationChanged(Interactable _interactable, string _newLocation)
    {
        if (mCurrentLocation == _newLocation) return;
        if (_newLocation == null || _newLocation == "") return; // 중복 호출 방지
        LogManager.Log("Agent", $"{mName}: 위치 변경 - {_interactable.name} -> {_newLocation}", 2);

        mCurrentLocation = _newLocation;
        
        SendCurrentLocationInfo(_newLocation);
        // mCurrentAction이 null이 아니고, 새로운 위치가 목표 위치와 같으면 상태 전환
        if (mCurrentAction != null && _newLocation == mCurrentAction.LocationName)
        {
            ChangeState(AgentState.MOVING_TO_INTERACTABLE);
        }
    }

    private void Start()
    {
        if (mAutoStart)
        {
            mStateMachine.Initialize(AgentState.WAITING);
        }

        if(mSpawnPoint == null)
        {
            mSpawnPoint = GameObject.FindWithTag("Respawn").GetComponent<Transform>();
            if(mSpawnPoint != null) transform.position = mSpawnPoint.position;
        }

        LoadData(SaveLoadManager.Instance.SavePath);
    }

    private void Update()
    {
        // 상태 머신 업데이트 호출
        mStateMachine.ProcessStateUpdate();

        // 상태 자동 증가 함수 호출
        AutoIncreaseAgentNeeds();
    }

    // 상태 전환 메서드
    public void ChangeState(AgentState _newState)
    {
        mStateMachine.ChangeState(_newState);
        mCurrentState = CurrentState;
    }

    // 새 활동 시작 (AgentScheduler에서 호출)
    public void StartAction(ScheduleItem _action)
    {
        if (_action == null)
        {
            LogManager.Log("Agent", $"{mName}: 잘못된 활동 정보 받음", 1);
            return;
        }
        if (mShowDebugInfo)
        {
            LogManager.Log("Agent", $"{mName}: 새 활동 수신 - {_action.ActionName} @ {_action.LocationName}", 2);
        }
        if (mCurrentAction != null && mStateMachine.CurrentStateType == AgentState.INTERACTING)
        {
            CompleteAction();
        }
        mActionNameForFeedback = _action.ActionName;
        InitFeedback();
        mCurrentAction = _action;
        mCurrentMemoryID = _action.memory_id;
        isSuccessForFeedback = false;
        mPreviousAction = $"{_action.ActionName} {_action.TargetName} at {_action.LocationName}";

        // 현재 위치와 목표 위치가 다르면 MOVE_TO_LOCATION 상태로 전환
        if (mCurrentAction.LocationName != null && mCurrentAction.LocationName != mInteractable.CurrentLocation)
        {
            ChangeState(AgentState.MOVING_TO_LOCATION);
        }

        // 현재 위치와 목표 위치가 같으면 오브젝트로 이동
        if (mCurrentAction.LocationName != null && mCurrentAction.LocationName == mInteractable.CurrentLocation)
        {
            ChangeState(AgentState.MOVING_TO_INTERACTABLE);
        }

        // 속마음 표시
        if (mCurrentAction != null)
        {
            mAgentUI.ShowThoughtInfo(mCurrentAction.Thought);
        }
    }

    // 활동 위치로 이동 시작
    public void StartMovingToAction()
    {
        if (mCurrentAction == null)
        {
            mCurrentAction = mScheduler.CurrentAction;

            if (string.IsNullOrEmpty(mCurrentAction.LocationName) || string.IsNullOrEmpty(mCurrentAction.TargetName))
            {
                if (mShowDebugInfo)
                {
                    LogManager.Log("Agent", $"{mName}: 이동할 목적지 또는 타겟이 없음", 1);
                }
                return;
            }
        }

        // 이동 시작
        TileController tileController = TileManager.Instance.GetTileController(mCurrentAction.LocationName);
        if (tileController == null)
        {
            // TODO: 잘못된 로케이션으로 가려고 할 때
            LogManager.Log("Agent", $"{mName}: {mCurrentAction.LocationName} 타일 컨트롤러를 찾을 수 없습니다.", 1);
            ChangeState(AgentState.WAITING);
            return;
        }

        switch (CurrentState)
        {
            case AgentState.MOVING_TO_LOCATION:
                Vector2 availablePosition = tileController.AvailablePosition;
                if (availablePosition != Vector2.zero)
                {
                    LogManager.Log("Agent", $"{mName}: {mCurrentAction.LocationName}로 이동 시작", 2);
                    mMovement.MoveToPosition(availablePosition);
                }
                else
                {
                    // TODO: 로케이션이 꽉 차있어서 이동 불가능할 때
                    LogManager.Log("Agent", $"{mName}: {mCurrentAction.LocationName} 타일에 이동 가능한 위치가 없습니다.", 1);
                    ChangeState(AgentState.WAITING);
                }
                break;

            case AgentState.MOVING_TO_INTERACTABLE:
                FindMovableInteractable(tileController);
                if (mCurrentTargetInteractable != null)
                {
                    LogManager.Log("Agent", $"{mName}: {mCurrentAction.ActionName} 위해 {mCurrentAction.TargetName}로 이동 시작", 2);
                    LogManager.Log("Agent", $"타겟컨트롤러: {mCurrentTargetInteractable.TargetController.name}", 2);
                    mMovement.MoveToTarget(mCurrentTargetInteractable.TargetController);
                }
                else
                {
                    LogManager.Log("Agent", $"{mName}: {mCurrentAction.TargetName} 상호작용 가능한 오브젝트를 찾을 수 없습니다.", 1);
                    
                    mMovement.ClearMovement();
                    ChangeState(AgentState.WAITING);
                    // 해당 위치에 원하는 오브젝트가 없다는 피드백 전송
                    SendFeedbackToAI(false, mCurrentAction.TargetName);
                    // TODO: 상호작용 가능한 오브젝트를 찾을 수 없을 때
                }
                break;
        }
    }

    // 오브젝트와 상호작용 시작
    public void StartInteraction()
    {
        if (mInteractionCoroutine != null)
        {
            StopCoroutine(mInteractionCoroutine);
            mInteractionCoroutine = null;
        }
        if(CurrentTargetInteractable != null && CurrentAction != null &&
         CurrentTargetInteractable.mInteractableData.mReplaceActionName == CurrentAction.ActionName){
            mCurrentAction.ActionName = CurrentTargetInteractable.mInteractableData.mReplacedActionName;
        }
        mInteractionCoroutine = StartCoroutine(InteractionRoutine());
        // 상호작용 UI 시작
        if (mAgentUI != null)
        {
            string interactionText = CurrentAction != null ? CurrentAction.ActionName : "";
            mAgentUI.StartInteractionUI(interactionText);
        }
    }

    private IEnumerator InteractionRoutine()
    {
        ScheduleItem action = mCurrentAction;
        if (action == null) yield break;

        TimeSpan scheduleEndTime = CurrentAction.EndTime;
        TimeSpan interactionStartTime = TimeManager.Instance.GetCurrentGameTime();
        double curDurationProgress = 0.0f;
        float interactionDuration = CurrentTargetInteractable.GetActionDuration(mCurrentAction.ActionName);
        // TODO: 인터랙션 종류에 따른 예외처리 추가
        if(interactionDuration <= 0)
        {
            LogManager.Log("Agent", $"{mName}: 상호작용 지속 시간이 0이하입니다, 상호작용 비정상 종료.", 1);
            EndInteraction();
            yield break;
        }
        TimeSpan lastTickTime = interactionStartTime;
        
        while (TimeManager.Instance.GetCurrentGameTime() < scheduleEndTime)
        {
            // 상호작용 대상 오브젝트가 사라졌는지 체크
            if (mCurrentTargetInteractable == null || mCurrentTargetInteractable.gameObject == null || !mCurrentTargetInteractable.gameObject.activeInHierarchy)
            {
                LogManager.Log("Agent", $"{mName}: 상호작용 대상이 사라져 상호작용을 종료합니다.", 2);
                EndInteraction();
                yield break;
            }

            TimeSpan now = TimeManager.Instance.GetCurrentGameTime();
            double delta = (now - lastTickTime).TotalSeconds;
            curDurationProgress += delta;
            mInteractionProgress = Mathf.Clamp01((float)(curDurationProgress / interactionDuration));

            // 효과 발생 (주기마다)
            if (curDurationProgress >= interactionDuration)
            {
                bool tryInteract = ApplyInteractionEffect();
                isSuccessForFeedback = tryInteract;
                curDurationProgress = 0.0f; // 주기 초기화
                lastTickTime = now;
                if (!tryInteract)
                {
                    LogManager.Log("Agent", "상호작용 예외발생",2);
                    EndInteraction();
                    yield break;
                }
            }
            else
            {
                lastTickTime = now;
            }

            yield return null;
        }

        // 스케줄 시간이 끝나면 종료
        LogManager.Log("Agent", $"{mName}: 스케줄 시간이 종료되어 상호작용을 종료합니다.", 2);
        EndInteraction();
        yield break;
    }

    // 상호작용 종료
    // 주의: 상호작용 scheduler에서 종료시 ScheduleItem이 없어진 후 이 함수를 호출하게됨
    public void EndInteraction() 
    {
        LogManager.Log("Agent", $"{mName}: 상호작용 종료", 2);
        if(CurrentState != AgentState.INTERACTING){
            LogManager.Log("Agent", $"{mName}: 상호작용 종료 조건 불충족", 1);
            return;
        }
        if(isSuccessForFeedback){
            SendFeedbackToAI(true, CurrentTargetInteractable.InteractableName, mActionNameForFeedback); // 행동 성공
        }
        else{
            SendFeedbackToAI(false, CurrentTargetInteractable.InteractableName, mActionNameForFeedback); // 행동 실패
        }
        mInteractionProgress = 0.0f;
        if (mInteractionCoroutine != null)
        {
            StopCoroutine(mInteractionCoroutine);
            mInteractionCoroutine = null;
        }
        LogManager.Log("Agent", $"{mName}: 상호작용 완료", 2);
        CompleteAction();
    }

    private bool ApplyInteractionEffect()
    {
        LogManager.Log("Agent", $"{mName}: 상호작용 효과 발생", 2);
        return CurrentTargetInteractable.Interact(gameObject, mCurrentAction.ActionName);
    }

    // 현재 활동 완료 처리하는 함수
    private void CompleteAction()
    {
        if (mCurrentAction != null)
        {
            if (mShowDebugInfo)
            {
                LogManager.Log("Agent", $"{mName}: 활동 완료 - {mCurrentAction.ActionName}", 2);
            }
            
            // 상태 초기화
            mCurrentAction = null;
            // 스케줄러에 활동 완료 알림
            mScheduler.CompleteCurrentAction();
            mStateMachine.ChangeState(AgentState.WAITING);
        }
    }

    // 대기 상태 업데이트
    public void UpdateWaitTime()
    {
        // 대기 시간 감소
        mWaitTime -= Time.deltaTime;
        
        // 대기 시간 종료 시 상태 변경
        if (mWaitTime <= 0f)
        {
            mStateMachine.ChangeState(AgentState.WAITING);
            if (mShowDebugInfo)
            {
                LogManager.Log("Agent", $"{mName}: 대기 상태 종료", 2);
            }
        }
    }

    // 감정 상태 자동 증가 함수
    private void AutoIncreaseAgentNeeds()
    {
        TimeSpan currentTime = TimeManager.Instance.GetCurrentGameTime();
        int lastMinutes = (int)mLastNeedsIncreaseTime.TotalMinutes;
        int currentMinutes = (int)currentTime.TotalMinutes;
        int minutesDiff = currentMinutes - lastMinutes;

        // 분 단위로 mNeedIntervalMinutes 이상 지났는지 확인
        if (minutesDiff >= mNeedIntervalMinutes)
        {
            // 각 감정 상태 증가
            ModifyNeed(AgentNeedsType.Hunger, 1);
            ModifyNeed(AgentNeedsType.Sleepiness, 1);
           //ModifyNeed(AgentNeedsType.Loneliness, 1);
            ModifyNeed(AgentNeedsType.Stress, 1);
            
            // 마지막 증가 시간 업데이트 (항상 분 단위까지만 저장)
            mLastNeedsIncreaseTime = TimeSpan.FromMinutes(currentMinutes);
        }
    }

    // 이동 가능한 오브젝트 탐색
    private void FindMovableInteractable(TileController _tileController)
    {
        mCurrentTargetInteractable = null;
        foreach (var interactable in _tileController.ChildInteractables)
        {
            if (interactable.InteractableName == mCurrentAction.TargetName)
            {
                interactable.TargetController.UpdateStandingPoints();
                if (interactable.TargetController.StandingPoints.Count > 0)
                {
                    mCurrentTargetInteractable = interactable;
                    return;
                }
            }
        }
    }

    // 반응 판단 하는 중에 UI 표시
    public void ShowReactUI(string _text, bool _isReact){
        mAgentUI.ShowReact(_text, _isReact);
    }

    // 반응 판단 받았을 때, AIBridge에서 이 함수를 호출
    public void ReactToResponse(bool _response, PerceiveEvent _perceiveEvent){
        LogManager.Log("Agent", $"{mName}: 반응 판단 결과 받음: {_response}", 2);
        mIsReactJudge = false;
        
        if(_response){            
            SendReactAction(_perceiveEvent);
        }
        else{
            // 반응하지 않는 것으로 판단
            mAgentUI.ShowReact("", false);
        }
    }

    // 반응 행동 요청
    public void SendReactAction(PerceiveEvent _perceiveEvent){
        // AIBridge_perceive에 반응 행동 요청하기
            AIBridge_Perceive.Instance.SendReactActionEvent(this, _perceiveEvent);
            // state를 WAITING FOR AI RESPONSE로 변경
            mStateMachine.ChangeState(AgentState.WAITING_FOR_AI_RESPONSE);
            mAgentUI.ShowReact("?", true);
    }

    // 피드백 초기화
    public void InitFeedback(){
        mCurrentFeedback = new PerceiveFeedback();
        mCurrentFeedback.agent_name = mName;
        mCurrentFeedback.current_location_name = "";
        mCurrentFeedback.time = TimeManager.Instance.GetCurrentGameTime().ToString();
        mCurrentFeedback.interactable_name = "";
        mCurrentFeedback.action_name = mActionNameForFeedback;
        mCurrentFeedback.success = false;
        mCurrentFeedback.feedback.feedback_description = "";
        mCurrentFeedback.feedback.memory_id = "";
        mCurrentFeedback.feedback.needs_diff.hunger = 0;
        mCurrentFeedback.feedback.needs_diff.sleepiness = 0;
        mCurrentFeedback.feedback.needs_diff.loneliness = 0;
        mCurrentFeedback.feedback.needs_diff.stress = 0;
        mInteractCountForFeedback = 0;
    }

    public void IncreaseNeedsForFeedback(AgentNeeds _needs){
        // use는 주기가 여러번 발생하므로 보정치 적용
        // 상호작용 최대 10번까지 발생하는 것을 기준으로 
        if(mInteractCountForFeedback < 10){
            mCurrentFeedback.feedback.needs_diff.hunger += _needs.Hunger;
            mCurrentFeedback.feedback.needs_diff.loneliness += _needs.Loneliness;
            mCurrentFeedback.feedback.needs_diff.sleepiness += _needs.Sleepiness;
            mCurrentFeedback.feedback.needs_diff.stress += _needs.Stress;
        }
        mInteractCountForFeedback ++;
    }

    // AI 서버에 피드백 보냄
    public void SendFeedbackToAI(bool _success, string _interactableName = "", string _actionName = "", string _memoryID = ""){
        mCurrentFeedback.current_location_name = "";
        mCurrentFeedback.time = TimeManager.Instance.GetCurrentGameDateString();
        mCurrentFeedback.interactable_name = _interactableName;
        mCurrentFeedback.action_name = _actionName;
        mCurrentFeedback.success = _success;
        mCurrentFeedback.feedback.feedback_description = "";
        PerceiveEvent perceiveEvent = new PerceiveEvent();
        // 실패했고 액션까지는 성공
        if(!_success && _actionName != ""){
            mCurrentFeedback.feedback.feedback_description = $"{_interactableName}: ";
        }
        // 타겟 로케이션에 타겟 오브젝트가 없는 경우
        else if (!_success && _actionName == ""){
            if (CurrentAction.ActionName == "find"){
                mCurrentFeedback.feedback.feedback_description = $"Let's find something in the {mCurrentLocation}.";
            }
            else{
                mCurrentFeedback.feedback.feedback_description = $"There are no {_interactableName} at the {mCurrentLocation}.";
            }
            
            LogManager.Log("Agent", $"{mName}: 로케이션에 오브젝트가 없어 피드백 보냄: {mCurrentFeedback.feedback.feedback_description}", 2);
            
            perceiveEvent.event_is_save = false;
            perceiveEvent.event_location = "";
            perceiveEvent.event_role = "";
            perceiveEvent.event_type = PerceiveEventType.TARGET_NOT_IN_LOCATION;
            string eventData = mCurrentFeedback.feedback.feedback_description + GetCurrentLocationInteractables(mCurrentLocation);
            perceiveEvent.event_description = eventData;
            // AIBridge_perceive에 바로 반응 행동 요청하기
            SendReactAction(perceiveEvent);
        }
        mCurrentFeedback.feedback.memory_id = mCurrentMemoryID;
        mCurrentFeedback.importance = 2;
        // 실제 전송되는 JSON 양식도 로그로 출력
        string feedbackJson = JsonUtility.ToJson(mCurrentFeedback);
        LogManager.Log("AI", $"{mName}: 피드백 전송 JSON: {feedbackJson}", 2);
        AIBridge_Perceive.Instance.SendFeedbackToAI(mCurrentFeedback);
    }
    // 에이전트의 현재 지역이 바뀌었을 때, 현재 지역의 오브젝트 목록을 가져옴
    public string GetCurrentLocationInteractables(string _newLocation){
        List<Interactable> interactables = TileManager.Instance.GetInteractablesInLocation(_newLocation);
        // mName과 같은 InteractableName은 제외
        var filtered = interactables.Where(i => i.InteractableName != mName);
        var grouped = filtered.GroupBy(i => i.InteractableName)
                                   .Select(g => $"{g.Key} x{g.Count()}");
        string interactableSummary = string.Join(", ", grouped);
        string eventData = $" {interactableSummary} in {_newLocation}.";
        return eventData;
    }
    // 에이전트의 현재 지역이 바뀌었을 때, 현재 지역의 오브젝트 목록을 전송
    public void SendCurrentLocationInfo(string _newLocation){
        PerceiveEvent perceiveEvent = new PerceiveEvent();
        perceiveEvent.event_type = PerceiveEventType.AGENT_LOCATION_CHANGE;
        perceiveEvent.event_location = CurrentLocation;
        perceiveEvent.event_role = $"{mName} saw";
        perceiveEvent.event_is_save = true;
        perceiveEvent.event_description = GetCurrentLocationInteractables(_newLocation);
        perceiveEvent.importance = 3;
        LogManager.Log("AI", $"{mName}: 위치 정보 전송: {perceiveEvent.event_description}", 2);
        AIBridge_Perceive.Instance.SendPerceiveEventLocation(this, perceiveEvent);      
    }
}
