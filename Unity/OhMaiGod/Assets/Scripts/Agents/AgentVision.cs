using UnityEngine;
using System.Collections.Generic;
using OhMAIGod.Perceive;

// 에이전트 시야 관리
// 에이전트 현재 보이는 오브젝트 관리
// 에이전트 이벤트 확인, 반응 서버에 전송
[RequireComponent(typeof(CircleCollider2D))]
public class AgentVision : MonoBehaviour
{
    [Header("Vision Settings")]
    [SerializeField] private float mVisionRange = 5f;        // 시야 범위
    [SerializeField] private string mAgentName;              // 에이전트 이름 (자신을 제외하기 위한 식별자)

    [Header("Target Layers")]
    [SerializeField] private LayerMask mObstaclesLayer;      // Obstacles 레이어
    [SerializeField] private LayerMask mNPCLayer;            // NPC 레이어

    [Header("Gizmo Settings")]
    [SerializeField] private Color mGizmoColor = new Color(0.2f, 0.8f, 1f, 0.2f);  // Gizmo 색상 (하늘색 반투명)
    [SerializeField] private bool mShowGizmo = true;         // Gizmo 표시 여부

    [Header("Debug View")]
    [SerializeField] private bool mShowVisibleObjects = true;    // 보이는 오브젝트 목록 표시 여부
    [SerializeField] private List<Interactable> mDebugVisibleList = new List<Interactable>();  // Inspector에서 보여질 목록

    private CircleCollider2D mVisionCollider;                // 시야 범위 콜라이더
    private HashSet<Interactable> mVisibleInteractables;     // 현재 보이는 Interactable 목록

    [SerializeField] private AgentController mAgentController;
    private AIBridge_Perceive mAIBridgePerceive;

    // 시야 범위에 변화가 있을 때 발생하는 이벤트
    public delegate void VisionChangeHandler(Interactable interactable, bool entered);
    public event VisionChangeHandler OnVisionChanged;

    private void Awake()
    {
        mVisibleInteractables = new HashSet<Interactable>();
        mVisionCollider = GetComponent<CircleCollider2D>();
        
        // 콜라이더 설정
        mVisionCollider.isTrigger = true;
        // Obstacles와 NPC 레이어 모두 감지하도록 설정
        LayerMask combinedMask = mObstaclesLayer | mNPCLayer;
        mVisionCollider.includeLayers = combinedMask;
        LogManager.Log("Vision", $"[AgentVision] Combined Layer Mask: {combinedMask.value}", 2);
        LogManager.Log("Vision", $"[AgentVision] Obstacles Layer: {mObstaclesLayer.value}, NPC Layer: {mNPCLayer.value}", 2);
        
        UpdateVisionRange(mVisionRange);
    }

    private void Start()
    {
        mAIBridgePerceive = GameObject.Find("AIBridge").GetComponent<AIBridge_Perceive>();
        // 초기 시야 범위 내의 오브젝트 검사
        CheckInitialVisionRange();
    }

    // 시야 범위 업데이트
    public void UpdateVisionRange(float newRange)
    {
        mVisionRange = newRange;
        mVisionCollider.radius = mVisionRange;
    }

    // 초기 시야 범위 내의 오브젝트 검사
    private void CheckInitialVisionRange()
    {
        // Obstacles와 NPC 레이어의 콜라이더 모두 검사
        LayerMask combinedMask = mObstaclesLayer | mNPCLayer;
        Collider2D[] colliders = Physics2D.OverlapCircleAll(transform.position, mVisionRange, combinedMask);
        
        LogManager.Log("Vision", $"[AgentVision] Initial Check - Found {colliders.Length} colliders in range", 2);
        foreach (Collider2D collider in colliders)
        {
            if (collider.gameObject.name.Contains(mAgentName))
            {
                LogManager.Log("Vision", $"[AgentVision] Skipping self: {collider.gameObject.name}", 3);
                continue;
            }

            LogManager.Log("Vision", $"[AgentVision] Found object: {collider.gameObject.name} on layer: {LayerMask.LayerToName(collider.gameObject.layer)}", 2);
            Interactable interactable = collider.GetComponent<Interactable>();
            if (interactable != null)
            {
                AddVisibleInteractable(interactable);
            }
        }
    }

