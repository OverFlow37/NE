using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AI;

public class MovementController : MonoBehaviour
{
    [Header("Movement Settings")]
    [SerializeField] private float mMoveSpeed = 3.0f;           // 이동 속도
    [SerializeField] private float mRotationSpeed = 120.0f;     // 회전 속도
    [SerializeField] private float mStoppingDistance = 0.1f;    // 목적지 도달 판정 거리
    [SerializeField] private bool mUseNavMesh = true;           // NavMesh 사용 여부

    [Header("Reference")]
    [SerializeField] private Animator mAnimator;            // 애니메이터 참조 (있는 경우)
    [SerializeField] private Transform mModelTransform;     // 모델 Transform (회전용)

    // 이동 관련 변수
    private Vector2 mTargetPosition;            // 목표 위치
    private string mTargetLocationName;         // 목표 위치 이름
    private bool mIsMoving = false;             // 이동 중 여부
    private bool mPathBlocked = false;          // 경로 막힘 여부
    private NavMeshAgent mNavMeshAgent;         // NavMesh 에이전트 (사용하는 경우)

    private System.Action mOnDestinationReached; // 목적지 도착 시 호출될 콜백


    private void Awake()
    {
        // NavMesh 사용 시 컴포넌트 초기화
        if (mUseNavMesh)
        {
            mNavMeshAgent = GetComponent<NavMeshAgent>();
            
            // NavMeshAgent가 없으면 추가
            if (mNavMeshAgent == null)
            {
                mNavMeshAgent = gameObject.AddComponent<NavMeshAgent>();
            }
            
            // NavMeshAgent 설정
            mNavMeshAgent.speed = mMoveSpeed;
            mNavMeshAgent.angularSpeed = mRotationSpeed;
            mNavMeshAgent.stoppingDistance = mStoppingDistance;
            mNavMeshAgent.autoBraking = true;
        }

        // 모델 Transform이 할당되지 않은 경우 자신으로 설정
        if (mModelTransform == null)
        {
            mModelTransform = transform;
        }
    }

    private void Update()
    {
        if (!mIsMoving) return;

        if (mUseNavMesh)
        {
            // NavMesh를 사용하는 경우, 도착 여부 확인
            if (!mNavMeshAgent.pathPending && mNavMeshAgent.remainingDistance <= mStoppingDistance)
            {
                OnReachedDestination();
            }

            // 애니메이션 업데이트
            UpdateAnimation(mNavMeshAgent.velocity.magnitude);
        }
        else
        {
            // 기본 이동 로직
            MoveTowardTarget();
        }
    }

    
    // 지정된 위치로 이동 (_targetPosition: 목표 위치, _onReached: 도착 시 콜백)
    public void MoveTo(Vector2 _targetPosition, System.Action _onReached = null)
    {
        mTargetPosition = _targetPosition;
        mOnDestinationReached = _onReached;
        mTargetLocationName = string.Empty;
        mIsMoving = true;
        mPathBlocked = false;

        // 이동 방식에 따라 분기
        if (mUseNavMesh)
        {
            // NavMesh 경로 설정 (Vector2를 Vector3로 변환)
            Vector3 targetPos3D = new Vector3(_targetPosition.x, 0, _targetPosition.y);
            mNavMeshAgent.SetDestination(targetPos3D);
            mNavMeshAgent.isStopped = false;
        }

        // 애니메이션 시작
        UpdateAnimation(mMoveSpeed);

        // 디버그 로그
        Debug.Log($"{gameObject.name}이(가) {_targetPosition}로 이동 시작");
    }

    // 위치 이름으로 이동 시작 (EnvironmentManager에서 위치 조회)
    public void MoveToLocation(string _locationName, System.Action _onReached = null)
    {
        // 위치 이름을 저장
        mTargetLocationName = _locationName;
        mOnDestinationReached = _onReached;

        // EnvironmentManager에서 위치 조회
        Vector2 position = GetLocationPosition(_locationName);
        
        // 위치 조회 실패 시
        if (position == Vector2.zero)
        {
            Debug.LogWarning($"위치를 찾을 수 없음: {_locationName}");
            return;
        }

        // 위치로 이동
        MoveTo(position, _onReached);
    }

    // 현재 이동 중지
    public void StopMovement()
    {
        if (!mIsMoving) return;

        mIsMoving = false;
        
        if (mUseNavMesh)
        {
            mNavMeshAgent.isStopped = true;
        }

        // 애니메이션 중지
        UpdateAnimation(0);

        Debug.Log($"{gameObject.name}의 이동이 중지됨");
    }

    // 이동 중인지 여부 반환
    public bool IsMoving => mIsMoving;

    // 현재 목적지 이름 반환
    public string CurrentDestination => mTargetLocationName;

    // 기본 이동 로직 (NavMesh 미사용 시)
    private void MoveTowardTarget()
    {
        // 현재 위치를 Vector2로 변환
        Vector2 currentPosition = new Vector2(transform.position.x, transform.position.y);
        
        // 목표 방향 계산
        Vector2 direction = (mTargetPosition - currentPosition).normalized;
        
        // 모델 회전 (2D에서는 Z축 회전)
        if (direction != Vector2.zero)
        {
            float angle = Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg;
            Quaternion targetRotation = Quaternion.Euler(0, 0, angle);
            mModelTransform.rotation = Quaternion.RotateTowards(
                mModelTransform.rotation, 
                targetRotation, 
                mRotationSpeed * Time.deltaTime
            );
        }
        
        // 이동 (2D)
        Vector3 movement = new Vector3(direction.x, direction.y, 0) * mMoveSpeed * Time.deltaTime;
        transform.position += movement;
        
        // 애니메이션 업데이트
        UpdateAnimation(direction.magnitude * mMoveSpeed);
        
        // 도착 확인
        float distance = Vector2.Distance(currentPosition, mTargetPosition);
        if (distance <= mStoppingDistance)
        {
            OnReachedDestination();
        }
    }

    // 목적지 도착 처리
    private void OnReachedDestination()
    {
        mIsMoving = false;
        UpdateAnimation(0);
        
        Debug.Log($"{gameObject.name}이(가) 목적지({mTargetLocationName})에 도착함");
        
        // 콜백 호출
        mOnDestinationReached?.Invoke();
        mOnDestinationReached = null;
    }

    // 애니메이션 상태 업데이트
    private void UpdateAnimation(float _speed)
    {
        if (mAnimator != null)
        {
            // 애니메이터에 속도 파라미터 전달
            mAnimator.SetFloat("Speed", _speed);
            
            // 이동 중 상태 전환
            mAnimator.SetBool("IsMoving", _speed > 0.1f);
        }
    }

    // 위치 이름으로 실제 좌표 가져오기
    private Vector2 GetLocationPosition(string _locationName)
    {
        // TODO: EnvironmentManager 구현 후 연동
        
        // 임시 구현: 씬 내에서 해당 이름의 GameObject 찾기
        GameObject locationObject = GameObject.Find(_locationName);
        
        if (locationObject != null)
        {
            Vector3 pos = locationObject.transform.position;
            return new Vector2(pos.x, pos.y);
        }
        
        // 위치 찾기 실패 시 로그 출력
        Debug.LogWarning($"위치를 찾을 수 없음: {_locationName}, EnvironmentManager 연동 필요");
        
        return Vector2.zero;
    }
}