using UnityEngine;
using System.Collections.Generic;

public class LogManager : MonoBehaviour
{
    public static LogManager Instance { get; private set; }

    [Header("로그 레벨 (0=Error, 1=Warning, 2=Info, 3=Debug)")]
    [Range(0, 3)]
    public int logLevel = 2;

    [Header("로그 카테고리")]
    [SerializeField] private List<string> categories = new List<string> { "Agent", "Scheduler", "Movement", "Vision", "AI", "Env", "Interact", "Time", "Default" };
    [SerializeField] private List<bool> categoryEnabled = new List<bool> { false, false, false, false, false, false, false, false, true };

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public static void Log(string category, string message, int level = 2)
    {
        if (Instance == null)
            return;

        if (!Instance.IsCategoryEnabled(category)) return;
        if (level > Instance.logLevel) return;

        string prefix = $"[{category}] ";
        switch (level)
        {
            case 0: Debug.LogError(prefix + message); break;
            case 1: Debug.LogWarning(prefix + message); break;
            case 2: Debug.Log(prefix + message); break;
            case 3: Debug.Log("[DEBUG] " + prefix + message); break;
        }
    }

    public static void Log(string message, int level = 2)
    {
        Log("Default", message, level);
    }

    public bool IsCategoryEnabled(string category)
    {
        int idx = categories.IndexOf(category);
        if (idx >= 0 && idx < categoryEnabled.Count)
            return categoryEnabled[idx];
        return false;
    }

    // Inspector에서 카테고리 추가/삭제/순서변경 시 bool 배열 동기화
    private void OnValidate()
    {
        while (categoryEnabled.Count < categories.Count)
            categoryEnabled.Add(true);
        while (categoryEnabled.Count > categories.Count)
            categoryEnabled.RemoveAt(categoryEnabled.Count - 1);
    }
}

