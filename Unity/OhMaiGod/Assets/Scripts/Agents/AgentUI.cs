// 에이전트의 UI 관리
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;
using OhMAIGod.Agent;

public class AgentUI : MonoBehaviour
{
    [Header("UI")]
    [SerializeField]
    private bool mIsSpeechBubble = true;
    [SerializeField]
    private GameObject mSpeechBubble; // Inspector에서 직접 할당
    
    private Camera mCam;

    [SerializeField]
    private Transform mCharacter; // 캐릭터의 Transform
    [SerializeField]
    private AgentController mAgentController;

    [System.Serializable]
    public class EmoteUI
    {
        public Text mHungerText;
        public Text mSleepinessText;
        public Text mLonelinessText;
        public Text mStressText;
    }

    [SerializeField]
    private EmoteUI mEmoteUI;

    public Vector3 mSpeechOffset = new Vector3(0, 1.2f, 0);
    public float mThoughtDuration = 10.0f; // 속마음이 표시되는 시간

    [SerializeField]
    private GameObject mInteractionInfo; // [text+fill Image] 상호작용 정보
    [SerializeField]
    private TextMeshProUGUI mInteractionText; // 상호작용 텍스트
    [SerializeField]
    private Image mInteractionFillImage; // 상호작용 진행도 표시용 fill 이미지
    [SerializeField]
    private TextMeshProUGUI mSpeechText;     // [text] 속마음 정보
    [SerializeField]
    private TextMeshProUGUI mReactText;     // [text] 반응 판단 정보


    private Coroutine mThoughtCoroutine;

    void Start()
    {
        mCam = Camera.main;
        if (mSpeechBubble == null)
        {
            LogManager.Log("AgentUI", $"SpeechBubble 오브젝트를 Inspector에서 할당해 주세요.", 1);
            return;
        }
        if (mSpeechText == null)
        {
            LogManager.Log("AgentUI", $"SpeechBubble에 TextMeshProUGUI 컴포넌트가 없습니다.", 1);
        }

        // Emote UI 연결
        Canvas mainCanvas = FindFirstObjectByType<Canvas>();
        if (mainCanvas != null)
        {
            Transform hungerObj = mainCanvas.transform.Find("EmoteHUNGER");
            Transform sleepinessObj = mainCanvas.transform.Find("EmoteSLEEPINESS");
            Transform lonelinessObj = mainCanvas.transform.Find("EmoteLONELINESS");
            Transform stressObj = mainCanvas.transform.Find("EmoteSTRESS");

            if (hungerObj != null)
                mEmoteUI.mHungerText = hungerObj.GetComponentInChildren<Text>();

            if (sleepinessObj != null)
                mEmoteUI.mSleepinessText = sleepinessObj.GetComponentInChildren<Text>();

            if (lonelinessObj != null)
                mEmoteUI.mLonelinessText = lonelinessObj.GetComponentInChildren<Text>();

            if (stressObj != null)
                mEmoteUI.mStressText = stressObj.GetComponentInChildren<Text>();
        }

        // Canvas에 이미 SpeechBubble이 있는지 확인
        if (mainCanvas != null)
        {
            // Canvas 하위에서 이름이 "SpeechBubble"인 오브젝트 탐색
            Transform existSpeech = mainCanvas.transform.Find("SpeechBubble");
            if (existSpeech != null)
            {
                // 이미 존재하면 해당 오브젝트 삭제
                LogManager.Log("Agent", $"Canvas에 이미 SpeechBubble이 있어 기존 오브젝트를 삭제합니다.", 2);
                Destroy(existSpeech.gameObject);
            }
            if (mSpeechBubble != null && mSpeechBubble.transform.parent != mainCanvas.transform)
            {
                // mSpeechBubble을 Canvas로 이동
                HideInteractionInfo();
                mSpeechBubble.transform.SetParent(mainCanvas.transform, false);
                LogManager.Log("Agent", $"SpeechBubble을 Canvas로 이동시켰습니다.", 2);
            }
        }
        StartCoroutine(UpdateSpeechLate());
        UpdateEmote();
    }

    void Update()
    {
        UpdateEmote();
        UpdateInteractionProgressUI();
        UpdateSpeechBubbleActive(); // 말풍선 활성화 상태도 매 프레임 체크
    }

    // 말풍선 따라다니기
    private IEnumerator UpdateSpeechLate()
    {
        if (mSpeechBubble == null) yield break;
        RectTransform speechTransform = mSpeechBubble.GetComponent<RectTransform>();
        while (true)
        {
            yield return new WaitForEndOfFrame();
            if (mSpeechBubble.activeSelf && mCharacter != null)
            {
                Vector3 worldPos = mCharacter.position + mSpeechOffset;
                Vector3 screenPos = RectTransformUtility.WorldToScreenPoint(mCam, worldPos);
                speechTransform.position = screenPos;
                speechTransform.rotation = Quaternion.identity;
            }
        }
    }