    // 시야 범위에 들어왔을 때
    private void OnTriggerEnter2D(Collider2D other)
    {
        LogManager.Log("Vision", $"[AgentVision] OnTriggerEnter2D - Object: {other.gameObject.name}, Layer: {LayerMask.LayerToName(other.gameObject.layer)}", 2);
        
        // 자신은 무시
        if (other.gameObject.name.Contains(mAgentName))
        {
            LogManager.Log("Vision", $"[AgentVision] Skipping self: {other.gameObject.name}", 3);
            return;
        }
        // 레이어 체크
        // 오브젝트 감지
        if (other.gameObject.layer == LayerMask.NameToLayer("Obstacles") || other.gameObject.layer == LayerMask.NameToLayer("NPC"))
        {
            Interactable interactable = other.GetComponent<Interactable>();
            if (interactable != null)
            {
                AddVisibleInteractable(interactable);
                // 흥미도 계산
                float threshold = 100.0f;
                float interestBase = interactable.mInteractableData.mInterest; // 오브젝트별 베이스 흥미도
                float totalInterest = interestBase;
                const float BROKEN_REPO = 20.0f; //베이스 흥미도가 20 이상이면 BROKEN이 추가 흥미도 발생
                bool isFirst = true;
                // 처음 보는 물체인지 체크
                // 반응이 이미 이루어진 물체인지 체크
                // 현재 오브젝트의 상태 체크
                switch (interactable.mInteractableData.mState)
                {
                    case InteractableData.States.Broken:
                        totalInterest += (interestBase - BROKEN_REPO) * 2.0f;
                        break;
                    case InteractableData.States.Installed:
                        // 설치된 물체이면서 처음 보는 오브젝트가 아닐 때
                        if (!isFirst)
                            totalInterest *= 0.5f;
                        break;
                    case InteractableData.States.Burn:
                        totalInterest += 50.0f + interestBase * 0.5f;
                        break;
                    case InteractableData.States.Rotten:
                        totalInterest += (interestBase - BROKEN_REPO) * 2.0f;
                        break;
                }
                // 랜덤 가중치 적용 (0.5f ~ 2.0f)
                float randomWeight = UnityEngine.Random.Range(0.5f, 2.0f);
                totalInterest *= randomWeight;
                // 에이전트의 선호 오브젝트, 비선호 오브젝트 체크
                // TODO: 반응과 관찰에 대한 임계치 분리, 호출 함수 분리
                if (totalInterest >= threshold){
                    // 이벤트 전송
                    PerceiveEvent perceiveEvent = new PerceiveEvent();
                    perceiveEvent.event_type = PerceiveEventType.INTERACTABLE_DISCOVER;
                    perceiveEvent.event_location = interactable.CurrentLocation;
                    // TODO: 오브젝트 이름이 아니라 이벤트 설명을 만든 뒤 설명을 전송해야함
                    perceiveEvent.event_description = interactable.mInteractableData.mName;
                    mAIBridgePerceive.SendPerceiveEvent(mAgentController, perceiveEvent);
                }
            }
        }
        // 이벤트 감지
        // TODO: 이벤트 레이어 감지가 우선?
        else if (other.gameObject.layer == LayerMask.NameToLayer("Event"))
        {
            EventController eventController = other.GetComponent<EventController>();
            if (eventController != null)
            {
                LogManager.Log("Vision", $"이벤트 감지: {eventController.mEventInfo.event_type}, {eventController.mEventInfo.event_location}, {eventController.mEventInfo.event_description}", 3);
                //PerceiveManager.Instance.SendEventToAIServer(eventController.mEventInfo.eventType, eventController.mEventInfo.eventLocation, eventController.mEventInfo.eventDescription);
                PerceiveEvent perceiveEvent = new PerceiveEvent();
                perceiveEvent.event_type = eventController.mEventInfo.event_type;
                // TODO: 이벤트 위치가 오브젝트 위치가 아니라 이벤트 위치를 전송해야함
                perceiveEvent.event_location = " ";
                perceiveEvent.event_description = eventController.mEventInfo.event_description;
                mAIBridgePerceive.SendReactJudgeEvent(mAgentController, perceiveEvent);
            }
        }
    }

