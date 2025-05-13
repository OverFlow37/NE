using UnityEngine;
using System.Collections;
using System.Text;
using UnityEngine.Networking;

namespace OhMAIGod.Perceive{
    // 반응인지 관찰인지 여부
    public enum RequestType
    {
        REACTION,
        PERCEIVE,
    }
    // 반응 또는 관찰을 유발한 Event 타입
    public enum PerceiveEventType
    {
        INTERACTABLE_DISCOVER,          // 오브젝트 발견
        INTERACTABLE_STATE_CHANGE,      // 오브젝트 상태 변화 감지
        POWER_OBSERVE,                  // 권능 목격
        OTHER_AGENT_REQUEST,            // 다른 에이전트의 상호작용 요청
        AGENT_LOCATION_CHANGE,          // 에이전트 지역 이동
        AGENT_NEED_LIMIT,               // 에이전트 욕구 한계치 도달
        AGENT_NO_TASK,                  // 현재 에이전트에 할당된 작업 없음
    }

    // 반응 또는 관찰을 유발한 Event에 대한 정보 구조화
    [System.Serializable]
    public struct PerceiveEvent
    {
        public PerceiveEventType eventType; // 이벤트 타입
        public string eventLocation;        // 이벤트 발생 위치
        public string eventDescription;     // 이벤트 설명
    }
}

public class PerceiveManager : MonoBehaviour
{
    private static PerceiveManager mInstance;
    public static PerceiveManager Instance
    {
        get
        {
            if (mInstance == null)
            {
                GameObject obj = new GameObject("PerceiveManager");
                mInstance = obj.AddComponent<PerceiveManager>();
                DontDestroyOnLoad(obj);
            }
            return mInstance;
        }
    }

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
    }


    public void SendEventToAIServer(OhMAIGod.Perceive.PerceiveEventType _eventType, string _eventLocation, string _interactable)
    {
        StartCoroutine(SendEventCoroutine(_eventType, _eventLocation, _interactable));
    }

    private IEnumerator SendEventCoroutine(OhMAIGod.Perceive.PerceiveEventType _eventType, string _eventLocation, string _interactable)
    {
        string json = $"{{\"event\":{{\"event_type\":\"{_eventType}\",\"event_location\":\"{_eventLocation}\",\"interactable\":\"{_interactable}\"}}}}";
        byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

        using (UnityWebRequest www = new UnityWebRequest("AI서버주소", "POST"))
        {
            www.uploadHandler = new UploadHandlerRaw(bodyRaw);
            www.downloadHandler = new DownloadHandlerBuffer();
            www.SetRequestHeader("Content-Type", "application/json");

            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                LogManager.Log("이벤트 전송 성공: " + www.downloadHandler.text);
            }
            else
            {
                LogManager.Log("이벤트 전송 실패: " + www.error);
            }
        }
    }
}
