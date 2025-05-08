using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

// NPC의 이동을 제어하는 컨트롤러
public class MovementController : MonoBehaviour
{
    [Header("Movement Settings")]
    [SerializeField] private float mMoveSpeed = 2f;                   // 이동 속도
    [SerializeField] private float mReachedDistance = 0.01f;          // 목표 지점 도달 판정 거리
    [SerializeField] private int mDetectionTileCount = 1;             // 정면 감지 타일 수

    [Header("Debug")]
    [SerializeField] private bool mDrawPath = true;                   // 경로 그리기 여부

    // 이동 관련 변수들
    private List<Node> mCurrentPath;                                  // 현재 경로
    private int mCurrentPathIndex;                                    // 현재 경로 인덱스
    private Vector2 mCurrentPoint;                                   // 현재 목표 위치
    private Vector2 mTargetPosition;                                  // 최종 목표 위치
    private TargetController mTargetController;                       // 목표 타겟 컨트롤러
    private bool mIsMoving;                                           // 이동 중 여부

    private SpriteRenderer mSpriteRenderer;                          // 스프라이트 렌더러
    private NPCLog mNPCLog;

    // 목적지 도착 이벤트
    public event System.Action OnDestinationReached;
    private bool mDestinationReachedEventFired = false;              // 이벤트 발생 여부 추적

    // 초기화
    private void Awake()
    {
        mNPCLog = GameObject.Find("NPCLog").GetComponent<NPCLog>();
        mSpriteRenderer = GetComponent<SpriteRenderer>();
    }

    // 매 프레임 업데이트
    private void Update()
    {
        if (mCurrentPoint == null || !mIsMoving) return;

        if (mTargetController != null && IsObstacleInPosition(mTargetPosition))
        {
            MoveToTarget(mTargetController);
        }

        if (IsObstacleInFrontTiles())
        {
            // 정면 장애물 감지 시 경로 재탐색
            UpdatePath();
        }
        
        MoveTowardTarget();
    }

    public void MoveToTarget(TargetController _targetController)
    {
        mTargetController = _targetController;
        List<Vector2> availablePositions = _targetController.StandingPoints;
        // 가장 비용이 적은 후보지로 이동
        if (availablePositions.Count > 0)
        {
            Vector2 nearestPosition = availablePositions[0];
            float minDistance = Vector2.Distance(transform.position, nearestPosition);
            foreach (Vector2 pos in availablePositions)
            {
                float distance = Vector2.Distance(transform.position, pos);
                if (distance < minDistance)
                {
                nearestPosition = pos;
                minDistance = distance;
                }
            }
            MoveToPosition(nearestPosition);
        }
        else
        {
            // TODO: 이동 불가능 이벤트 발생
            Debug.LogWarning($"{gameObject.name}이(가) 목표 타겟의 유효한 위치가 없습니다.");
        }
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
            mCurrentPoint = TileManager.Instance.GroundTilemap.GetCellCenterWorld(
                new Vector3Int(mCurrentPath[mCurrentPathIndex].x, mCurrentPath[mCurrentPathIndex].y, 0));
            mIsMoving = true;
        }
        else
        {
            LogManager.Log("Movement", $"{gameObject.name}이(가) {_targetPosition}까지의 경로를 찾을 수 없습니다.", 1);
            mIsMoving = false;
            return;
        }
    }

    private void UpdatePath()
    {
        mCurrentPath = PathFinder.Instance.FindPath(transform.position, mTargetPosition, this.gameObject);
    }

    // 현재 이동 중지
    public void StopMovement()
    {
        if (!mIsMoving) return;

        mIsMoving = false;

        LogManager.Log("Movement", $"{gameObject.name}의 이동이 중지됨", 2);
    }

    // 이동을 재개
    public void ResumeMovement()
    {
        if (mIsMoving) return;

        mIsMoving = true;

        LogManager.Log("Movement", $"{gameObject.name}의 이동이 재개됨", 2);
    }

    // 이동 중인지 여부 반환
    public bool IsMoving => mIsMoving;

    // 기본 이동 로직
    private void MoveTowardTarget()
    {
        if (mTargetPosition == null) return;
        // 현재 위치를 Vector2로 변환
        Vector2 currentPosition = new Vector2(transform.position.x, transform.position.y);

        // 목표 방향 계산
        Vector2 direction = (mCurrentPoint - currentPosition).normalized;
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
        float distance = Vector2.Distance(currentPosition, mCurrentPoint);
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
            mNPCLog.SetNPCLog($"{gameObject.name}이(가) 이동 중");
            mCurrentPathIndex++;
            mCurrentPoint = TileManager.Instance.GroundTilemap.GetCellCenterWorld(new Vector3Int(mCurrentPath[mCurrentPathIndex].x, mCurrentPath[mCurrentPathIndex].y, 0));
            mIsMoving = true;
        }
        else
        {
            mIsMoving = false;
            transform.position = mTargetPosition;
            mNPCLog.SetNPCLog($"{gameObject.name}이(가) 목적지에 도착함");
            Debug.Log($"{gameObject.name}이(가) 목적지({mCurrentPoint})에 도착함");
            mCurrentPath = null;
            mCurrentPathIndex = 0;
            mCurrentPoint = Vector2.zero;
            mTargetPosition = Vector2.zero;
            mTargetController = null;
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
                if (collider.gameObject == this.gameObject)  // 자기 자신은 이벤트 발생하지 않음
                    continue;
                if (mTargetController != null && collider.gameObject == mTargetController.gameObject)  // 목표 타겟은 이벤트 발생하지 않음
                    continue;
                // 감지된 오브젝트가 있으면 true 반환
                return true;
            }
        }
        return false;
    }

    private bool IsObstacleInPosition(Vector2 _position)
    {
        // 해당 위치의 셀 좌표
        Vector3Int cell = TileManager.Instance.GroundTilemap.WorldToCell(_position);
        Vector3 checkWorldPos = TileManager.Instance.GroundTilemap.GetCellCenterWorld(cell);

        // 해당 셀 중심에서 충돌체 감지
        Collider2D[] colliders = Physics2D.OverlapCircleAll(checkWorldPos, 0.4f, TileManager.Instance.ObstacleLayerMask);
        foreach (Collider2D collider in colliders)
        {
            if (collider.gameObject == this.gameObject)  // 자기 자신은 이벤트 발생하지 않음
                continue;
            if (collider.gameObject == mTargetController.gameObject)  // 목표 타겟은 이벤트 발생하지 않음
                continue;
            // 감지된 오브젝트가 있으면 true 반환
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