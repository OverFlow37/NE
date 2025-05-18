using UnityEngine;
using System.Collections.Generic;
using UnityEngine.SceneManagement;
using System.Xml.Serialization;
using System.Collections;

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

    private void OnSceneLoaded(Scene _scene, LoadSceneMode _mode)
    {
        if(_scene.name == "LoadingScene")
        {
            // 로딩 씬에서는 AIBridge_Perceive, TimeManager disbale
            AIBridge_Perceive.Instance.gameObject.SetActive(false);
            TimeManager.Instance.gameObject.SetActive(false);
            return;
        } 

        //  씬 로드할때 세이브 파일로부터 값 읽어와서 오브젝트 생성
        LoadData();
    }

    public void LoadScene()
    {
        // 게임씬으로 로드할때는 AIBridge_Perceive, TimeManager enable
        AIBridge_Perceive.Instance.gameObject.SetActive(true);
        TimeManager.Instance.gameObject.SetActive(true);

        // 동기로 로드
        SceneManager.LoadScene("Main_SYE");

        // 비동기 씬 로드 및 로딩 씬 언로드 코루틴 시작 => 오류 너무 많음...
        // StartCoroutine(LoadAndSwitchSceneCoroutine());
    }

    // Main_SYE 비동기 로드 후 로딩 씬 언로드 코루틴
    // private IEnumerator LoadAndSwitchSceneCoroutine()
    // {
    //     // Main_SYE 씬을 Additive로 비동기 로드
    //     AsyncOperation mAsyncLoad = SceneManager.LoadSceneAsync("Main_SYE", LoadSceneMode.Additive);
    //     LogManager.Log("SaveLoad", "Main_SYE 씬 비동기 로드 시작", 2);

    //     // 로딩 중에는 Main_SYE 오브젝트가 Hierarchy에 있지만, 아직 활성 씬은 아님
    //     while (!mAsyncLoad.isDone)
    //     {
    //         yield return null;
    //     }

    //     LogManager.Log("SaveLoad", "Main_SYE 씬 로드 완료, 활성 씬 전환 및 로딩 씬 언로드 시작", 2);

    //     // Main_SYE를 활성 씬으로 설정
    //     Scene mMainScene = SceneManager.GetSceneByName("Main_SYE");
    //     if (mMainScene.IsValid())
    //     {
    //         SceneManager.SetActiveScene(mMainScene);
    //     }
    //     else
    //     {
    //         LogManager.Log("SaveLoad", "Main_SYE 씬 활성화 실패", 0);
    //     }

    //     LoadData();

    //     // 로딩 씬 언로드
    //     string mLoadingSceneName = "LoadingScene";
    //     AsyncOperation mAsyncUnload = SceneManager.UnloadSceneAsync(mLoadingSceneName);

    //     while (!mAsyncUnload.isDone)
    //     {
    //         yield return null;
    //     }

    //     LogManager.Log("SaveLoad", "로딩 씬 언로드 완료, Main_SYE 진입", 2);
    // }

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

        Inventory.Instance.GetComponentInChildren<ChatPower>().SetAgentController();
    }

    private void OnDestroy()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }
}