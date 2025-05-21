using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class TimeManager : MonoBehaviour, ISaveable
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
    private int mDays = 1;                  // 누적 일 수
    private bool mIsPaused = false;         // 시간 흐름 일시정지 상태 여부

    // 하루에 한 번만 저장하도록 플래그 변수 추가
    private bool mIsSavedToday = false;

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
        mGameDate = new DateTime(2025, 5, 19);
        mCurrentGameTime = new TimeSpan(7, 0, 0);
        mDays = 1;
    }

    private void Update()
    {
        if (mIsPaused) return;
        
        // 게임 시간 업데이트
        UpdateGameTime();

        // 게임 시간이 19시(=TimeSpan(19,0,0))를 넘으면 저장
        if (!mIsSavedToday && mCurrentGameTime >= new TimeSpan(19, 0, 0))
        {
            CalculateDaily();
        }
    }

    // 게임 시간 업데이트
    private void UpdateGameTime()
    {
        // 현실 시간의 흐름에 따라 게임 내 분 단위로 시간 증가
        mCurrentGameTime = mCurrentGameTime.Add(TimeSpan.FromMinutes(Time.deltaTime * mGameMinutesPerRealSecond));
    }

    // 게임 시간 하루가 지나면 호출되는 정산 함수
    public void CalculateDaily()
    {
        mIsSavedToday = true;
        GameManager.Instance.DailySettlement(); // 일일 정산
    }

    // 게임 시간 저장할 구조체
    [Serializable]
    private struct TimeSaveData
    {
        public string GameDate; // DateTime (yyyy-MM-dd)
        public int Days;       // 누적 일 수
    }

    public void SaveData(string _savePath)
    {
        // 저장할 때만 mGameDate에 하루를 더해서 저장 (실제 mGameDate에는 영향 없음)
        DateTime saveDate = mGameDate.AddDays(1);
        mDays++;

        // DateTime을 문자열(ISO 8601)로 변환해서 저장
        TimeSaveData saveData = new TimeSaveData { GameDate = saveDate.ToString("o"), Days = mDays };
        string json = JsonUtility.ToJson(saveData);
        string path = System.IO.Path.Combine(_savePath, "time.json");
        System.IO.File.WriteAllText(path, json);
    }

    public void LoadData(string _loadPath)
    {
        string path = System.IO.Path.Combine(_loadPath, "time.json");
        if (System.IO.File.Exists(path))
        {
            string json = System.IO.File.ReadAllText(path);
            TimeSaveData saveData = JsonUtility.FromJson<TimeSaveData>(json);
            mGameDate = DateTime.Parse(saveData.GameDate); // 문자열을 DateTime으로 변환
            mDays = saveData.Days;
            mCurrentGameTime = new TimeSpan(7, 0, 0); // 게임 시간은 07:00으로 초기화
            mIsSavedToday = false;
            if (mShowDebugInfo)
            {
                LogManager.Log("Time", $"저장된 날짜로 복원: {mGameDate.ToString("yyyy-MM-dd")}, 시간은 07:00으로 초기화", 3);
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

    public int GetDays()
    {
        return mDays;
    }

    // 현재 게임 날짜를 yyyy.MM.dd.HH:mm 형식의 문자열로 반환
    public string GetCurrentGameDateString()
    {
        // yyyy.MM.dd는 mGameDate, HH:mm은 mCurrentGameTime을 사용해서 조합
        string datePart = mGameDate.ToString("yyyy.MM.dd");
        string timePart = string.Format("{0:D2}:{1:D2}", mCurrentGameTime.Hours, mCurrentGameTime.Minutes);
        return $"{datePart}.{timePart}";
    }

    // 현재 요일을 문자열로 반환
    public string GetDayOfWeekString()
    {
        string[] dayNames = { "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" };
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
        return $"{mGameDate.Month}/ {mGameDate.Day} ({GetDayOfWeekString()})";
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

    // 게임 시간 배속 반환
    public float GetGameMinutesPerRealSecond()
    {
        return mGameMinutesPerRealSecond;
    }
}