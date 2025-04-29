using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

/// <summary>
/// A* 알고리즘을 사용하여 경로를 찾는 싱글톤 클래스
/// </summary>
public class PathFinder : MonoBehaviour
{
    [SerializeField] private bool mShowDebug = true;
    [SerializeField] private Tilemap mGroundTilemap; // 바닥 타일맵 참조 [추후에 MapController 등에서 참조, 지금은 인스펙터에서 지정]
    private static PathFinder mInstance;
    // 싱글톤 인스턴스를 반환하는 프로퍼티
    public static PathFinder Instance
    {
        get
        {
            if (mInstance == null)
            {
                mInstance = FindAnyObjectByType<PathFinder>();
                if (mInstance == null)
                {
                    GameObject go = new GameObject("PathFinder");
                    mInstance = go.AddComponent<PathFinder>();
                }
            }
            return mInstance;
        }
    }

    private int mSizeX, mSizeY;                              // 맵 크기
    private Node[,] mNodeArray;                              // 노드 배열
    private NodePriorityQueue mOpenList; // 열린 목록(우선순위 큐)
    private List<Node> mClosedList;                          // 닫힌 목록
    private Vector3Int mMapMinCell;                          // 타일맵 최소 셀
    private Vector3Int mMapMaxCell;                          // 타일맵 최대 셀

    private void Awake()
    {
        if (mInstance != null && mInstance != this)
        {
            Destroy(gameObject);
            return;
        }
        mInstance = this;
        DontDestroyOnLoad(gameObject);
        // 타일맵 범위 계산
        if (mGroundTilemap != null)
        {
            mMapMinCell = mGroundTilemap.cellBounds.min;
            mMapMaxCell = mGroundTilemap.cellBounds.max - Vector3Int.one; // max는 exclusive
        }
        else
        {
            Debug.LogError("PathFinder에 타일맵이 할당되지 않았습니다!", this);
        }
    }

    /// <summary>
    /// 시작점에서 목표점까지의 경로를 찾는 메서드 (타일맵 기준)
    /// </summary>
    /// <param name="_startPos">시작 위치(월드좌표)</param>
    /// <param name="_targetPos">목표 위치(월드좌표)</param>
    /// <returns>찾은 경로의 노드 리스트</returns>
    public List<Node> FindPath(Vector2 _startPos, Vector2 _targetPos)
    {
        if (mGroundTilemap == null)
        {
            Debug.LogError("PathFinder에 타일맵이 할당되지 않았습니다!", this);
            return null;
        }
        // 월드좌표를 셀좌표로 변환
        Vector3Int startCell = mGroundTilemap.WorldToCell(_startPos);
        Vector3Int targetCell = mGroundTilemap.WorldToCell(_targetPos);
        // 맵 범위 체크
        if (!IsPositionInMap(startCell) || !IsPositionInMap(targetCell))
        {
            Debug.LogError($"시작점({startCell}) 또는 목표점({targetCell})이 맵 범위를 벗어났습니다. 맵: {mMapMinCell} ~ {mMapMaxCell}");
            return null;
        }
        InitializeNodeArray();
        Node startNode = mNodeArray[startCell.x - mMapMinCell.x, startCell.y - mMapMinCell.y];
        Node targetNode = mNodeArray[targetCell.x - mMapMinCell.x, targetCell.y - mMapMinCell.y];

        // 시작점이나 목표점이 벽인지 확인
        if (startNode.isWall)
        {
            Debug.LogError($"시작점이 벽입니다. 위치: {startCell}");
            return null;
        }
        if (targetNode.isWall)
        {
            Debug.LogError($"목표점이 벽입니다. 위치: {targetCell}");
            return null;
        }

        mOpenList = new NodePriorityQueue();
        mOpenList.Enqueue(startNode);
        mClosedList = new List<Node>();
        List<Node> finalPath = new List<Node>();

        while (mOpenList.Count > 0)
        {
            Node currentNode = mOpenList.Dequeue(); // F값이 가장 낮은 노드 pop
            mClosedList.Add(currentNode);

            if (currentNode == targetNode)
            {
                finalPath = ReconstructPath(targetNode, startNode);
                finalPath = SmoothPath(finalPath);
                return finalPath;
            }
            ExploreNeighbors(currentNode, targetNode);
        }

        Debug.LogWarning($"경로를 찾을 수 없습니다. 시작점: {startCell}, 목표점: {targetCell}");
        return null;
    }

