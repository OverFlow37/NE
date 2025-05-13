using UnityEngine;

public class DeletePower : MonoBehaviour
{
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

        // 삭제 가능한 오브젝트만(예: Interactable 레이어) 감지
        int interactableLayer = LayerMask.NameToLayer("Obstacles");
        int mask = 1 << interactableLayer;
        Collider2D hit = Physics2D.OverlapPoint(mouseWorldPos, mask);

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
            Destroy(mHighlightedObject);
            mHighlightedObject = null;
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
}
