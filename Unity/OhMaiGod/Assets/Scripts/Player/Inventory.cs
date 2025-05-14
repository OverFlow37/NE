using System.Collections.Generic;
using UnityEngine;

public class Inventory : MonoBehaviour
{
    // 싱글톤 인스턴스
    public static Inventory Instance { get; private set; }

    public class ResourceItems
    {
        public int wood = 0;
        public int stone = 0;
        public int power = 0;
    }

    [SerializeField, ReadOnly] private List<GameObject> mItems = new List<GameObject>();
    [SerializeField, ReadOnly] public ResourceItems mResourceItems { get; private set; } = new ResourceItems();


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

    public void AddItem(GameObject _item)
    {
        mItems.Add(_item);
    }

    public void RemoveItem(GameObject _item)
    {
        mItems.Remove(_item);
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

    // UI에서 인벤토리를 표시할 수 있도록 임시로 문자열로 반환하는 메서드 추가
    public string GetInventoryString()
    {
        if (mItems == null || mItems.Count == 0)
            return "인벤토리 비어있음";
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        foreach (var item in mItems)
        {
            sb.AppendLine($"{item.GetComponent<Interactable>().InteractableName} : {item.name}");
        }
        return sb.ToString();
    }

    
    public enum ResourceType
    {
        Wood,
        Stone,
        Power
    };
}
