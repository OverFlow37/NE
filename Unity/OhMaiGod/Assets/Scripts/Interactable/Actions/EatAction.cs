using UnityEngine;
using System.Collections;

// InteractionAction을 상속받아 잠금 해제 행동을 구현합니다.
// CreateAssetMenu 경로를 Interaction Actions로 변경
[CreateAssetMenu(fileName = "EatAction", menuName = "Game/Interaction Actions/Eat")]
public class EatAction : InteractionAction
{
    // InteractionAction의 Execute 메서드 구현
    public override bool Execute(GameObject interactor, GameObject targetObject)
    {
        // targetObject에서 Interactable 컴포넌트를 가져옵니다.
        Interactable targetInteractable = targetObject.GetComponent<Interactable>();
        if (targetInteractable == null)
        {
            Debug.LogWarning($"상호작용 대상에 Interactable 컴포넌트가 없습니다: {targetObject.name}");
            return false;
        }
        if(targetInteractable.mInteractableData.mType != InteractableData.Types.Food)
        {
            Debug.LogWarning($"상호작용 대상이 음식이 아닙니다: {targetObject.name}");
            return false;
        }
        if(interactor == null)
        {
            Debug.LogWarning($"상호작용 주체가 없습니다: {interactor.name}");
            return false;
        }
        
        // 음식을 먹은 후 배고픔 감소 (음식 특성에 따른 추가 효과는 Interactable에서 처리)
        var agentController = interactor.GetComponent<AgentController>();
        agentController.ModifyHunger(targetInteractable.mInteractableData.mHungerEffect);

        // 특정 시간동안 행동 수행

        // 행동 완료 후 음식 오브젝트 제거
        targetInteractable.RemoveObject();

        return true;
    }
}