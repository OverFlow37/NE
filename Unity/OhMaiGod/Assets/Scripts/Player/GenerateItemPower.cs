using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
public class GenerateItemPower : MonoBehaviour
{
    [Header("배치할 아이템")]
    public GameObject mSelectedItem;
    [Header("배치할 이벤트")]
    public GameObject mSelectedEvent;
    [Header("배치할 이펙트")]
    public GameObject mSelectedEffect;

    private bool mIsPlacementMode = false;
    private GameObject mPreviewObject;

    void Update()
    {
        // 1. 프리뷰 활성화: mSelectedPrefab이 할당되어 있으면 프리뷰 생성
        if (mIsPlacementMode)
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
            Debug.LogWarning("해당 타일에 벽, 장애물 또는 NPC가 있어 배치할 수 없습니다.");
            return;
        }

        // 아이템 생성
        bool isSpawned = tileController.InteractableSpawner.Spawn(cellCenter);
        if (!isSpawned)
        {
            Debug.LogWarning("해당 타일에 아이템을 생성할 수 없습니다.");
            return;
        }
        // 이벤트 생성
        Instantiate(mSelectedEvent, cellCenter, Quaternion.identity);
        // 이펙트 생성
        Instantiate(mSelectedEffect, cellCenter, Quaternion.identity);
    }


    public void EnterPlacementMode()
    {
        mIsPlacementMode = true;
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
    public void OnClickPlaceObjectButton()
    {
        EnterPlacementMode();
    }
}