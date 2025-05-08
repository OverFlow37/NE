using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using OhMAIGod.Agent;

public class AgentScheduler : MonoBehaviour
{
    [Header("디버깅")]
    [SerializeField] private bool mShowDebugInfo = true; // 디버그 로그 출력 여부

    // ==== 스케줄 관리 변수들 ====
    private List<ScheduleItem> mDailySchedule = new List<ScheduleItem>();   // 하루 전체 일정 목록
    private ScheduleItem mCurrentAction = null;                             // 현재 수행 중인 활동
    private ScheduleItem mNextAction = null;                                // 다음 예정된 활동

    private AgentController mAgentController;  // 에이전트 동작 제어를 위한 컨트롤러 참조

    private void Awake()
    {
        // 에이전트 컨트롤러 참조 가져오기
        mAgentController = GetComponent<AgentController>();
        
        // 기본 일정 생성 (빈 일정으로 초기화)
        ResetSchedule();
    }

    private void Update()
    {
        if (TimeManager.Instance.isPaused) return;
        
        // 현재 활동 업데이트
        UpdateAction();
    }

    // 새로운 일정 항목 추가
    public bool AddScheduleItem(ScheduleItem _item)
    {
        // ID 중복 확인
        if (mDailySchedule.Any(item => item.ID == _item.ID))
        {
            LogManager.Log("Scheduler", $"중복된 ID의 일정 항목: {_item.ID}", 1);
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
                LogManager.Log("AgentScheduler", $"일정 충돌 발생: {_item.ActionName} @ {_item.StartTime}", 1);
                foreach (var conflict in conflictingItems)
                {
                    LogManager.Log("AgentScheduler", $" - 충돌 항목: {conflict.ActionName} @ {conflict.StartTime}", 1);
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
            LogManager.Log("Scheduler", $"새 일정 추가됨: {_item.ActionName} @ {_item.StartTime}-{_item.EndTime}", 2);
        }
        
        return true;
    }

    // 지정된 ID의 일정 항목을 삭제하는 함수
    public bool RemoveScheduleItem(string _itemID)
    {
        int initialCount = mDailySchedule.Count;
        mDailySchedule.RemoveAll(item => item.ID == _itemID);
        
        bool removed = mDailySchedule.Count < initialCount;
        
        if (removed)
        {
            // 현재 활동이 삭제된 경우 재평가
            if (mCurrentAction != null && mCurrentAction.ID == _itemID)
            {
                mCurrentAction = null;
                UpdateAction();
            }
            
            if (mShowDebugInfo)
            {
                LogManager.Log("Scheduler", $"일정 항목 삭제됨: {_itemID}", 2);
            }
        }
        
        return removed;
    }

    // 전체 일정 갱신
    public void UpdateSchedule(List<ScheduleItem> _newSchedule)
    {
        // 현재 진행 중인 활동은 보존
        ScheduleItem currentAction = mCurrentAction;
        
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
            var matchingItem = mDailySchedule.FirstOrDefault(item => item.ID == completed.ID);
            if (matchingItem != null)
            {
                matchingItem.IsCompleted = true;
            }
        }
        
        // 활동 재평가
        UpdateAction();
        
        if (mShowDebugInfo)
        {
            LogManager.Log("Scheduler", $"전체 일정 갱신됨: {mDailySchedule.Count}개 항목", 2);
        }
    }

    // 현재 활동 완료 처리
    public void CompleteCurrentAction()
    {
        if (mCurrentAction != null)
        {
            mCurrentAction.IsCompleted = true;
            
            if (mShowDebugInfo)
            {
                LogManager.Log("Scheduler", $"활동 완료: {mCurrentAction.ActionName}", 2);
            }
            
            // 다음 활동 평가
            mCurrentAction = null;
            UpdateAction();
        }
    }

    // 현재 활동의 목적지 반환하는 함수 (없으면 빈 문자열 반환)
    public string GetCurrentDestinationLocation()
    {
        return mCurrentAction?.LocationName ?? string.Empty;
    }

    // 현재 활동의 목적지 이름 반환하는 함수 (없으면 빈 문자열 반환)
    public string GetCurrentDestinationTarget()
    {
        return mCurrentAction?.TargetName ?? string.Empty;
    }

    // 현재 활동 이름 반환하는 함수 (없으면 "대기 중" 반환)
    public string GetCurrentActionName()
    {
        return mCurrentAction?.ActionName ?? "대기 중";
    }

    // 다음 활동 시작까지 남은 시간 반환하는 함수
    public TimeSpan GetTimeUntilNextAction()
    {
        if (mNextAction == null) return TimeSpan.MaxValue;
        
        return mNextAction.StartTime - TimeManager.Instance.GetCurrentGameTime();
    }

