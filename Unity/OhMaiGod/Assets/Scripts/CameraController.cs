using UnityEngine;
using UnityEngine.EventSystems;

public class CameraController : MonoBehaviour
{
    private bool mIsDragging = false;
    private Vector3 mDragOrigin;
    private Vector3 mCameraOrigin;

    [Header("카메라 줌 설정")]
    public float mZoomSpeed = 2f;
    public float mMinZoom = 2f;
    public float mMaxZoom = 20f;
    private Camera mCam;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Awake()
    {
        mCam = Camera.main;
    }

    // Update is called once per frame
    void Update()
    {
        // 마우스 휠버튼(중간 버튼) 클릭 시 드래그 시작
        if (Input.GetMouseButtonDown(2))
        {
            mIsDragging = true;
            mDragOrigin = Input.mousePosition;
            mCameraOrigin = transform.position;
        }
        // 마우스 휠버튼(중간 버튼) 떼면 드래그 종료
        if (Input.GetMouseButtonUp(2))
        {
            mIsDragging = false;
        }
        // 드래그 중이면 카메라 이동
        if (mIsDragging)
        {
            Vector3 mouseDelta = Input.mousePosition - mDragOrigin;
            Vector3 worldDelta = mCam.ScreenToWorldPoint(mDragOrigin) - mCam.ScreenToWorldPoint(mDragOrigin + mouseDelta);
            worldDelta.z = 0;
            transform.position = mCameraOrigin + worldDelta;
        }

        // 마우스 휠로 부드러운 줌인/줌아웃
        float scroll = Input.GetAxis("Mouse ScrollWheel");

        // 마우스가 게임 화면(카메라 뷰포트) 안에 있는지 체크
        bool isMouseInGameScreen = false;
        if (mCam != null)
        {
            Vector3 mouseViewportPos = mCam.ScreenToViewportPoint(Input.mousePosition);
            isMouseInGameScreen =
                mouseViewportPos.x >= 0f && mouseViewportPos.x <= 1f &&
                mouseViewportPos.y >= 0f && mouseViewportPos.y <= 1f;
        }

        // 게임 창에 포커스, 마우스가 게임 화면 안, UI 위에 없을 때만 동작
        if (Mathf.Abs(scroll) > 0.01f && mCam != null && Application.isFocused && isMouseInGameScreen && !EventSystem.current.IsPointerOverGameObject())
        {
            mCam.orthographicSize = Mathf.Clamp(
                mCam.orthographicSize - scroll * mZoomSpeed,
                mMinZoom, mMaxZoom
            );
        }
    }
}
