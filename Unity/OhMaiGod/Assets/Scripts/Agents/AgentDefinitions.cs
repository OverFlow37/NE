using System;
using UnityEngine;

namespace OhMAIGod.Agent
{
    // Agent의 행동 상태
    [System.Serializable]
    public enum AgentState
    {
        WAITING,
        WAITING_FOR_AI_RESPONSE,
        MOVING_TO_LOCATION,
        MOVING_TO_INTERACTABLE,
        INTERACTING,        // 모든 행동
    }

    public abstract class AgentStateHandler
    {
        // 상태 진입 시 호출
        public virtual void OnStateEnter(AgentController _controller)
        {
            LogManager.Log("Agent", $"{_controller.AgentName}: {GetStateName()} 상태 진입", 2);
        }

        // 매 프레임 호출되는 메서드 (자식 클래스에서 반드시 구현)
        public abstract void OnStateExecute(AgentController _controller);

        // 상태 종료 시 호출
        public virtual void OnStateExit(AgentController _controller)
        {
            LogManager.Log("Agent", $"{_controller.AgentName}: {GetStateName()} 상태 종료", 2);
        }

        // 상태 이름 변환 함수 (디버깅용)
        protected abstract string GetStateName();
    }
    [System.Serializable]
    public enum AgentNeedsType
    {
        Hunger,
        Sleepiness,
        Loneliness,
        Stress
    }
    [System.Serializable]
    public struct AgentNeeds
    {
        [SerializeField] private int hunger;      // 배고픔 수치
        [SerializeField] private int sleepiness;  // 졸림 수치
        [SerializeField] private int loneliness;  // 외로움 수치
        [SerializeField] private int stress;      // 스트레스 수치

        public int Hunger 
        { 
            get => hunger;
            set => hunger = Mathf.Clamp(value, -100, 100);
        }

        public int Sleepiness
        {
            get => sleepiness;
            set => sleepiness = Mathf.Clamp(value, -100, 100);
        }

        public int Loneliness
        {
            get => loneliness;
            set => loneliness = Mathf.Clamp(value, -100, 100);
        }

        public int Stress{
            get => stress;
            set => stress = Mathf.Clamp(value, -100, 100);
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

    [Serializable]
    public class ScheduleItem
    {
        public string ID;                   // 활동 고유 식별자
        public string ActionName;           // 활동 이름
        public string LocationName;         // 목적지 위치 이름
        public string TargetName;           // 목적지 대상 이름
        [Range(0,23)] public int StartHour;
        [Range(0,59)] public int StartMinute;
        [Range(0,59)] public int StartSecond;
        [Range(0,23)] public int EndHour;
        [Range(0,59)] public int EndMinute;
        [Range(0,59)] public int EndSecond;
        public int Priority;                // 우선순위 (높을수록 중요)
        public bool IsCompleted;            // 완료 여부
        public string Reason;               // 활동 선택 이유

        // 런타임 변환용 프로퍼티
        public TimeSpan StartTime
        {
            get => new TimeSpan(StartHour, StartMinute, StartSecond);
            set { StartHour = value.Hours; StartMinute = value.Minutes; StartSecond = value.Seconds; }
        }
        public TimeSpan EndTime
        {
            get => new TimeSpan(EndHour, EndMinute, EndSecond);
            set { EndHour = value.Hours; EndMinute = value.Minutes; EndSecond = value.Seconds; }
        }

        // 다른 일정과의 시간 충돌 여부를 검사하는 함수
        public bool ConflictsWith(ScheduleItem other)
        {
            return (StartTime >= other.StartTime && StartTime < other.EndTime) ||
                   (EndTime > other.StartTime && EndTime <= other.EndTime) ||
                   (StartTime <= other.StartTime && EndTime >= other.EndTime);
        }

        // 생성자
        public ScheduleItem(string _actionName, string _locationName, string _targetName, TimeSpan _startTime, TimeSpan _endTime,
                            int _priority, string _reason)
        {
            ID = System.Guid.NewGuid().ToString();
            ActionName = _actionName;
            LocationName = _locationName;
            TargetName = _targetName;
            StartHour = _startTime.Hours;
            StartMinute = _startTime.Minutes;
            StartSecond = 0;
            EndHour = _endTime.Hours;
            EndMinute = _endTime.Minutes;
            EndSecond = 0;
            Priority = _priority;
            IsCompleted = false;
            Reason = _reason;
        }
    }
}