    // 주어진 셀 좌표가 맵 범위 내에 있는지 확인 (타일맵 기준)
    private bool IsPositionInMap(Vector3Int cell)
    {
        return cell.x >= mMapMinCell.x && cell.x <= mMapMaxCell.x &&
               cell.y >= mMapMinCell.y && cell.y <= mMapMaxCell.y &&
               mGroundTilemap.HasTile(cell);
    }

    // 노드 배열을 타일맵 기준으로 초기화
    private void InitializeNodeArray()
    {
        mSizeX = mMapMaxCell.x - mMapMinCell.x + 1;
        mSizeY = mMapMaxCell.y - mMapMinCell.y + 1;
        mNodeArray = new Node[mSizeX, mSizeY];
        for (int i = 0; i < mSizeX; i++)
        {
            for (int j = 0; j < mSizeY; j++)
            {
                Vector3Int cell = new Vector3Int(i + mMapMinCell.x, j + mMapMinCell.y, 0);
                bool isWall = CheckForWall(cell);
                mNodeArray[i, j] = new Node(isWall, cell.x, cell.y);
            }
        }
    }

    // 해당 셀에 벽이 있는지 확인 (타일맵 기준)
    private bool CheckForWall(Vector3Int cell)
    {
        if (!mGroundTilemap.HasTile(cell)) return true; // 타일이 없으면 벽으로 간주
        Vector2 checkPos = mGroundTilemap.GetCellCenterWorld(cell);
        int wallLayer = LayerMask.GetMask("Wall");
        int obstacleLayer = LayerMask.GetMask("Obstacles");
        int layerMask = wallLayer | obstacleLayer;
        Collider2D[] colliders = Physics2D.OverlapCircleAll(checkPos, 0.4f, layerMask);
        if (colliders.Length > 0)
        {
            foreach (Collider2D collider in colliders)
            {
                if (((1 << collider.gameObject.layer) & layerMask) != 0)
                {
                    return true;
                }
            }
        }
        return false;
    }

    // 현재 노드의 이웃 노드들을 탐색하는 메서드
    private void ExploreNeighbors(Node _currentNode, Node _targetNode)
    {
        // 상하좌우 4방향
        Vector3Int[] directions = new Vector3Int[]
        {
            Vector3Int.up,    // 위쪽 셀
            Vector3Int.down,  // 아래쪽 셀
            Vector3Int.left,  // 왼쪽 셀
            Vector3Int.right  // 오른쪽 셀
        };

        // 각 방향별로 이웃 셀을 확인
        foreach (Vector3Int dir in directions)
        {
            // 이웃 셀 좌표 계산
            Vector3Int neighborCell = new Vector3Int(_currentNode.x, _currentNode.y, 0) + dir;

            // 타일맵 범위 및 타일 존재 여부 확인
            if (!IsPositionInMap(neighborCell)) continue;

            // 노드 배열 인덱스 변환
            Node neighborNode = mNodeArray[neighborCell.x - mMapMinCell.x, neighborCell.y - mMapMinCell.y];

            // 이미 닫힌 목록에 있거나 벽(또는 장애물)이면 스킵
            if (mClosedList.Contains(neighborNode) || neighborNode.isWall) continue;

            // 기본 이동 비용
            int moveCost = _currentNode.G + 10;

            // 방향 전환 패널티 계산
            if (_currentNode.ParentNode != null)
            {
                Vector2Int currentDirection = new Vector2Int(dir.x, dir.y); // 현재 이동 방향
                Vector2Int previousDirection = _currentNode.Direction;      // 이전 이동 방향

                // 이전 방향과 다르면 패널티 적용
                if (currentDirection != previousDirection)
                {
                    if (currentDirection == -previousDirection)
                        moveCost += 30; // 180도 회전(U턴) 패널티
                    else
                        moveCost += 15; // 90도 회전 패널티
                }
            }

            // 휴리스틱(맨해튼 거리)
            int heuristic = Mathf.Abs(neighborNode.x - _targetNode.x) + Mathf.Abs(neighborNode.y - _targetNode.y);

            // 더 나은 경로를 찾았거나 아직 열린 목록에 없는 경우
            if (!mOpenList.Contains(neighborNode) || moveCost < neighborNode.G)
            {
                neighborNode.G = moveCost;                              // 실제 이동 비용
                neighborNode.H = heuristic * 10;                        // 휴리스틱(예상 비용)
                neighborNode.ParentNode = _currentNode;                 // 부모 노드 갱신
                neighborNode.Direction = new Vector2Int(dir.x, dir.y);  // 이동 방향 저장

                // 열린 목록에 추가
                if (!mOpenList.Contains(neighborNode))
                {
                    mOpenList.Enqueue(neighborNode);
                }
                else
                {
                    mOpenList.UpdatePriority(neighborNode);
                }
            }
        }
    }

