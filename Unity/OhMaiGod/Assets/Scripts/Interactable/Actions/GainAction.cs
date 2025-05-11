using UnityEngine;
using System.Collections;

// InteractionAction을 상속받아 잠금 해제 행동을 구현합니다.
// CreateAssetMenu 경로를 Interaction Actions로 변경
[CreateAssetMenu(fileName = "GainAction", menuName = "Game/Interaction Actions/Gain")]
public class GainAction : InteractionAction
{
    // 프롬프트에 전달할 액션 이름
    [SerializeField] private string _actionName = "Gain";
    public override string mActionName
    {
        get => _actionName;
        set => _actionName = value;
    }
    // InteractionAction의 Execute 메서드 구현
    public override bool Execute(GameObject interactor, GameObject targetObject)
    {
        // targetObject에서 Interactable 컴포넌트를 가져옵니다.
        Interactable targetInteractable = targetObject.GetComponent<Interactable>();
        if (targetInteractable == null)
        {
            LogManager.Log("Interact", $"상호작용 대상에 Interactable 컴포넌트가 없습니다: {targetObject.name}", 1);
            return false;
        }
        if(interactor == null)
        {
            LogManager.Log("Interact", $"상호작용 주체가 없습니다: {interactor.name}", 1);
            return false;
        }
        
        // 아이템 획득(분기)
        if(targetInteractable.mInteractableData.mType == InteractableData.Types.Resource)
        {
            // TODO: 자원일 경우 -> GameManager에서 처리
        }
        else if(targetInteractable.mInteractableData.mType == InteractableData.Types.Food)
        {
            // TODO: 음식일 경우 -> 인벤토리(또는 창고)에 추가
        }
        else
        {
            // TODO: 자원이나 음식이 아닌 경우 추후 구현
            // ex) 소라, 조개 등 -> 공물로 소모
        }


        return true;
    }
}