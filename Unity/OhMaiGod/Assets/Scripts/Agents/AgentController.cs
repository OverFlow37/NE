using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class AgentController : MonoBehaviour
{
    // GET, SET 함수로 접근 가능해야함
    public enum AgentActionState
    {
        IDLE = 0,
        MOVING,
        INTERACTING,   // 오브젝트와 상호작용
        TALKING,
        WAITING,
        SLEEPING,
        EATING,
        DIE,
        MovingToLocation,
        PerformingActivity
    }

    private enum AgentEmoteState
    {
        HUNGER = 0,
        SLEEPINESS,
        LONELINESS,
        HAPPINESS,
        STRESS,
    }

    [Header("Base Profile")]
    [SerializeField] private int mID;                               // 에이전트 고유 식별자
    [SerializeField] private string mName;                          // 이름
    [SerializeField] private string mDescription;                   // 초기 설명    
    [SerializeField] private Transform mVisualRange;                // 시야 범위
    [SerializeField] private float mActivityMinDuration = 1.0f;     // 활동 최소 지속 시간 (분)
    [SerializeField] private bool mAutoStart = true;                // 자동 시작 여부

    private Vector3 mPosition;
    private AgentActionState mCurrentState = AgentActionState.IDLE;

    [SerializeField] private AgentScheduler mScheduler;
    [SerializeField] private MovementController mMovement;

    [Header("디버깅")]
    [SerializeField] private bool mShowDebugInfo = true;            // 디버그 정보 표시 여부

    private float mCurrentActivityTime = 0f;                        // 현재 활동 진행 시간
    private AgentScheduler.ScheduleItem mCurrentActivity = null;    // 현재 활동 정보
    private GameObject mInteractionTarget = null;                   // 상호작용 대상
    private float mWaitTime = 0f;                                   // 대기 시간 (다음 활동까지)
    public AgentActionState CurrentState => mCurrentState;          // 에이전트 현재 상태
    public string AgentName => mName;
    public int AgentID => mID;

    private void Awake()
    {
        // 참조 가져오기
        if (mScheduler == null)
            mScheduler = GetComponent<AgentScheduler>();
            
        if (mMovement == null)
            mMovement = GetComponent<MovementController>();
    }

    private void Start()
    {
        if (mAutoStart)
        {
            // 초기 AI 요청 (실제 구현에서는 AIBridge 사용)
            // 지금은 AgentScheduler의 더미 데이터 사용
            
            // 현재 상태 평가 시작
            StartCoroutine(EvaluateStateRoutine());
        }
    }

    private void Update()
    {
        // 상태별 업데이트 처리
        switch (mCurrentState)
        {
            case AgentActionState.PerformingActivity:
                UpdateActivity();
                break;
                
            case AgentActionState.WAITING:
                UpdateWaiting();
                break;
        }
    }

    // 새 활동 시작 (AgentScheduler에서 호출)
    public void OnNewActivity(AgentScheduler.ScheduleItem _activity)
    {
        if (_activity == null)
        {
            Debug.LogWarning($"{mName}: 잘못된 활동 정보 받음");
            return;
        }

        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}: 새 활동 수신 - {_activity.ActivityName} @ {_activity.LocationName}");
        }

        // 이전 활동 정리
        if (mCurrentActivity != null && mCurrentState == AgentActionState.PerformingActivity)
        {
            CompleteActivity();
        }

        // 새 활동 설정
        mCurrentActivity = _activity;
        
        // 현재 위치가 활동 위치와 다른 경우 이동 시작
        if (NeedsToMoveForActivity(_activity))
        {
            // 활동 위치로 이동 시작
            StartMovingToActivity();
        }
        else
        {
            // 이미 올바른 위치에 있으면 활동 시작
            StartActivity();
        }
    }

    // 목적지 도착 처리 (MovementController에서 호출)
    public void OnReachedDestination()
    {
        if (mCurrentState == AgentActionState.MovingToLocation)
        {
            if (mShowDebugInfo)
            {
                Debug.Log($"{mName}: 목적지 도착 - {mCurrentActivity?.LocationName}");
            }
            
            // 활동 시작
            StartActivity();
        }
    }

    // AI로부터 새 명령 수신
    public void OnAICommandReceived(string _command)
    {
        // TODO: AI 명령 파싱 및 처리 구현
        // 지금은 더미 구현
        Debug.Log($"{mName}이(가) AI 명령 받음: {_command}");
    }

    // 상태 평가 코루틴 (지속적으로 상태 확인)
    private IEnumerator EvaluateStateRoutine()
    {
        while (true)
        {
            // 이미 활동 중이거나 이동 중이면 건너뛰기
            if (mCurrentState != AgentActionState.IDLE && mCurrentState != AgentActionState.WAITING)
            {
                yield return new WaitForSeconds(1.0f);
                continue;
            }
            
            // 현재 활동 확인
            string destination = mScheduler.GetCurrentDestination();
            
            if (!string.IsNullOrEmpty(destination))
            {
                // 활동 있음 - 위치로 이동 시작
                mCurrentActivity = null; // AgentScheduler에서 정보를 다시 가져오기 위해 초기화
                StartMovingToActivity();
            }
            else
            {
                // 활동 없음 - 다음 활동까지 대기
                TimeSpan timeUntilNext = mScheduler.GetTimeUntilNextActivity();
                
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
    private bool NeedsToMoveForActivity(AgentScheduler.ScheduleItem _activity)
    {
        // 현재 위치 확인 로직 구현
        // 지금은 단순히 이름으로 비교
        string currentLocation = GetCurrentLocationName();
        return currentLocation != _activity.LocationName;
    }

    // 현재 위치 이름 가져오기
    private string GetCurrentLocationName()
    {
        // TODO: 실제 위치 확인 로직 구현

        // 지금은 MovementController에서 마지막 도착 위치 사용
        return mMovement?.CurrentDestination ?? string.Empty;
    }

    // 활동 위치로 이동 시작
    private void StartMovingToActivity()
    {
        // 현재 활동 정보 가져오기 (없으면 스케줄러에서 가져오기)
        if (mCurrentActivity == null)
        {
            string activityName = mScheduler.GetCurrentActivityName();
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
            mCurrentActivity = new AgentScheduler.ScheduleItem
            {
                ActivityName = activityName,
                LocationName = destination
            };
        }
        
        // 상태 변경
        mCurrentState = AgentActionState.MovingToLocation;
        
        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}: {mCurrentActivity.LocationName}(으)로 이동 시작 ({mCurrentActivity.ActivityName} 위해)");
        }
        
        // 이동 시작 (도착 시 OnReachedDestination 호출됨)
        mMovement.MoveToLocation(mCurrentActivity.LocationName, OnReachedDestination);
    }

    private void StartActivity()
    {
        // 활동 정보 없으면 스케줄러에서 가져오기
        if (mCurrentActivity == null)
        {
            string activityName = mScheduler.GetCurrentActivityName();
            
            if (activityName == "대기 중")
            {
                // 활동 없음 - 대기 상태로
                mCurrentState = AgentActionState.IDLE;
                return;
            }
            
            // 임시 활동 객체 생성
            mCurrentActivity = new AgentScheduler.ScheduleItem
            {
                ActivityName = activityName,
                LocationName = mScheduler.GetCurrentDestination()
            };
        }
        
        // 상태 변경
        mCurrentState = AgentActionState.PerformingActivity;
        mCurrentActivityTime = 0f;
        
        if (mShowDebugInfo)
        {
            Debug.Log($"{mName}: 활동 시작 - {mCurrentActivity.ActivityName} @ {mCurrentActivity.LocationName}");
        }
        
    }

    private void CompleteActivity()
    {
        if (mCurrentActivity != null)
        {
            if (mShowDebugInfo)
            {
                Debug.Log($"{mName}: 활동 완료 - {mCurrentActivity.ActivityName}");
            }
            
            // 스케줄러에 활동 완료 알림
            mScheduler.CompleteCurrentActivity();
            
            // 상태 초기화
            mCurrentActivity = null;
            mCurrentState = AgentActionState.IDLE;
        }
    }

    private void UpdateActivity()
    {
        // 활동 시간 증가
        mCurrentActivityTime += Time.deltaTime;
        
        // 최소 지속 시간 이후 활동 완료
        if (mCurrentActivityTime >= mActivityMinDuration * 60f)
        {
            CompleteActivity();
        }
    }

    // 대기 상태로 전환
    private void EnterWaitingState(float _waitTimeMinutes)
    {
        mCurrentState = AgentActionState.WAITING;
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
            mCurrentState = AgentActionState.IDLE;
            
            if (mShowDebugInfo)
            {
                Debug.Log($"{mName}: 대기 상태 종료");
            }
        }
    }

    /// 활동 이름에 해당하는 애니메이션 트리거 가져오기
    // private string GetAnimationTriggerForActivity(string _activityName)
    // {
    //     // 활동 이름 기반으로 애니메이션 트리거 결정
    //     // 실제 구현에서는 더 복잡한 매핑 필요
    //     switch (_activityName.ToLower())
    //     {
    //         case "아침 식사":
    //         case "점심 식사":
    //         case "저녁 식사":
    //             return "Eating";
                
    //         case "오전 업무":
    //         case "오후 업무":
    //             return "Working";
                
    //         case "여가 시간":
    //             return "Leisure";
                
    //         case "취침":
    //             return "Sleeping";
                
    //         default:
    //             return "Idle";
    //     }
    // }
}
