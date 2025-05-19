using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
public class CreateRockPower : Power
{
    [Header("생성할 아이템")]
    public GameObject mSelectedPrefab; // UI에서 할당
    [Header("생성할 이벤트")]
    public GameObject mSelectedEvent;
    [Header("생성할 이펙트")]
    public GameObject mSelectedEffect;
    [Header("생성할 수 있는 아이템")]
    [SerializeField] private List<GameObject> mItemList;


    private GameObject mPreviewObject;

    void Update()
    {
        // UI 위에 마우스가 있으면 프리뷰 숨김
        if (EventSystem.current != null && mPreviewObject != null)
        {
            if (EventSystem.current.IsPointerOverGameObject())
            {
                if (mPreviewObject.activeSelf)
                    mPreviewObject.SetActive(false);
            }
            else
            {
                if (!mPreviewObject.activeSelf)
                    mPreviewObject.SetActive(true);
            }
        }
        // 1. 프리뷰 활성화: mSelectedPrefab이 할당되어 있으면 프리뷰 생성
        if (base.mIsActive)
        {
            if (mPreviewObject == null)
                StartPreview();

            // 2. 마우스 위치에 프리뷰 이동
            Vector3 mouseWorldPos = Camera.main.ScreenToWorldPoint(Input.mousePosition);
            mouseWorldPos.z = 0;
            UpdatePreviewPosition(mouseWorldPos);

            // 3. 마우스 클릭 시 실제 오브젝트 생성
            if (Input.GetMouseButtonDown(0))
            {
                PlaceObject(mouseWorldPos);
            }
            // 오른쪽 마우스 버튼 누르면 취소
            if (Input.GetMouseButtonDown(1))
            {
                Deactive();
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

    public void StartPreview()
    {
        // 기존 프리뷰 제거
        if (mPreviewObject != null)
            Destroy(mPreviewObject);

        // 프리뷰용 빈 오브젝트 생성
        mPreviewObject = new GameObject("PreviewObject");
        var previewRenderer = mPreviewObject.AddComponent<SpriteRenderer>();

        // 노란색 반투명 사각형(오버레이) 생성
        Texture2D tex = new Texture2D(1, 1);
        tex.SetPixel(0, 0, Color.yellow);
        tex.Apply();
        Rect rect = new Rect(0, 0, 1, 1);
        Vector2 pivot = new Vector2(0.5f, 0.5f);
        // 픽셀 퍼 유닛을 1로 설정 (1픽셀 = 1유닛)
        Sprite yellowSprite = Sprite.Create(tex, rect, pivot, 1f);
        previewRenderer.sprite = yellowSprite;
        previewRenderer.color = new Color(1f, 1f, 0f, 0.5f); // 노란색 반투명
        previewRenderer.sortingOrder = 1000; // 항상 위에 보이도록

        // 타일맵 셀 크기에 맞게 스케일 조정
        Vector3 cellSize = TileManager.Instance.GroundTilemap.cellSize;
        mPreviewObject.transform.localScale = cellSize;
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

    public void PlaceObject(Vector3 _mouseWorldPos)
    {
        // UI 위에 마우스가 있으면 동작하지 않음
        if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject())
        {
            LogManager.Log("Default", "UI 위에서는 아이템을 생성할 수 없습니다.", 1);
            return;
        }
        Vector3Int cellPos = TileManager.Instance.GroundTilemap.WorldToCell(_mouseWorldPos);
        TileController tileController = TileManager.Instance.GetTileController(cellPos);
        Vector2 cellCenter = TileManager.Instance.GroundTilemap.GetCellCenterWorld(cellPos);

        if (tileController == null)
        {
            return;
        }

        // Wall, Obstacles, NPC 레이어에 오브젝트가 있으면 설치 불가
        Collider2D hit = Physics2D.OverlapPoint(cellCenter, TileManager.Instance.AllLayerMask);
        if (hit != null)
        {
            LogManager.Log("Default", "해당 타일에 벽, 장애물 또는 NPC가 있어 배치할 수 없습니다.", 1);
            return;
        }

        // 아이템 목록에서 랜덤 아이템 선택
        if (mItemList == null || mItemList.Count == 0)
        {
            LogManager.Log("Default", "mItemList가 비어있습니다.", 1);
            return;
        }
        GameObject randomItem = mItemList[Random.Range(0, mItemList.Count)];
        Instantiate(randomItem, cellCenter, Quaternion.identity);
        // 이벤트 생성
        EventController eventController = Instantiate(mSelectedEvent, cellCenter, Quaternion.identity).GetComponent<EventController>();
        eventController.mEventInfo.event_location = TileManager.Instance.GetTileController(cellPos).LocationName;
        eventController.mEventInfo.event_description += $" at {eventController.mEventInfo.event_location}";
        eventController.mEventInfo.importance = 4;
        // 이펙트 생성
        Instantiate(mSelectedEffect, cellCenter, Quaternion.identity);
    }


    public override void Active()
    {
        base.Active();
    }
    public override void Deactive()
    {
        base.Deactive();
        if (mPreviewObject != null)
        {
            Destroy(mPreviewObject);
            mPreviewObject = null;
        }
    }
}