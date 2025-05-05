using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

// NPC의 이동을 제어하는 컨트롤러
public class MovementController : MonoBehaviour
{
    [Header("Movement Settings")]
    [SerializeField] private float mMoveSpeed = 2f;                   // 이동 속도
    [SerializeField] private float mReachedDistance = 0.01f;          // 목표 지점 도달 판정 거리
    [SerializeField] private string mTargetLocationName;               // 현재 찾아갈 로케이션의 이름
    [SerializeField] private string mTargetName;                      // 찾아갈 목표물의 이름
    [SerializeField] private float mTargetSearchInterval = 2f;        // 목표물 탐색 간격
    [SerializeField] private bool mDrawPath = true;                   // 경로 그리기 여부
    [SerializeField] private int mDetectionTileCount = 1;             // 정면 감지 타일 수

    // 이동 관련 변수들
    private List<Node> mCurrentPath;                                  // 현재 경로
    private int mCurrentPathIndex;                                    // 현재 경로 인덱스
    private Vector2 mTargetPosition;                                  // 현재 목표 위치
    private bool mIsMoving;                                           // 이동 중 여부
    private Transform mCurrentTarget;                                 // 현재 목표물
    private Vector2 mCurrentPoint;                                   // 현재 목표 위치
    private float mLastTargetSearchTime;                             // 마지막 목표물 탐색 시간
    private SpriteRenderer mSpriteRenderer;                          // 스프라이트 렌더러
    private NPCLog mNPCLog;
    // 목적지 도착 이벤트
    public event System.Action OnDestinationReached;
    private bool mDestinationReachedEventFired = false;              // 이벤트 발생 여부 추적

    // 초기화
    private void Awake()
    {
        mLastTargetSearchTime = Time.time;
        mNPCLog = GameObject.Find("NPCLog").GetComponent<NPCLog>();
        mSpriteRenderer = GetComponent<SpriteRenderer>();
    }

    // 매 프레임 업데이트
    private void Update()
    {
        if (mCurrentPoint == null) return;
        // 일정 간격으로 목표물 탐색
        if (Time.time - mLastTargetSearchTime >= mTargetSearchInterval)
        {
            // 현재 목표물 저장
            Vector2 previousPoint = mCurrentPoint;
            FindTargetPosition();
            mLastTargetSearchTime = Time.time;

            // 목표 지점이 변경된 경우에만 경로 업데이트
            if (previousPoint != mCurrentPoint)
            {
                Debug.Log($"{gameObject.name}의 목표물이 변경되어 경로를 업데이트합니다. 이전: {previousPoint}, 현재: {mCurrentPoint}");
                UpdatePath();
            }
        }

        if (!mIsMoving) return;
        
        // 목표 위치에 장애물이 있으면 최종 목표 위치 변경
        if (IsObstacleInPoint())
        {
            Debug.Log($"{gameObject.name} 목표 위치에 장애물 감지, 최종 목표 위치 변경");
            FindTargetPosition();
        }

        // 정면 타일 감지 영역 내에 장애물 또는 NPC가 있으면 경로 재탐색
        if (IsObstacleInFrontTiles())
        {
            Debug.Log($"{gameObject.name} 정면 타일 감지 영역에 장애물 또는 NPC 감지, 경로 재탐색");
            UpdatePath();
        }

        MoveTowardTarget();
    }

    // 위치 이름으로 이동 시작
    public void MoveToLocation(string _targetName, string _targetLocationName, System.Action _onReached = null)
    {
        Debug.Log($"{gameObject.name}이(가) {_targetLocationName}로 이동 시작");
        mTargetName = _targetName;
        mTargetLocationName = _targetLocationName;
        mIsMoving = true;
        mDestinationReachedEventFired = false;  // 새로운 이동 시작 시 플래그 초기화
        FindTargetPosition();
    }

