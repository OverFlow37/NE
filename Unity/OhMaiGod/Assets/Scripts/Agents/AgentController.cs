using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class AgentController : MonoBehaviour
{
    [SerializeField]
    private AgentUI agentUI;

    // Agent의 행동 상태
    public enum AgentState
    {
        IDLE = 0,
        WAITING,
        MOVING,
        INTERACTING,   // 오브젝트와 상호작용
        MovingToLocation,
        PerformingAction
    }

    // AgentStatus라고 변경하자
    public enum NeedType
    {
        HUNGER = 0,
        SLEEPINESS,
        LONELINESS,
        // HAPPINESS,
        // STRESS,
    }

    [System.Serializable]
    public struct AgentNeeds
    {
        [SerializeField] private int hunger;      // 1-10 범위의 배고픔 수치
        [SerializeField] private int sleepiness;  // 1-10 범위의 졸림 수치
        [SerializeField] private int loneliness;  // 1-10 범위의 외로움 수치

        public int Hunger 
        { 
            get => hunger;
            set => hunger = Mathf.Clamp(value, 1, 10);
        }

        public int Sleepiness
        {
            get => sleepiness;
            set => sleepiness = Mathf.Clamp(value, 1, 10);
        }

        public int Loneliness
        {
            get => loneliness;
            set => loneliness = Mathf.Clamp(value, 1, 10);
        }

        public int GetValue(NeedType _type)
        {
            switch (_type)
            {
                case NeedType.HUNGER:
                    return Hunger;
                case NeedType.SLEEPINESS:
                    return Sleepiness;
                case NeedType.LONELINESS:
                    return Loneliness;
                default:
                    Debug.LogWarning($"알 수 없는 감정 상태: {_type}");
                    return 1;  // 기본값을 최솟값인 1로 반환
            }
        }

        public void SetValue(NeedType _type, int _value)
        {
            // 값을 1-10 범위로 제한
           _value = Mathf.Clamp(_value, 1, 10);

            switch (_type)
            {
                case NeedType.HUNGER:
                    Hunger = _value;
                    break;
                case NeedType.SLEEPINESS:
                    Sleepiness = _value;
                    break;
                case NeedType.LONELINESS:
                    Loneliness = _value;
                    break;
                default:
                    Debug.LogWarning($"알 수 없는 감정 상태: {_type}");
                    break;
            }
        }
    }

    [System.Serializable]
    public struct LocationEmoteEffect
    {
        public string locationName;        // 장소 이름
        [Range(-10, 0)]
        public int hungerEffect;          // 배고픔 변화량
        [Range(-10, 0)]
        public int sleepinessEffect;      // 졸림 변화량
        [Range(-10, 0)]
        public int lonelinessEffect;      // 외로움 변화량
    }

    [Header("Agent States")]
    [SerializeField] private AgentNeeds mEmoteStatus;

    [Header("Location Effects")]
    [SerializeField] private LocationEmoteEffect[] locationEffects;    // 장소별 감정 상태 효과

    // 감정 상태 접근을 위한 public 메서드들
    public AgentNeeds GetEmoteState()
    {
        return mEmoteStatus;
    }

    public int GetEmoteValue(NeedType _type)
    {
        return mEmoteStatus.GetValue(_type);
    }

    public void SetEmoteValue(NeedType _type, int _value)
    {
        mEmoteStatus.SetValue(_type, _value);
    }

    [Header("Base Profile")]
    [SerializeField] private int mID;                               // 에이전트 고유 식별자
    [SerializeField] private string mName;                          // 이름
    [SerializeField] private string mDescription;                   // 초기 설명    
    [SerializeField] private Transform mVisualRange;                // 시야 범위
    [SerializeField] private float mActionMinDuration = 1.0f;       // 활동 최소 지속 시간 (분)
    [SerializeField] private bool mAutoStart = true;                // 자동 시작 여부

    private AgentState mCurrentState = AgentState.IDLE;

    [SerializeField] private AgentScheduler mScheduler;
    [SerializeField] private MovementController mMovement;

    [Header("디버깅")]
    [SerializeField] private bool mShowDebugInfo = true;            // 디버그 정보 표시 여부

    private float mCurrentActionTime = 0f;                          // 현재 활동 진행 시간
    private ScheduleItem mCurrentAction = null;                     // 현재 활동 정보
    // private GameObject mInteractionTarget = null;                // 상호작용 대상
    private float mWaitTime = 0f;                                   // 대기 시간 (다음 활동까지)
    public AgentState CurrentState => mCurrentState;                // 에이전트 현재 상태
    public string AgentName => mName;                               // 에이전트 이름
    public int AgentID => mID;                                      // 에이전트 ID

    private Animator animator;  // 애니메이터

    private void Awake()
    {
        // 참조 가져오기
        if (mScheduler == null)
            mScheduler = GetComponent<AgentScheduler>();
            
        if (mMovement == null)
            mMovement = GetComponent<MovementController>();

        // MovementController의 목적지 도착 이벤트 구독
        if (mMovement != null)
        {
            mMovement.OnDestinationReached += HandleDestinationReached;
        }

        // 감정 상태 초기화
        mEmoteStatus.SetValue(NeedType.HUNGER, 1);
        mEmoteStatus.SetValue(NeedType.SLEEPINESS, 1);
        mEmoteStatus.SetValue(NeedType.LONELINESS, 1);

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

        // 도착한 위치에 따라 감정 상태 업데이트
        UpdateEmoteStateByLocation(mMovement.TargetName);

        // 활동 시작
        StartAction();
    }

    private void Start()
    {
        if (mAutoStart)
        {
            // 현재 상태 평가 시작
            StartCoroutine(EvaluateStateRoutine());

            // 감정 상태 자동 증가 시작
            StartCoroutine(AutoIncreaseEmoteStates());
        }
    }

    private void Update()
    {
        // 상태별 업데이트 처리
        switch (mCurrentState)
        {
            case AgentState.PerformingAction:
                UpdateAction();
                break;
                
            case AgentState.WAITING:
                UpdateWaiting();
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
        if (mCurrentAction != null && mCurrentState == AgentState.PerformingAction)
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

    // 위치에 따른 감정 상태 업데이트
    private void UpdateEmoteStateByLocation(string locationName)
    {
        if (string.IsNullOrEmpty(locationName)) return;

        // 해당 장소의 효과 찾기
        var locationEffect = System.Array.Find(locationEffects, 
            effect => effect.locationName.ToLower() == locationName.ToLower());

        if (locationEffect.locationName != null)
        {
            // 각 감정 상태에 효과 적용
            // SetEmoteValue(EmoteType.HUNGER, GetEmoteValue(EmoteType.HUNGER) + locationEffect.hungerEffect);
            // SetEmoteValue(EmoteType.SLEEPINESS, GetEmoteValue(EmoteType.SLEEPINESS) + locationEffect.sleepinessEffect);
            // SetEmoteValue(EmoteType.LONELINESS, GetEmoteValue(EmoteType.LONELINESS) + locationEffect.lonelinessEffect);

            mEmoteStatus.Hunger += locationEffect.hungerEffect;
            mEmoteStatus.Sleepiness += locationEffect.sleepinessEffect;
            mEmoteStatus.Loneliness += locationEffect.lonelinessEffect;

            if (mShowDebugInfo)
            {
                Debug.Log($"{mName}의 현재 상태 - 배고픔: {mEmoteStatus.Hunger}, " +
                         $"졸림: {mEmoteStatus.Sleepiness}, " +
                         $"외로움: {mEmoteStatus.Loneliness}");

                // Debug.Log($"{mName}의 현재 상태 - 배고픔: {GetEmoteValue(EmoteType.HUNGER)}, " +
                //          $"졸림: {GetEmoteValue(EmoteType.SLEEPINESS)}, " +
                //          $"외로움: {GetEmoteValue(EmoteType.LONELINESS)}");
            }
        }
    }

    // 상태 평가 코루틴 (지속적으로 상태 확인)
    // 코루틴 사용안하고 Update에 넣어서 매 프레임 확인하게 하는것 고려해보기
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
            string destination = mScheduler.GetCurrentDestination();
            
            if (!string.IsNullOrEmpty(destination))
            {
                // 활동 있음 - 위치로 이동 시작
                mCurrentAction = null; // AgentScheduler에서 정보를 다시 가져오기 위해 초기화
                StartMovingToAction();
            }
            else
            {
                // 활동 없음 - 다음 활동까지 대기
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

    // 활동을 위해 이동 필요한지 확인
    private bool NeedsToMoveForAction(ScheduleItem _action)
    {
        // 현재 위치 확인 로직 구현
        // 지금은 단순히 이름으로 비교
        string currentLocation = GetCurrentLocationName();
        return currentLocation != _action.LocationName;
    }

    // 현재 위치 이름 가져오기 
    private string GetCurrentLocationName()
    {
        // TODO: EnvironmentSystem 만들어지면 WorldTree 통해서 이름 얻어오는 부분 구현해야 함

        // 지금은 MovementController에서 마지막 도착 위치 사용
        return mMovement?.TargetName ?? string.Empty;
    }

    // 활동 위치로 이동 시작
    private void StartMovingToAction()
    {
        // 현재 활동 정보 가져오기 (없으면 스케줄러에서 가져오기)
        if (mCurrentAction == null)
        {
            string actionName = mScheduler.GetCurrentActionName();
            string destination = mScheduler.GetCurrentDestination();
            
            if (string.IsNullOrEmpty(destination))
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
                LocationName = destination
            };
        }
        
        // 상태 변경
        mCurrentState = AgentState.MovingToLocation;
        
        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}: {mCurrentAction.LocationName}(으)로 이동 시작 ({mCurrentAction.ActionName} 위해)");
        }
        
        // 이동 시작
        mMovement.MoveToLocation(mCurrentAction.LocationName);

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
                LocationName = mScheduler.GetCurrentDestination()
            };
        }
        
        // 상태 변경
        mCurrentState = AgentState.PerformingAction;
        mCurrentActionTime = 0f;
        
        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}: 활동 시작 - {mCurrentAction.ActionName} @ {mCurrentAction.LocationName}");
        }
        
    }

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

    private void UpdateAction()
    {
        // 활동 시간 증가
        mCurrentActionTime += Time.deltaTime;
        
        // 최소 지속 시간 이후 활동 완료
        if (mCurrentActionTime >= mActionMinDuration * 60f)
        {
            CompleteAction();
        }
    }

    // 대기 상태로 전환
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
    private void UpdateWaiting()
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

    // 감정 상태 자동 증가 코루틴
    private IEnumerator AutoIncreaseEmoteStates()
    {
        TimeSpan lastIncreaseTime = mScheduler.GetCurrentGameTime();

        while (true)
        {
            yield return new WaitForSeconds(1f); // 1초마다 체크

            TimeSpan currentTime = mScheduler.GetCurrentGameTime();
            TimeSpan timeDifference = currentTime - lastIncreaseTime;

            // 게임 시간으로 30분이 지났는지 확인
            if (timeDifference.TotalMinutes >= 30)
            {
                // 각 감정 상태 증가
                SetEmoteValue(NeedType.HUNGER, GetEmoteValue(NeedType.HUNGER) + 1);
                SetEmoteValue(NeedType.SLEEPINESS, GetEmoteValue(NeedType.SLEEPINESS) + 1);
                SetEmoteValue(NeedType.LONELINESS, GetEmoteValue(NeedType.LONELINESS) + 1);

                if (mShowDebugInfo)
                {
                    Debug.Log($"[게임시간 {currentTime:hh\\:mm}] {mName}의 감정 상태 자동 증가 - " +
                            $"배고픔: {GetEmoteValue(NeedType.HUNGER)}, " +
                            $"졸림: {GetEmoteValue(NeedType.SLEEPINESS)}, " +
                            $"외로움: {GetEmoteValue(NeedType.LONELINESS)}");
                }

                // 마지막 증가 시간 업데이트
                lastIncreaseTime = currentTime;
            }
        }
    }
}
