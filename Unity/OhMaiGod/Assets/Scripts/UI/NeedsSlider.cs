using UnityEngine;
using UnityEngine.UI;

public class NeedsSlider : MonoBehaviour
{
    [Header("참조 오브젝트")]
    [SerializeField] private Slider mSlider; // UI 슬라이더
    [SerializeField] private Image[] mFills; // 여러 색상의 fill 오브젝트 (ex: 빨강, 노랑, 초록 등)
    [SerializeField] private AgentController mAgentController; // 에이전트 컨트롤러 참조
    [SerializeField] private int mNeedsTypeIndex = 0; // 0: Hunger, 1: Sleepiness, 2: Loneliness, 3: Stress

    private void Awake()
    {
        // 참조가 없으면 자동 할당 시도
        if (mAgentController == null)
            mAgentController = FindFirstObjectByType<AgentController>();
        if (mSlider == null)
            mSlider = GetComponentInChildren<Slider>();
        if (mFills == null || mFills.Length == 0)
            mFills = GetComponentsInChildren<Image>(true); // true: 비활성 포함
    }

    private void Update()
    {
        if (mAgentController == null || mSlider == null || mFills == null || mFills.Length == 0)
            return;

        int needsValue = 0;
        switch (mNeedsTypeIndex)
        {
            case 0:
                needsValue = mAgentController.AgnetNeeds.Hunger;
                break;
            case 1:
                needsValue = mAgentController.AgnetNeeds.Sleepiness;
                break;
            case 2:
                needsValue = mAgentController.AgnetNeeds.Loneliness;
                break;
            case 3:
                needsValue = mAgentController.AgnetNeeds.Stress;
                break;
            default:
                needsValue = 0;
                break;
        }

        // -100~100을 0~1로 변환 (0이 0.5)
        float normalizedValue = (needsValue * -1 + 100f) / 200f;
        mSlider.value = normalizedValue;

        // fill 색상별로 활성화/비활성화 (예: 0~0.33: 빨강, 0.33~0.66: 노랑, 0.66~1: 초록)
        for (int i = 0; i < mFills.Length; i++)
            mFills[i].gameObject.SetActive(false);
        int fillIndex = 0;
        if (needsValue <= -70)
            fillIndex = 0; // 파랑
        else if (needsValue <= -30)
            fillIndex = 1; // 초록
        else if (needsValue <= 70)
            fillIndex = 2; // 주황
        else
            fillIndex = 3; // 빨강
        if (fillIndex < mFills.Length)
        {
            mFills[fillIndex].gameObject.SetActive(true);
            mSlider.fillRect = mFills[fillIndex].rectTransform;
            // 슬라이더 value와 연동 (Image 타입이 Fill일 때만)
            if (mFills[fillIndex].type == Image.Type.Filled)
                mFills[fillIndex].fillAmount = normalizedValue;
        }
    }
}
