using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class TimeManager : MonoBehaviour
{
    // 싱글톤
    private static TimeManager mInstance;
    
    public static TimeManager Instance
    {
        get
        {
            if (mInstance == null)
            {
                GameObject obj = new GameObject("TimeManager");
                mInstance = obj.AddComponent<TimeManager>();
                DontDestroyOnLoad(obj);
            }
            return mInstance;
        }
    }

    [Header("시간 설정")]
    [Tooltip("현실 시간 1초당 게임 내 시간이 몇 초 흐를지 설정")]
    [SerializeField] private float mGameToRealTimeRatio = 60.0f;    // 기본: 1초당 1분(60초)
    
    [Header("디버깅")]
    [SerializeField] private bool mShowDebugInfo = true;            // 디버그 로그 출력 여부

    // 시간 관리 변수들
    [SerializeField]private DateTime mGameDate;             // 현재 게임 날짜
    [SerializeField]private TimeSpan mCurrentGameTime;      // 현재 게임 내 시간
    private bool mIsPaused = false;     // 시간 흐름 일시정지 상태 여부

    public DateTime GameDate {get => mGameDate;}
    public TimeSpan GameTime {get => mCurrentGameTime;}
    public bool isPaused {get => mIsPaused; set => mIsPaused = value; }

    // public event Action OnDayChanged;

    private void Awake()
    {
        // 싱글톤 인스턴스 설정
        if (mInstance != null && mInstance != this)
        {
            Destroy(gameObject);
            return;
        }

        mInstance = this;
        DontDestroyOnLoad(gameObject);
        
        // 게임 날짜 및 시간 초기화 (오전 8시 시작)
        mGameDate = DateTime.Today;
        mCurrentGameTime = new TimeSpan(8, 0, 0);
    }

    private void Update()
    {
        if (mIsPaused) return;
        
        // 이전 값 저장
        DateTime prevDate = mGameDate;
        
        // 게임 시간 업데이트
        UpdateGameTime();
        
        // 날짜가 변경된 경우 이벤트 발생
        // if (prevDate.Date != mGameDate.Date && OnDayChanged != null)
        // {
        //     OnDayChanged.Invoke();
        // }
    }

    // 게임 시간 업데이트
    private void UpdateGameTime()
    {
        // 실제 시간의 흐름이 인게임 시간의 흐름과 어느 비율로 흐르는지에 따라 인게임 시간 계산
        mCurrentGameTime = mCurrentGameTime.Add(TimeSpan.FromSeconds(Time.deltaTime * mGameToRealTimeRatio));
        
        // 날짜 변경 확인
        if (mCurrentGameTime.Days > 0)
        {
            mGameDate = mGameDate.AddDays(1);
            mCurrentGameTime = new TimeSpan(mCurrentGameTime.Hours, mCurrentGameTime.Minutes, mCurrentGameTime.Seconds);
            
            if (mShowDebugInfo)
            {
                Debug.Log($"새로운 날: {mGameDate.ToString("yyyy-MM-dd")} ({GetDayOfWeekString()})");
            }
        }
    }

    // 현재 게임 내 시간 반환
    public TimeSpan GetCurrentGameTime()
    {
        return mCurrentGameTime;
    }

    // 현재 게임 날짜 반환
    public DateTime GetCurrentGameDate()
    {
        return mGameDate;
    }

    // 현재 요일을 문자열로 반환
    public string GetDayOfWeekString()
    {
        string[] dayNames = { "일", "월", "화", "수", "목", "금", "토" };
        return dayNames[(int)mGameDate.DayOfWeek];
    }

    // 현재 시간을 "HH:mm" 형식의 문자열로 반환
    public string GetTimeString()
    {
        return $"{mCurrentGameTime.Hours:D2}:{mCurrentGameTime.Minutes:D2}";
    }

    // 현재 날짜를 "MM월 dd일 (요일)" 형식의 문자열로 반환
    public string GetDateString()
    {
        return $"{mGameDate.Month}월 {mGameDate.Day}일 ({GetDayOfWeekString()})";
    }

    // 특정 시간과 현재 시간의 차이를 반환
    public TimeSpan GetTimeDifference(TimeSpan _targetTime)
    {
        return _targetTime - mCurrentGameTime;
    }

    // 게임 시간 흐름 속도 설정
    public void SetTimeScale(float _minutesPerSecond)
    {
        mGameToRealTimeRatio = _minutesPerSecond;

        if (mShowDebugInfo)
        {
            Debug.Log($"시간 속도 변경: {_minutesPerSecond}분/초");
        }
    }

    // 날짜 및 시간 설정
    public void SetDateTime(DateTime _date, int _hours, int _minutes)
    {
        mGameDate = _date;
        mCurrentGameTime = new TimeSpan(_hours, _minutes, 0);
        
        if (mShowDebugInfo)
        {
            Debug.Log($"날짜/시간 설정: {GetDateString()} {GetTimeString()}");
        }
    }

    // 현재 시간이 지정된 시간 범위 내에 있는지 확인
    public bool IsTimeInRange(TimeSpan _startTime, TimeSpan _endTime)
    {
        return mCurrentGameTime >= _startTime && mCurrentGameTime <= _endTime;
    }
}