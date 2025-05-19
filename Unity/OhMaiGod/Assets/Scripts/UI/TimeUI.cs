using UnityEngine;
using UnityEngine.UI;

public class TimeUI : MonoBehaviour
{
    
    public Text mDateText;   // 날짜를 표시할 Text 컴포넌트 
    public Text mTimeText;   // 시간을 표시할 Text 컴포넌트
    public Text mDaysText;   // 누적 일 수를 표시할 Text 컴포넌트

    // 매 프레임마다 날짜와 시간을 갱신하여 UI에 표시
    private void Update()
    {
        if (TimeManager.Instance != null)
        {
            // 날짜 문자열 표시
            mDateText.text = TimeManager.Instance.GetDateString();

            // 시간 문자열 표시
            mTimeText.text = TimeManager.Instance.GetTimeString();

            // 누적 일 수 표시
            mDaysText.text = TimeManager.Instance.GetDays().ToString() + " 일차";
        }
    }
}
