using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 인스펙터에서 직접 에이전트의 스케줄을 테스트하기 위한 컴포넌트
/// </summary>
public class ScheduleTester : MonoBehaviour
{
    [Header("에이전트 참조")]
    [SerializeField] private AgentController mTargetAgent;

    [Header("현재 시간 정보")]
    [SerializeField] private float mTimeScale = 60f; // 분/초
    [SerializeField] private string mCurrentTime = "00:00";
    [SerializeField] private string mCurrentActivity = "없음";

    [Header("활동 추가")]
    [SerializeField] private string mActivityName = "식사하기";
    [SerializeField] private string mLocationName = "Kitchen";
    [SerializeField] private string mStartTime = "08:00";
    [SerializeField] private string mEndTime = "08:30";
    [SerializeField] private int mPriority = 5;
    [SerializeField] private bool mIsFlexible = false;

    [Header("액션")]
    [SerializeField] private bool mAddActivity = false;
    [SerializeField] private bool mCompleteCurrentActivity = false;
    [SerializeField] private bool mClearAllSchedule = false;
    [SerializeField] private bool mApplyTimeScale = false;

    // 내부 참조
    private AgentScheduler mScheduler;

    private void Start()
    {
        if (mTargetAgent != null)
        {
            mScheduler = mTargetAgent.GetComponent<AgentScheduler>();
        }
        else
        {
            Debug.LogError("대상 에이전트가 설정되지 않았습니다.");
        }

        // 매 프레임 업데이트가 아닌 주기적 업데이트 시작
        StartCoroutine(UpdateInfoRoutine());
    }

    private void Update()
    {
        // 인스펙터에서 버튼 액션 처리
        if (mAddActivity)
        {
            mAddActivity = false;
            AddActivity();
        }

        if (mCompleteCurrentActivity)
        {
            mCompleteCurrentActivity = false;
            CompleteCurrentActivity();
        }

        if (mClearAllSchedule)
        {
            mClearAllSchedule = false;
            ClearAllSchedule();
        }

        if (mApplyTimeScale)
        {
            mApplyTimeScale = false;
            ApplyTimeScale();
        }
    }

    /// <summary>
    /// 현재 정보 업데이트 코루틴
    /// </summary>
    private IEnumerator UpdateInfoRoutine()
    {
        while (true)
        {
            if (mScheduler != null)
            {
                // 현재 시간 정보 업데이트
                TimeSpan currentTime = mScheduler.GetCurrentGameTime();
                mCurrentTime = $"{currentTime.Hours:D2}:{currentTime.Minutes:D2}";
                
                // 현재 활동 정보 업데이트
                string activity = mScheduler.GetCurrentActivityName();
                string location = mScheduler.GetCurrentDestination();
                
                if (!string.IsNullOrEmpty(location))
                {
                    mCurrentActivity = $"{activity} @ {location}";
                }
                else
                {
                    mCurrentActivity = activity;
                }
            }

            yield return new WaitForSeconds(0.5f);
        }
    }

    /// <summary>
    /// 인스펙터에서 설정한 값으로 활동 추가
    /// </summary>
    public void AddActivity()
    {
        if (mScheduler == null)
        {
            Debug.LogError("스케줄러 참조가 없습니다.");
            return;
        }

        try
        {
            // 시간 파싱
            TimeSpan startTime = ParseTimeInput(mStartTime);
            TimeSpan endTime = ParseTimeInput(mEndTime);

            if (endTime <= startTime)
            {
                Debug.LogError("종료 시간은 시작 시간보다 나중이어야 합니다.");
                return;
            }

            // 스케줄 아이템 생성
            AgentScheduler.ScheduleItem item = new AgentScheduler.ScheduleItem
            {
                Id = $"test_{System.Guid.NewGuid().ToString().Substring(0, 8)}",
                ActivityName = mActivityName,
                LocationName = mLocationName,
                StartTime = startTime,
                EndTime = endTime,
                Priority = mPriority,
                IsFlexible = mIsFlexible
            };

            // 스케줄에 추가
            bool success = mScheduler.AddScheduleItem(item);
            
            if (success)
            {
                Debug.Log($"새 활동 추가됨: {mActivityName} @ {mLocationName} ({startTime}-{endTime})");
            }
            else
            {
                Debug.LogWarning("활동 추가 실패. 기존 활동과 충돌이 있을 수 있습니다.");
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"스케줄 추가 실패: {ex.Message}");
        }
    }

