using UnityEngine;
using System.Collections.Generic;
using UnityEngine.SceneManagement;

public class DontDestroy : MonoBehaviour
{
    // 오브젝트 이름별로 유일한 인스턴스를 관리하는 딕셔너리
    private static Dictionary<string, DontDestroy> mInstanceDict = new Dictionary<string, DontDestroy>();

    private void Awake()
    {
        string _objName = gameObject.name;
        if (!mInstanceDict.ContainsKey(_objName))
        {
            mInstanceDict[_objName] = this;
            DontDestroyOnLoad(gameObject);
        }
        // 중복된 오브젝트 삭제
        else if (mInstanceDict[_objName] != this)
        {
            Destroy(gameObject);
        }

        SceneManager.sceneLoaded += OnSceneLoaded;
    }

    private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        if(scene.name == "LoadingScene")
        {
            this.gameObject.SetActive(false);
        }
        else if (scene.name.StartsWith("Main"))
        {
            this.gameObject.SetActive(true);
        }
    }

    private void OnDestroy()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }
}