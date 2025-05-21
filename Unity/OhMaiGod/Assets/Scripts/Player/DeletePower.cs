using System.Collections;
using UnityEngine;
using UnityEngine.EventSystems;

public class DeletePower : Power
{
    [Header("번개줄기 이펙트")]
    [SerializeField] private GameObject mLightningEffect;
    [Header("번개치기 이펙트")]
    [SerializeField] private GameObject mLightningStrikeEffect;
    [Header("오브젝트 번개 이벤트")]
    [SerializeField] private GameObject mLightningStrikeEvent;
    [Header("NPC 번개 이벤트")]
    [SerializeField] private GameObject mLightningStrikeEventNPC;

    private GameObject mHighlightedObject = null;
    private Color mOriginalColor;


    // Update is called once per frame
    void Update()
    {
        if (base.mIsActive)
        {
            // UI 위에 마우스가 있으면 하이라이트 숨김
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject())
            {
                RestoreHighlight();
                return;
            }
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
            // UI 위에 마우스가 있으면 동작하지 않음
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject())
            {
                LogManager.Log("Default", "UI 위에서는 삭제가 불가능합니다.", 1);
                return;
            }
            if(Inventory.Instance.ResourceItems.power < mPowerCost){
            LogManager.Log("Default", "파워가 부족합니다.", 1);
            return;
            }
            Inventory.Instance.AddResource(Inventory.ResourceType.Power, -mPowerCost);
            LightningStrike();
        }

        // 우클릭: 취소
        if (Input.GetMouseButtonDown(1))
        {
            Deactive();
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

    private void LightningStrike()
    {
        // 코루틴 시작 시점의 오브젝트를 지역 변수로 저장
        GameObject targetObject = mHighlightedObject;

        // 셀 계산
        Vector3Int cellPos = TileManager.Instance.GroundTilemap.WorldToCell(targetObject.transform.position);
        Vector3 cellCenter = TileManager.Instance.GroundTilemap.GetCellCenterWorld(cellPos);

        // 번개치기 이펙트
        Instantiate(mLightningStrikeEffect, cellCenter, Quaternion.identity);
        Instantiate(mLightningEffect, cellCenter, Quaternion.identity);

        // NPC 레이어 체크 (NPC 레이어에 속하면 true)
        bool isNPC = ((1 << targetObject.layer) & TileManager.Instance.NPCLayerMask) != 0;
        Interactable interactable = targetObject.GetComponent<Interactable>();
            
        if (!isNPC)
        {
            EventController lightningEvent = Instantiate(mLightningStrikeEvent, cellCenter, Quaternion.identity).GetComponent<EventController>();
            lightningEvent.mEventInfo.event_location = interactable.CurrentLocation;
            lightningEvent.mEventInfo.event_description += $" {interactable.InteractableName} is broken! at {interactable.CurrentLocation}";
            lightningEvent.mEventInfo.importance = 4;
            // 1초 대기
            interactable.PlayEffect("break");
            Destroy(targetObject, 0.5f);
        }
        else
        {
            EventController lightningEvent = Instantiate(mLightningStrikeEventNPC, cellCenter, Quaternion.identity).GetComponent<EventController>();
            lightningEvent.mEventInfo.event_location = interactable.CurrentLocation;
            lightningEvent.mEventInfo.event_is_save = true;
            lightningEvent.mEventInfo.importance = 10;

            AgentController agentController = targetObject.GetComponent<AgentController>();
            //agentController.ModifyNeed(OhMAIGod.Agent.AgentNeedsType.Stress, 100);
            lightningEvent.mEventInfo.event_description = $" terrifying lightning strike over {agentController.AgentName}, maybe God is angry";
            
        }
    }
    public override void Active()
    {
        base.Active();
    }
    public override void Deactive()
    {
        base.Deactive();
    }
    
    
}
