using UnityEngine;
using System.Collections;

// 씬의 상호작용 가능한 게임 오브젝트에 붙는 컴포넌트 (MonoBehaviour)
public class Interactable : MonoBehaviour
{
    [Header("Data")]
    [Tooltip("이 오브젝트의 기본 데이터를 담고 있는 ObjectData ScriptableObject 애셋")]
    // 인스펙터에서 Project 창의 ObjectData 애셋을 여기에 드래그하여 할당합니다.
    public InteractableData mInteractableData;

    // 오브젝트 이름 (InteractableData와 동기화)
    public string InteractableName { get; private set; }
    // 오브젝트 타입 (InteractableData와 동기화)
    public InteractableData.Types InteractableType { get; private set; }


    // 현재 위치 정보
    public string CurrentLocation { get; private set; }

    // 오브젝트가 제거될 때 발생하는 이벤트
    public delegate void InteractableRemovedHandler(Interactable interactable);
    public event InteractableRemovedHandler OnInteractableRemoved;

    // 위치 변경 이벤트 델리게이트 및 이벤트 정의
    public delegate void LocationChangedHandler(Interactable interactable, string newLocation);
    public event LocationChangedHandler OnLocationChanged;

    // 타일매니저
    TileManager mtileManager;
    // 타겟컨트롤러
    private TargetController mTargetController;
    public TargetController TargetController { get { return mTargetController; } }
    // 스프라이트 렌더러
    private SpriteRenderer mSpriteRenderer;

    void Awake()
    {
        // ObjectData가 할당되지 않았으면 경고
        if (mInteractableData == null)
        {
            LogManager.Log("Interact", "Interactable 컴포넌트에 mInteractableData 할당되지 않았습니다: " + gameObject.name, 1);
        }
        else
        {
            // InteractableData와 동기화
            InteractableName = mInteractableData.mName;
            InteractableType = mInteractableData.mType;

            mSpriteRenderer = GetComponent<SpriteRenderer>();
            if (mSpriteRenderer != null)
            {
                mInteractableData.mIcon = mSpriteRenderer.sprite;
            }
        }

        mTargetController = GetComponent<TargetController>();
    }

    void Start()
    {
        RegisterToEnvironment();
    }

    void OnEnable()
    {
        // 오브젝트가 활성화될 때마다 환경 등록 시도
        RegisterToEnvironment();
    }

    void OnDisable()
    {
        // 오브젝트가 비활성화될 때 환경에서 직접 제거
        if (TileManager.Instance != null)
        {
            TileManager.Instance.UnregisterTarget(this);
        }
    }

    // 환경에 자신을 등록
    private void RegisterToEnvironment()
    {
        LogManager.Log("Interact", "RegisterToEnvironment: " + gameObject.name, 3);
        if (TileManager.Instance == null) return;
        TileManager.Instance.RegisterTarget(this);
    }

    // 환경에서 자신을 제거
    private void UnregisterFromEnvironment()
    {
        if (TileManager.Instance == null) return;
        TileManager.Instance.UnregisterTarget(this);
    }

    // 상호작용 주체(Interactor)로부터 상호작용 요청을 받는 메서드
    public bool Interact(GameObject interactor, string actionName)
    {
        // InteractableData가 없거나 행동 목록이 없으면 상호작용 처리 불가
        if (mInteractableData == null || mInteractableData.mActions == null || mInteractableData.mActions.Length == 0)
        {
            LogManager.Log("Interact", $"Interactable 오브젝트에 정의된 행동이 없어 상호작용 처리 불가: {gameObject.name}", 1);
            return false;
        }

        LogManager.Log("Interact", $"{interactor.name}가 {mInteractableData.mName}와 상호작용 시도.", 2);

        // === 상호작용 처리 로직 ===
        // actionName과 일치하는 mAction만 실행
        bool actionFound = false;
        foreach (var action in mInteractableData.mActions)
        {
            LogManager.Log("Interact", "action: "+action.mAction.mActionName+ "actionName: "+actionName, 3);
            if (action.mAction != null && action.mAction.mActionName.ToLower() == actionName.ToLower())
            {
                actionFound = true;
                // InteractionAction의 Execute 메서드 호출
                if (action.mAction.Execute(interactor, this.gameObject))
                {
                    LogManager.Log("Interact", $"{mInteractableData.mName} 상호작용 성공.", 2);
                    return true;
                }
                break; // 일치하는 것만 실행하고 종료
            }
        }

        if (!actionFound)
        {
            LogManager.Log("Interact", $"{mInteractableData.mName}에 해당하는 행동({actionName})이 정의되어 있지 않음.", 1);
        }
        else
        {
            LogManager.Log("Interact", $"{mInteractableData.mName} 상호작용 실패.", 2);
        }
        return false;
    }