    // 시야 범위에서 나갔을 때
    private void OnTriggerExit2D(Collider2D other)
    {
        if (other.gameObject.layer == LayerMask.NameToLayer("Obstacles") || other.gameObject.layer == LayerMask.NameToLayer("NPC"))
        {
            Interactable interactable = other.GetComponent<Interactable>();
            if (interactable != null)
            {
                RemoveVisibleInteractable(interactable);
            }
        }
    }


    // Interactable 추가
    private void AddVisibleInteractable(Interactable interactable)
    {
        if (mVisibleInteractables.Add(interactable))
        {
            LogManager.Log("Vision", $"[AgentVision] {interactable.name} 시야 범위 진입", 3);
            UpdateDebugList();
            OnVisionChanged?.Invoke(interactable, true);
        }
    }

    // Interactable 제거
    private void RemoveVisibleInteractable(Interactable interactable)
    {
        if (mVisibleInteractables.Remove(interactable))
        {
            LogManager.Log("Vision", $"[AgentVision] {interactable.name} 시야 범위 이탈", 3);
            UpdateDebugList();
            OnVisionChanged?.Invoke(interactable, false);
        }
    }

    // 디버그 목록 업데이트
    private void UpdateDebugList()
    {
        if (!mShowVisibleObjects) return;

        mDebugVisibleList.Clear();
        if (mVisibleInteractables == null) return;
        foreach (var interactable in mVisibleInteractables)
        {
            mDebugVisibleList.Add(interactable);
        }
    }

    // 현재 보이는 모든 Interactable 가져오기
    public IReadOnlyCollection<Interactable> GetVisibleInteractables()
    {
        return mVisibleInteractables;
    }

    // 특정 Interactable이 시야 범위 내에 있는지 확인
    public bool IsInteractableVisible(Interactable interactable)
    {
        return mVisibleInteractables.Contains(interactable);
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    private void OnDrawGizmos()
    {
        if (!mShowGizmo) return;

        // 기존 Gizmo 색상 저장
        Color prevColor = Gizmos.color;

        // 시야 범위 표시
        Gizmos.color = mGizmoColor;
        Gizmos.DrawSphere(transform.position, mVisionRange);

        // Gizmo 색상 복원
        Gizmos.color = prevColor;
    }

    // 에디터에서만 보이는 시야 범위 (선택되지 않았을 때도 표시)
    private void OnDrawGizmosSelected()
    {
        if (!mShowGizmo) return;

        // 기존 Gizmo 색상 저장
        Color prevColor = Gizmos.color;

        // 시야 범위 외곽선 표시
        Gizmos.color = new Color(mGizmoColor.r, mGizmoColor.g, mGizmoColor.b, 1f);
        Gizmos.DrawWireSphere(transform.position, mVisionRange);

        // Gizmo 색상 복원
        Gizmos.color = prevColor;
    }

    private void OnValidate()
    {
        // AgentName이 비어있으면 게임오브젝트 이름으로 설정
        if (string.IsNullOrEmpty(mAgentName))
        {
            mAgentName = gameObject.name;
        }

        // Inspector에서 값이 변경될 때마다 디버그 목록 업데이트
        if (Application.isPlaying && mShowVisibleObjects)
        {
            UpdateDebugList();
        }

        // 레이어 설정이 변경되었을 때 로그
        if (Application.isPlaying)
        {
            if (LogManager.Instance != null)
            {
                LogManager.Log("Vision", $"[AgentVision] Layer Settings - Obstacles: {mObstaclesLayer.value}, NPC: {mNPCLayer.value}", 2);
            }
        }
    }
}
