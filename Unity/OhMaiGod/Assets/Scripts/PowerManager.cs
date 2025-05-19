using UnityEngine;
using System;

public class PowerManager : MonoBehaviour
{
    public static PowerManager Instance { get; private set; }

    [SerializeField]
    private Power[] mPowers;

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        // 같은 오브젝트에 붙은 모든 Power 컴포넌트를 자동으로 할당
        mPowers = GetComponents<Power>();
        foreach (var power in mPowers)
        {
            power.Deactive();
            LogManager.Log("PowerManager", power.name + " 비활성화");
        }
    }

    public void DeactiveOtherPowers()
    {
        foreach (var power in mPowers)
        {
            power.Deactive();
        }
        LogManager.Log("PowerManager", "모든 Power 비활성화");
    }
}
