using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;
using OhMAIGod.Perceive;
using NUnit.Framework.Interfaces;
using UnityEditor.VersionControl;

public class ChatPower : Power
{
    [SerializeField]
    private GameObject mChatPowerObject;
    [SerializeField]
    private TMP_InputField mChatInputField;
    [SerializeField]
    private AgentController mAgentController; // 임시 TODO: Agent 선택하는 UI 필요

    private Coroutine mScaleCoroutine;
    private Vector3 mShowScale = Vector3.one;
    private Vector3 mHideScale = Vector3.zero;
    private float mAnimDuration = 0.05f;

    private void Awake()
    {
        // 엔터 입력 시 처리
        mChatInputField.onEndEdit.AddListener(OnInputEndEdit);
        mChatPowerObject.transform.localScale = mHideScale;
        mChatPowerObject.SetActive(false);

         SetAgentController();
    }
    

    private IEnumerator ScaleAnim(Vector3 _from, Vector3 _to, bool _afterShow)
    {
        float t = 0f;
        mChatPowerObject.transform.localScale = _from;
        while (t < mAnimDuration)
        {
            t += Time.unscaledDeltaTime;
            float ratio = Mathf.Clamp01(t / mAnimDuration);
            mChatPowerObject.transform.localScale = Vector3.Lerp(_from, _to, ratio);
            yield return null;
        }
        mChatPowerObject.transform.localScale = _to;
        if (!_afterShow)
            mChatPowerObject.SetActive(false);
        mScaleCoroutine = null;
    }

    public void SetAgentController()
    {
        mAgentController = GameObject.FindWithTag("NPC").GetComponent<AgentController>();
    }

    // 엔터 입력 시 호출
    private void OnInputEndEdit(string _input)
    {   
        // 에이전트가 반응 대기 중이면 채팅 입력 X
        if(mAgentController.CurrentState == OhMAIGod.Agent.AgentState.WAITING_FOR_AI_RESPONSE)
            return;
        if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter) || !Application.isMobilePlatform)
        {
            SubmitChat();
        }
    }

    // Submit 버튼에서 호출
    public void OnClickSubmitButton()
    {
        SubmitChat();
    }

    private void SubmitChat()
    {
        string chatText = mChatInputField.text;
        if (!string.IsNullOrWhiteSpace(chatText))
        {
            PerceiveEvent perceiveEvent = new PerceiveEvent();
            perceiveEvent.event_type = PerceiveEventType.POWER_OBSERVE;
            perceiveEvent.event_location = "";
            perceiveEvent.event_role = "GOD says";
            perceiveEvent.event_is_save = true;
            perceiveEvent.importance = 8;
            string message = chatText;
            perceiveEvent.event_description = message;
            mAgentController.ReactToResponse(true, perceiveEvent);
        }
        mChatInputField.text = "";
        Deactive();
    }

    // 실제 텍스트 전달 함수 (외부에서 구현/연결)
    private void OnSubmitChat(string _text)
    {
        LogManager.Log("Power", $"채팅 입력: {_text}");
        // TODO: 실제 채팅 처리 로직 구현
    }

    public override void Active()
    {
        base.Active();
        if (mScaleCoroutine != null)
            StopCoroutine(mScaleCoroutine);
        mChatPowerObject.SetActive(true);
        mChatInputField.text = "";
        mChatInputField.ActivateInputField();
        mScaleCoroutine = StartCoroutine(ScaleAnim(mHideScale, mShowScale, true));
    }

    public override void Deactive()
    {
        base.Deactive();
        if (mScaleCoroutine != null)
            StopCoroutine(mScaleCoroutine);
        mScaleCoroutine = StartCoroutine(ScaleAnim(mShowScale, mHideScale, false));
        mChatPowerObject.SetActive(false);
    }
}
