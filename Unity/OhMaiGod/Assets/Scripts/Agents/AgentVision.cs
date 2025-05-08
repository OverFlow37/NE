using UnityEngine;
using System.Collections.Generic;

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

        if (!IsInTargetLayer(other.gameObject.layer))
        {
            LogManager.Log("Vision", $"[AgentVision] Object {other.gameObject.name} is not in target layers", 3);
            return;
        }

        Interactable interactable = other.GetComponent<Interactable>();
        if (interactable != null)
        {
            AddVisibleInteractable(interactable);
        }
    }

    // 시야 범위에서 나갔을 때
    private void OnTriggerExit2D(Collider2D other)
    {
        if (!IsInTargetLayer(other.gameObject.layer)) return;

        Interactable interactable = other.GetComponent<Interactable>();
        if (interactable != null)
        {
            RemoveVisibleInteractable(interactable);
        }
    }

    // 레이어 마스크 체크
    private bool IsInTargetLayer(int layer)
    {
        bool isInObstacles = ((1 << layer) & mObstaclesLayer) != 0;
        bool isInNPC = ((1 << layer) & mNPCLayer) != 0;
        LogManager.Log("Vision", $"[AgentVision] Layer Check - Layer: {layer}, IsInObstacles: {isInObstacles}, IsInNPC: {isInNPC}", 3);
        return isInObstacles || isInNPC;
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