    // actionName에 해당하는 action의 duration을 반환하는 함수
    public float GetActionDuration(string _actionName)
    {
        if (mInteractableData == null || mInteractableData.mActions == null)
            return -1f;
        foreach (var action in mInteractableData.mActions)
        {
            if (action.mAction != null && action.mAction.mActionName == _actionName)
            {
                return action.mDuration;
            }
        }
        return -1f;
    }

    // 오브젝트를 제거하는 공통 메서드
    public virtual void RemoveObject()
    {
        // 환경에서 제거
        UnregisterFromEnvironment();

        // 제거되기 전에 이벤트 발생
        OnInteractableRemoved?.Invoke(this);

        // TODO: 필요한 경우 파티클 효과 재생
        // TODO: 필요한 경우 사운드 재생
        // TODO: 필요한 경우 애니메이션 재생
        // TODO: 필요한 경우 인벤토리 시스템과 연동
        // TODO: 필요한 경우 통계/업적 시스템과 연동

        // 오브젝트 비활성화
        gameObject.SetActive(false);
    }

    private void OnTriggerExit2D(Collider2D other)
    {
        // 게임오브젝트가 비활성화 중이면 무시
        if (!gameObject.activeInHierarchy) return;

        // Location 레이어인 경우에만 처리
        if (other.gameObject.layer == LayerMask.NameToLayer("Location"))
        {
            LogManager.Log("Interact", $"[{gameObject.name}] {other.name} 영역에서 벗어남", 2);
            StartCoroutine(UpdateEnvironmentRegistration());
        }
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        // Location 레이어인 경우에만 처리
        if (other.gameObject.layer == LayerMask.NameToLayer("Location"))
        {
            LogManager.Log("Interact", $"[{gameObject.name}] {other.name} 영역으로 진입", 2);
            StartCoroutine(UpdateEnvironmentRegistration());
        }
    }

    private IEnumerator UpdateEnvironmentRegistration()
    {
        // TileManager 초기화 대기
        while (TileManager.Instance == null || !TileManager.Instance.IsInitialized)
        {
            yield return new WaitForSeconds(0.1f);
        }

        // 현재 위치의 TileController 찾기
        Vector3Int cellPosition = TileManager.Instance.GroundTilemap.WorldToCell(transform.position);
        TileController newTileController = TileManager.Instance.GetTileController(cellPosition);

        if (newTileController != null)
        {
            // 기존 환경에서 제거 후 새로운 환경에 등록
            TileManager.Instance.UnregisterTarget(this);
            TileManager.Instance.RegisterTarget(this);
            LogManager.Log("Interact", $"[{gameObject.name}] 환경 업데이트 완료 - 새 위치: {newTileController.LocationName}", 2);
        }
        else
        {
            // 새로운 환경을 찾지 못한 경우 기존 환경에서만 제거
            TileManager.Instance.UnregisterTarget(this);
            LogManager.Log("Interact", $"[{gameObject.name}] 유효한 환경을 찾을 수 없음", 1);
        }
    }

    // 현재 위치 업데이트 메서드 (TileManager에서 호출)
    public void UpdateCurrentLocation(string locationName)
    {
        if (CurrentLocation != locationName)
        {
            CurrentLocation = locationName;
            // 위치가 변경되면 이벤트 발생
            LogManager.Log("Interact", $"[{gameObject.name}] 위치 변경: {locationName}", 2);
            OnLocationChanged?.Invoke(this, locationName);
        }
    }
}