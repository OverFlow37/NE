using System.Collections.Generic;
using UnityEngine;

public class Inventory : MonoBehaviour, ISaveable
{
    // 싱글톤 인스턴스
    public static Inventory Instance { get; private set; }
    
    [System.Serializable]
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
        // if (Input.GetKeyDown(KeyCode.E))
        // {
        //     InventoryUI.Instance.ToggleInventoryUI();
        // }
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

    // 인벤토리 저장용 DTO 클래스
    [System.Serializable]
    private struct InventorySaveData
    {
        public List<string> itemNames; // 아이템 이름 리스트
        public ResourceItemsCount resourceItems; // 자원 정보
    }

    public void SaveData()
    {
        // 인벤토리 데이터를 JSON 파일로 저장
        InventorySaveData saveData = new InventorySaveData
        {
            itemNames = new List<string>(),
            resourceItems = mResourceItems
        };
        
        // mItems의 각 아이템 이름 저장
        foreach (GameObject item in mItems)
        {
            saveData.itemNames.Add(item.name);
        }

        string json = JsonUtility.ToJson(saveData);
        string path = System.IO.Path.Combine(Application.persistentDataPath, "Inventory.json");
        System.IO.File.WriteAllText(path, json);
        LogManager.Log("인벤토리 저장 완료: " + path);
    }

    public void LoadData()
    {
        string path = System.IO.Path.Combine(Application.persistentDataPath, "Inventory.json");
        if (System.IO.File.Exists(path))
        {
            string json = System.IO.File.ReadAllText(path);
            InventorySaveData saveData = JsonUtility.FromJson<InventorySaveData>(json);
            
            // 아이템 이름 리스트로부터 GameObject를 찾아서 mItems에 추가
            mItems.Clear();
            if (saveData.itemNames != null)
            {
                foreach (string itemName in saveData.itemNames)
                {
                    GameObject itemPrefab = Resources.Load<GameObject>(itemName);
                    if (itemPrefab != null)
                    {
                        mItems.Add(Instantiate(itemPrefab));
                    }
                    else
                    {
                        LogManager.Log($"아이템 프리팹을 찾을 수 없음: {itemName}");
                    }
                }
            }
            
            // 자원 정보 복사
            if (saveData.resourceItems != null)
            {
                mResourceItems.wood = saveData.resourceItems.wood;
                mResourceItems.stone = saveData.resourceItems.stone;
                mResourceItems.power = saveData.resourceItems.power;
            }
            LogManager.Log("인벤토리 로드 완료: " + path);
        }
        else
        {
            LogManager.Log("저장된 인벤토리 파일이 없습니다: " + path);
        }
    }
}
