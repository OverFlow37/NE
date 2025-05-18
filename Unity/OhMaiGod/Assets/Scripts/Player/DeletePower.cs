using System.Collections;
using UnityEngine;

public class DeletePower : MonoBehaviour
{
    [Header("번개치기 이펙트")]
    [SerializeField] private GameObject mLightningStrikeEffect;
    [Header("오브젝트 번개 이벤트")]
    [SerializeField] private GameObject mLightningStrikeEvent;
    [Header("NPC 번개 이벤트")]
    [SerializeField] private GameObject mLightningStrikeEventNPC;

    private bool mIsDeleteMode = false;
    private GameObject mHighlightedObject = null;
    private Color mOriginalColor;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        
    }

    // 삭제 모드 진입
    public void EnterDeleteMode()
    {
        mIsDeleteMode = true;
    }

    // 삭제 모드 취소
    public void CancelDeleteMode()
    {
        mIsDeleteMode = false;
        RestoreHighlight();
    }

    // Update is called once per frame
    void Update()
    {
        if (mIsDeleteMode)
        {
            HandleDeleteMode();
        }
    }

    void HandleDeleteMode()
    {
        // 마우스 위치에 오브젝트가 있으면 하이라이트
        Vector3 mouseWorldPos = Camera.main.ScreenToWorldPoint(Input.mousePosition);
        mouseWorldPos.z = 0;

        // 번개치기 가능한 오브젝트만(예: Interactable 레이어) 감지
        Collider2D hit = Physics2D.OverlapPoint(mouseWorldPos, TileManager.Instance.InteractableLayerMask);
        GameObject target = hit ? hit.gameObject : null;

        // 하이라이트 갱신
        if (mHighlightedObject != target)
        {
            RestoreHighlight();
            mHighlightedObject = target;
            if (mHighlightedObject != null)
            {
                SpriteRenderer sr = mHighlightedObject.GetComponent<SpriteRenderer>();
                if (sr != null)
                {
                    mOriginalColor = sr.color;
                    sr.color = new Color(1, 0, 0, 0.5f); // 빨간색 반투명
                }
            }
        }

        // 좌클릭: 삭제
        if (Input.GetMouseButtonDown(0) && mHighlightedObject != null)
        {
            StartCoroutine(LightningStrike());
        }

        // 우클릭: 취소
        if (Input.GetMouseButtonDown(1))
        {
            CancelDeleteMode();
        }
    }

    void RestoreHighlight()
    {
        if (mHighlightedObject != null)
        {
            SpriteRenderer sr = mHighlightedObject.GetComponent<SpriteRenderer>();
            if (sr != null)
                sr.color = mOriginalColor;
            mHighlightedObject = null;
        }
    }

    private IEnumerator LightningStrike()
    {
        // 코루틴 시작 시점의 오브젝트를 지역 변수로 저장
        GameObject targetObject = mHighlightedObject;

        // 셀 계산
        Vector3Int cellPos = TileManager.Instance.GroundTilemap.WorldToCell(targetObject.transform.position);
        Vector3 cellCenter = TileManager.Instance.GroundTilemap.GetCellCenterWorld(cellPos);

        // 번개치기 이펙트
        Instantiate(mLightningStrikeEffect, cellCenter, Quaternion.identity);

        // NPC 레이어 체크 (NPC 레이어에 속하면 true)
        bool isNPC = ((1 << targetObject.layer) & TileManager.Instance.NPCLayerMask) != 0;

        if (!isNPC)
        {
            Instantiate(mLightningStrikeEvent, cellCenter, Quaternion.identity);
            // 1초 대기
            yield return new WaitForSeconds(1f);
            Destroy(targetObject);
        }
        else
        {
            Instantiate(mLightningStrikeEventNPC, cellCenter, Quaternion.identity);
        }
    }
}