    public void UpdateEmote()
    {
        if (mEmoteUI == null || mAgentController == null) return;
        mEmoteUI.mHungerText.text = "HUNGER    : " + string.Format("{0}", (int)mAgentController.AgnetNeeds.Hunger);
        mEmoteUI.mSleepinessText.text = "SLEEPINESS: " + string.Format("{0}", (int)mAgentController.AgnetNeeds.Sleepiness);
        mEmoteUI.mLonelinessText.text = "LONELINESS: " + string.Format("{0}", (int)mAgentController.AgnetNeeds.Loneliness);
        mEmoteUI.mStressText.text = "STRESS    : " + string.Format("{0}", (int)mAgentController.AgnetNeeds.Stress);
    }

    // 상호작용 정보 표시
    public void ShowInteractionInfo(string _text)
    {
        if (mInteractionInfo != null)
        {
            mInteractionInfo.SetActive(true);
            if (mInteractionText != null)
                mInteractionText.text = _text;
        }
        UpdateSpeechBubbleActive();
    }

    public void HideInteractionInfo()
    {
        if (mInteractionInfo != null)
            mInteractionInfo.SetActive(false);
        UpdateSpeechBubbleActive();
    }

    // 속마음 정보 표시
    public void ShowThoughtInfo(string _text)
    {
        if (mThoughtCoroutine != null)
        {
            StopCoroutine(mThoughtCoroutine);
            mThoughtCoroutine = null;
        }
        mThoughtCoroutine = StartCoroutine(ShowThoughtCoroutine(_text));
    }

    private IEnumerator ShowThoughtCoroutine(string _text)
    {
        if (mSpeechText != null)
        {
            mSpeechText.gameObject.SetActive(true);
            mSpeechText.text = _text;
            UpdateSpeechBubbleActive();
            yield return new WaitForSeconds(mThoughtDuration);
            mSpeechText.gameObject.SetActive(false);
            UpdateSpeechBubbleActive();
        }
        mThoughtCoroutine = null;
    }

    public void HideThoughtInfo()
    {
        if (mThoughtCoroutine != null)
        {
            StopCoroutine(mThoughtCoroutine);
            mThoughtCoroutine = null;
        }
        if (mSpeechText != null)
            mSpeechText.gameObject.SetActive(false);
        UpdateSpeechBubbleActive();
    }

    // speechBubble 활성화/비활성화 관리
    private void UpdateSpeechBubbleActive()
    {
        if (mSpeechBubble != null)
        {
            bool isActive = (mInteractionInfo != null && mInteractionInfo.activeSelf) ||
                            (mSpeechText != null && mSpeechText.gameObject.activeSelf) ||
                            (mReactText != null && mReactText.gameObject.activeSelf);
            mSpeechBubble.SetActive(isActive);
        }
    }

    private void UpdateInteractionProgressUI()
    {
        if (mInteractionFillImage != null && mAgentController != null)
        {
            mInteractionFillImage.fillAmount = mAgentController.mInteractionProgress;
        }
    }

    // 상호작용 UI 시작
    public void StartInteractionUI(string _text)
    {
        if (mInteractionInfo != null)
        {
            switch(_text){
                case "eat":
                    mInteractionText.text = " eating...";
                    break;
                case "use":
                    mInteractionText.text = " using...";
                    break;
                case "offer":
                    mInteractionText.text = " offering...";
                    break;
                case "break":
                    mInteractionText.text = " breaking...";
                    break;
            }
            mInteractionInfo.SetActive(true);
            UpdateSpeechBubbleActive();
            // 텍스트/이미지 등 세팅 필요시 여기서 처리
            // 예: mInteractionInfo.GetComponentInChildren<TextMeshProUGUI>().text = _text;
        }
        
    }

    // 상호작용 UI 종료
    public void EndInteractionUI()
    {
        if (mInteractionInfo != null)
            mInteractionInfo.SetActive(false);
        UpdateSpeechBubbleActive();
    }

    // 반응 판단 여부를 텍스트로 표시
    public void ShowReact(string _text, bool _isReact){
        if(_isReact){
            if(mReactText != null){
            mReactText.gameObject.SetActive(true);
            mReactText.text = _text;
            UpdateSpeechBubbleActive();
            }
        }
        else{
            // 반응 텍스트 비활성화
            if(mReactText != null){
            mReactText.gameObject.SetActive(false);
            UpdateSpeechBubbleActive();
            }
        }
    }
}
