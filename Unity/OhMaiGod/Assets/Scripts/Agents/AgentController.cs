using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using OhMAIGod.Agent;

public class AgentController : MonoBehaviour
{
    [SerializeField] private AgentUI agentUI;
    [SerializeField] private AgentVision agentVision;  // AgentVision 컴포넌트 참조 추가

    [Header("Agent States")]
    [SerializeField] private AgentNeeds mAgentNeeds;                // 현재 Agent의 욕구 수치
    
    // Needs 수정을 위한 메서드들
    public void ModifyHunger(int amount) 
    { 
        mAgentNeeds.Hunger = Mathf.Clamp(mAgentNeeds.Hunger + amount, 0, 10);
        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}의 배고픔 변화: {amount} (현재: {mAgentNeeds.Hunger})");
        }
    }
    
    public void ModifySleepiness(int amount) 
    { 
        mAgentNeeds.Sleepiness = Mathf.Clamp(mAgentNeeds.Sleepiness + amount, 0, 10);
        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}의 졸림 변화: {amount} (현재: {mAgentNeeds.Sleepiness})");
        }
    }
    
    public void ModifyLoneliness(int amount) 
    { 
        mAgentNeeds.Loneliness = Mathf.Clamp(mAgentNeeds.Loneliness + amount, 0, 10);
        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}의 외로움 변화: {amount} (현재: {mAgentNeeds.Loneliness})");
        }
    }

    [Header("Base Profile")]
    [SerializeField] private int mID;                               // 에이전트 고유 식별자
    [SerializeField] private string mName;                          // 이름
    [SerializeField] private string mDescription;                   // 초기 설명    
    [SerializeField] private float mVisualRange;                // 시야 범위
    [SerializeField] private float mActionMinDuration = 1.0f;       // 활동 최소 지속 시간 (분)
    [SerializeField] private bool mAutoStart = true;                // 자동 시작 여부
    private AgentState mCurrentState = AgentState.IDLE;             // 에이전트의 현재 State

    [Header("디버깅")]
    [SerializeField] private bool mShowDebugInfo = true;            // 디버그 정보 표시 여부

    private float mCurrentActionTime = 0f;                          // 현재 활동 진행 시간
    private ScheduleItem mCurrentAction = null;                     // 현재 활동 정보
    private float mWaitTime = 0f;                                   // 대기 시간 (다음 활동까지)
    public AgentState CurrentState => mCurrentState;                // 에이전트 현재 상태
    public string AgentName => mName;                               // 에이전트 이름
    public int AgentID => mID;                                      // 에이전트 ID
    public AgentNeeds AgnetNeeds => mAgentNeeds;

    private Animator animator;  // 애니메이터
    // AIBridge에서 Agent만 가져오면 나머지도 가져올 수 있게 public으로 변경
    [SerializeField] public AgentScheduler mScheduler;
    [SerializeField] public MovementController mMovement;


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
        }

        // AgentVision의 이벤트 구독
        if (agentVision != null)
        {
            agentVision.OnVisionChanged += HandleVisionChanged;
            // 초기 시야 범위 내 오브젝트들 추가
            var initialInteractables = agentVision.GetVisibleInteractables();
            mVisibleInteractables.AddRange(initialInteractables);
        }

        // 감정 상태 초기화
        mAgentNeeds.Hunger = 1;
        mAgentNeeds.Sleepiness = 1;
        mAgentNeeds.Loneliness = 1;

        // 애니메이션 참조
        animator = GetComponent<Animator>();
    }

    private void OnDestroy()
    {
        // 이벤트 구독 해제
        if (mMovement != null)
        {
            mMovement.OnDestinationReached -= HandleDestinationReached;
        }

        if (agentVision != null)
        {
            agentVision.OnVisionChanged -= HandleVisionChanged;
        }
    }

    // 목적지 도착 이벤트 발생 시 호출되는 함수
    // 애니메이션 업데이트, Status 업데이트, 활동 시작
    private void HandleDestinationReached()
    {
        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}: 목적지 도착 - {mMovement.TargetName}");
        }

        // 이동 애니메이션 정지
        animator.SetBool("isMoving", false);

        // 도착한 위치에 따라 감정 상태 업데이트 -> 타겟 오브젝트에 따라 감정 상태 업데이트
        //UpdateAgentNeedsByLocation(mMovement.TargetName);

        // 활동 시작
        StartAction();
    }

    // 시야 범위 변경 이벤트 처리
    private void HandleVisionChanged(Interactable interactable, bool entered)
    {
        if (entered)
        {
            if (!mVisibleInteractables.Contains(interactable))
            {
                mVisibleInteractables.Add(interactable);
                if (mShowDebugInfo)
                {
                    Debug.Log($"{mName}이(가) {interactable.name}을(를) 발견했습니다.");
                }
            }
        }
        else
        {
            mVisibleInteractables.Remove(interactable);
            if (mShowDebugInfo)
            {
                Debug.Log($"{mName}이(가) {interactable.name}을(를) 시야에서 놓쳤습니다.");
            }
        }
    }

    private void Start()
    {
        if (mAutoStart)
        {
            // 현재 상태 평가 시작
            // 수정필요
            StartCoroutine(EvaluateStateRoutine());

            // 감정 상태 자동 증가 시작
            StartCoroutine(AutoIncreaseAgentNeeds());
        }
    }

    private void Update()
    {
        // 상태별 현재 상태 유지 시간 업데이트 처리
        switch (mCurrentState)
        {
            case AgentState.INTERACTION:
                UpdateActionTime();
                break;
                
            case AgentState.WAITING:
                UpdateWaitTime();
                break;
        }
    }

    // 새 활동 시작 (AgentScheduler에서 호출)
    public void StartNewAction(ScheduleItem _action)
    {
        if (_action == null)
        {
            Debug.LogWarning($"{mName}: 잘못된 활동 정보 받음");
            return;
        }

        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}: 새 활동 수신 - {_action.ActionName} @ {_action.LocationName}");
        }

        // 이전 활동 정리
        if (mCurrentAction != null && mCurrentState == AgentState.INTERACTION)
        {
            CompleteAction();
        }

        // 새 활동 설정
        mCurrentAction = _action;
        
        // 현재 위치가 활동 위치와 다른 경우 이동 시작
        // if (NeedsToMoveForAction(_Action))
        // {
        //     // 활동 위치로 이동 시작
        //     StartMovingToAction();
        // }
        // else
        // {
        //     // 이미 올바른 위치에 있으면 활동 시작
        //     StartAction();
        // }
        StartMovingToAction();

        // 활동 시작 시 말풍선 표시
        agentUI.StartSpeech(mCurrentAction.Reason);
    }



    // 활동 위치로 이동 시작
    private void StartMovingToAction()
    {
        // 현재 활동 정보 가져오기 (없으면 스케줄러에서 가져오기)
        if (mCurrentAction == null)
        {
            string actionName = mScheduler.GetCurrentActionName();
            string destinationLocation = mScheduler.GetCurrentDestinationLocation();
            string destinationTarget = mScheduler.GetCurrentDestinationTarget();
            
            if (string.IsNullOrEmpty(destinationTarget))
            {
                if (mShowDebugInfo)
                {
                    Debug.LogWarning($"{mName}: 이동할 목적지 없음");
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
        
        // 상태 변경
        mCurrentState = AgentState.MovingToLocation;
        
        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}: {mCurrentAction.LocationName}(으)로 이동 시작. ({mCurrentAction.ActionName} 위해)");
        }
        
        // 이동 시작
        mMovement.MoveToLocation(mCurrentAction.TargetName, mCurrentAction.LocationName);

        // 이동 애니메이션 시작
        animator.SetBool("isMoving", true);
    }

    // 활동 시작하는 함수
    private void StartAction()
    {
        // 활동 정보 없으면 스케줄러에서 가져오기
        if (mCurrentAction == null)
        {
            string actionName = mScheduler.GetCurrentActionName();
            
            if (actionName == "대기 중")
            {
                // 활동 없음 - 대기 상태로
                mCurrentState = AgentState.IDLE;
                return;
            }
            
            // 임시 활동 객체 생성
            mCurrentAction = new ScheduleItem
            {
                ActionName = actionName,
                LocationName = mScheduler.GetCurrentDestinationLocation(),
                TargetName = mScheduler.GetCurrentDestinationTarget()
            };
        }

        // 현재 위치에서 상호작용 가능한 오브젝트 찾기
        GameObject interactableObject = FindInteractableInCurrentLocation();

        if (interactableObject != null)
        {
            Debug.Log($"상호작용 가능한 오브젝트 찾음: {interactableObject}");
            // 상호작용 가능한 오브젝트가 있으면 상호작용 시작
            StartInteraction(interactableObject);
        }
        else
        {
            // 상호작용 가능한 오브젝트가 없으면 일반 활동 수행
            mCurrentState = AgentState.INTERACTION;
            mCurrentActionTime = 0f;
        }
    }

    // 현재 위치에서 상호작용 가능한 오브젝트 찾기
    private GameObject FindInteractableInCurrentLocation()
    {
        Debug.Log("오브젝트 찾기");
        // 현재 위치에 있는 모든 Interactable 컴포넌트를 가진 오브젝트 찾기
        // 현재 콜라이더 기반으로 찾음, 추후에는 지역에 등록된 오브젝트 가져오는 것으로 변경필요
        Collider2D[] colliders = Physics2D.OverlapCircleAll(transform.position, 2f); // 2f는 상호작용 범위
        
        foreach (Collider2D collider in colliders)
        {
            Interactable interactable = collider.GetComponent<Interactable>();
            if (interactable != null)
            {
                Debug.Log($"발견된 Interactable 오브젝트: {collider.gameObject.name}");
                Debug.Log($"Interactable 컴포넌트: {interactable}");
                Debug.Log($"InteractableData: {interactable.mInteractableData}");
                
                if (interactable.mInteractableData != null)
                {
                    Debug.Log($"InteractableData 이름: {interactable.mInteractableData.mName}");
                }
                
                if (interactable.mInteractableData != null)
                {
                    return collider.gameObject;
                }
            }
        }
        
        return null;
    }

    // 오브젝트와 상호작용 시작
    private void StartInteraction(GameObject interactableObject)
    {
        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}: {interactableObject.name}와(과) 상호작용 시작");
        }
        Debug.Log("상호작용 시작");

        mCurrentState = AgentState.INTERACTION;
        
        // Interactable 컴포넌트의 Interact 메서드 호출
        var interactable = interactableObject.GetComponent<Interactable>();
        if (interactable != null)
        {
            interactable.Interact(gameObject);
        }
        
        // 상호작용 완료 후 활동 완료 처리
        CompleteAction();
    }

    // 현재 활동 완료 처리하는 함수
    private void CompleteAction()
    {
        if (mCurrentAction != null)
        {
            if (mShowDebugInfo)
            {
                Debug.Log($"{mName}: 활동 완료 - {mCurrentAction.ActionName}");
            }
            
            // 스케줄러에 활동 완료 알림
            mScheduler.CompleteCurrentAction();
            
            // 상태 초기화
            mCurrentAction = null;
            mCurrentState = AgentState.IDLE;
        }
    }

    // 활동 시간 증가 함수
    private void UpdateActionTime()
    {
        // 활동 시간 증가
        mCurrentActionTime += Time.deltaTime;
        
        // 최소 지속 시간 이후 활동 완료
        if (mCurrentActionTime >= mActionMinDuration * 60f)
        {
            CompleteAction();
        }
    }

    // 대기 상태로 전환하는 함수
    private void EnterWaitingState(float _waitTimeMinutes)
    {
        mCurrentState = AgentState.WAITING;
        mWaitTime = Mathf.Min(_waitTimeMinutes * 60f, 300f); // 최대 5분 (300초)
        
        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}: 대기 상태 시작 ({_waitTimeMinutes:F1}분)");
        }
    }

    // 대기 상태 업데이트
    private void UpdateWaitTime()
    {
        // 대기 시간 감소
        mWaitTime -= Time.deltaTime;
        
        // 대기 시간 종료 시 상태 변경
        if (mWaitTime <= 0f)
        {
            mCurrentState = AgentState.IDLE;
            
            if (mShowDebugInfo)
            {
                Debug.Log($"{mName}: 대기 상태 종료");
            }
        }
    }

    // 상태 평가 코루틴 (지속적으로 상태 확인)
    // TODO: 코루틴 사용안하고 Update에 넣어서 매 프레임 확인하게 하는것 고려해보기
    private IEnumerator EvaluateStateRoutine()
    {
        while (true)
        {
            // 이미 활동 중이거나 이동 중이면 건너뛰기
            if (mCurrentState != AgentState.IDLE && mCurrentState != AgentState.WAITING)
            {
                yield return new WaitForSeconds(1.0f);
                continue;
            }
            
            // 현재 활동 확인
            string destination = mScheduler.GetCurrentDestinationTarget();

            if (!string.IsNullOrEmpty(destination))
            {
                // 활동 있음 => 위치로 이동 시작
                mCurrentAction = null; // AgentScheduler에서 정보를 다시 가져오기 위해 초기화
                StartMovingToAction();
            }
            else
            {
                // 활동 없음 => 다음 활동까지 대기
                TimeSpan timeUntilNext = mScheduler.GetTimeUntilNextAction();
                
                // 1시간 이상 남았으면 대기 상태로 전환
                if (timeUntilNext.TotalMinutes > 60)
                {
                    EnterWaitingState((float)timeUntilNext.TotalMinutes);
                }
            }
            
            yield return new WaitForSeconds(3.0f);
        }
    }

    // 감정 상태 자동 증가 코루틴
    private IEnumerator AutoIncreaseAgentNeeds()
    {
        TimeSpan lastIncreaseTime = TimeManager.Instance.GetCurrentGameTime();

        while (true)
        {
            yield return new WaitForSeconds(1f); // 1초마다 체크

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
                    Debug.Log($"[게임시간 {currentTime:hh\\:mm}] {mName}의 감정 상태 자동 증가");
                }

                // 마지막 증가 시간 업데이트
                lastIncreaseTime = currentTime;
            }
        }
    }
}
