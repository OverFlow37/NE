using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(fileName = "NewInteractableData", menuName = "Game/Interactable Data")]
public class InteractableData : ScriptableObject
{
    [Tooltip("오브젝트의 설명(개발자용)")]
    [TextArea] 
    [SerializeField] public string mDescription; // 개발자 확인용 오브젝트 설명
    [Tooltip("오브젝트의 이름")]
    [SerializeField] public string mName; // 오브젝트 이름  
    [Tooltip("오브젝트의 설명(AI프롬프트용)")]
    [TextArea] 
    [SerializeField] public string mDescriptionPrompt; // 프롬프트 전송용 오브젝트 설명
    [Tooltip("오브젝트의 타입")]
    [SerializeField] public Types mType;
    [Tooltip("오브젝트의 현재 상태")]
    [SerializeField] public States mState;
    [Tooltip("오브젝트의 흥미도")]
    [SerializeField, Range(0, 100)] public float mInterest;

    [System.Serializable]
    public struct InteractionActionInfo
    {
        public InteractionAction mAction;
        public int mDuration;
        [Header("상호작용 효과")]
        [SerializeField, Range(-10, 10)] public int mHungerEffect;
        [SerializeField, Range(-10, 10)] public int mSleepinessEffect;
        [SerializeField, Range(-10, 10)] public int mLonelinessEffect;
    }

    [Tooltip("이 오브젝트와 상호작용했을 때 실행될 행동 및 소요 시간 목록")]
    [SerializeField] public InteractionActionInfo[] mActions;


    // 오브젝트의 타입
    public enum Types{
        Agent,
        Food,
        Resource,
        Furniture,
        Misc,
    }

    // 오브젝트의 상태
    public enum States
    {
        Idle,
        Broken,
        Rotten,
        Installed,
        Burn,
    }
    // 오브젝트의 상호작용 목록
    public enum Actions{
        Eat,
        Get,
        Break,
        Use,
        Offer,
    }
}