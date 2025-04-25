using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

// 타겟의 서있는 지점을 관리하는 컨트롤러
public class TargetController : MonoBehaviour
{
    [SerializeField] private GameObject mStandingPointPrefab;    // 서있는 지점 프리팹
    [SerializeField] private float mCheckRadius = 0.4f;          // 주변 충돌 확인 반경 (타일 크기에 맞게 조정)
    [SerializeField] private LayerMask mWallLayer;              // 벽 레이어
    [SerializeField] private LayerMask mTargetLayer;            // 타겟 레이어
    [SerializeField] private Tilemap mGroundTilemap;           // 바닥 타일맵 참조
    [SerializeField] private bool mShowDebug = true;            // 디버그 정보 표시 여부

    private List<GameObject> mStandingPoints;                   // 생성된 서있는 지점들
    private List<Vector2> mAvailablePositions;                  // 사용 가능한 위치 목록
    private Collider2D mTargetCollider;                         // 타겟의 콜라이더
    private HashSet<Vector3Int> mOccupiedCells;                 // 타겟이 차지하는 셀 목록

    // 초기화
    private void Awake() // Start 대신 Awake 사용 고려 (Collider 참조 등)
    {
        mTargetCollider = GetComponent<Collider2D>();
        if (mTargetCollider == null)
        {
            Debug.LogError("TargetController에 Collider2D가 없습니다!", this);
            enabled = false;
            return;
        }

        if (mGroundTilemap == null)
        {
            Debug.LogError("GroundTilemap이 할당되지 않았습니다! 인스펙터에서 연결해주세요.", this);
            enabled = false;
            return;
        }
        mStandingPoints = new List<GameObject>();
        mAvailablePositions = new List<Vector2>();
        mOccupiedCells = new HashSet<Vector3Int>();
    }

    private void Start()
    {
        InitializeStandingPoints();
    }

    // 서있는 지점들 초기화
    private void InitializeStandingPoints()
    {
        if (mStandingPointPrefab == null)
        {
            Debug.LogError("StandingPointPrefab이 할당되지 않았습니다!", this);
            return;
        }

        ClearStandingPoints();
        FindOccupiedCells(); // 타겟이 차지하는 셀 먼저 찾기
        FindAvailableAdjacentCells(); // 차지하는 셀 주변의 사용 가능한 셀 찾기
        CreateStandingPoints();
    }

    // 기존 서있는 지점들 제거
    private void ClearStandingPoints()
    {
        foreach (Transform child in transform)
        {
            if (child.CompareTag("StandingPoint"))
            {
                Destroy(child.gameObject);
            }
        }
        mStandingPoints.Clear();
        mAvailablePositions.Clear();
        mOccupiedCells.Clear();
    }

    // 타겟이 차지하는 셀 찾기
    private void FindOccupiedCells()
    {
        Bounds bounds = mTargetCollider.bounds;
        Vector3Int minCell = mGroundTilemap.WorldToCell(bounds.min);
        Vector3Int maxCell = mGroundTilemap.WorldToCell(bounds.max);

        for (int x = minCell.x; x <= maxCell.x; x++)
        {
            for (int y = minCell.y; y <= maxCell.y; y++)
            {
                Vector3Int cellPos = new Vector3Int(x, y, 0);
                Vector2 cellCenter = mGroundTilemap.GetCellCenterWorld(cellPos);
                // 콜라이더가 실제로 해당 셀 중심을 포함하는지 확인 (더 정확한 방법)
                if (mTargetCollider.OverlapPoint(cellCenter) && mGroundTilemap.HasTile(cellPos))
                {
                    mOccupiedCells.Add(cellPos);
                }
            }
        }
        if (mShowDebug)
        {
            Debug.Log($"[{gameObject.name}] 차지하는 셀 {mOccupiedCells.Count}개 찾음.", this);
        }
    }

