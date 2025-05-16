using UnityEngine;
using UnityEngine.UI;

public class CameraUI : MonoBehaviour
{
    public static CameraUI Instance { get; private set; }

    [Header("버튼")]
    [SerializeField] private Button mMoveCameraButton;
    [SerializeField] private Button mFollowCameraButton;

    private CameraController mCameraController;

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        mCameraController = GetComponent<CameraController>();
    }

    private void Update()
    {
        if (mCameraController.IsFollowMode)
        {
            mMoveCameraButton.gameObject.SetActive(true);
            mFollowCameraButton.gameObject.SetActive(false);
        }
        else
        {
            mMoveCameraButton.gameObject.SetActive(false);
            mFollowCameraButton.gameObject.SetActive(true);
        }
    }
}