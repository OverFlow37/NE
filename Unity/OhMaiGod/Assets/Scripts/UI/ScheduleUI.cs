using UnityEngine;
using UnityEngine.UI;

public class ScheduleUI : MonoBehaviour
{
    public AgentScheduler scheduler;
    public Text scheduleText;

    void Update()
    {
        if (scheduler != null && scheduleText != null)
        {
            scheduleText.text = scheduler.GetScheduleString();
        }
    }
}