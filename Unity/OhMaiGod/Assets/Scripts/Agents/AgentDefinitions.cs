using System;
using UnityEngine;

namespace OhMAIGod.Agent
{
    // Agent의 행동 상태
    public enum AgentState
    {
        IDLE = 0,
        WAITING,
        MOVING,
        INTERACTION,        // 모든 행동
        MovingToLocation,
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
        public TimeSpan StartTime;          // 시작 시간 (하루 중)
        public TimeSpan EndTime;            // 종료 시간 (하루 중)
        public int Priority;                // 우선순위 (높을수록 중요)
        public bool IsFlexible;             // 시간이 유연한지 여부
        public bool IsCompleted;            // 완료 여부
        public string ActionDetails;        // 활동에 대한 추가 정보 (JSON)
        public string Reason;               // 활동 선택 이유

        // 다른 일정과의 시간 충돌 여부를 검사하는 함수
        public bool ConflictsWith(ScheduleItem other)
        {
            return (StartTime >= other.StartTime && StartTime < other.EndTime) ||
                   (EndTime > other.StartTime && EndTime <= other.EndTime) ||
                   (StartTime <= other.StartTime && EndTime >= other.EndTime);
        }
    }
}
