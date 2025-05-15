using UnityEngine;

public class DontDestroy : MonoBehaviour
{
    private static DontDestroy mInstance;

    private void Awake()
    {
        if (mInstance == null)
        {
            mInstance = this;
            DontDestroyOnLoad(gameObject);
        }
        else if (mInstance != this && gameObject.name == this.name)
        {
            Destroy(gameObject);
        }
    }
}