    // 지정된 위치로 이동
    // _targetPosition: 목표 위치
    // _onReached: 도착 시 콜백
    public void MoveToPosition(Vector2 _targetPosition, System.Action _onReached = null)
    {
        mTargetPosition = _targetPosition;
        mIsMoving = true;
        // PathFinder의 FindPath는 월드좌표(Vector2)만 받음
        mCurrentPath = PathFinder.Instance.FindPath(transform.position, _targetPosition, this.gameObject);
        if (mCurrentPath != null && mCurrentPath.Count > 0)
        {
            mCurrentPathIndex = 0;
            // 첫 번째 경로 노드의 타일 중심으로 이동
            mTargetPosition = TileManager.Instance.GroundTilemap.GetCellCenterWorld(new Vector3Int(mCurrentPath[0].x, mCurrentPath[0].y, 0));
            mIsMoving = true;
        }
        else
        {
            Debug.LogWarning($"{gameObject.name}이(가) {_targetPosition}까지의 경로를 찾을 수 없습니다.");
            mIsMoving = false;
            return;
        }
    }

    // 목표물을 찾고 이동을 시작하는 메서드
    private void FindTargetPosition()
    {
        if (string.IsNullOrEmpty(mTargetName)) return;
        
        // Location 참조
        TileController targetLocation = TileManager.Instance.GetTileController(mTargetLocationName);
        if (targetLocation == null)
        {
            Debug.LogWarning($"{gameObject.name}이(가) {mTargetLocationName} 위치를 찾을 수 없습니다.");
            mIsMoving = false;
            OnDestinationReached?.Invoke();
            return;
        }

        Transform closestTarget = null;
        float closestDistance = float.MaxValue;
        foreach (TargetController target in targetLocation.ChildInteractables)
        {
            if (target.name == mTargetName)
            {
                float distance = Vector2.Distance(transform.position, target.transform.position);
                if (distance < closestDistance)
                {
                    closestDistance = distance;
                    closestTarget = target.transform;
                }
            }
        }
        if (closestTarget != null)
        {
            if (mCurrentTarget == closestTarget) return;
            mCurrentTarget = closestTarget;
            TargetController targetController = mCurrentTarget.GetComponent<TargetController>();
            if (targetController != null)
            {
                List<Vector2> standingPoints = targetController.GetStandingPositions();
                if (standingPoints.Count > 0)
                {
                    Vector2 closestStandingPoint = standingPoints[0];
                    float minPathCost = float.MaxValue;
                    foreach (Vector2 point in standingPoints)
                    {
                        float pathCost = PathFinder.Instance.CalculatePathCost(transform.position, point, this.gameObject);
                        if (pathCost < minPathCost)
                        {
                            minPathCost = pathCost;
                            closestStandingPoint = point;
                        }
                    }
                    mCurrentPoint = closestStandingPoint;
                    MoveToPosition(mCurrentPoint);
                }
            }
        }
        else
        {
            Debug.LogWarning($"이름이 {mTargetName}인 목표물을 찾을 수 없습니다.");
            mIsMoving = false;
            OnDestinationReached?.Invoke();
        }
    }

    // 현재 경로를 업데이트하는 메서드
    private void UpdatePath()
    {
        if (mCurrentTarget == null) return;
        TargetController targetController = mCurrentTarget.GetComponent<TargetController>();
        if (targetController != null)
        {
            List<Vector2> standingPoints = targetController.GetStandingPositions();
            if (standingPoints.Count > 0)
            {
                Vector2 closestStandingPoint = standingPoints[0];
                float minPathCost = float.MaxValue;
                foreach (Vector2 point in standingPoints)
                {
                    float pathCost = PathFinder.Instance.CalculatePathCost(transform.position, point, this.gameObject);
                    if (pathCost < minPathCost)
                    {
                        minPathCost = pathCost;
                        closestStandingPoint = point;
                    }
                }
                MoveToPosition(closestStandingPoint);
            }
        }
    }

