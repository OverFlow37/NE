using UnityEngine;
using OhMAIGod.Agent;

// InteractionAction을 상속받아 잠금 해제 행동을 구현합니다.
// CreateAssetMenu 경로를 Interaction Actions로 변경
[CreateAssetMenu(fileName = "GetAction", menuName = "Game/Interaction Actions/Get")]
public class GetAction : InteractionAction
{
    // 프롬프트에 전달할 액션 이름
    [SerializeField] private string _actionName = "Get";
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
        
        // 1. 현재 액션에 해당하는 효과 정보 찾기 (mActions 배열 직접 순회)
        InteractableData.InteractionActionInfo actionInfo = default;
        foreach (var info in targetInteractable.mInteractableData.mActions)
        {
            if (info.mAction != null && info.mAction.mActionName == mActionName)
            {
                actionInfo = info;
                break;
            }
        }

        if (actionInfo.mAction == null)
        {
            LogManager.Log("Interact", $"해당 액션에 대한 정보를 찾을 수 없습니다: {mActionName}", 1);
            return false;
        }

        // 2. 효과값 반영
        AgentController agentController = interactor.GetComponent<AgentController>();
        if (agentController != null)
        {
            agentController.ModifyNeed(AgentNeedsType.Hunger, actionInfo.mHungerEffect);
            agentController.ModifyNeed(AgentNeedsType.Sleepiness, actionInfo.mSleepinessEffect);
            agentController.ModifyNeed(AgentNeedsType.Loneliness, actionInfo.mLonelinessEffect);
            agentController.ModifyNeed(AgentNeedsType.Stress, actionInfo.mStressEffect);
        }


        // Furniture나 Resource가 아니라면 인벤토리로 이동 시도
        if (targetInteractable.InteractableType != InteractableData.Types.Furniture && targetInteractable.InteractableType != InteractableData.Types.Resource)
        {
            // 인벤토리가 가득 찼으면 피드백
            if (Inventory.Instance.Items.Count >= Inventory.Instance.MaxSlotCount)
            {
                LogManager.Log("Interact", $"인벤토리가 가득 찼습니다.", 1);
                return false;
            }
            // 행동 완료 후 오브젝트 제거
            LogManager.Log("Interact", $"get {targetInteractable.InteractableName}");
            targetInteractable.RemoveObject();
            Inventory.Instance.AddItem(targetObject);
        }
        else
        {
            // TODO: Furniture나 Resource라면 피드백
            LogManager.Log("Interact", $"{targetInteractable.InteractableName} 는 가지고 갈 수 없습니다.", 1);
            return false;
        }

        return true;
    }
}