using UnityEngine;
using System.Collections.Generic;
using UnityEngine.SceneManagement;
using System.Xml.Serialization;

public class SaveLoadManager : MonoBehaviour
{
    // 싱글톤
    private static SaveLoadManager mInstance;
    
    public static SaveLoadManager Instance
    {
        get
        {
            if (mInstance == null)
            {
                GameObject obj = new GameObject("SaveLoadManager");
                mInstance = obj.AddComponent<SaveLoadManager>();
                DontDestroyOnLoad(obj);
            }
            return mInstance;
        }
    }

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

        // 씬 로드 이벤트 등록
        SceneManager.sceneLoaded += OnSceneLoaded;
    }

    private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        //  씬 로드할때 세이브 파일로부터 값 읽어와서 오브젝트 생성
        LoadData();
    }

    public void LoadScene()
    {
        SceneManager.LoadScene("LoadScene");
    }

    public void SaveData()
    {
        // 세이브 파일로 값 저장
        TileManager.Instance.SaveData();
        
        // 'NPC' 태그를 가진 모든 오브젝트의 AgentController의 SaveData 호출
        GameObject[] npcObjects = GameObject.FindGameObjectsWithTag("NPC");
        foreach (var go in npcObjects)
        {
            AgentController agent = go.GetComponent<AgentController>();
            if (agent != null)
                agent.SaveData();
        }

        // 인벤토리 저장
        Inventory.Instance.SaveData();

        // 시간 저장
        TimeManager.Instance.SaveData();
    }

    public void LoadData()
    {
        TileManager.Instance.LoadData();
        Inventory.Instance.LoadData();
        TimeManager.Instance.LoadData();
    }

    private void OnDestroy()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }
}