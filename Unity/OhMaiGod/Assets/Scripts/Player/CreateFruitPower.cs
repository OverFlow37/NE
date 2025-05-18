using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
public class CreateFruitPower : MonoBehaviour
{
    [Header("생성할 아이템")]
    public GameObject mSelectedPrefab; // UI에서 할당
    [Header("생성할 이벤트")]
    public GameObject mSelectedEvent;
    [Header("생성할 이펙트")]
    public GameObject mSelectedEffect;
    [Header("생성할 수 있는 아이템")]
    [SerializeField] private List<GameObject> mItemList;


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
        // 프리뷰 색상 변경
        if (mPreviewObject != null)
        {
            var previewRenderer = mPreviewObject.GetComponent<SpriteRenderer>();
            if (previewRenderer != null)
                previewRenderer.color = new Color(1, 1, 1, 0.5f); // 흰색 반투명
        }
    }

    public void PlaceObject(Vector3 _mouseWorldPos)
    {
        StartCoroutine(PlaceObjectsSequentially(_mouseWorldPos));
    }

    // 여러 아이템을 하나씩 순차적으로 생성하는 코루틴 (떨어지는 연출 없이 생성만 순차)
    private IEnumerator PlaceObjectsSequentially(Vector3 mouseWorldPos)
    {
        Vector3Int centerCell = TileManager.Instance.GroundTilemap.WorldToCell(mouseWorldPos);
        Vector3 centerCellWorld = TileManager.Instance.GroundTilemap.GetCellCenterWorld(centerCell);

        // 3x3 주변 셀 좌표 구하기
        List<Vector3Int> cellList = new List<Vector3Int>();
        for (int dx = -1; dx <= 1; dx++)
        {
            for (int dy = -1; dy <= 1; dy++)
            {
                cellList.Add(new Vector3Int(centerCell.x + dx, centerCell.y + dy, centerCell.z));
            }
        }

        // 2~4개 랜덤 개수 선택
        int itemCount = Random.Range(2, 5);
        // 셀 위치 랜덤 셔플
        for (int i = 0; i < cellList.Count; i++)
        {
            Vector3Int temp = cellList[i];
            int randIdx = Random.Range(i, cellList.Count);
            cellList[i] = cellList[randIdx];
            cellList[randIdx] = temp;
        }

        // 순차적으로 아이템 배치
        int placed = 0;
        for (int i = 0; i < cellList.Count && placed < itemCount; i++)
        {
            Vector3 cellCenter = TileManager.Instance.GroundTilemap.GetCellCenterWorld(cellList[i]);
            // 장애물 체크
            Collider2D hit = Physics2D.OverlapPoint(cellCenter, TileManager.Instance.AllLayerMask);
            if (hit != null)
                continue;
            // mItemList에서 랜덤 아이템 선택
            if (mItemList == null || mItemList.Count == 0)
            {
                LogManager.Log("Default", "mItemList가 비어있습니다.", 1);
                break;
            }
            GameObject randomItem = mItemList[Random.Range(0, mItemList.Count)];
            Instantiate(randomItem, cellCenter, Quaternion.identity);
            // 생성되는 아이템마다 이펙트 생성
            if (mSelectedEffect != null)
            {
                Instantiate(mSelectedEffect, cellCenter, Quaternion.identity);
            }
            placed++;
            // 0.2초 간격으로 순차 생성
            yield return new WaitForSeconds(0.2f);
        }
        // 이벤트 생성(즉시 생성)
        if (mSelectedEvent != null)
        {
            Instantiate(mSelectedEvent, centerCellWorld, Quaternion.identity);
        }
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