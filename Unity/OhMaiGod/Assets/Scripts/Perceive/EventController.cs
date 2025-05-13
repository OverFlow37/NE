using UnityEngine;
using OhMAIGod.Perceive;
using System;
// 플레이어가 감지하는 이벤트 객체
public class EventController : MonoBehaviour
{
    [SerializeField]
    public PerceiveEvent mEventInfo;
    [SerializeField]
    private int mLifeDuration; // 이벤트 수명
    private TimeSpan mStartTime;


    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        mStartTime = TimeManager.Instance.GetCurrentGameTime();
    }

    void Update()
    {
        // 이벤트 수명 체크
        if (TimeManager.Instance.GetCurrentGameTime() - mStartTime > TimeSpan.FromSeconds(mLifeDuration))
        {
            Destroy(gameObject);
        }
    }
}