    /// <summary>
    /// 시간 문자열 파싱 (시:분 또는 시:분:초 형식)
    /// </summary>
    private TimeSpan ParseTimeInput(string timeString)
    {
        // 시:분 형식 확인
        if (timeString.Split(':').Length == 2)
        {
            timeString += ":00"; // 초 추가
        }

        return TimeSpan.Parse(timeString);
    }

    /// <summary>
    /// 현재 활동 완료 처리
    /// </summary>
    public void CompleteCurrentActivity()
    {
        if (mScheduler != null)
        {
            mScheduler.CompleteCurrentActivity();
            Debug.Log("현재 활동 완료 처리됨");
        }
    }

    /// <summary>
    /// 모든 스케줄 지우기
    /// </summary>
    public void ClearAllSchedule()
    {
        if (mScheduler != null)
        {
            mScheduler.ClearSchedule();
            Debug.Log("모든 스케줄 지움");
        }
    }

    /// <summary>
    /// 시간 속도 적용
    /// </summary>
    public void ApplyTimeScale()
    {
        if (mScheduler != null)
        {
            mScheduler.SetTimeScale(mTimeScale);
            Debug.Log($"시간 속도 변경: {mTimeScale}분/초");
        }
    }

    /// <summary>
    /// 빠른 테스트를 위한 사전 정의된 일정 추가
    /// </summary>
    [ContextMenu("Add Test Schedule")]
    public void AddTestSchedule()
    {
        if (mScheduler == null) return;

        // 현재 시간 가져오기
        TimeSpan currentTime = mScheduler.GetCurrentGameTime();
        int currentHour = currentTime.Hours;
        
        // 다음 시간부터 일정 추가 (현재 시간 + 15분부터)
        int startHour = currentHour;
        int startMinute = (currentTime.Minutes + 15) % 60;
        if (startMinute < currentTime.Minutes) startHour = (currentHour + 1) % 24;
        
        // 15분 후 활동
        AddCustomActivity("휴식하기", $"{startHour:D2}:{startMinute:D2}", 
            $"{startHour:D2}:{(startMinute + 15) % 60:D2}", "LivingRoom", 5);
        
        // 30분 후 활동
        int nextHour = startHour;
        int nextMinute = (startMinute + 15) % 60;
        if (nextMinute < startMinute) nextHour = (startHour + 1) % 24;
        
        AddCustomActivity("식사하기", $"{nextHour:D2}:{nextMinute:D2}", 
            $"{nextHour:D2}:{(nextMinute + 30) % 60:D2}", "Kitchen", 8);
        
        Debug.Log("테스트 스케줄 추가 완료");
    }

    /// <summary>
    /// 커스텀 활동 추가 도우미 메서드
    /// </summary>
    private void AddCustomActivity(string activity, string start, string end, string location, int priority)
    {
        try
        {
            TimeSpan startTime = ParseTimeInput(start);
            TimeSpan endTime = ParseTimeInput(end);
            
            AgentScheduler.ScheduleItem item = new AgentScheduler.ScheduleItem
            {
                Id = $"test_{System.Guid.NewGuid().ToString().Substring(0, 8)}",
                ActivityName = activity,
                LocationName = location,
                StartTime = startTime,
                EndTime = endTime,
                Priority = priority,
                IsFlexible = false
            };
            
            mScheduler.AddScheduleItem(item);
            Debug.Log($"추가: {activity} @ {location} ({start}-{end})");
        }
        catch (Exception ex)
        {
            Debug.LogError($"활동 추가 실패: {ex.Message}");
        }
    }
}