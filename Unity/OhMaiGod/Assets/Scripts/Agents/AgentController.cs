using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using OhMAIGod.Agent;

public class AgentController : MonoBehaviour
{
    [SerializeField] private AgentUI mAgentUI;
    [SerializeField] private AgentVision agentVision;  // AgentVision 컴포넌트 참조 추가

    [Header("Agent States")]
    [SerializeField] private AgentNeeds mAgentNeeds;                // 현재 Agent의 욕구 수치
    
    // Needs 수정을 위한 메서드들
    public void ModifyHunger(int _amount)
    {
        mAgentNeeds.Hunger = Mathf.Clamp(mAgentNeeds.Hunger + _amount, 0, 10);
        if (mShowDebugInfo)
        {
            LogManager.Log("Agent", $"{mName}의 배고픔 변화: {_amount} (현재: {mAgentNeeds.Hunger})", 3);
        }
    }
    
    public void ModifySleepiness(int _amount)
    {
        mAgentNeeds.Sleepiness = Mathf.Clamp(mAgentNeeds.Sleepiness + _amount, 0, 10);
        if (mShowDebugInfo)
        {
            LogManager.Log("Agent", $"{mName}의 졸림 변화: {_amount} (현재: {mAgentNeeds.Sleepiness})", 3);
        }
    }
    
    public void ModifyLoneliness(int _amount)
    {
        mAgentNeeds.Loneliness = Mathf.Clamp(mAgentNeeds.Loneliness + _amount, 0, 10);
        if (mShowDebugInfo)
        {
            LogManager.Log("Agent", $"{mName}의 외로움 변화: {_amount} (현재: {mAgentNeeds.Loneliness})", 3);
        }
    }

    [Header("Base Profile")]
    [SerializeField] private int mID;                               // 에이전트 고유 식별자
    [SerializeField] private string mName;                          // 이름
    [SerializeField] private string mDescription;                   // 초기 설명    
    [SerializeField] private float mVisualRange;                    // 시야 범위
    [SerializeField] private float mActionMinDuration = 1.0f;       // 활동 최소 지속 시간 (분)
    [SerializeField] private bool mAutoStart = true;                // 자동 시작 여부
    private AgentStateMachine mStateMachine;

    [Header("디버깅")]
    [SerializeField] private bool mShowDebugInfo = true;            // 디버그 정보 표시 여부
    [SerializeField, ReadOnly] private AgentState mCurrentState; // 현재 상태 Inspector 디버그용
    [SerializeField, ReadOnly] private string mCurrentLocation;  // 현재 위치 Inspector 디버그용
    [SerializeField, ReadOnly] private Interactable mCurrentTargetInteractable;    // 현재 타겟 Inspector 디버그용
    private float mCurrentActionTime = 0f;                          // 현재 활동 진행 시간
    private ScheduleItem mCurrentAction = null;                     // 현재 활동 정보
    private float mWaitTime = 0f;                                   // 대기 시간 (다음 활동까지)

    public AgentState CurrentState => mStateMachine.CurrentStateType;       // 에이전트 현재 상태
    public string AgentName => mName;                                       // 에이전트 이름
    public int AgentID => mID;                                              // 에이전트 ID
    public AgentNeeds AgnetNeeds => mAgentNeeds;
    public ScheduleItem CurrentAction => mCurrentAction;
    public string CurrentLocation => mCurrentLocation;
    public Interactable CurrentTargetInteractable => mCurrentTargetInteractable;
    public Animator animator;  // 애니메이터
    // AIBridge에서 Agent만 가져오면 나머지도 가져올 수 있게 public으로 변경
    [SerializeField] public AgentScheduler mScheduler;
    [SerializeField] public MovementController mMovement;
    [SerializeField] public Interactable mInteractable;


