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

    }

    public void LoadData()
    {
        TileManager.Instance.LoadData();
    }

    private void OnDestroy()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }
}