using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

public class InventoryUI : MonoBehaviour
{
    public static InventoryUI Instance { get; private set; }

    [Header("버튼")]
    [SerializeField] private bool mIsOpen = false;
    [SerializeField] private Button mOpenButton;
    [SerializeField] private Button mCloseButton;

    [Header("아이템 슬롯")]
    [SerializeField] private Transform mItemSlotParent; // 아이템 슬롯들을 담을 부모 오브젝트 (GridLayoutGroup이 붙어있어야 함)
    [SerializeField] private ArrangeItem mArrangeItem;  // 아이템 배치 관련 스크립트
    [SerializeField] private GameObject mItemSlotPrefab; // 아이템 슬롯 프리팹 (Image 컴포넌트 필요)

    private CanvasGroup mCanvasGroup;
    private List<GameObject> mItemSlots = new List<GameObject>();

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        mCanvasGroup = GetComponent<CanvasGroup>();
    }

    private void Start()
    {
        // 슬롯 20개 미리 생성
        for (int i = 0; i < Inventory.Instance.MaxSlotCount; i++)
        {
            GameObject slot = Instantiate(mItemSlotPrefab, mItemSlotParent);
            int capturedIndex = i; // 람다에서 인덱스 캡처
            var button = slot.GetComponent<Button>();
            if (button != null)
            {
                button.onClick.AddListener(() => OnSlotClicked(capturedIndex));
            }
            mItemSlots.Add(slot);
        }
        if (mOpenButton != null)
        {
            mOpenButton.gameObject.SetActive(!mIsOpen);
        }
        if (mCloseButton != null)
        {
            mCloseButton.gameObject.SetActive(mIsOpen);
        }

        mCanvasGroup.alpha = mIsOpen ? 1f : 0f; // 투명도
        mCanvasGroup.interactable = mIsOpen;    // 버튼 등 상호작용
        mCanvasGroup.blocksRaycasts = mIsOpen;  // 마우스 클릭 차단
        UpdateInventoryUI();
    }

    // 인벤토리 UI를 갱신하는 함수
    public void UpdateInventoryUI()
    {
        LogManager.Log("Default", $"인벤토리 UI 갱신, 아이템 개수: {Inventory.Instance.Items.Count}개", 2);
        var items = Inventory.Instance != null ? Inventory.Instance.Items : null;
        if (items == null)
        {
            LogManager.Log("UI", "인벤토리 인스턴스 또는 아이템 목록이 null입니다.", 1);
            return;
        }

        for (int i = 0; i < Inventory.Instance.MaxSlotCount; i++)
        {
            // 슬롯 프리팹 구조: 부모(배경 Image) + 자식("Icon" 이름의 Image)
            var iconImage = mItemSlots[i].transform.GetChild(0).GetComponent<Image>();
            if (i < items.Count && items[i] != null)
            {
                var interactable = items[i].GetComponent<Interactable>();
                if (interactable != null && interactable.mInteractableData != null)
                {
                    iconImage.sprite = interactable.mInteractableData.mIcon;
                    iconImage.color = Color.white; // 아이콘이 있으면 보이게
                }
                else
                {
                    iconImage.sprite = null;
                    iconImage.color = new Color(1,1,1,0); // 투명 처리
                    LogManager.Log("UI", $"{i}번 슬롯: Interactable 또는 InteractableData가 null입니다.", 1);
                }
            }
            else
            {
                iconImage.sprite = null;
                iconImage.color = new Color(1,1,1,0); // 투명 처리
            }
        }
        LogManager.Log("UI", "인벤토리 UI 갱신 완료", 2);
    }

    // 슬롯 클릭 시 호출되는 함수
    private void OnSlotClicked(int _slotIndex)
    {
        var items = Inventory.Instance.Items;
        if (_slotIndex < items.Count && items[_slotIndex] != null)
        {
            var item = items[_slotIndex];
            var interactable = item.GetComponent<Interactable>();
            if (interactable != null)
            {
                LogManager.Log("UI", $"슬롯 {_slotIndex} 클릭: {interactable.mInteractableData.mName}", 2);
                mArrangeItem.EnterPlacementMode(item);
            }
        }
        else
        {
            LogManager.Log("UI", $"슬롯 {_slotIndex} 클릭: 아이템 없음", 2);
        }
    }

    // 인벤토리 UI 오브젝트 활성/비활성 토글 함수 (버튼에서 호출)
    public void ToggleInventoryUI()
    {
        mIsOpen = !mIsOpen;
        if (mCanvasGroup != null)
        {
            mCanvasGroup.alpha = mIsOpen ? 1f : 0f; // 투명도
            mCanvasGroup.interactable = mIsOpen;    // 버튼 등 상호작용
            mCanvasGroup.blocksRaycasts = mIsOpen;  // 마우스 클릭 차단
        }

        if (mOpenButton != null)
        {
            mOpenButton.gameObject.SetActive(!mIsOpen);
        }
        if (mCloseButton != null)
        {
            mCloseButton.gameObject.SetActive(mIsOpen);
        }
        if (mIsOpen)
        {
            UpdateInventoryUI();
        }
    }
}
