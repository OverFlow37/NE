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
        public int power = 100;
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

    public void SaveData(string _savePath)
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
            // 아이템 이름은 오브젝트 이름에서 ( 전까지 추출
            string itemName = item.name.Split('(')[0].Trim();
            saveData.itemNames.Add(itemName);
        }

        string json = JsonUtility.ToJson(saveData);
        string path = System.IO.Path.Combine(_savePath, "inventory.json");
        System.IO.File.WriteAllText(path, json);
        LogManager.Log("인벤토리 저장 완료: " + path);
    }

    public void LoadData(string _loadPath)
    {
        string path = System.IO.Path.Combine(_loadPath, "inventory.json");
        if (System.IO.File.Exists(path))
        {
            string json = System.IO.File.ReadAllText(path);
            InventorySaveData saveData = JsonUtility.FromJson<InventorySaveData>(json);
            
            // 아이템 이름 리스트로부터 PrefabManager에서 프리팹을 찾아 mItems에 추가
            mItems.Clear();
            if (saveData.itemNames != null)
            {
                foreach (string itemName in saveData.itemNames)
                {
                    // PrefabManager에서 프리팹을 이름으로 찾아옴
                    GameObject itemPrefab = PrefabManager.Instance.GetPrefabByName(itemName);
                    if (itemPrefab != null)
                    {
                        GameObject item = Instantiate(itemPrefab);
                        item.SetActive(false);
                        mItems.Add(item);
                    }
                    else
                    {
                        LogManager.Log("Inventory", $"프리팹 {itemName}을(를) 찾을 수 없습니다.", 1);
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
