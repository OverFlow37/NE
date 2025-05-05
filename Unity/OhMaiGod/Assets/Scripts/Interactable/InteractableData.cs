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
    [SerializeField] public string mDescriptionPrompt; // 개발자 확인용 오브젝트 설명
    [Tooltip("오브젝트의 타입")]
    [SerializeField] public Types mType;
    [Tooltip("오브젝트의 현재 상태")]
    [SerializeField] public States mState;

    [Tooltip("이 오브젝트와 상호작용했을 때 실행될 행동 목록")]
    [SerializeField] public InteractionAction[] mActions;

    // 상호작용 효과
    [Header("Interaction Effects")]
    [Tooltip("상호작용으로 인한 배고픔 변화량")]
    [SerializeField, Range(-10, 10)] public int mHungerEffect;
    [Tooltip("상호작용으로 인한 졸림 변화량")]
    [SerializeField, Range(-10, 10)] public int mSleepinessEffect;
    [Tooltip("상호작용으로 인한 외로움 변화량")]
    [SerializeField, Range(-10, 10)] public int mLonelinessEffect;

    // 오브젝트의 타입
    public enum Types{
        Food,
        Tool,
        Resource,
        Furniture,
        Other,
    }

    // 오브젝트의 상태
    // 나중에 사용할 예정
    public enum States
    {
        Idle,
        Broken,
        Rotten,
        Hidden,
    }
    // 오브젝트의 상호작용 목록
    // 현재 미사용
    public enum Actions{
        Eat,
        Get,
        Break,
        Use,
    }
}