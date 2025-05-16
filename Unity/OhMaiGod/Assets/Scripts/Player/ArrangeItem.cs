using UnityEngine;

public class ArrangeItem : MonoBehaviour
{
    [Header("배치할 아이템")]
    public GameObject mSelectedItem; // UI에서 할당
    [Header("배치할 이벤트")]
    public GameObject mSelectedEvent;
    [Header("배치할 이펙트")]
    public GameObject mSelectedEffect;

    private bool mIsPlacementMode = false;
    private GameObject mPreviewObject;

    void Update()
    {
        // 1. 프리뷰 활성화: mSelectedItem이 할당되어 있으면 프리뷰 생성
        if (mIsPlacementMode && mSelectedItem != null)
        {
            if (mPreviewObject == null)
                StartPreview(mSelectedItem);

            // 2. 마우스 위치에 프리뷰 이동
            Vector3 mouseWorldPos = Camera.main.ScreenToWorldPoint(Input.mousePosition);
            mouseWorldPos.z = 0;
            UpdatePreviewPosition(mouseWorldPos);

            // 3. 마우스 클릭 시 실제 오브젝트 생성
            if (Input.GetMouseButtonDown(0))
            {
                PlaceObject(mSelectedItem, mouseWorldPos);
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

    public void StartPreview(GameObject _item)
    {
        // 기존 프리뷰 제거
        if (mPreviewObject != null)
            Destroy(mPreviewObject);

        // 프리뷰용 빈 오브젝트 생성
        mPreviewObject = new GameObject("PreviewObject");
        var previewRenderer = mPreviewObject.AddComponent<SpriteRenderer>();

        // 원본 프리팹의 SpriteRenderer에서 sprite, sortingLayer, order 복사
        var itemRenderer = _item.GetComponent<SpriteRenderer>();
        if (itemRenderer != null)
        {
            previewRenderer.sprite = itemRenderer.sprite;
            previewRenderer.sortingLayerID = itemRenderer.sortingLayerID;
            previewRenderer.sortingOrder = itemRenderer.sortingOrder;
            previewRenderer.color = new Color(1, 1, 1, 0.5f); // 반투명
        }
        else
        {
            Debug.LogWarning("아이템에 SpriteRenderer가 없습니다.");
        }

        mPreviewObject.layer = LayerMask.NameToLayer("Ignore Raycast");
    }

    public void UpdatePreviewPosition(Vector3 mouseWorldPos)
    {
        Vector3Int cellPos = TileManager.Instance.GroundTilemap.WorldToCell(mouseWorldPos);
        Vector3 cellCenter = TileManager.Instance.GroundTilemap.GetCellCenterWorld(cellPos);
        mPreviewObject.transform.position = cellCenter;

        // 설치 가능 여부에 따라 프리뷰 색상 변경
        Collider2D hit = Physics2D.OverlapPoint(cellCenter, TileManager.Instance.AllLayerMask);
        SpriteRenderer sr = mPreviewObject.GetComponent<SpriteRenderer>();
        if (sr != null)
        {
            if (hit != null)
                sr.color = new Color(1, 0, 0, 0.5f); // 빨간색 반투명
            else
                sr.color = new Color(1, 1, 1, 0.5f); // 흰색 반투명
        }
    }

    public void PlaceObject(GameObject _item, Vector3 mouseWorldPos)
    {
        if (_item == null)
        {
            Debug.LogWarning("프리팹이 할당되지 않았습니다.");
            return;
        }
        Vector3Int cellPos = TileManager.Instance.GroundTilemap.WorldToCell(mouseWorldPos);
        Vector3 cellCenter = TileManager.Instance.GroundTilemap.GetCellCenterWorld(cellPos);

        // Wall, Obstacles, NPC 레이어에 오브젝트가 있으면 설치 불가
        Collider2D hit = Physics2D.OverlapPoint(cellCenter, TileManager.Instance.AllLayerMask);
        if (hit != null)
        {
            Debug.LogWarning("해당 타일에 벽, 장애물 또는 NPC가 있어 배치할 수 없습니다.");
            return;
        }

        // 이벤트 생성
        GameObject eventObject = Instantiate(mSelectedEvent, cellCenter, Quaternion.identity);
        eventObject.GetComponent<EventController>().mEventInfo = mSelectedEvent.GetComponent<EventController>().mEventInfo;
        // 이펙트 생성 및 자동 파괴
        if (mSelectedEffect != null)
        {
            GameObject effect = Instantiate(mSelectedEffect, cellCenter, Quaternion.identity);
            Destroy(effect, 1.5f); // 1.5초 뒤에 이펙트 오브젝트 삭제
        }
        
        _item.transform.position = cellCenter;
        _item.SetActive(true);
        Inventory.Instance.RemoveItem(mSelectedItem);
        CancelPlacementMode();
    }

    public void EnterPlacementMode(GameObject _item)
    {
        mSelectedItem = _item;
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
    public void OnClickPlaceObjectButton(GameObject _item)
    {
        EnterPlacementMode(_item);
    }
}