using UnityEngine;
using System.Collections;
using System.Linq;

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
        
        // 사용 효과 적용 (수면 및 외로움 수치 변화)
        // TODO: 부가적인 이펙트 추가(낚시터 -> 물고기 획득, 제단 -> 기도 효과)
        var agentController = interactor.GetComponent<AgentController>();
        agentController.ModifyNeed(OhMAIGod.Agent.AgentNeedsType.Sleepiness, targetInteractable.mInteractableData.mActions.FirstOrDefault(action => action.mAction == this).mSleepinessEffect);
        agentController.ModifyNeed(OhMAIGod.Agent.AgentNeedsType.Loneliness, targetInteractable.mInteractableData.mActions.FirstOrDefault(action => action.mAction == this).mLonelinessEffect);


        // 특정 시간동안 행동 수행

        // 사용 후 내구도 감소?

        // 사용 후 오브젝트 제거
        LogManager.Log("Interact", $"use {targetInteractable.InteractableName}", 1);

        return true;
    }
}