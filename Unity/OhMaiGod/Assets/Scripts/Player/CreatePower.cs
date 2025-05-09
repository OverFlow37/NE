using UnityEngine;

public class CreatePower : MonoBehaviour
{
    [Header("생성할 프리팹")]
    public GameObject mSelectedPrefab; // UI에서 할당

    private bool mIsPlacementMode = false;
    private GameObject mPreviewObject;

    void Update()
    {
        // 1. 프리뷰 활성화: mSelectedPrefab이 할당되어 있으면 프리뷰 생성
        if (mIsPlacementMode && mSelectedPrefab != null)
        {
            if (mPreviewObject == null)
                StartPreview(mSelectedPrefab);

            // 2. 마우스 위치에 프리뷰 이동
            Vector3 mouseWorldPos = Camera.main.ScreenToWorldPoint(Input.mousePosition);
            mouseWorldPos.z = 0;
            UpdatePreviewPosition(mouseWorldPos);

            // 3. 마우스 클릭 시 실제 오브젝트 생성
            if (Input.GetMouseButtonDown(0))
            {
                PlaceObject(mSelectedPrefab, mouseWorldPos);
            }
            // 오른쪽 마우스 버튼 누르면 취소
            if (Input.GetMouseButtonDown(1))
            {
                CancelPlacementMode();
            }
        }
        else
        {
            // 선택 해제 시 프리뷰 제거
            if (mPreviewObject != null)
            {
                Destroy(mPreviewObject);
                mPreviewObject = null;
            }
        }
    }

    public void StartPreview(GameObject _prefab)
    {
        // 기존 프리뷰 제거
        if (mPreviewObject != null)
            Destroy(mPreviewObject);

        // 프리뷰용 빈 오브젝트 생성
        mPreviewObject = new GameObject("PreviewObject");
        var previewRenderer = mPreviewObject.AddComponent<SpriteRenderer>();

        // 원본 프리팹의 SpriteRenderer에서 sprite, sortingLayer, order 복사
        var prefabRenderer = _prefab.GetComponent<SpriteRenderer>();
        if (prefabRenderer != null)
        {
            previewRenderer.sprite = prefabRenderer.sprite;
            previewRenderer.sortingLayerID = prefabRenderer.sortingLayerID;
            previewRenderer.sortingOrder = prefabRenderer.sortingOrder;
            previewRenderer.color = new Color(1, 1, 1, 0.5f); // 반투명
        }
        else
        {
            Debug.LogWarning("프리팹에 SpriteRenderer가 없습니다.");
        }

        mPreviewObject.layer = LayerMask.NameToLayer("Ignore Raycast");
    }

    public void UpdatePreviewPosition(Vector3 mouseWorldPos)
    {
        Vector3Int cellPos = TileManager.Instance.GroundTilemap.WorldToCell(mouseWorldPos);
        Vector3 cellCenter = TileManager.Instance.GroundTilemap.GetCellCenterWorld(cellPos);
        mPreviewObject.transform.position = cellCenter;

        // 설치 가능 여부에 따라 프리뷰 색상 변경
        int wallLayer = LayerMask.NameToLayer("Wall");
        int obstaclesLayer = LayerMask.NameToLayer("Obstacles");
        int npcLayer = LayerMask.NameToLayer("NPC");
        int mask = (1 << wallLayer) | (1 << obstaclesLayer) | (1 << npcLayer);
        Collider2D hit = Physics2D.OverlapPoint(cellCenter, mask);
        SpriteRenderer sr = mPreviewObject.GetComponent<SpriteRenderer>();
        if (sr != null)
        {
            if (hit != null)
                sr.color = new Color(1, 0, 0, 0.5f); // 빨간색 반투명
            else
                sr.color = new Color(1, 1, 1, 0.5f); // 흰색 반투명
        }
    }

    public void PlaceObject(GameObject _prefab, Vector3 mouseWorldPos)
    {
        if (_prefab == null)
        {
            Debug.LogWarning("프리팹이 할당되지 않았습니다.");
            return;
        }
        Vector3Int cellPos = TileManager.Instance.GroundTilemap.WorldToCell(mouseWorldPos);
        Vector3 cellCenter = TileManager.Instance.GroundTilemap.GetCellCenterWorld(cellPos);

        // Wall, Obstacles, NPC 레이어에 오브젝트가 있으면 설치 불가
        int wallLayer = LayerMask.NameToLayer("Wall");
        int obstaclesLayer = LayerMask.NameToLayer("Obstacles");
        int npcLayer = LayerMask.NameToLayer("NPC");
        int mask = (1 << wallLayer) | (1 << obstaclesLayer) | (1 << npcLayer);
        Collider2D hit = Physics2D.OverlapPoint(cellCenter, mask);
        if (hit != null)
        {
            Debug.LogWarning("해당 타일에 벽, 장애물 또는 NPC가 있어 설치할 수 없습니다.");
            return;
        }

        Instantiate(_prefab, cellCenter, Quaternion.identity);
        // 프리뷰는 계속 유지, mSelectedPrefab도 null로 만들지 않음
    }

    public void EnterPlacementMode(GameObject prefab)
    {
        mSelectedPrefab = prefab;
        mIsPlacementMode = true;
        // 프리뷰는 Update에서 자동 생성됨
    }

    public void CancelPlacementMode()
    {
        mIsPlacementMode = false;
        if (mPreviewObject != null)
        {
            Destroy(mPreviewObject);
            mPreviewObject = null;
        }
    }

    // UI 버튼에서 호출
    public void OnClickPlaceObjectButton(GameObject prefab)
    {
        FindFirstObjectByType<CreatePower>().EnterPlacementMode(prefab);
    }
}