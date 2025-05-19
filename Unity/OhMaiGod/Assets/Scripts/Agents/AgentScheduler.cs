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
    [Header("테스트 옵션")]
    [SerializeField] public bool mUseDummySchedule = false; // 더미 스케줄 등록 여부
    private bool mPrevUseDummySchedule = false; // 더미 스케줄 등록 체크박스 이전 상태 저장

    // ==== 스케줄 관리 변수들 ====
    private List<ScheduleItem> mDailySchedule = new List<ScheduleItem>();   // 하루 전체 일정 목록
    private ScheduleItem mCurrentAction = null;                             // 현재 수행 중인 활동
    private ScheduleItem mNextAction = null;                                // 다음 예정된 활동

    public ScheduleItem CurrentAction => mCurrentAction;

    private AgentController mAgentController;  // 에이전트 동작 제어를 위한 컨트롤러 참조

    private void Awake()
    {
        // 에이전트 컨트롤러 참조 가져오기
        mAgentController = GetComponent<AgentController>();
        
        // 빈 일정으로 초기화
        ResetSchedule();

        // 데일리 일정 가져와서 적용
        ApplyDailySchedule();
    }

    private void Update()
    {
        if (TimeManager.Instance.isPaused) return;
        
        // 인스펙터에서 더미 스케줄 등록 체크박스가 켜진 순간에만 실행
        if (!mPrevUseDummySchedule && mUseDummySchedule)
        {
            CreateDummySchedule();
            LogManager.Log("Scheduler", "더미 스케줄이 등록되었습니다.", 2);
        }
        mPrevUseDummySchedule = mUseDummySchedule;
        
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
        
        // 충돌 확인 (우선순위가 낮은 경우 추가 거부)
        var conflictingItems = mDailySchedule.Where(item => 
            !item.IsCompleted && 
            item.ConflictsWith(_item)).ToList();

        if (conflictingItems.Count > 0)
        {
            // 1. 새 스케줄의 우선순위가 낮으면(Priority 값이 더 크면) 추가하지 않음
            bool isLowerPriority = conflictingItems.Any(item => item.Priority < _item.Priority);
            if (isLowerPriority)
            {
                if (mShowDebugInfo)
                {
                    LogManager.Log("Scheduler", $"일정 충돌: 우선순위가 낮아 추가 불가 - {_item.ActionName} (우선순위: {_item.Priority})", 1);
                    foreach (var conflict in conflictingItems)
                    {
                        LogManager.Log("Scheduler", $" - 충돌 항목: {conflict.ActionName} (우선순위: {conflict.Priority}) @ {conflict.StartTime}", 1);
                    }
                }
                return false;
            }

            // 2. 새 스케줄의 우선순위가 높거나 같으면 추가
            foreach (var conflict in conflictingItems)
            {
                // 충돌 스케줄이 현재 진행 중인 활동이라면 완료 처리
                if (mCurrentAction != null && conflict.ID == mCurrentAction.ID)
                {
                    LogManager.Log("Scheduler", $"현재 활동({mCurrentAction.ActionName})이 새 스케줄로 인해 완료 처리됩니다.", 2);
                    CompleteCurrentAction();
                    continue;
                }

                if (_item.Priority < conflict.Priority)
                {
                    // 충돌난 스케줄이 새 스케줄의 시간 범위 안에 완전히 포함되는 경우 삭제
                    if (conflict.StartTime >= _item.StartTime && conflict.EndTime <= _item.EndTime)
                    {
                        RemoveScheduleItem(conflict.ID);
                        LogManager.Log("Scheduler", $"우선순위가 높은 새 스케줄의 시간 범위에 포함되어 삭제: {conflict.ActionName}", 2);
                        continue;
                    }
                    // 우선순위가 더 높으면(Priority 값이 더 작으면), 기존 스케줄의 시작시간을 새 스케줄의 끝 시간 이후로 변경
                    TimeSpan newStart = _item.EndTime.Add(new TimeSpan(0, 1, 0)); // 1분 뒤로 밀기
                    TimeSpan duration = conflict.EndTime - conflict.StartTime;
                    LogManager.Log("Scheduler", $"충돌 스케줄 duration: {duration}", 2);
                    conflict.StartTime = newStart;
                    conflict.EndTime = newStart.Add(duration);
                    if (mShowDebugInfo)
                    {
                        LogManager.Log("Scheduler", $"충돌 스케줄 시작시간 조정: {conflict.ActionName} → {conflict.StartTime}", 2);
                    }
                }
                // 우선순위가 같을 때
                else if (_item.Priority == conflict.Priority)
                {
                    // 시작/끝 시간이 모두 동일한 경우 기존 스케줄을 삭제하고 새 스케줄로 대체
                    if (_item.StartTime == conflict.StartTime && _item.EndTime == conflict.EndTime)
                    {
                        RemoveScheduleItem(conflict.ID);
                        LogManager.Log("Scheduler", $"동일 시간/우선순위 스케줄 대체: {conflict.ActionName} → {_item.ActionName}", 2);
                    }
                    // 시간만 겹치는 경우 기존 스케줄의 끝 시간을 새 스케줄 시작 1분 전으로 조정
                    else if (conflict.EndTime > _item.StartTime)
                    {
                        TimeSpan newEnd = _item.StartTime.Add(new TimeSpan(0, -1, 0));
                        if (newEnd > conflict.StartTime)
                        {
                            conflict.EndTime = newEnd;
                            LogManager.Log("Scheduler", $"동일 우선순위 충돌: {conflict.ActionName}의 종료 시간을 {_item.ActionName} 시작 1분 전({newEnd})으로 조정", 2);
                        }
                    }
                }
            }
        }
        
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
            }
            
            if (mShowDebugInfo)
            {
                LogManager.Log("Scheduler", $"일정 항목 삭제됨: {_itemID}", 2);
            }
        }
        
        return removed;
    }

    // 데일리 일정 가져와서 적용
    private void ApplyDailySchedule()
    {
        mDailySchedule = AIBridge_Perceive.Instance.NextDayPlans;
    }
    

    // 현재 활동 완료 처리
    public void CompleteCurrentAction()
    {
        if (mCurrentAction != null)
        {
            mCurrentAction.EndTime = TimeManager.Instance.GetCurrentGameTime();
            mCurrentAction.IsCompleted = true;
            
            if (mShowDebugInfo)
            {
                LogManager.Log("Scheduler", $"활동 완료: {mCurrentAction.ActionName}", 2);
            }
            
            // 다음 활동 평가
            mCurrentAction = null;
            mAgentController.ChangeState(AgentState.WAITING);
        }
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
        // 상태 변경 불가한 상태(AI 응답 대기 중)인 경우 처리 안함
        if(!mAgentController.AllowStateChange) return;

        // 현재 활동이 있고 아직 유효한 경우
        if (mCurrentAction != null)
        {
            // 현재 시간에 해당하는 미완료 활동 중 우선순위가 같거나 높은것 선택
            var mustBeStarted = mDailySchedule
                .Where(item => !item.IsCompleted &&
                       TimeManager.Instance.GetCurrentGameTime() >= item.StartTime &&
                       TimeManager.Instance.GetCurrentGameTime() < item.EndTime)
                .OrderBy(item => item.Priority) // 우선순위 높은 것(숫자 작은 것) 우선
                .ThenByDescending(item => item.StartTime)   // 시작시간이 늦은 것 우선 (이렇게 해야 현재 활동이 끝나고 바로 다음 활동이 시작됨)
                .ToList();

            var bestActivity = mustBeStarted.FirstOrDefault();

            // 현재 활동 강제 완료
            if (bestActivity != null && (mCurrentAction.ID != bestActivity.ID))
            {
                if (!mCurrentAction.IsCompleted)
                {
                    CompleteCurrentAction();
                }
            }
            else if (bestActivity == null && TimeManager.Instance.GetCurrentGameTime() > mCurrentAction.EndTime)
            {
                // 기존 종료 조건도 유지
                if (!mCurrentAction.IsCompleted)
                {
                    CompleteCurrentAction();
                }
            }
            else
            {
                // 현재 활동 계속
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
            .OrderBy(item => item.Priority)
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
                mAgentController.StartAction(mCurrentAction);
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
            .ThenBy(item => item.Priority)
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
        // 현재 게임 시간 가져오기
        TimeSpan startTime = TimeManager.Instance.GetCurrentGameTime().Add(new TimeSpan(0, 1, 0)); // 1분 뒤로 시작
        TimeSpan duration = new TimeSpan(0, 30, 0); // 30분 간격
        TimeSpan actionDuration = new TimeSpan(0, 25, 0); // 각 일정 25분

        // 첫 번째 스케줄: use, house, Bed
        AddScheduleItem(new ScheduleItem(
            "use",
            "house",
            "Bed",
            startTime,
            startTime.Add(actionDuration),
            2,
            "Dummy Schedule 1 : use, house, Bed"
        ));

        // 두 번째 스케줄: eat, cafeteria, Grape (첫 스케줄 시작 30분 뒤)
        TimeSpan secondStart = startTime.Add(duration);
        AddScheduleItem(new ScheduleItem(
            "eat",
            "cafeteria",
            "Grape",
            secondStart,
            secondStart.Add(actionDuration),
            2,
            "Dummy Schedule 2 : eat, cafeteria, Grape"
        ));

        // 세 번째 스케줄: break, outdoor, Tree (두 번째 스케줄 시작 30분 뒤)
        TimeSpan thirdStart = secondStart.Add(duration);
        AddScheduleItem(new ScheduleItem(
            "break",
            "outdoor",
            "Tree",
            thirdStart,
            thirdStart.Add(actionDuration),
            2,
            "Dummy Schedule 3 : break, outdoor, Tree"
        ));

        // 네 번째 스케줄: get, outdoor, Jewel (세 번째 스케줄 시작 30분 뒤)
        TimeSpan fourthStart = thirdStart.Add(duration);
        AddScheduleItem(new ScheduleItem(
            "get",
            "outdoor",
            "Jewel",
            fourthStart,
            fourthStart.Add(actionDuration),
            2,
            "Dummy Schedule 4 : get, outdoor, Jewel"
        ));

        // 다섯 번째 스케줄: offer, outdoor, Flower (네 번째 스케줄 시작 30분 뒤)
        TimeSpan fifthStart = fourthStart.Add(duration);
        AddScheduleItem(new ScheduleItem(
            "offer",
            "outdoor",
            "Flower",
            fifthStart,
            fifthStart.Add(actionDuration),
            2,
            "Dummy Schedule 5 : offer, outdoor, Flower"
        ));
    }

    // UI에서 스케줄을 표시할 수 있도록 문자열로 반환하는 메서드 추가
    public string GetScheduleString()
    {
        if (mDailySchedule == null || mDailySchedule.Count == 0)
            return "스케줄 없음";
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        foreach (var item in mDailySchedule)
        {
            // 완료여부 표시: [완료], [진행중], [대기] 중 하나
            string status = item.IsCompleted ? "[완료]" :
                (mCurrentAction != null && mCurrentAction.ID == item.ID ? "[진행중]" : "[대기]");
            sb.AppendLine($"{status} {item.ActionName} ({item.LocationName}/{item.TargetName}) : {item.StartTime.ToString(@"hh\:mm\:ss")} ~ {item.EndTime.ToString(@"hh\:mm\:ss")} | 우선순위: {item.Priority}");
        }
        return sb.ToString();
    }
}