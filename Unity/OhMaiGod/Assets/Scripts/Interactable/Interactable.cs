using UnityEngine;
using System.Collections.Generic; // List를 사용하기 위해 필요

// 씬의 상호작용 가능한 게임 오브젝트에 붙는 컴포넌트 (MonoBehaviour)
public class Interactable : MonoBehaviour
{
    [Header("Data")]
    [Tooltip("이 오브젝트의 기본 데이터를 담고 있는 ObjectData ScriptableObject 애셋")]
    // 인스펙터에서 Project 창의 ObjectData 애셋을 여기에 드래그하여 할당합니다.
    public InteractableData mInteractableData;

    // 오브젝트가 제거될 때 발생하는 이벤트
    public delegate void InteractableRemovedHandler(Interactable interactable);
    public event InteractableRemovedHandler OnInteractableRemoved;

    void Awake()
    {
        // ObjectData가 할당되지 않았으면 경고
        if (mInteractableData == null)
        {
            Debug.LogWarning("Interactable 컴포넌트에 mInteractableData 할당되지 않았습니다: " + gameObject.name);
        }
    }

    // 상호작용 주체(Interactor)로부터 상호작용 요청을 받는 메서드
    public void Interact(GameObject interactor)
    {
        // InteractableData가 없거나 행동 목록이 없으면 상호작용 처리 불가
        if (mInteractableData == null || mInteractableData.mActions == null || mInteractableData.mActions.Length == 0)
        {
            Debug.LogWarning($"Interactable 오브젝트에 정의된 행동이 없어 상호작용 처리 불가: {gameObject.name}");
            return;
        }

        Debug.Log($"{interactor.name}가 {mInteractableData.mName}와 상호작용 시도.");

        // === 상호작용 처리 로직 ===
        // InteractableData에 연결된 모든 InteractionAction을 순회하며 실행
        bool anyActionSuccessful = false; // 하나라도 성공했는지 여부 플래그

        foreach (var action in mInteractableData.mActions)
        {
            if (action != null)
            {
                // InteractionAction의 Execute 메서드 호출
                // 이 메서드 안에서 실제 행동 로직이 실행됩니다.
                if (action.Execute(interactor, this.gameObject)) // 상호작용 주체와 대상 오브젝트를 넘겨줌
                {
                    anyActionSuccessful = true;
                }
            }
        }

        if (anyActionSuccessful)
        {
            Debug.Log($"{mInteractableData.mName} 상호작용 성공.");
        }
        else
        {
            Debug.Log($"{mInteractableData.mName} 상호작용 실패 또는 실행된 행동 없음.");
        }
    }

    // 오브젝트를 제거하는 공통 메서드
    public virtual void RemoveObject()
    {
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
}