    // 목표 노드에서 시작 노드까지의 경로를 재구성하는 메서드
    private List<Node> ReconstructPath(Node _targetNode, Node _startNode)
    {
        List<Node> path = new List<Node>();
        Node currentNode = _targetNode;

        while (currentNode != _startNode)
        {
            path.Add(currentNode);
            currentNode = currentNode.ParentNode;
        }
        path.Add(_startNode);
        path.Reverse();

        return path;
    }

    // 경로를 부드럽게 만드는 메서드
    private List<Node> SmoothPath(List<Node> _path)
    {
        if (_path == null || _path.Count <= 2) return _path;

        List<Node> smoothedPath = new List<Node>();
        smoothedPath.Add(_path[0]);

        int currentIndex = 0;
        while (currentIndex < _path.Count - 1)
        {
            int nextIndex = currentIndex + 1;
            while (nextIndex < _path.Count - 1)
            {
                // 두 노드가 같은 행이나 열에 있는 경우에만 직선 경로로 간주
                if ((_path[currentIndex].x == _path[nextIndex + 1].x ||
                     _path[currentIndex].y == _path[nextIndex + 1].y) &&
                    HasDirectPath(_path[currentIndex], _path[nextIndex + 1]))
                {
                    nextIndex++;
                }
                else
                {
                    break;
                }
            }
            smoothedPath.Add(_path[nextIndex]);
            currentIndex = nextIndex;
        }

        return smoothedPath;
    }

    // 두 노드 사이에 직선 경로가 있는지 확인하는 메서드
    private bool HasDirectPath(Node _start, Node _end)
    {
        Vector2 startPos = new Vector2(_start.x + 0.5f, _start.y + 0.5f);
        Vector2 endPos = new Vector2(_end.x + 0.5f, _end.y + 0.5f);
        Vector2 direction = (endPos - startPos).normalized;
        float distance = Vector2.Distance(startPos, endPos);

        // 벽과 장애물 레이어 모두 확인
        int wallLayer = LayerMask.GetMask("Wall");
        int obstacleLayer = LayerMask.GetMask("Obstacles");
        int layerMask = wallLayer | obstacleLayer;  // 두 레이어를 모두 포함

        RaycastHit2D hit = Physics2D.Raycast(startPos, direction, distance, layerMask);
        return hit.collider == null;
    }

