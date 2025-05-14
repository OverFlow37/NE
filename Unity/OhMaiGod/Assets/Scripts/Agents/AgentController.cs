using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using OhMAIGod.Agent;
using OhMAIGod.Perceive;
public class AgentController : MonoBehaviour
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
                if (mShowDebugInfo)
                {
                    //LogManager.Log("Agent", $"{mName}의 배고픔 변화: {_amount} (현재: {mAgentNeeds.Hunger})", 3);
                }
                break;
            
            case AgentNeedsType.Sleepiness:
                mAgentNeeds.Sleepiness = Mathf.Clamp(mAgentNeeds.Sleepiness + _amount, -100, 100);
                if (mShowDebugInfo)
                {
                    //LogManager.Log("Agent", $"{mName}의 졸림 변화: {_amount} (현재: {mAgentNeeds.Sleepiness})", 3);
                }
                break;
            
            case AgentNeedsType.Loneliness:
                mAgentNeeds.Loneliness = Mathf.Clamp(mAgentNeeds.Loneliness + _amount, -100, 100);
                if (mShowDebugInfo)
                {
                    //LogManager.Log("Agent", $"{mName}의 외로움 변화: {_amount} (현재: {mAgentNeeds.Loneliness})", 3);
                }
                break;
            
            case AgentNeedsType.Stress:
                mAgentNeeds.Stress = Mathf.Clamp(mAgentNeeds.Stress + _amount, -100, 100);
                if (mShowDebugInfo)
                {
                    //LogManager.Log("Agent", $"{mName}의 스트레스 변화: {_amount} (현재: {mAgentNeeds.Stress})", 3);
                }
                break;
        }
    }

    [Header("Base Profile")]
    [SerializeField] private int mID;                               // 에이전트 고유 식별자
    [SerializeField] private string mName;                          // 이름
    [SerializeField] private string mDescription;                   // 초기 설명    
    [SerializeField] private float mVisualRange;                    // 시야 범위
    [SerializeField] private bool mAutoStart = true;                // 자동 시작 여부
    [SerializeField] [Tooltip("감정 상태 자동 증가 간격 (분)")] private int mNeedIntervalMinutes = 30;
    private TimeSpan mLastNeedsIncreaseTime; // 마지막 감정 상태 자동 증가 시각

    [Header("디버깅")]
    [SerializeField] private bool mShowDebugInfo = true;            // 디버그 정보 표시 여부
    [SerializeField, ReadOnly] private AgentState mCurrentState; // 현재 상태 Inspector 디버그용
    [SerializeField, ReadOnly] private string mCurrentLocation;  // 현재 위치 Inspector 디버그용
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
        mLastNeedsIncreaseTime = TimeSpan.FromMinutes(TimeManager.Instance.GetCurrentGameTime().TotalMinutes);

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
        if (mStateMachine.CurrentStateType == AgentState.MOVING_TO_INTERACTABLE)
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
        mCurrentLocation = _newLocation;
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
        mCurrentAction = _action;
        
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
                    // TODO: 상호작용 가능한 오브젝트를 찾을 수 없을 때
                    LogManager.Log("Agent", $"{mName}: {mCurrentAction.TargetName} 상호작용 가능한 오브젝트를 찾을 수 없습니다.", 1);
                    ChangeState(AgentState.WAITING);
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
                ApplyInteractionEffect();
                curDurationProgress = 0.0f; // 주기 초기화
                lastTickTime = now;
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
        mInteractionProgress = 0.0f;
        if (mInteractionCoroutine != null)
        {
            StopCoroutine(mInteractionCoroutine);
            mInteractionCoroutine = null;
        }
        LogManager.Log("Agent", $"{mName}: 상호작용 완료", 2);
        CompleteAction();
    }

    private void ApplyInteractionEffect()
    {
        LogManager.Log("Agent", $"{mName}: 상호작용 효과 발생", 2);
        CurrentTargetInteractable.Interact(gameObject, mCurrentAction.ActionName);
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
            
            // 스케줄러에 활동 완료 알림
            mScheduler.CompleteCurrentAction();
            
            // 상태 초기화
            mCurrentAction = null;
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
            ModifyNeed(AgentNeedsType.Loneliness, 1);
            ModifyNeed(AgentNeedsType.Stress, 1);
            if (mShowDebugInfo)
            {
                //LogManager.Log("Agent", $"[게임시간 {currentTime:hh\\:mm}] {mName}의 감정 상태 자동 증가", 2);
            }
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

    // 반응 판단 받았을 때, AIBridge에서 이 함수를 호출
    public void ReactToResponse(bool _response, PerceiveEvent _perceiveEvent){
        LogManager.Log("Agent", $"{mName}: 반응 판단 결과 받음: {_response}", 2);
        mIsReactJudge = false;
        // TODO: 반응 UI 종료 처리
        if(_response){            
            // AIBridge_perceive에 반응 행동 요청하기
            AIBridge_Perceive.Instance.SendReactActionEvent(this, _perceiveEvent);
            // state를 WAITING FOR AI RESPONSE로 변경
            mStateMachine.ChangeState(AgentState.WAITING_FOR_AI_RESPONSE);
        }
        else{
            // 반응 판단 결과 처리
        }
    }
}
