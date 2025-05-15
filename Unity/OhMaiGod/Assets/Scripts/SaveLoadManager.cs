using UnityEngine;
using UnityEngine.SceneManagement;

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
    }

    // Update is called once per frame
    void Update()
    {
        // 테스트용 : 스페이스바 누르면 로드 씬으로 이동 (씬 로드 테스트)
        if(Input.GetKeyDown(KeyCode.Space))
        {
            SceneManager.LoadScene("LoadScene");
        }
    }
}