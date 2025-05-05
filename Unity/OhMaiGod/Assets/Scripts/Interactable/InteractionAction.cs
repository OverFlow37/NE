using UnityEngine;

// 모든 상호작용 행동의 기본 클래스
// ScriptableObject로 만들어 에셋으로 관리할 수 있게 합니다.
// abstract 키워드로 이 클래스 자체는 직접 인스턴스화할 수 없게 합니다.
public abstract class InteractionAction : ScriptableObject
{
    // 상호작용 행동을 실제로 실행하는 메서드
    // 상속받는 클래스는 반드시 이 메서드를 구현해야 합니다 (override).
    // interactor: 상호작용을 시도한 게임 오브젝트 (예: 플레이어 캐릭터)
    // targetObject: 상호작용 대상인 Interactable 컴포넌트가 붙어있는 게임 오브젝트
    // 반환값: 행동 실행 성공 여부 (필요에 따라 다르게 사용 가능)
    public abstract bool Execute(GameObject interactor, GameObject targetObject);

}