    // 현재 이동 중지
    public void StopMovement()
    {
        if (!mIsMoving) return;

        mIsMoving = false;

        Debug.Log($"{gameObject.name}의 이동이 중지됨");
    }

    // 이동을 재개
    public void ResumeMovement()
    {
        if (mIsMoving) return;

        mIsMoving = true;

        Debug.Log($"{gameObject.name}의 이동이 재개됨");
    }

    // 이동 중인지 여부 반환
    public bool IsMoving => mIsMoving;

    // 현재 목적지 이름 반환
    public string CurrentDestination => mCurrentTarget != null ? mCurrentTarget.name : string.Empty;

    // 현재 타겟 이름 반환
    public string TargetName => mTargetName;

    // 기본 이동 로직
    private void MoveTowardTarget()
    {
        if (mTargetPosition == null) return;
        // 현재 위치를 Vector2로 변환
        Vector2 currentPosition = new Vector2(transform.position.x, transform.position.y);

        // 목표 방향 계산
        Vector2 direction = (mTargetPosition - currentPosition).normalized;
        // 이동 (2D)
        Vector3 movement = new Vector3(direction.x, direction.y, 0) * mMoveSpeed * Time.deltaTime;
        transform.position += movement;
        // 이동방향이 왼쪽이면 x축 플립
        if (direction.x < 0)
        {
            mSpriteRenderer.flipX = true;
        }
        else
        {
            mSpriteRenderer.flipX = false;
        }
        // 도착 확인
        float distance = Vector2.Distance(currentPosition, mTargetPosition);
        if (distance <= mReachedDistance)
        {
            OnReachedDestination();
        }
    }

    // 목적지 도착 처리
    private void OnReachedDestination()
    {
        // 현재 경로의 다음 지점으로 이동
        if (mCurrentPath != null && mCurrentPathIndex < mCurrentPath.Count - 1)
        {
            mNPCLog.SetNPCLog($"{gameObject.name}이(가) 목적지({mCurrentTarget?.name})로 이동 중");
            Debug.Log($"{gameObject.name}이(가) 목적지({mCurrentTarget?.name})로 이동 중");
            mCurrentPathIndex++;
            mTargetPosition = TileManager.Instance.GroundTilemap.GetCellCenterWorld(new Vector3Int(mCurrentPath[mCurrentPathIndex].x, mCurrentPath[mCurrentPathIndex].y, 0));
            mIsMoving = true;
        }
        else
        {
            mIsMoving = false;
            transform.position = mTargetPosition;
            mNPCLog.SetNPCLog($"{gameObject.name}이(가) 목적지({mCurrentTarget?.name})에 도착함");
            Debug.Log($"{gameObject.name}이(가) 목적지({mCurrentTarget?.name})에 도착함");
            mCurrentTarget = null;
            mCurrentPath = null;
            mCurrentPathIndex = 0;
            mTargetPosition = Vector2.zero;
            if (!mDestinationReachedEventFired)
            {
                OnDestinationReached?.Invoke();
                mDestinationReachedEventFired = true;
            }
        }
    }

    // 정면 방향 기준 감지 함수
    private bool IsObstacleInFrontTiles()
    {
        // 이동 방향(혹은 바라보는 방향) 계산
        Vector2 direction = mTargetPosition - (Vector2)transform.position;
        if (direction.sqrMagnitude < 0.01f) return false; // 방향이 없으면 감지 안 함
        direction.Normalize();

        // 타일맵 참조
        Tilemap groundTilemap = TileManager.Instance.GroundTilemap;

        // 현재 위치의 셀 좌표
        Vector3Int currentCell = groundTilemap.WorldToCell(transform.position);

        for (int i = 1; i <= mDetectionTileCount; i++)
        {
            // 정면 방향으로 i칸 앞 셀 좌표 계산
            Vector3Int checkCell = currentCell + new Vector3Int(Mathf.RoundToInt(direction.x * i), Mathf.RoundToInt(direction.y * i), 0);
            Vector3 checkWorldPos = groundTilemap.GetCellCenterWorld(checkCell);

            // 해당 셀 중심에서 충돌체 감지
            Collider2D[] colliders = Physics2D.OverlapCircleAll(checkWorldPos, 0.4f, TileManager.Instance.ObstacleLayerMask);
            foreach (Collider2D collider in colliders)
            {
                if (collider.gameObject == mCurrentTarget?.gameObject)  // 목표물은 이벤트 발생하지 않음
                    continue;
                if (collider.gameObject == this.gameObject)  // 자기 자신은 이벤트 발생하지 않음
                    continue;
                // 감지된 오브젝트가 있으면 true 반환
                return true;
            }
        }
        return false;
    }

