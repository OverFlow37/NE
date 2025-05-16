using UnityEngine;

public class GameManager : MonoBehaviour
{
    public void Awake()
    {
        Application.runInBackground = true;
    }

    // 모든 매니저의 SaveData 호출
    public void SaveData()
    {
        SaveLoadManager.Instance.SaveData();
    }
}

