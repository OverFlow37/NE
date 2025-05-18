using UnityEngine;

public class ChangeSceneButton : MonoBehaviour
{
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    public void ChangeSceneToLoadScene()
    {
        SaveLoadManager.Instance.LoadScene();
    }
}