    // 두 지점 사이의 경로 비용을 계산하는 메서드
    public float CalculatePathCost(Vector2 startWorldPos, Vector2 targetWorldPos)
    {
        // FindPath로 경로를 구함
        List<Node> path = FindPath(startWorldPos, targetWorldPos);
        if (path == null || path.Count == 0)
            return float.MaxValue; // 경로가 없으면 최대값 반환

        // 마지막 노드의 G값(누적 실제 비용)을 반환
        return path[path.Count - 1].G;
    }

    // 디버그용 기즈모를 그리는 메서드
    private void OnDrawGizmos()
    {
        if (mNodeArray == null) return;
        if (!mShowDebug) return;

        // 모든 노드 표시
        for (int x = 0; x < mSizeX; x++)
        {
            for (int y = 0; y < mSizeY; y++)
            {
                Node node = mNodeArray[x, y];
                // 타일의 중심 좌표로 표시
                Vector2 pos = new Vector2(node.x + 0.5f, node.y + 0.5f);

                // 벽은 빨간색으로 표시
                if (node.isWall)
                {
                    Gizmos.color = Color.red;
                    Gizmos.DrawCube(pos, Vector3.one * 0.8f);
                }
                // 열린 리스트의 노드는 초록색으로 표시
                else if (mOpenList != null && mOpenList.Contains(node))
                {
                    Gizmos.color = Color.green;
                    Gizmos.DrawWireCube(pos, Vector3.one * 0.8f);
                }
                // 닫힌 리스트의 노드는 파란색으로 표시
                else if (mClosedList != null && mClosedList.Contains(node))
                {
                    Gizmos.color = Color.blue;
                    Gizmos.DrawWireCube(pos, Vector3.one * 0.8f);
                }
                // 그 외의 노드는 회색으로 표시
                else
                {
                    Gizmos.color = Color.gray;
                    Gizmos.DrawWireCube(pos, Vector3.one * 0.8f);
                }

                // 타일 중심점 표시
                Gizmos.color = Color.white;
                Gizmos.DrawSphere(pos, 0.05f);
            }
        }
    }
}

// 최소 힙 기반 우선순위 큐 (F값 기준)
public class NodePriorityQueue
{
    private List<Node> heap = new List<Node>();
    public int Count => heap.Count;
    public void Enqueue(Node node)
    {
        heap.Add(node);
        int i = heap.Count - 1;
        while (i > 0)
        {
            int parent = (i - 1) / 2;
            if (Compare(heap[i], heap[parent]) >= 0) break;
            Swap(i, parent);
            i = parent;
        }
    }
    public Node Dequeue()
    {
        if (heap.Count == 0) return null;
        Node root = heap[0];
        heap[0] = heap[heap.Count - 1];
        heap.RemoveAt(heap.Count - 1);
        Heapify(0);
        return root;
    }
    public bool Contains(Node node) => heap.Contains(node);
    public void UpdatePriority(Node node)
    {
        int i = heap.IndexOf(node);
        if (i >= 0)
        {
            // 위로 올리기
            while (i > 0)
            {
                int parent = (i - 1) / 2;
                if (Compare(heap[i], heap[parent]) >= 0) break;
                Swap(i, parent);
                i = parent;
            }
            // 아래로 내리기
            Heapify(i);
        }
    }
    private void Heapify(int i)
    {
        int left = 2 * i + 1, right = 2 * i + 2, smallest = i;
        if (left < heap.Count && Compare(heap[left], heap[smallest]) < 0) smallest = left;
        if (right < heap.Count && Compare(heap[right], heap[smallest]) < 0) smallest = right;
        if (smallest != i)
        {
            Swap(i, smallest);
            Heapify(smallest);
        }
    }
    private int Compare(Node a, Node b)
    {
        // F값이 낮은 게 우선, F가 같으면 H가 낮은 게 우선
        if (a.F != b.F) return a.F.CompareTo(b.F);
        return a.H.CompareTo(b.H);
    }
    private void Swap(int i, int j)
    {
        Node tmp = heap[i];
        heap[i] = heap[j];
        heap[j] = tmp;
    }
}