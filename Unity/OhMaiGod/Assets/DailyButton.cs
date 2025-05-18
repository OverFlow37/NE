using UnityEngine;
using UnityEngine.UI;

public class DailyButton : MonoBehaviour
{
    void Start()
    {
        // 인게임 시간으로 하루 넘어가는 버튼
        GetComponent<Button>().onClick.AddListener(TimeManager.Instance.CalculateDaily);
    }
}
