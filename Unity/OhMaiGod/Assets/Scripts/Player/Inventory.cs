using System.Collections.Generic;
using UnityEngine;

public class Inventory : MonoBehaviour
{
    // 싱글톤 인스턴스
    public static Inventory Instance { get; private set; }

    public class ResourceItemsCount
    {
        public int wood = 0;
        public int stone = 0;
        public int power = 0;
    }

    [SerializeField] private List<GameObject> mItems = new List<GameObject>();
    [SerializeField] private ResourceItemsCount mResourceItems = new ResourceItemsCount();
    [SerializeField] public int mMaxSlotCount = 20;
    public ResourceItemsCount ResourceItems => mResourceItems;
    public int MaxSlotCount => mMaxSlotCount;

    public List<GameObject> Items => mItems;

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.E))
        {
            InventoryUI.Instance.ToggleInventoryUI();
        }
    }

    public void AddItem(GameObject _item)
    {
        mItems.Add(_item);
        InventoryUI.Instance.UpdateInventoryUI();
    }

    public void RemoveItem(GameObject _item)
    {
        mItems.Remove(_item);
        InventoryUI.Instance.UpdateInventoryUI();
    }

    public void AddResource(ResourceType _resourceType, int _amount)
    {
        switch (_resourceType)
        {
            case ResourceType.Wood:
                mResourceItems.wood += _amount;
                break;
            case ResourceType.Stone:
                mResourceItems.stone += _amount;
                break;
            case ResourceType.Power:
                mResourceItems.power += _amount;
                break;
        }
    }

    public void RemoveResource(ResourceType _resourceType, int _amount)
    {
        switch (_resourceType)
        {
            case ResourceType.Wood:
                mResourceItems.wood -= _amount;
                if (mResourceItems.wood < 0)
                    mResourceItems.wood = 0;
                break;
            case ResourceType.Stone:
                mResourceItems.stone -= _amount;
                if (mResourceItems.stone < 0)
                    mResourceItems.stone = 0;
                break;
            case ResourceType.Power:
                mResourceItems.power -= _amount;
                if (mResourceItems.power < 0)
                    mResourceItems.power = 0;
                break;
        }
    }
    
    public enum ResourceType
    {
        Wood,
        Stone,
        Power
    };
}
