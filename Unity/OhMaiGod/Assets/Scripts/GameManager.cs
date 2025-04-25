using UnityEngine;

public class GameManager : MonoBehaviour
{
    public void Awake()
    {
        Application.runInBackground = true;
    }
}
