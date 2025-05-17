using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

public class ScheduleUI : MonoBehaviour
{
    public AgentScheduler mScheduler;
    public Text mScheduleText;

    private void Start()
    {
        if (mScheduler == null)
        {
            mScheduler = GameObject.FindGameObjectWithTag("NPC").GetComponent<AgentScheduler>();
        }

        if (mScheduleText == null)
        {
            mScheduleText = this.GetComponent<Text>();
        }

        // 씬 로드 이벤트 등록
        SceneManager.sceneLoaded += OnSceneLoaded;
    }

    private void Update()
    {
        if (mScheduler != null && mScheduleText != null)
        {
            mScheduleText.text = mScheduler.GetScheduleString();
        }
    }

    private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        if (mScheduler == null)
        {
            mScheduler = GameObject.FindGameObjectWithTag("NPC").GetComponent<AgentScheduler>();
        }
    }

    private void OnDestroy()
    {
        // 오브젝트가 파괴될 때 씬 로드 이벤트 해제
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }
}