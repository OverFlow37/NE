using UnityEngine;
using System.Collections;
using System.Linq;

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
        // 특정 시간동안 행동 수행

        // 행동 완료 후 오브젝트 제거
        LogManager.Log("Interact", $"get {targetInteractable.InteractableName}", 1);
        targetInteractable.RemoveObject();

        // TODO: 인벤토리로 이동

        return true;
    }
}