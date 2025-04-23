using System.Collections.Generic;
using UnityEngine;

// 타겟의 서있는 지점을 관리하는 컨트롤러
public class TargetController : MonoBehaviour
{
    [SerializeField] private GameObject mStandingPointPrefab;    // 서있는 지점 프리팹
    [SerializeField] private float mCheckRadius = 0.5f;          // 주변 노드 확인 반경
    [SerializeField] private LayerMask mWallLayer;              // 벽 레이어
    [SerializeField] private LayerMask mTargetLayer;            // 타겟 레이어
    [SerializeField] private float mStandingPointOffset = 1f;   // 타겟으로부터의 최소 거리
    [SerializeField] private Vector2 mTableSize = new Vector2(2f, 2f);  // 테이블의 크기
    [SerializeField] private bool mShowDebug = true;            // 디버그 정보 표시 여부

    private float mMaxDistanceFromTarget;                       // 타겟으로부터 최대 거리
    private List<GameObject> mStandingPoints;                   // 생성된 서있는 지점들
    private List<Vector2Int> mAvailableNodes;                   // 사용 가능한 노드 목록
    private Collider2D mTargetCollider;                         // 타겟의 Collider

    // 초기화
    private void Start()
    {
        mTargetCollider = GetComponent<Collider2D>();
        mStandingPoints = new List<GameObject>();
        mAvailableNodes = new List<Vector2Int>();
        // 타겟의 크기를 고려하여 최대 거리 설정 (중심으로부터 모서리까지 거리)
        mMaxDistanceFromTarget = Mathf.Sqrt(mTableSize.x * mTableSize.x + mTableSize.y * mTableSize.y);
        InitializeStandingPoints();
    }

    // 서있는 지점들 초기화
    private void InitializeStandingPoints()
    {
        if (mStandingPointPrefab == null)
        {
            Debug.LogError("StandingPointPrefab이 할당되지 않았습니다!");
            return;
        }

        ClearStandingPoints();
        FindAvailableNodes();
        CreateStandingPoints();
    }

    // 기존 서있는 지점들 제거
    private void ClearStandingPoints()
    {
        foreach (GameObject point in mStandingPoints)
        {
            if (point != null)
            {
                Destroy(point);
            }
        }
        mStandingPoints.Clear();
        mAvailableNodes.Clear();
    }

    // 사용 가능한 노드 찾기
    private void FindAvailableNodes()
    {
        if (mTargetCollider == null)
        {
            Debug.LogError("TargetCollider가 없습니다!");
            return;
        }

        // 테이블의 크기를 고려하여 검색 범위 설정
        Vector2 tableHalfSize = mTableSize * 0.5f;
        Vector2Int minPos = new Vector2Int(
            Mathf.RoundToInt(transform.position.x - tableHalfSize.x - mStandingPointOffset),
            Mathf.RoundToInt(transform.position.y - tableHalfSize.y - mStandingPointOffset)
        );
        Vector2Int maxPos = new Vector2Int(
            Mathf.RoundToInt(transform.position.x + tableHalfSize.x + mStandingPointOffset),
            Mathf.RoundToInt(transform.position.y + tableHalfSize.y + mStandingPointOffset)
        );

        if (mShowDebug)
        {
            Debug.Log($"[{gameObject.name}] 검색 범위: Min({minPos.x}, {minPos.y}) ~ Max({maxPos.x}, {maxPos.y})");
        }

        // 타겟 주변의 모든 가능한 위치 확인
        for (int x = minPos.x; x <= maxPos.x; x++)
        {
            for (int y = minPos.y; y <= maxPos.y; y++)
            {
                Vector2 checkPos = new Vector2(x + 0.5f, y + 0.5f);
                
                // 테이블 영역 내부인지 확인
                bool isInsideTable = Mathf.Abs(checkPos.x - transform.position.x) < tableHalfSize.x &&
                                   Mathf.Abs(checkPos.y - transform.position.y) < tableHalfSize.y;
                
                // 타겟으로부터의 거리 확인
                float distanceFromTarget = Vector2.Distance(checkPos, transform.position);
                bool isWithinMaxDistance = distanceFromTarget <= mMaxDistanceFromTarget;
                
                if (!isInsideTable && isWithinMaxDistance)
                {
                    // 벽이나 다른 타겟이 없는지 확인
                    bool hasWall = Physics2D.OverlapCircle(checkPos, mCheckRadius, mWallLayer);
                    bool hasTarget = Physics2D.OverlapCircle(checkPos, mCheckRadius, mTargetLayer);

                    // 테이블과의 직선 경로에 벽이 있는지 확인
                    bool hasWallInPath = false;
                    Vector2 direction = (checkPos - (Vector2)transform.position).normalized;
                    float distance = Vector2.Distance(checkPos, transform.position);
                    RaycastHit2D hit = Physics2D.Raycast(transform.position, direction, distance, mWallLayer);
                    if (hit.collider != null)
                    {
                        hasWallInPath = true;
                    }

                    if (!hasWall && !hasTarget && !hasWallInPath)
                    {
                        mAvailableNodes.Add(new Vector2Int(x, y));
                        if (mShowDebug)
                        {
                            Debug.Log($"사용 가능한 노드 추가: ({x}, {y}), 거리: {distanceFromTarget:F2}");
                        }
                    }
                }
            }
        }

        if (mShowDebug)
        {
            Debug.Log($"총 {mAvailableNodes.Count}개의 사용 가능한 노드를 찾았습니다.");
        }
    }

