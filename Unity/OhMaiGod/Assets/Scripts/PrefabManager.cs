using UnityEngine;
using System.Collections.Generic;

public class PrefabManager : MonoBehaviour
{
    // 싱글톤
    private static PrefabManager mInstance;
    
    public static PrefabManager Instance
    {
        get
        {
            if (mInstance == null)
            {
                GameObject obj = new GameObject("PrefabManager");
                mInstance = obj.AddComponent<PrefabManager>();
                DontDestroyOnLoad(obj);
            }
            return mInstance;
        }
    }

    // 인스펙터에서 프리팹을 할당받는 리스트
    [SerializeField]
    private List<GameObject> mPrefabList = new List<GameObject>();

    // 내부적으로 이름-프리팹 매핑 딕셔너리
    private Dictionary<string, GameObject> mPrefabDict = new Dictionary<string, GameObject>();

    
    private void Awake()
    {
        // 싱글톤 인스턴스 설정
        if (mInstance != null && mInstance != this)
        {
            Destroy(gameObject);
            return;
        }

        mInstance = this;
        DontDestroyOnLoad(gameObject);

        // 딕셔너리 초기화
        mPrefabDict.Clear();
        foreach (GameObject prefab in mPrefabList)
        {
            if (prefab != null)
            {
                if (!mPrefabDict.ContainsKey(prefab.name))
                {
                    mPrefabDict.Add(prefab.name, prefab);
                }
                else
                {
                    LogManager.Log("Prefab", $"중복된 프리팹 이름: {prefab.name}", 1);
                }
            }
        }
    }

    // 프리팹 이름으로 프리팹 오브젝트 반환
    public GameObject GetPrefabByName(string _name)
    {
        if (mPrefabDict.TryGetValue(_name, out GameObject prefab))
        {
            return prefab;
        }
        LogManager.Log("Prefab", $"프리팹 이름 {_name}을(를) 찾을 수 없습니다.", 1);
        return null;
    }
}