    private bool IsObstacleInPoint()
    {
        Vector3Int checkCell = TileManager.Instance.GroundTilemap.WorldToCell(mCurrentPoint);
        Vector2 checkWorldPos = TileManager.Instance.GroundTilemap.GetCellCenterWorld(checkCell);
        Collider2D[] colliders = Physics2D.OverlapCircleAll(checkWorldPos, 0.4f, TileManager.Instance.ObstacleLayerMask);
        foreach (Collider2D collider in colliders)
        {
            if (collider.gameObject == mCurrentTarget?.gameObject)  // 목표물은 이벤트 발생하지 않음
                continue;
            if (collider.gameObject == this.gameObject)  // 자기 자신은 이벤트 발생하지 않음
                continue;
            return true;
        }
        return false;
    }

    private void OnDrawGizmos()
    {
        // 현재 경로가 있는 경우에만 그리기
        if (mCurrentPath != null && mCurrentPath.Count > 0 && mDrawPath)
        {
            Gizmos.color = Color.red;

            // 시작점부터 끝점까지 선으로 연결
            for (int i = 0; i < mCurrentPath.Count - 1; i++)
            {
                Vector3 startPos = new Vector3(mCurrentPath[i].x + 0.5f, mCurrentPath[i].y + 0.5f, 0);
                Vector3 endPos = new Vector3(mCurrentPath[i + 1].x + 0.5f, mCurrentPath[i + 1].y + 0.5f, 0);
                Gizmos.DrawLine(startPos, endPos);
            }

            // 각 노드 위치에 구체 그리기
            Gizmos.color = Color.yellow;
            foreach (Node node in mCurrentPath)
            {
                Vector3 nodePos = new Vector3(node.x + 0.5f, node.y + 0.5f, 0);
                Gizmos.DrawSphere(nodePos, 0.2f);
            }

            // 현재 목표 위치 표시
            if (mTargetPosition != Vector2.zero)
            {
                Gizmos.color = Color.green;
                Gizmos.DrawSphere(new Vector3(mTargetPosition.x, mTargetPosition.y, 0), 0.3f);
            }
        }

        // --- 정면 타일 감지 영역 시각화 ---
        if (TileManager.Instance != null && TileManager.Instance.GroundTilemap != null)
        {
            Vector2 direction = mTargetPosition - (Vector2)transform.position;
            if (direction.sqrMagnitude >= 0.01f)
            {
                direction.Normalize();
                Vector3Int currentCell = TileManager.Instance.GroundTilemap.WorldToCell(transform.position);
                Gizmos.color = new Color(0, 0.5f, 1f, 0.3f); // 파란색(반투명)
                for (int i = 1; i <= mDetectionTileCount; i++)
                {
                    Vector3Int checkCell = currentCell + new Vector3Int(Mathf.RoundToInt(direction.x * i), Mathf.RoundToInt(direction.y * i), 0);
                    Vector3 checkWorldPos = TileManager.Instance.GroundTilemap.GetCellCenterWorld(checkCell);
                    Gizmos.DrawWireCube(checkWorldPos, Vector3.one * 0.9f); // 셀 크기만큼 네모로 표시
                }
            }
        }
    }
}