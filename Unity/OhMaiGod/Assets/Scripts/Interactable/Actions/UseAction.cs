using UnityEngine;
using OhMAIGod.Agent;

// InteractionAction을 상속받아 잠금 해제 행동을 구현합니다.
// CreateAssetMenu 경로를 Interaction Actions로 변경
[CreateAssetMenu(fileName = "UseAction", menuName = "Game/Interaction Actions/Use")]
public class UseAction : InteractionAction
{
    // 프롬프트에 전달할 액션 이름
    [SerializeField] private string _actionName = "Use";
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
        // 에이전트의 상태가 INTERACTION이 아니면(행동 주체가 이상하져 ㅈㅅ... ㅠㅠ)
        if(agentController.CurrentState != AgentState.INTERACTING){
            LogManager.Log("Interact", $"에이전트가 상호작용 가능한 상태가 아닙니다.: {mActionName}", 1);
            return false;
        }
        if (agentController != null)
        {
            if(targetInteractable.mInteractableData.mFaithUse > 0){
                Inventory.Instance.AddResource(Inventory.ResourceType.Power, targetInteractable.mInteractableData.mFaithUse);
            }
            agentController.ModifyNeed(AgentNeedsType.Hunger, actionInfo.mHungerEffect);
            agentController.ModifyNeed(AgentNeedsType.Sleepiness, actionInfo.mSleepinessEffect);
            agentController.ModifyNeed(AgentNeedsType.Loneliness, actionInfo.mLonelinessEffect);
            agentController.ModifyNeed(AgentNeedsType.Stress, actionInfo.mStressEffect);
        }
        // 피드백에 효과 반영
        IncreaseNeedsForFeedback(agentController, actionInfo);

        // 로그 출력
        LogManager.Log("Interact", $"use {targetInteractable.InteractableName}");

        return true;
    }
}