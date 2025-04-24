using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public class AgentScheduler : MonoBehaviour
{
    [Serializable]
    public class ScheduleItem
    {
        public string Id;                  // 활동 고유 식별자
        public string ActivityName;        // 활동 이름
        public string LocationName;        // 목적지 위치 이름
        public TimeSpan StartTime;         // 시작 시간 (하루 중)
        public TimeSpan EndTime;           // 종료 시간 (하루 중)
        public int Priority;               // 우선순위 (높을수록 중요)
        public bool IsFlexible;            // 시간이 유연한지 여부
        public bool IsCompleted;           // 완료 여부
        public string ActivityDetails;     // 활동에 대한 추가 정보 (JSON)

        // 시간 충돌 검사
        public bool ConflictsWith(ScheduleItem other)
        {
            // 시작 또는 종료 시간이 다른 활동 범위 내에 있는지 확인
            return (StartTime >= other.StartTime && StartTime < other.EndTime) ||
                   (EndTime > other.StartTime && EndTime <= other.EndTime) ||
                   (StartTime <= other.StartTime && EndTime >= other.EndTime);
        }
    }

    [Header("시간 설정")]
    [SerializeField] private float mGameToRealTimeRatio = 60.0f; // 게임 시간 흐름 비율 (기본: 1분 = 1초)
    
    [Header("디버깅")]
    [SerializeField] private bool mShowDebugInfo = true;

    // 스케줄 관리
    private List<ScheduleItem> mDailySchedule = new List<ScheduleItem>();
    private ScheduleItem mCurrentActivity = null;
    private ScheduleItem mNextActivity = null;
    
    
    private TimeSpan mCurrentGameTime;
    private DateTime mGameDate;
    private bool mIsPaused = false;

    private AgentController mAgentController;


    private void Awake()
    {
        // 에이전트 컨트롤러 참조 가져오기
        mAgentController = GetComponent<AgentController>();
        
        // 기본 일정 생성 (빈 일정으로 초기화)
        ResetSchedule();
        
        // 게임 날짜 및 시간 초기화 (오전 8시 시작)
        mGameDate = DateTime.Today;
        mCurrentGameTime = new TimeSpan(8, 0, 0);
    }

    private void Update()
    {
        if (mIsPaused) return;
        
        // 게임 시간 업데이트
        UpdateGameTime();
        
        // 현재 활동 평가
        EvaluateCurrentActivity();
    }

    // 새로운 일정 항목 추가
    public bool AddScheduleItem(ScheduleItem _item)
    {
        // ID 중복 확인
        if (mDailySchedule.Any(item => item.Id == _item.Id))
        {
            Debug.LogWarning($"중복된 ID의 일정 항목: {_item.Id}");
            return false;
        }
        
        // 기존 일정 모두 취소하고 새 일정만 추가
        ClearSchedule();
        
        /* 충돌 확인 (우선순위가 낮은 경우만 충돌 거부)
        var conflictingItems = mDailySchedule.Where(item => 
            !item.IsCompleted && 
            item.ConflictsWith(_item) && 
            item.Priority >= _item.Priority).ToList();
        
        if (conflictingItems.Count > 0)
        {
            if (mShowDebugInfo)
            {
                Debug.Log($"일정 충돌 발생: {_item.ActivityName} @ {_item.StartTime}");
                foreach (var conflict in conflictingItems)
                {
                    Debug.Log($" - 충돌 항목: {conflict.ActivityName} @ {conflict.StartTime}");
                }
            }
            return false;
        }
        */
        
        // 일정에 항목 추가
        mDailySchedule.Add(_item);
        
        // 일정 재정렬
        SortSchedule();
        
        if (mShowDebugInfo)
        {
            Debug.Log($"새 일정 추가됨: {_item.ActivityName} @ {_item.StartTime}-{_item.EndTime}");
        }
        
        return true;
    }

    // 일정 항목 삭제
    public bool RemoveScheduleItem(string _itemId)
    {
        int initialCount = mDailySchedule.Count;
        mDailySchedule.RemoveAll(item => item.Id == _itemId);
        
        bool removed = mDailySchedule.Count < initialCount;
        
        if (removed)
        {
            // 현재 활동이 삭제된 경우 재평가
            if (mCurrentActivity != null && mCurrentActivity.Id == _itemId)
            {
                mCurrentActivity = null;
                EvaluateCurrentActivity();
            }
            
            if (mShowDebugInfo)
            {
                Debug.Log($"일정 항목 삭제됨: {_itemId}");
            }
        }
        
        return removed;
    }

    // 전체 일정 갱신
    public void UpdateSchedule(List<ScheduleItem> _newSchedule)
    {
        // 현재 진행 중인 활동은 보존
        ScheduleItem currentActivity = mCurrentActivity;
        
        // 완료된 활동 목록 보존
        var completedActivities = mDailySchedule
            .Where(item => item.IsCompleted)
            .ToList();
        
        // 새 일정으로 교체 (우선순위 기준 정렬)
        mDailySchedule = _newSchedule
            .OrderBy(item => item.StartTime)
            .ThenByDescending(item => item.Priority)
            .ToList();
        
        // 완료된 활동 상태 복원
        foreach (var completed in completedActivities)
        {
            var matchingItem = mDailySchedule.FirstOrDefault(item => item.Id == completed.Id);
            if (matchingItem != null)
            {
                matchingItem.IsCompleted = true;
            }
        }
        
        // 활동 재평가
        EvaluateCurrentActivity();
        
        if (mShowDebugInfo)
        {
            Debug.Log($"전체 일정 갱신됨: {mDailySchedule.Count}개 항목");
        }
    }

    // 현재 활동 완료 처리
    public void CompleteCurrentActivity()
    {
        if (mCurrentActivity != null)
        {
            mCurrentActivity.IsCompleted = true;
            
            if (mShowDebugInfo)
            {
                Debug.Log($"활동 완료: {mCurrentActivity.ActivityName}");
            }
            
            // 다음 활동 평가
            mCurrentActivity = null;
            EvaluateCurrentActivity();
        }
    }

    // 현재 활동의 목적지 가져오기
    // 반환: 목적지 위치 이름 (활동이 없으면 빈 문자열)
    public string GetCurrentDestination()
    {
        return mCurrentActivity?.LocationName ?? string.Empty;
    }

    // 현재 활동 이름 가져오기
    // 반환: 활동 이름 (활동이 없으면 "대기 중")
    public string GetCurrentActivityName()
    {
        return mCurrentActivity?.ActivityName ?? "대기 중";
    }

    // 다음 활동 시작까지 남은 시간
    // 반환: 남은 시간 (TimeSpan)
    public TimeSpan GetTimeUntilNextActivity()
    {
        if (mNextActivity == null) return TimeSpan.MaxValue;
        
        return mNextActivity.StartTime - mCurrentGameTime;
    }

    // 현재 게임 내 시간 가져오기
    // 반환: 현재 게임 시간
    public TimeSpan GetCurrentGameTime()
    {
        return mCurrentGameTime;
    }

    // 현재 게임 날짜 가져오기
    // <returns>현재 게임 날짜</returns>
    public DateTime GetCurrentGameDate()
    {
        return mGameDate;
    }

    // 시간 흐름 일시정지/재개
    public void SetPaused(bool _paused)
    {
        mIsPaused = _paused;
    }

    // 게임 시간 업데이트
    private void UpdateGameTime()
    {
        // 실제 시간을 게임 시간으로 변환
        mCurrentGameTime = mCurrentGameTime.Add(TimeSpan.FromSeconds(Time.deltaTime * mGameToRealTimeRatio));
        
        // 날짜 변경 확인
        if (mCurrentGameTime.Days > 0)
        {
            mGameDate = mGameDate.AddDays(1);
            mCurrentGameTime = new TimeSpan(mCurrentGameTime.Hours, mCurrentGameTime.Minutes, mCurrentGameTime.Seconds);
            
            // 새 날에 대한 일정 초기화
            ResetSchedule();
        }
    }

    // 현재 시간에 맞는 활동 평가
    private void EvaluateCurrentActivity()
    {
        // 현재 활동이 있고 아직 유효한 경우
        if (mCurrentActivity != null)
        {
            // 활동 종료 시간이 지났는지 확인
            if (mCurrentGameTime > mCurrentActivity.EndTime)
            {
                if (!mCurrentActivity.IsCompleted)
                {
                    // 자동으로 완료 처리
                    mCurrentActivity.IsCompleted = true;
                    
                    if (mShowDebugInfo)
                    {
                        Debug.Log($"활동 자동 완료 (시간 초과): {mCurrentActivity.ActivityName}");
                    }
                }
                
                // 활동 종료 및 다음 활동 평가
                mCurrentActivity = null;
            }
            else
            {
                // 현재 활동이 계속 유효함
                return;
            }
        }
        
        // 시간순으로 다음 활동 찾기
        mCurrentActivity = null;
        mNextActivity = null;
        
        // 미완료 활동 중 현재 시간에 해당하는 것 찾기
        var currentTimeActivities = mDailySchedule
            .Where(item => !item.IsCompleted && 
                   mCurrentGameTime >= item.StartTime && 
                   mCurrentGameTime < item.EndTime)
            .OrderByDescending(item => item.Priority)
            .ToList();
        
        if (currentTimeActivities.Count > 0)
        {
            // 현재 시간에 가장 우선순위 높은 활동 선택
            mCurrentActivity = currentTimeActivities[0];
            
            if (mShowDebugInfo)
            {
                Debug.Log($"새 활동 시작: {mCurrentActivity.ActivityName} @ {mCurrentActivity.LocationName}");
            }
            
            // 에이전트에 활동 시작 알림
            if (mAgentController != null)
            {
                mAgentController.OnNewActivity(mCurrentActivity);
            }
        }
        else
        {
            // 다음으로 예정된 활동 찾기
            var futureActivities = mDailySchedule
                .Where(item => !item.IsCompleted && mCurrentGameTime < item.StartTime)
                .OrderBy(item => item.StartTime)
                .ToList();
            
            if (futureActivities.Count > 0)
            {
                mNextActivity = futureActivities[0];
                
                if (mShowDebugInfo)
                {
                    TimeSpan timeUntilNext = mNextActivity.StartTime - mCurrentGameTime;
                    Debug.Log($"다음 활동: {mNextActivity.ActivityName} (남은 시간: {timeUntilNext.Hours}시간 {timeUntilNext.Minutes}분)");
                }
            }
        }
    }

    // 일정 정렬 (시간순, 우선순위순)
    private void SortSchedule()
    {
        mDailySchedule = mDailySchedule
            .OrderBy(item => item.StartTime)
            .ThenByDescending(item => item.Priority)
            .ToList();
    }

    // 일정 초기화
    private void ResetSchedule()
    {
        mDailySchedule.Clear();
        mCurrentActivity = null;
        mNextActivity = null;
    }

    public void SetTimeScale(float _minutesPerSecond)
    {
        mGameToRealTimeRatio = _minutesPerSecond;

        if (mShowDebugInfo)
        {
            Debug.Log($"시간 속도 변경: {_minutesPerSecond}분/초");
        }
    }

    public void ClearSchedule()
    {
        // 현재 활동 외의 항목 모두 삭제
        var currentActivity = mCurrentActivity;
        mDailySchedule.Clear();
        
        // 현재 활동이 있다면 유지
        if (currentActivity != null)
        {
            mDailySchedule.Add(currentActivity);
        }
        
        mNextActivity = null;
        
        if (mShowDebugInfo)
        {
            Debug.Log("모든 스케줄 항목 삭제됨");
        }
    }

    // 테스트용 더미 일정 생성
    private void CreateDummySchedule()
    {
        // 아침 식사
        AddScheduleItem(new ScheduleItem
        {
            Id = "breakfast",
            ActivityName = "아침 식사",
            LocationName = "Kitchen",
            StartTime = new TimeSpan(8, 0, 0),
            EndTime = new TimeSpan(8, 30, 0),
            Priority = 5,
            IsFlexible = false
        });
        
        // 오전 일과
        AddScheduleItem(new ScheduleItem
        {
            Id = "morning_work",
            ActivityName = "오전 업무",
            LocationName = "Desk",
            StartTime = new TimeSpan(9, 0, 0),
            EndTime = new TimeSpan(9, 30, 0),
            Priority = 8,
            IsFlexible = false
        });
        
        // 점심 식사
        AddScheduleItem(new ScheduleItem
        {
            Id = "lunch",
            ActivityName = "점심 식사",
            LocationName = "Cafeteria",
            StartTime = new TimeSpan(10, 0, 0),
            EndTime = new TimeSpan(10, 30, 0),
            Priority = 5,
            IsFlexible = true
        });
        
        // 오후 일과
        AddScheduleItem(new ScheduleItem
        {
            Id = "afternoon_work",
            ActivityName = "오후 업무",
            LocationName = "Desk",
            StartTime = new TimeSpan(11, 0, 0),
            EndTime = new TimeSpan(11, 30, 0),
            Priority = 8,
            IsFlexible = false
        });
        
        // 저녁 식사
        AddScheduleItem(new ScheduleItem
        {
            Id = "dinner",
            ActivityName = "저녁 식사",
            LocationName = "Kitchen",
            StartTime = new TimeSpan(12, 0, 0),
            EndTime = new TimeSpan(12, 30, 0),
            Priority = 5,
            IsFlexible = true
        });
        
        // 여가 시간
        AddScheduleItem(new ScheduleItem
        {
            Id = "leisure",
            ActivityName = "여가 시간",
            LocationName = "LivingRoom",
            StartTime = new TimeSpan(13, 0, 0),
            EndTime = new TimeSpan(13, 30, 0),
            Priority = 3,
            IsFlexible = true
        });
        
        // 취침
        AddScheduleItem(new ScheduleItem
        {
            Id = "sleep",
            ActivityName = "취침",
            LocationName = "Bedroom",
            StartTime = new TimeSpan(14, 0, 0),
            EndTime = new TimeSpan(14, 30, 30),
            Priority = 7,
            IsFlexible = false
        });
    }

}