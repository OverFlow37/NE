// 에이전트의 UI 관리
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;

public class AgentUI : MonoBehaviour
{
    [Header("UI")]
    [SerializeField]
    private bool isSpeechBubble = true;
    [SerializeField] 
    private GameObject speechBubble;
    private TextMeshProUGUI speechText;
    private Camera cam;

    [SerializeField]
    private Transform character; // 캐릭터의 Transform
    [SerializeField]
    private AgentController agentController;

    [System.Serializable]
    public class EmoteUI
    {
        public Text hungerText;
        public Text sleepinessText;
        public Text lonelinessText;
    }

    [SerializeField]
    private EmoteUI emoteUI;

    public Vector3 speech_offset = new Vector3(0, 1.2f, 0);
    public float speechDuration = 10.0f; // 말풍선이 표시되는 시간

    void Start()
    {
        cam = Camera.main;
        speechText = speechBubble.GetComponentInChildren<TextMeshProUGUI>();
        StartCoroutine(UpdateSpeechLate());
        UpdateEmote();
    }

    void Update()
    {
        UpdateEmote();
    }

    // 말풍선 따라다니기
    private IEnumerator UpdateSpeechLate()
    {
        RectTransform speechTransform = speechBubble.GetComponent<RectTransform>();
        
        while (true)
        {
            yield return new WaitForEndOfFrame();
            if (speechBubble.activeSelf && character != null)
            {
                // World Space에서는 직접 위치를 설정
                speechTransform.position = character.position + speech_offset;
                
                // 말풍선이 항상 카메라를 향하도록 회전
                if (cam != null)
                {
                    speechTransform.rotation = cam.transform.rotation;
                }
            }
        }
    }

    // AgentController에서 호출
    // 말풍선 텍스트 업데이트 + 말풍선 표시 -> 일정 시간 이후 말풍선 비활성화
    public void StartSpeech(string speech)
    {
        StopAllCoroutines(); // 이전 타이머 코루틴 중지
        StartCoroutine(UpdateSpeechLate()); // 위치 업데이트 코루틴 재시작
        StartCoroutine(ShowSpeechBubble(speech));
    }

    private IEnumerator ShowSpeechBubble(string speech)
    {
        speechText.text = speech;
        if(isSpeechBubble)
        {
            speechBubble.SetActive(true);
            
            yield return new WaitForSeconds(speechDuration);
            
            speechBubble.SetActive(false);
        }
    }

    public void UpdateEmote()
    {
        emoteUI.hungerText.text = "HUNGER    : " + string.Format("{0}", (int)agentController.AgnetNeeds.Hunger);
        emoteUI.sleepinessText.text = "SLEEPINESS: " + string.Format("{0}", (int)agentController.AgnetNeeds.Sleepiness);
        emoteUI.lonelinessText.text = "LONELINESS: " + string.Format("{0}", (int)agentController.AgnetNeeds.Loneliness);
    }
}