    // 서있는 지점들 생성
    private void CreateStandingPoints()
    {
        foreach (Vector2Int node in mAvailableNodes)
        {
            Vector3 spawnPos = new Vector3(node.x + 0.5f, node.y + 0.5f, 0);
            GameObject standingPoint = Instantiate(mStandingPointPrefab, spawnPos, Quaternion.identity, transform);
            mStandingPoints.Add(standingPoint);
        }
    }

    // 서있는 지점들 업데이트
    public void UpdateStandingPoints()
    {
        InitializeStandingPoints();
    }

    // 서있는 지점들의 위치 목록 반환
    public List<Vector2> GetStandingPositions()
    {
        List<Vector2> positions = new List<Vector2>();
        if (mStandingPoints != null)
        {
            foreach (GameObject point in mStandingPoints)
            {
                if (point != null)
                {
                    positions.Add(point.transform.position);
                }
            }
        }
        return positions;
    }

    // 디버그 정보 표시
    private void OnDrawGizmos()
    {
        if (!mShowDebug) return;

        // 최대 거리 범위 표시
        Gizmos.color = new Color(1f, 1f, 0f, 0.2f);
        Gizmos.DrawWireSphere(transform.position, mMaxDistanceFromTarget);

        // 사용 가능한 노드 표시
        if (mAvailableNodes != null)
        {
            Gizmos.color = Color.green;
            foreach (Vector2Int node in mAvailableNodes)
            {
                Vector2 pos = new Vector2(node.x + 0.5f, node.y + 0.5f);
                Gizmos.DrawWireSphere(pos, 0.2f);
            }
        }

        // 서있는 지점 표시
        if (mStandingPoints != null)
        {
            Gizmos.color = Color.blue;
            foreach (GameObject point in mStandingPoints)
            {
                if (point != null)
                {
                    Gizmos.DrawWireSphere(point.transform.position, 0.3f);
                }
            }
        }

        // 테이블 범위 표시
        Gizmos.color = Color.yellow;
        Vector2 tableHalfSize = mTableSize * 0.5f;
        Vector3 center = transform.position;
        Gizmos.DrawWireCube(center, new Vector3(mTableSize.x, mTableSize.y, 0));

        // 테이블에서 각 노드까지의 경로 표시
        if (mAvailableNodes != null)
        {
            Gizmos.color = Color.cyan;
            foreach (Vector2Int node in mAvailableNodes)
            {
                Vector2 pos = new Vector2(node.x + 0.5f, node.y + 0.5f);
                Gizmos.DrawLine(transform.position, pos);
            }
        }
    }
}