    // 차지하는 셀 주변의 사용 가능한 인접 셀 찾기
    private void FindAvailableAdjacentCells()
    {
        HashSet<Vector3Int> neighborCells = new HashSet<Vector3Int>();
        Vector3Int[] directions = { Vector3Int.up, Vector3Int.down, Vector3Int.left, Vector3Int.right };

        // 1. 모든 차지된 셀의 인접 셀들을 수집 (중복 제거)
        foreach (Vector3Int occupiedCell in mOccupiedCells)
        {
            foreach (Vector3Int dir in directions)
            {
                Vector3Int neighbor = occupiedCell + dir;
                // 차지된 셀이 아닌 경우에만 후보로 추가
                if (!mOccupiedCells.Contains(neighbor))
                {
                    neighborCells.Add(neighbor);
                }
            }
        }

        if (mShowDebug) { Debug.Log($"[{gameObject.name}] 인접 후보 셀 {neighborCells.Count}개 찾음."); }

        // 2. 인접 셀들의 유효성 검사
        foreach (Vector3Int cell in neighborCells)
        {
            if (mGroundTilemap.HasTile(cell))
            {
                Vector2 worldPos = mGroundTilemap.GetCellCenterWorld(cell);
                bool hasWall = Physics2D.OverlapCircle(worldPos, mCheckRadius, mWallLayer);
                Collider2D[] targets = Physics2D.OverlapCircleAll(worldPos, mCheckRadius, mTargetLayer);
                bool hasOtherTarget = false;
                foreach (var targetCollider in targets)
                {
                    // 자기 자신의 콜라이더가 아닌 다른 타겟 콜라이더가 있는지 확인
                    if (targetCollider != mTargetCollider)
                    {
                        hasOtherTarget = true;
                        break;
                    }
                }

                if (!hasWall && !hasOtherTarget)
                {
                    mAvailablePositions.Add(worldPos);
                }
                else if (mShowDebug)
                {
                    Debug.LogWarning($"[{gameObject.name}] 위치 {worldPos} (셀: {cell}) 사용 불가 - 벽: {hasWall}, 타겟: {hasOtherTarget}", this);
                }
            }
            else if (mShowDebug)
            {
                Debug.LogWarning($"[{gameObject.name}] 셀 {cell} 에 타일 없음", this);
            }
        }

        if (mShowDebug)
        {
            Debug.Log($"[{gameObject.name}] 최종 사용 가능 위치 {mAvailablePositions.Count}개 확정.", this);
        }
    }

    // 서있는 지점들 생성
    private void CreateStandingPoints()
    {
        foreach (Vector2 pos in mAvailablePositions)
        {
            GameObject standingPoint = Instantiate(mStandingPointPrefab, pos, Quaternion.identity, transform);
            standingPoint.tag = "StandingPoint";
            mStandingPoints.Add(standingPoint);
        }
    }

    // 서있는 지점들 업데이트
    public void UpdateStandingPoints()
    {
        if (mGroundTilemap == null || mTargetCollider == null) return;
        InitializeStandingPoints();
    }

    // 서있는 지점들의 위치 목록 반환
    public List<Vector2> GetStandingPositions()
    {
        return new List<Vector2>(mAvailablePositions);
    }

    // 디버그 정보 표시
    private void OnDrawGizmos()
    {
        if (!mShowDebug || mGroundTilemap == null || !Application.isPlaying) return; // Awake/Start 이후 실행 보장

        // 차지하는 셀 표시
        if (mOccupiedCells != null)
        {
            Gizmos.color = new Color(1f, 0.5f, 0f, 0.5f); // 주황색 반투명
            foreach (Vector3Int cell in mOccupiedCells)
            {
                Gizmos.DrawCube(mGroundTilemap.GetCellCenterWorld(cell), mGroundTilemap.cellSize * 0.9f);
            }
        }

        // 사용 가능한 최종 위치 표시
        if (mAvailablePositions != null)
        {
            Gizmos.color = Color.green;
            foreach (Vector2 pos in mAvailablePositions)
            {
                Gizmos.DrawWireSphere(pos, 0.25f); // 조금 더 잘 보이게
            }
        }

        // (옵션) 검사한 모든 인접 셀 표시
        // HashSet<Vector3Int> neighborCells = new HashSet<Vector3Int>();
        // if (mOccupiedCells != null)
        // {
        //     Vector3Int[] directions = { Vector3Int.up, Vector3Int.down, Vector3Int.left, Vector3Int.right };
        //     foreach (Vector3Int occupiedCell in mOccupiedCells)
        //     {
        //         foreach (Vector3Int dir in directions)
        //         {
        //             Vector3Int neighbor = occupiedCell + dir;
        //             if (!mOccupiedCells.Contains(neighbor))
        //             {
        //                 neighborCells.Add(neighbor);
        //             }
        //         }
        //     }
        //     Gizmos.color = Color.gray;
        //     foreach(var cell in neighborCells)
        //     {
        //         if (!mAvailablePositions.Contains(mGroundTilemap.GetCellCenterWorld(cell)))
        //             Gizmos.DrawWireCube(mGroundTilemap.GetCellCenterWorld(cell), mGroundTilemap.cellSize * 0.7f);
        //     }
        // }
    }
}
