using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

[ExecuteInEditMode]
public class TileController : MonoBehaviour
{
    [SerializeField] public string mLocationName = "";
    [SerializeField] public string mDescription = "";
    
    private List<Interactable> mChildInteractables;
    private bool mIsInitialized = false;
    private Tilemap mTilemap;

    private void Awake()
    {
        mTilemap = GetComponent<Tilemap>();
        mChildInteractables = new List<Interactable>();
    }

    private void Start()
    {
        // TileManager에 자신을 등록
        if (TileManager.Instance != null && !mIsInitialized)
        {
            TileManager.Instance.AddLocationTilemap(this);
            mIsInitialized = true;
        }
    }

    public Tilemap Tilemap { get { return mTilemap; } }
    public string LocationName { get { return mLocationName; } }
    public List<Interactable> ChildInteractables { get { return mChildInteractables; } }

    public void AddChildInteractable(Interactable interactable)
    {
        if (!mChildInteractables.Contains(interactable))
        {
            mChildInteractables.Add(interactable);
        }
    }

    public bool RemoveChildInteractable(Interactable interactable)
    {
        if (mChildInteractables.Contains(interactable))
        {
            mChildInteractables.Remove(interactable);
            return true;
        }
        return false;
    }

    public void RemoveAllChildInteractables()
    {
        mChildInteractables.Clear();
    }

    public Vector2 AvailablePosition
    {
        get
        {
            // 중심 셀 좌표 계산
            Vector3Int centerCell = new Vector3Int(
                Mathf.RoundToInt(mTilemap.cellBounds.center.x),
                Mathf.RoundToInt(mTilemap.cellBounds.center.y),
                0);

            // BFS 탐색을 위한 큐와 방문 집합
            Queue<Vector3Int> queue = new Queue<Vector3Int>();
            HashSet<Vector3Int> visited = new HashSet<Vector3Int>();

            queue.Enqueue(centerCell);
            visited.Add(centerCell);

            // 8방향 이동 벡터
            Vector3Int[] directions = new Vector3Int[]
            {
                Vector3Int.up, Vector3Int.down, Vector3Int.left, Vector3Int.right,
                Vector3Int.up + Vector3Int.left, Vector3Int.up + Vector3Int.right,
                Vector3Int.down + Vector3Int.left, Vector3Int.down + Vector3Int.right
            };

            BoundsInt bounds = mTilemap.cellBounds;

            while (queue.Count > 0)
            {
                Vector3Int cell = queue.Dequeue();

                // 셀 범위 내, 타일 존재, 장애물 없음이면 반환
                if (bounds.Contains(cell) && mTilemap.HasTile(cell))
                {
                    bool hasObstacle = Physics2D.OverlapCircle(
                        mTilemap.GetCellCenterWorld(cell), 0.2f, TileManager.Instance.ObstacleLayerMask);
                    if (!hasObstacle)
                    {
                        return mTilemap.GetCellCenterWorld(cell);
                    }
                }

                // 8방향 인접 셀 탐색
                foreach (var dir in directions)
                {
                    Vector3Int next = cell + dir;
                    if (!visited.Contains(next) && bounds.Contains(next))
                    {
                        queue.Enqueue(next);
                        visited.Add(next);
                    }
                }
            }

            // 이동 가능한 셀이 없으면 Vector2.zero 반환
            return Vector2.zero;
        }
    }

    // 위치 이름 기반으로 고유한 색상 생성
    private Color GetLocationColor()
    {
        if (string.IsNullOrEmpty(mLocationName)) return Color.white;
        
        // 위치 이름의 해시코드를 사용하여 색상 생성
        int hash = mLocationName.GetHashCode();
        float hue = (hash % 360) / 360f;  // 0-1 사이의 색조값
        return Color.HSVToRGB(hue, 0.7f, 0.7f);
    }

    // 환경 구조 시각화
    private void OnDrawGizmos()
    {
        if (mTilemap == null) return;

        // 구역별 고유 색상 가져오기
        Color locationColor = GetLocationColor();
        
        // 타일이 있는 셀들의 중심점 계산
        Vector3 centerPoint = Vector3.zero;
        int tileCount = 0;
        
        // 구역 범위 표시
        BoundsInt bounds = mTilemap.cellBounds;
        for (int x = bounds.min.x; x < bounds.max.x; x++)
        {
            for (int y = bounds.min.y; y < bounds.max.y; y++)
            {
                Vector3Int tilePosition = new Vector3Int(x, y, 0);
                if (mTilemap.HasTile(tilePosition))
                {
                    // 타일이 있는 위치에만 Gizmo 표시
                    Vector3 worldPos = mTilemap.GetCellCenterWorld(tilePosition);
                    Gizmos.color = new Color(locationColor.r, locationColor.g, locationColor.b, 0.2f);
                    Gizmos.DrawCube(worldPos, mTilemap.cellSize);
                    
                    // 중심점 계산을 위해 위치 누적
                    centerPoint += worldPos;
                    tileCount++;
                }
            }
        }

        // 실제 타일이 있는 영역의 중심점 계산
        if (tileCount > 0)
        {
            centerPoint /= tileCount;
        }

        // 관리 중인 Interactable들 연결선 표시
        if (mChildInteractables != null)
        {
            foreach (var interactable in mChildInteractables)
            {
                if (interactable != null)
                {
                    // 타일 영역의 중심점에서 인터랙터블로 선 그리기
                    Gizmos.color = locationColor;
                    Gizmos.DrawLine(centerPoint, interactable.transform.position);
                    
                    // 인터랙터블 위치에 구체 표시
                    Gizmos.color = new Color(locationColor.r, locationColor.g, locationColor.b, 0.7f);
                    Gizmos.DrawWireSphere(interactable.transform.position, 0.3f);
                }
            }
        }

        // 구역 이름 표시 (중심점 위치에)
        #if UNITY_EDITOR
            UnityEditor.Handles.Label(centerPoint, $"{mLocationName}");
        #endif
    }
}
