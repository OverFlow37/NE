using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AI;

// NPC의 이동을 제어하는 컨트롤러
public class MovementController : MonoBehaviour
{
    [Header("Movement Settings")]
    [SerializeField] private float mMoveSpeed = 2f;                   // 이동 속도
    [SerializeField] private float mReachedDistance = 0.01f;          // 목표 지점 도달 판정 거리
    [SerializeField] private Vector2Int mMapBottomLeft;               // 맵의 왼쪽 하단 좌표
    [SerializeField] private Vector2Int mMapTopRight;                 // 맵의 오른쪽 상단 좌표
    [SerializeField] private string mTargetName;                      // 찾아갈 목표물의 이름
    [SerializeField] private float mTargetSearchInterval = 2f;        // 목표물 탐색 간격
    [SerializeField] private bool mDrawPath = true;                   // 경로 그리기 여부

    // 이동 관련 변수들
    private List<Node> mCurrentPath;                                  // 현재 경로
    private int mCurrentPathIndex;                                    // 현재 경로 인덱스
    private Vector2 mTargetPosition;                                  // 현재 목표 위치
    private bool mIsMoving;                                          // 이동 중 여부
    private Transform mCurrentTarget;                                 // 현재 목표물
    private Vector2 mCurrentPoint;                                  // 현재 목표 위치
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

        MoveTowardTarget();
    }

    // 위치 이름으로 이동 시작
    public void MoveToLocation(string _locationName, System.Action _onReached = null)
    {
        Debug.Log($"{gameObject.name}이(가) {_locationName}로 이동 시작");
        mTargetName = _locationName;
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

        // NPC의 현재 위치를 타일 중심으로 조정
        Vector2Int startPos = new Vector2Int(
            Mathf.FloorToInt(transform.position.x),
            Mathf.FloorToInt(transform.position.y)
        );

        // 목표 위치를 타일 중심으로 조정
        Vector2Int targetPos = new Vector2Int(
            Mathf.FloorToInt(_targetPosition.x),
            Mathf.FloorToInt(_targetPosition.y)
        );

        // 맵 범위 확인 및 기본값 설정
        if (mMapBottomLeft == Vector2Int.zero && mMapTopRight == Vector2Int.zero)
        {
            Debug.LogWarning($"{gameObject.name}의 맵 범위가 설정되지 않았습니다. 기본값으로 설정합니다.");
            mMapBottomLeft = new Vector2Int(-50, -50);
            mMapTopRight = new Vector2Int(50, 50);
        }

        // Debug.Log($"시작 위치: {startPos}, 목표 위치: {targetPos}");

        // A* 알고리즘으로 경로 찾기
        mCurrentPath = PathFinder.Instance.FindPath(startPos, targetPos, mMapBottomLeft, mMapTopRight);

        if (mCurrentPath != null && mCurrentPath.Count > 0)
        {
            mCurrentPathIndex = 0;
            // 첫 번째 경로 노드의 타일 중심으로 이동
            mTargetPosition = new Vector2(
                mCurrentPath[0].x + 0.5f,
                mCurrentPath[0].y + 0.5f
            );
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

        // "Target" 태그를 가진 모든 오브젝트 찾기
        GameObject[] targets = GameObject.FindGameObjectsWithTag("Target");
        Transform closestTarget = null;
        float closestDistance = float.MaxValue;

        // 가장 가까운 목표물 찾기
        foreach (GameObject target in targets)
        {
            if (target.name == mTargetName)
            {
                // 현재 위치와 목표물 사이의 거리 계산 (맨해튼)
                Vector2Int currentPos = new Vector2Int(
                    Mathf.FloorToInt(transform.position.x),
                    Mathf.FloorToInt(transform.position.y)
                );
                Vector2Int targetPos = new Vector2Int(
                    Mathf.FloorToInt(target.transform.position.x),
                    Mathf.FloorToInt(target.transform.position.y)
                );

                // 맨해튼 거리 계산
                int distance = Mathf.Abs(currentPos.x - targetPos.x) +
                               Mathf.Abs(currentPos.y - targetPos.y);

                if (distance < closestDistance)
                {
                    closestDistance = distance;
                    closestTarget = target.transform;
                }
            }
        }

        // 가장 가까운 목표물이 있으면 목표물의 가장 가까운 StandingPoint 위치로 이동
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
                    // 현재 위치
                    Vector2Int currentPos = new Vector2Int(
                        Mathf.FloorToInt(transform.position.x),
                        Mathf.FloorToInt(transform.position.y)
                    );

                    // 가장 가까운 StandingPoint 찾기
                    Vector2 closestStandingPoint = standingPoints[0];
                    float minPathCost = float.MaxValue;

                    foreach (Vector2 point in standingPoints)
                    {
                        // 실제 경로 거리 계산
                        Vector2Int targetPos = new Vector2Int(
                            Mathf.FloorToInt(point.x),
                            Mathf.FloorToInt(point.y)
                        );

                        float pathCost = PathFinder.Instance.CalculatePathCost(
                            currentPos,
                            targetPos,
                            mMapBottomLeft,
                            mMapTopRight
                        );

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
                // 가장 가까운 StandingPoint 찾기
                Vector2 closestStandingPoint = standingPoints[0];
                float minDistance = float.MaxValue;
                foreach (Vector2 point in standingPoints)
                {
                    Vector2 direction = (point - (Vector2)mCurrentTarget.position).normalized;
                    float distance = Vector2.Distance(transform.position, point);
                    // 대각선 방향의 경우 거리에 페널티 추가
                    if (direction.x != 0 && direction.y != 0)
                    {
                        distance += 2f;
                    }

                    if (distance < minDistance)
                    {
                        minDistance = distance;
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
            mNPCLog.SetNPCLog($"{gameObject.name}이(가) 목적지({mCurrentTarget.name})로 이동 중");
            Debug.Log($"{gameObject.name}이(가) 목적지({mCurrentTarget.name})로 이동 중");
            mCurrentPathIndex++;
            mTargetPosition = new Vector2(
                mCurrentPath[mCurrentPathIndex].x + 0.5f,
                mCurrentPath[mCurrentPathIndex].y + 0.5f
            );
            mIsMoving = true;
        }
        else
        {
            mIsMoving = false;
            transform.position = new Vector2(mTargetPosition.x, mTargetPosition.y);
            mNPCLog.SetNPCLog($"{gameObject.name}이(가) 목적지({mCurrentTarget.name})에 도착함");
            Debug.Log($"{gameObject.name}이(가) 목적지({mCurrentTarget.name})에 도착함");
            mCurrentTarget = null;
            mCurrentPath = null;
            mCurrentPathIndex = 0;
            mTargetPosition = Vector2.zero;

            // 최종 목적지 도착 시 이벤트를 한 번만 발생
            if (!mDestinationReachedEventFired)
            {
                OnDestinationReached?.Invoke();
                mDestinationReachedEventFired = true;
            }
        }
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
    }
}