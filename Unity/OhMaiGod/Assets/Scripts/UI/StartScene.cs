using UnityEngine;
using TMPro;
using UnityEngine.UI;
using System.IO; // 파일 존재 확인을 위해 추가
using System.Collections;

public class StartScene : MonoBehaviour
{
    private TextMeshProUGUI mText;
    private Button mNewGameButton;
    private Button mContinueButton;
    private Button mContinueButtonDisabled;
    private Button mExitButton;
    [SerializeField] private Canvas mLoadingUI;

    private void Awake()
    {
        // 자식텍스트중 이름이 "NoSavedData"인 것
        mText = transform.Find("NoSavedData").GetComponent<TextMeshProUGUI>();
        // 자식버튼중 이름이 "NewGame"인 것
        mNewGameButton = transform.Find("NewGame").GetComponent<Button>();
        // 자식버튼중 이름이 "Continue"인 것 
        mContinueButton = transform.Find("Continue").GetComponent<Button>();
        // 자식버튼중 이름이 "ContinueDisabled"인 것
        mContinueButtonDisabled = transform.Find("ContinueDisabled").GetComponent<Button>();
        // 자식버튼중 이름이 "Exit"인 것
        mExitButton = transform.Find("Exit").GetComponent<Button>();
    }

    private void Start()
    {
        mText.gameObject.SetActive(false);

        // 세이브 데이터 폴더가 존재하는지 확인
        if (SaveLoadManager.Instance.IsSaveDataExist())
        {
            // 세이브 파일이 있으면 이어하기 버튼 활성화, 비활성 버튼 비활성화
            mContinueButton.gameObject.SetActive(true);
            mContinueButtonDisabled.gameObject.SetActive(false);
        }
        else
        {
            // 세이브 파일이 없으면 이어하기 버튼 비활성화, 비활성 버튼 활성화
            mContinueButton.gameObject.SetActive(false);
            mContinueButtonDisabled.gameObject.SetActive(true);
        }

        mNewGameButton.onClick.AddListener(OnClickNewGame);
        mContinueButton.onClick.AddListener(OnClickContinue);
        mContinueButtonDisabled.onClick.AddListener(OnClickContinueDisabled);
        mExitButton.onClick.AddListener(OnClickExit);
    }

    // 새 게임 시작 버튼에 연결할 함수
    public void OnClickNewGame()
    {
        mLoadingUI.gameObject.SetActive(true);   // 로딩 UI 활성화
        SaveLoadManager.Instance.ResetData();   // 기존 세이브 데이터 삭제

        // AI 서버에 에이전트 메모리 데이터 삭제 요청
        AIBridge_Perceive.Instance.ResetMemoryAllAgent(() =>
        {
            SaveLoadManager.Instance.LoadScene();  // AI서버의 메모리 데이터 삭제 완료 후, 동기 로드
        });
    }

    // 이어하기 버튼에 연결할 함수
    public void OnClickContinue()
    {
        mLoadingUI.gameObject.SetActive(true);   // 로딩 UI 활성화

        SaveLoadManager.Instance.LoadScene();
    }

    public void OnClickContinueDisabled()
    {
        mText.gameObject.SetActive(true);
        // 3초 후 텍스트 숨기기 코루틴 시작
        StartCoroutine(HideTextAfterSeconds(3f));
    }

    // 텍스트를 지정한 시간 후에 숨기는 코루틴
    private IEnumerator HideTextAfterSeconds(float _seconds)
    {
        yield return new WaitForSeconds(_seconds);
        mText.gameObject.SetActive(false);
    }

    // 종료 버튼에 연결할 함수
    public void OnClickExit()
    {
        #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
        #else
            Application.Quit();
        #endif
    }
}
