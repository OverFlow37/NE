using UnityEngine;
using UnityEngine.SceneManagement;

public class GameManager : MonoBehaviour
{
    // 싱글톤
    private static GameManager mInstance;
    
    public static GameManager Instance
    {
        get
        {
            if (mInstance == null)
            {
                GameObject obj = new GameObject("GameManager");
                mInstance = obj.AddComponent<GameManager>();
                DontDestroyOnLoad(obj);
            }
            return mInstance;
        }
    }

    public void Awake()
    {
        Application.runInBackground = true;

        // 싱글톤 인스턴스 설정
        if (mInstance != null && mInstance != this)
        {
            Destroy(gameObject);
            return;
        }

        mInstance = this;
        DontDestroyOnLoad(gameObject);
    }

    // 모든 매니저의 SaveData 호출
    public void SaveData()
    {
        SaveLoadManager.Instance.SaveData();

        SceneManager.LoadScene("LoadScene");
    }
}

