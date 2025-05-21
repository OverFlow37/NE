using UnityEngine;
using UnityEngine.UI;

public class MusicController : MonoBehaviour
{
    [Header("버튼 참조")]
    [SerializeField] private Button mMuteButton;      // 음소거 버튼
    [SerializeField] private Button mUnmuteButton;    // 음소거 해제 버튼
    [Header("볼륨 설정")]
    [Range(0f, 1f)]
    [SerializeField] private float mOriginalVolume = 1.0f; // 복구할 볼륨값

    private GameObject mBGMObject;    // 배경음 오브젝트
    private AudioSource mBGMSource;   // 배경음 AudioSource
    private bool mIsMuted = false;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        mBGMObject = GameObject.Find("BackgroundMusic");
        if (mBGMObject == null)
        {
            LogManager.Log("UI", "BGM 오브젝트를 찾을 수 없습니다.", 0);
            return;
        }
        mBGMSource = mBGMObject.GetComponent<AudioSource>();
        if (mBGMSource == null)
        {
            LogManager.Log("UI", "BGM 오브젝트에 AudioSource가 없습니다.", 0);
            return;
        }
        mBGMSource.volume = mOriginalVolume;
        mIsMuted = false;
        if (mMuteButton != null) mMuteButton.onClick.AddListener(MuteBGM);
        if (mUnmuteButton != null) mUnmuteButton.onClick.AddListener(UnmuteBGM);
        UpdateButtonState();
        LogManager.Log("UI", "MusicController 초기화 완료");
    }

    public void MuteBGM()
    {
        if (mBGMSource == null) return;
        mBGMSource.volume = 0f;
        mIsMuted = true;
        UpdateButtonState();
        LogManager.Log("UI", "배경음 음소거");
    }

    public void UnmuteBGM()
    {
        if (mBGMSource == null) return;
        mBGMSource.volume = mOriginalVolume;
        mIsMuted = false;
        UpdateButtonState();
        LogManager.Log("UI", "배경음 음소거 해제");
    }

    private void UpdateButtonState()
    {
        if (mMuteButton != null) mMuteButton.gameObject.SetActive(!mIsMuted);
        if (mUnmuteButton != null) mUnmuteButton.gameObject.SetActive(mIsMuted);
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
