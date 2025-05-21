using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using TMPro;

public class CameraUI : MonoBehaviour
{
    [Header("버튼")]
    [SerializeField] private Button mMoveCameraButton;
    [SerializeField] private Button mFollowCameraButton;

    private CameraController mCameraController;
    private TextMeshProUGUI mNameText;

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

        // namePanel을 자식에서 찾기
        Transform namePanelTransform = transform.Find("namePanel");
        if (namePanelTransform != null)
        {
            mNameText = namePanelTransform.GetComponentInChildren<TextMeshProUGUI>();
            mNameText.text = "Tom";
        }
        else
        {
            LogManager.Log("UI", "namePanel을 찾을 수 없습니다.", 1);
        }

        mMoveCameraButton.onClick.AddListener(mCameraController.ToggleFollowMode);
        mFollowCameraButton.onClick.AddListener(mCameraController.ToggleFollowMode);
    }

    private void Update()
    {
        if (mCameraController.IsFollowMode)
        {
            mNameText.text = "Tom"; // 나중에 에이전트이름참조하는걸로
            mMoveCameraButton.gameObject.SetActive(true);
            mFollowCameraButton.gameObject.SetActive(false);
        }
        else
        {
            mNameText.text = "";           
            mMoveCameraButton.gameObject.SetActive(false);
            mFollowCameraButton.gameObject.SetActive(true);
        }
    }

    private void OnDestroy()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }
}