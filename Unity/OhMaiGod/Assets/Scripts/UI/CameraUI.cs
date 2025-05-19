using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

public class CameraUI : MonoBehaviour
{
    [Header("버튼")]
    [SerializeField] private Button mMoveCameraButton;
    [SerializeField] private Button mFollowCameraButton;

    private CameraController mCameraController;

    private void Awake()
    {
        SceneManager.sceneLoaded += OnSceneLoaded;

        Initialize();
    }

    private void OnSceneLoaded(Scene _scene, LoadSceneMode _mode)
    {
        if(_scene.name.StartsWith("Main"))
        {   
            Initialize();
        }
    }

    private void Initialize()
    {
        GameObject cinemachineCam = GameObject.Find("CinemachineCamera");

        mCameraController = cinemachineCam.GetComponent<CameraController>();     

        mMoveCameraButton.onClick.AddListener(mCameraController.ToggleFollowMode);
        mFollowCameraButton.onClick.AddListener(mCameraController.ToggleFollowMode);
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

    private void OnDestroy()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }
}