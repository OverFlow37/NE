using UnityEngine;
using UnityEngine.EventSystems;
using Unity.Cinemachine;
using UnityEngine.Tilemaps;

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
    private CinemachineCamera mCinemachineCam;

    [Header("NPC 추적 타겟")]
    public Transform mFollowTarget;
    private bool mIsFollowMode = true; // true: 추적, false: 수동
    public bool IsFollowMode { get { return mIsFollowMode; } }

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Awake()
    {
        mCam = Camera.main;
        mCinemachineCam = GetComponent<CinemachineCamera>();
        if (mFollowTarget == null)
        {
            mFollowTarget = GameObject.Find("NPC").transform;  // 기본 Tom 추적
        }
    }

    // Update is called once per frame
    void Update()
    {
        // 마우스 휠버튼(중간 버튼) 클릭 시 드래그 시작 (수동 모드에서만)
        if (!mIsFollowMode && Input.GetMouseButtonDown(2))
        {
            mIsDragging = true;
            mDragOrigin = Input.mousePosition;
            mCameraOrigin = transform.position;
        }
        // 마우스 휠버튼(중간 버튼) 떼면 드래그 종료 (수동 모드에서만)
        if (!mIsFollowMode && Input.GetMouseButtonUp(2))
        {
            mIsDragging = false;
        }
        // 드래그 중이면 카메라 이동 (수동 모드에서만)
        if (!mIsFollowMode && mIsDragging)
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
            float prevSize = mCinemachineCam.Lens.OrthographicSize;
            float newSize = Mathf.Clamp(
                prevSize - scroll * mZoomSpeed,
                mMinZoom, mMaxZoom
            );
            mCinemachineCam.Lens.OrthographicSize = newSize;
        }
    }

    void LateUpdate()
    {
        // 카메라 위치를 타일맵 영역 내로 제한
        ClampCameraPosition();
    }

    // 카메라가 타일맵 영역 밖으로 나가지 않도록 위치를 제한하는 함수
    void ClampCameraPosition()
    {
        if (mCam == null) return;

        // 카메라의 반쪽 크기(orthographicSize, 화면 비율 고려)
        float vertExtent = mCam.orthographicSize;
        float horzExtent = vertExtent * mCam.aspect;

        // 타일맵의 월드 영역
        Bounds bounds = TileManager.Instance.GroundTilemap.localBounds;
        float minX = bounds.min.x + horzExtent;
        float maxX = bounds.max.x - horzExtent;
        float minY = bounds.min.y + vertExtent;
        float maxY = bounds.max.y - vertExtent;

        Vector3 pos = transform.position;
        pos.x = Mathf.Clamp(pos.x, minX, maxX);
        pos.y = Mathf.Clamp(pos.y, minY, maxY);
        transform.position = pos;
    }

    // 카메라 모드 토글용 public 메서드
    public void ToggleFollowMode()
    {
        mIsFollowMode = !mIsFollowMode;
        if (mCinemachineCam != null)
        {
            mCinemachineCam.Follow = mIsFollowMode ? mFollowTarget : null;
        }
        LogManager.Log("Camera", mIsFollowMode ? "NPC 추적 모드로 전환" : "수동 이동 모드로 전환", 2);
    }

    public void SetFollowTarget(Transform _target)
    {
        mFollowTarget = _target;
    }
}
