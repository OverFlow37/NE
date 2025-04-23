using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;
using System.Text;

public class AgentSender : MonoBehaviour
{
    [Header("에이전트 기본 정보")]
    public string agentName = "Steve";
    public string location = "townhall";
    [TextArea]
    public string personality = "introverted, practical, punctual";

    [Header("상태 수치 (0~10)")]
    [Range(0, 10)] public int hunger = 5;
    [Range(0, 10)] public int sleepiness = 3;
    [Range(0, 10)] public int loneliness = 4;
    [Range(0, 10)] public int stress = 2;
    [Range(0, 10)] public int happiness = 6;

    [Header("오브젝트 그룹 (인식 가능)")]
    [SerializeField]
    public List<ObjectGroup> visibleObjects = new List<ObjectGroup>();

    [Header("오브젝트 그룹 (상호작용 가능)")]
    [SerializeField]
    public List<ObjectGroup> interactableItems = new List<ObjectGroup>();

    public Button sendButton;
    private bool isRequesting = false;

    // ========== 데이터 구조 ==========
    [System.Serializable]
    public class AgentState
    {
        public int hunger;
        public int sleepiness;
        public int loneliness;
        public int stress;
        public int happiness;
    }

    [System.Serializable]
    public class ObjectGroup
    {
        public string location;
        public List<string> objects;  // 인스펙터에서 리스트로 입력 가능
    }

    [System.Serializable]
    public class Agent
    {
        public string name;
        public AgentState state;
        public string location;
        public string personality;
        public ObjectGroup[] visible_objects;
        public ObjectGroup[] interactable_items;
        public string[] nearby_agents;
    }

    [System.Serializable]
    public class AgentRequest
    {
        public Agent[] agents;
    }

    // ========== 요청 시작 ==========
    public void SendAgent()
    {
        if (isRequesting)
        {
            Debug.LogWarning("요청 진행 중입니다. 기다려주세요.");
            return;
        }

        StartCoroutine(SendAgentData());
    }

    IEnumerator SendAgentData()
    {
        isRequesting = true;
        if (sendButton != null) sendButton.interactable = false;

        AgentRequest requestData = new AgentRequest
        {
            agents = new Agent[]
            {
                new Agent
                {
                    name = agentName,
                    state = new AgentState
                    {
                        hunger = hunger,
                        sleepiness = sleepiness,
                        loneliness = loneliness,
                        stress = stress,
                        happiness = happiness
                    },
                    location = location,
                    personality = personality,
                    visible_objects = visibleObjects.ToArray(),
                    interactable_items = interactableItems.ToArray(),
                    nearby_agents = new string[] { } // 필요시 인스펙터로 확장 가능
                }
            }
        };

        string jsonData = JsonUtility.ToJson(requestData, true); // 보기 쉽게 출력
        Debug.Log("보낼 JSON:\n" + jsonData);

        UnityWebRequest request = new UnityWebRequest("http://127.0.0.1:5000/action", "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        var stopwatch = new System.Diagnostics.Stopwatch();
        stopwatch.Start();

        yield return request.SendWebRequest();

        stopwatch.Stop();
        long elapsedMs = stopwatch.ElapsedMilliseconds;

        isRequesting = false;
        if (sendButton != null) sendButton.interactable = true;

        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("✅ 응답: " + request.downloadHandler.text);
            Debug.Log($"⏱️ 요청 소요 시간: {elapsedMs} ms");
        }
        else
        {
            Debug.LogError("❌ 실패: " + request.error);
        }
    }
}