    // 시야 내의 오브젝트 목록
    public List<Interactable> mVisibleInteractables = new List<Interactable>();

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
        mAgentNeeds.Hunger = 1;
        mAgentNeeds.Sleepiness = 1;
        mAgentNeeds.Loneliness = 1;

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
        if (mStateMachine.CurrentStateType == AgentState.MOVE_TO_INTERACTABLE)
            mStateMachine.ChangeState(AgentState.INTERACTION); // 상태 INTERACTION으로 전환
    }

    // 이동 불가능 이벤트 핸들러
    private void HandleMovementBlocked()
    {
        // 현재 상태에 따라 처리 (기본적으로 WAIT 상태로 전환)
        switch (CurrentState)
        {
            case AgentState.MOVE_TO_LOCATION:
                // TODO: 로케이션으로 이동할 수 없는 경우 반응
                LogManager.Log("Agent", $"{mName}: 로케이션으로 이동할 수 없습니다.", 1);
                ChangeState(AgentState.WAIT);
                break;
            case AgentState.MOVE_TO_INTERACTABLE:
                ChangeState(AgentState.WAIT);
                FindMovableInteractable(TileManager.Instance.GetTileController(mCurrentAction.LocationName));
                if (mCurrentTargetInteractable == null)
                {
                    // TODO: 이동 가능한 새로운 오브젝트를 찾을 수 없을 때
                    LogManager.Log("Agent", $"{mName}: 이동 가능한 오브젝트를 찾을 수 없습니다.", 1);
                    ChangeState(AgentState.WAIT);
                }
                else
                {
                    ChangeState(AgentState.MOVE_TO_INTERACTABLE);  // 이동 재개
                }
                break;
            default:
                // TODO: 기타 이동 불가능 상황 반응
                ChangeState(AgentState.WAIT);
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
            ChangeState(AgentState.MOVE_TO_INTERACTABLE);
        }
    }

    private void Start()
    {
        if (mAutoStart)
        {
            // 현재 상태 평가 시작
            // 수정필요
            // StartCoroutine(EvaluateStateRoutine());

            // 상태 머신 초기화 (현재 상태 지정) 
            // (AI 서버에서 호출먼저 받는 테스트하느라 주석처리)
            // mStateMachine.Initialize(AgentState.WAIT);

            // 감정 상태 자동 증가 시작
            StartCoroutine(AutoIncreaseAgentNeeds());
        }
    }

    private void Update()
    {
        // 상태 머신 업데이트 호출
        mStateMachine.ProcessStateUpdate();
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
        if (mCurrentAction != null && mStateMachine.CurrentStateType == AgentState.INTERACTION)
        {
            CompleteAction();
        }
        mCurrentAction = _action;
        
        // 현재 위치와 목표 위치가 다르면 MOVE_TO_LOCATION 상태로 전환
        if (mCurrentAction.LocationName != null && mCurrentAction.LocationName != mInteractable.CurrentLocation)
        {
            ChangeState(AgentState.MOVE_TO_LOCATION);
        }

        // 현재 위치와 목표 위치가 같으면 오브젝트로 이동
        if (mCurrentAction.LocationName != null && mCurrentAction.LocationName == mInteractable.CurrentLocation)
        {
            ChangeState(AgentState.MOVE_TO_INTERACTABLE);
        }

        // 활동 시작 시 말풍선 표시
        mAgentUI.StartSpeech(mCurrentAction.Reason);
    }

    // 활동 위치로 이동 시작
    public void StartMovingToAction()
    {
        if (mCurrentAction == null)
        {
            string actionName = mScheduler.GetCurrentActionName();
            string destinationLocation = mScheduler.GetCurrentDestinationLocation();
            string destinationTarget = mScheduler.GetCurrentDestinationTarget();
            if (string.IsNullOrEmpty(destinationTarget))
            {
                if (mShowDebugInfo)
                {
                    LogManager.Log("Agent", $"{mName}: 이동할 목적지 없음", 1);
                }
                return;
            }
            
            // 임시 활동 객체 생성
            mCurrentAction = new ScheduleItem
            {
                ActionName = actionName,
                LocationName = destinationLocation,
                TargetName = destinationTarget
            };
        }

        // 이동 시작
        TileController tileController = TileManager.Instance.GetTileController(mCurrentAction.LocationName);
        if (tileController == null)
        {
            // TODO: 잘못된 로케이션으로 가려고 할 때
            LogManager.Log("Agent", $"{mName}: {mCurrentAction.LocationName} 타일 컨트롤러를 찾을 수 없습니다.", 1);
            ChangeState(AgentState.WAIT);
            return;
        }

        switch (CurrentState)
        {
            case AgentState.MOVE_TO_LOCATION:
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
                    ChangeState(AgentState.WAIT);
                }
                break;

            case AgentState.MOVE_TO_INTERACTABLE:
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
                    ChangeState(AgentState.WAIT);
                }
                break;
        }
    }

    // 활동 시작하는 함수
    // public void StartAction()
    // {
    //     // 활동 정보 없으면 스케줄러에서 가져오기
    //     if (mCurrentAction == null)
    //     {
    //         string actionName = mScheduler.GetCurrentActionName();
    //         if (actionName == "대기 중")
    //         {
    //             // 활동 없음 - 대기 상태로
    //             // mCurrentState = AgentState.IDLE;
    //             mStateMachine.ChangeState(AgentState.IDLE);
    //             return;
    //         }
            
    //         // 임시 활동 객체 생성
    //         mCurrentAction = new ScheduleItem
    //         {
    //             ActionName = actionName,
    //             LocationName = mScheduler.GetCurrentDestinationLocation(),
    //             TargetName = mScheduler.GetCurrentDestinationTarget()
    //         };
    //     }
    // }

    // // 상호작용 시작
    // public void StartInteraction()
    // {
        
    // }

    // 상호작용 진행
    public void ProcessInteraction()
    {
        //
    }

    // 상호작용 종료        
    public void EndInteraction() 
    {
        //
    }


    // 오브젝트와 상호작용 시작
    // 일단 대기
    public void StartInteraction()
    {
        if (mShowDebugInfo)
        {
            LogManager.Log("Agent", $"{mName}: {CurrentTargetInteractable.name}와(과) 상호작용 시작", 2);
        }
        LogManager.Log("Agent", "상호작용 시작: "+mCurrentAction.ActionName, 3);
        CurrentTargetInteractable?.Interact(gameObject,mCurrentAction.ActionName);
        CompleteAction();
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
            mStateMachine.ChangeState(AgentState.WAIT);
        }
    }

    // 활동 시간 증가 함수
    // public void UpdateActionTime()
    // {
    //     // 활동 시간 증가
    //     mCurrentActionTime += Time.deltaTime;
        
    //     // 최소 지속 시간 이후 활동 완료
    //     if (mCurrentActionTime >= mActionMinDuration * 60f)
    //     {
    //         CompleteAction();
    //     }
    // }

    // 대기 상태로 전환하는 함수
    private void EnterWaitingState(float _waitTimeMinutes)
    {
        mStateMachine.ChangeState(AgentState.WAIT);
        mWaitTime = Mathf.Min(_waitTimeMinutes * 60f, 300f);
        if (mShowDebugInfo)
        {
            LogManager.Log("Agent", $"{mName}: 대기 상태 시작 ({_waitTimeMinutes:F1}분)", 2);
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
            mStateMachine.ChangeState(AgentState.WAIT);
            if (mShowDebugInfo)
            {
                LogManager.Log("Agent", $"{mName}: 대기 상태 종료", 2);
            }
        }
    }

    // 감정 상태 자동 증가 코루틴
    private IEnumerator AutoIncreaseAgentNeeds()
    {
        TimeSpan lastIncreaseTime = TimeManager.Instance.GetCurrentGameTime();
        while (true)
        {
            yield return new WaitForSeconds(1f);
            TimeSpan currentTime = TimeManager.Instance.GetCurrentGameTime();
            TimeSpan timeDifference = currentTime - lastIncreaseTime;

            // 게임 시간으로 30분이 지났는지 확인
            if (timeDifference.TotalMinutes >= 30)
            {
                // 각 감정 상태 증가
                ModifyHunger(1);
                ModifySleepiness(1);
                ModifyLoneliness(1);
                if (mShowDebugInfo)
                {
                    LogManager.Log("Agent", $"[게임시간 {currentTime:hh\\:mm}] {mName}의 감정 상태 자동 증가", 2);
                }

                // 마지막 증가 시간 업데이트
                lastIncreaseTime = currentTime;
            }
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
}