    // 현재 시간에 맞는 활동 시작하게 업데이트 하는 함수
    private void UpdateAction()
    {
        // 현재 활동이 있고 아직 유효한 경우
        if (mCurrentAction != null)
        {
            // 활동 종료 시간이 지났는지 확인
            if (TimeManager.Instance.GetCurrentGameTime() > mCurrentAction.EndTime)
            {
                if (!mCurrentAction.IsCompleted)
                {
                    // 자동으로 완료 처리
                    mCurrentAction.IsCompleted = true;
                    
                    if (mShowDebugInfo)
                    {
                        LogManager.Log("Scheduler", $"활동 자동 완료 (시간 초과): {mCurrentAction.ActionName}", 2);
                    }
                }
                
                // 활동 종료
                mCurrentAction = null;
            }
            else
            {
                // 현재 활동이 계속 유효함
                return;
            }
        }
        
        // 시간순으로 다음 활동 찾기
        mCurrentAction = null;
        mNextAction = null;
        
        // 미완료 활동 중 현재 시간에 해당하는 것 찾기
        var currentTimeActivities = mDailySchedule
            .Where(item => !item.IsCompleted && 
                   TimeManager.Instance.GetCurrentGameTime() >= item.StartTime && 
                   TimeManager.Instance.GetCurrentGameTime() < item.EndTime)
            .OrderByDescending(item => item.Priority)
            .ToList();
        
        if (currentTimeActivities.Count > 0)
        {
            // 현재 시간에 가장 우선순위 높은 활동 선택
            mCurrentAction = currentTimeActivities[0];
            
            if (mShowDebugInfo)
            {
                LogManager.Log("Scheduler", $"새 활동 시작: {mCurrentAction.ActionName} @ {mCurrentAction.LocationName}", 2);
            }
            
            // 에이전트에 활동 시작 알림
            if (mAgentController != null)
            {
                mAgentController.StartNewAction(mCurrentAction);
            }
        }
        else
        {
            // 다음으로 예정된 활동 찾기
            var futureActivities = mDailySchedule
                .Where(item => !item.IsCompleted && TimeManager.Instance.GetCurrentGameTime() < item.StartTime)
                .OrderBy(item => item.StartTime)
                .ToList();
            
            if (futureActivities.Count > 0)
            {
                mNextAction = futureActivities[0];
                
                if (mShowDebugInfo)
                {
                    TimeSpan timeUntilNext = mNextAction.StartTime - TimeManager.Instance.GetCurrentGameTime();
                    LogManager.Log("Scheduler", $"다음 활동: {mNextAction.ActionName} (남은 시간: {timeUntilNext.Hours}시간 {timeUntilNext.Minutes}분)", 2);
                }
            }
        }
    }

    // 일정 정렬 (시간순 -> 우선순위순)
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
        mCurrentAction = null;
        mNextAction = null;
    }

    // 현재 진행 중인 활동을 제외한 모든 일정 삭제하는 함수
    public void ClearSchedule()
    {
        // 현재 활동 외의 항목 모두 삭제
        var currentAction = mCurrentAction;
        mDailySchedule.Clear();
        
        // 현재 활동이 있다면 유지
        if (currentAction != null)
        {
            mDailySchedule.Add(currentAction);
        }
        
        mNextAction = null;
        
        if (mShowDebugInfo)
        {
            LogManager.Log("Scheduler", "모든 스케줄 항목 삭제됨", 2);
        }
    }

    // 테스트용 더미 일정 생성
    private void CreateDummySchedule()
    {
        // 아침 식사
        AddScheduleItem(new ScheduleItem
        {
            ID = "breakfast",
            ActionName = "아침 식사",
            LocationName = "Kitchen",
            StartTime = new TimeSpan(8, 0, 0),
            EndTime = new TimeSpan(8, 30, 0),
            Priority = 5,
            IsFlexible = false
        });
        
        // 오전 일과
        AddScheduleItem(new ScheduleItem
        {
            ID = "morning_work",
            ActionName = "오전 업무",
            LocationName = "Desk",
            StartTime = new TimeSpan(9, 0, 0),
            EndTime = new TimeSpan(9, 30, 0),
            Priority = 8,
            IsFlexible = false
        });
        
        // 점심 식사
        AddScheduleItem(new ScheduleItem
        {
            ID = "lunch",
            ActionName = "점심 식사",
            LocationName = "Cafeteria",
            StartTime = new TimeSpan(10, 0, 0),
            EndTime = new TimeSpan(10, 30, 0),
            Priority = 5,
            IsFlexible = true
        });
        
        // 오후 일과
        AddScheduleItem(new ScheduleItem
        {
            ID = "afternoon_work",
            ActionName = "오후 업무",
            LocationName = "Desk",
            StartTime = new TimeSpan(11, 0, 0),
            EndTime = new TimeSpan(11, 30, 0),
            Priority = 8,
            IsFlexible = false
        });
        
        // 저녁 식사
        AddScheduleItem(new ScheduleItem
        {
            ID = "dinner",
            ActionName = "저녁 식사",
            LocationName = "Kitchen",
            StartTime = new TimeSpan(12, 0, 0),
            EndTime = new TimeSpan(12, 30, 0),
            Priority = 5,
            IsFlexible = true
        });
        
        // 여가 시간
        AddScheduleItem(new ScheduleItem
        {
            ID = "leisure",
            ActionName = "여가 시간",
            LocationName = "LivingRoom",
            StartTime = new TimeSpan(13, 0, 0),
            EndTime = new TimeSpan(13, 30, 0),
            Priority = 3,
            IsFlexible = true
        });
        
        // 취침
        AddScheduleItem(new ScheduleItem
        {
            ID = "sleep",
            ActionName = "취침",
            LocationName = "Bedroom",
            StartTime = new TimeSpan(14, 0, 0),
            EndTime = new TimeSpan(14, 30, 30),
            Priority = 7,
            IsFlexible = false
        });
    }
}