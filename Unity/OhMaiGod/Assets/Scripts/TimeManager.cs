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
    [Tooltip("현실 시간 1초당 게임 내 시간이 몇 분 흐를지 설정")]
    [SerializeField] private float mGameMinutesPerRealSecond = 1.0f;    // 현실 1초에 게임 내 몇 분이 흐를지
    
    [Header("디버깅")]
    [SerializeField] private bool mShowDebugInfo = true;            // 디버그 로그 출력 여부

    // 시간 관리 변수들
    private DateTime mGameDate;             // 현재 게임 날짜
    private TimeSpan mCurrentGameTime;      // 현재 게임 내 시간
    private bool mIsPaused = false;         // 시간 흐름 일시정지 상태 여부

    public bool isPaused {get => mIsPaused; set => mIsPaused = value; }

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
        
        // 게임 날짜 및 시간 초기화
        mGameDate = DateTime.Today;
        mCurrentGameTime = new TimeSpan(6, 0, 0);
    }

    private void Update()
    {
        if (mIsPaused) return;
        
        // 게임 시간 업데이트
        UpdateGameTime();
    }

    // 게임 시간 업데이트
    private void UpdateGameTime()
    {
        // 현실 시간의 흐름에 따라 게임 내 분 단위로 시간 증가
        mCurrentGameTime = mCurrentGameTime.Add(TimeSpan.FromMinutes(Time.deltaTime * mGameMinutesPerRealSecond));
        
        // 날짜 변경 확인
        if (mCurrentGameTime.Days > 0)
        {
            mGameDate = mGameDate.AddDays(1);
            mCurrentGameTime = new TimeSpan(mCurrentGameTime.Hours, mCurrentGameTime.Minutes, mCurrentGameTime.Seconds);
            
            if (mShowDebugInfo)
            {
                LogManager.Log("Time", $"새로운 날: {mGameDate.ToString("yyyy-MM-dd")} ({GetDayOfWeekString()})", 3);
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
        return $"{mCurrentGameTime.Hours:D2}:{mCurrentGameTime.Minutes:D2}:{mCurrentGameTime.Seconds:D2}";
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
        mGameMinutesPerRealSecond = _minutesPerSecond;

        if (mShowDebugInfo)
        {
            LogManager.Log("Time", $"시간 속도 변경: {_minutesPerSecond}분/초", 3);
        }
    }

    // 날짜 및 시간 설정
    public void SetDateTime(DateTime _date, int _hours, int _minutes)
    {
        mGameDate = _date;
        mCurrentGameTime = new TimeSpan(_hours, _minutes, 0);
        
        if (mShowDebugInfo)
        {
            LogManager.Log("Time", $"날짜/시간 설정: {GetDateString()} {GetTimeString()}", 3);
        }
    }

    // 현재 시간이 지정된 시간 범위 내에 있는지 확인
    public bool IsTimeInRange(TimeSpan _startTime, TimeSpan _endTime)
    {
        return mCurrentGameTime >= _startTime && mCurrentGameTime <= _endTime;
    }
}