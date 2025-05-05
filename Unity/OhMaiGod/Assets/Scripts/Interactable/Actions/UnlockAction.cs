// 액션 예시입니다.

using UnityEngine;

// InteractionAction을 상속받아 잠금 해제 행동을 구현합니다.
// CreateAssetMenu 경로를 Interaction Actions로 변경
[CreateAssetMenu(fileName = "UnlockAction", menuName = "Game/Interaction Actions/Unlock")]
public class UnlockAction : InteractionAction
{
    [Tooltip("이 오브젝트를 잠금 해제하기 위해 필요한 키 아이템의 ID (예시)")]
    [SerializeField] private int _requiredKeyID = 0; // 변수명 규칙 적용 및 Serialize

    [Tooltip("잠금 해제에 성공했을 때 대상 오브젝트의 상태를 무엇으로 변경할지")]
    [SerializeField] private string _stateAfterUnlock = "Unlocked"; // 변수명 규칙 적용 및 Serialize

    // InteractionAction의 Execute 메서드 구현
    public override bool Execute(GameObject interactor, GameObject targetObject)
    {
        // targetObject에서 Interactable 컴포넌트를 가져옵니다.
        Interactable targetInteractable = targetObject.GetComponent<Interactable>();
        // if (targetInteractable == null)
        // {
        //     Debug.LogWarning($"상호작용 대상에 Interactable 컴포넌트가 없습니다: {targetObject.name}");
        //     return false;
        // }

        // // 상호작용 대상이 현재 "Locked" 상태인지 확인 (예시)
        // // Interactable 스크립트에 GetCurrentState() 메서드가 있어야 합니다.
        // if (targetInteractable.GetCurrentState() == "Locked")
        // {
        //     // === 실제 잠금 해제 로직 ===
        //     // 예: interactor (플레이어)가 _requiredKeyID에 해당하는 아이템을 가지고 있는지 확인
        //     // Inventory inventory = interactor.GetComponent<Inventory>();
        //     // bool hasKey = (inventory != null && inventory.HasItem(_requiredKeyID));

        //     // if (hasKey)
        //     // {
        //         Debug.Log($"{targetObject.name} 잠금 해제!");

        //         // Interactable 오브젝트의 상태를 변경
        //         // Interactable 스크립트에 SetState() 메서드가 있어야 합니다.
        //         targetInteractable.SetState(_stateAfterUnlock);

        //         // 문 열림 애니메이션 재생, 사운드 재생 등 추가 효과
        //         // targetObject.GetComponent<Animator>()?.SetTrigger("Unlock");

        //         // 아이템 소비 로직 (필요하다면)
        //         // inventory.RemoveItem(_requiredKeyID);

        //         return true; // 잠금 해제 성공
        //     // }
        //     // else
        //     // {
        //     //     Debug.Log($"{interactor.name}: 열쇠가 없습니다.");
        //     //     return false; // 열쇠 부족으로 실패
        //     // }

        //     // 예시에서는 조건을 주석처리하고 항상 성공하도록 했습니다. 실제 구현 시 위 주석 부분을 활용하세요.
        //      Debug.Log($"{targetObject.name} 잠금 해제!");
        //      targetInteractable.SetState(_stateAfterUnlock);
        //      return true;
        // }
        // else
        // {
        //     Debug.Log($"{targetObject.name}는 이미 잠금 해제된 상태입니다.");
        //     return false; // 이미 잠금 해제된 상태
        // }
        return true;
    }
}