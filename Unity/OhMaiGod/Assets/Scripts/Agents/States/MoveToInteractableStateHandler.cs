using UnityEngine;
using OhMAIGod.Agent;

namespace OhMAIGod.Agent
{
    public class MoveToInteractableStateHandler : AgentStateHandler
    {
        public override void OnStateEnter(AgentController _controller)
        {
            base.OnStateEnter(_controller);
            
            // 상호작용 오브젝트로 이동 시작 (필요시 별도 메서드 구현)
            // _controller.StartMovingToInteractable();
        }

        public override void OnStateExecute(AgentController _controller)
        {
            // 이동 중 도착 여부는 MovementController의 이벤트로 처리됨
            // 도착 시 HandleDestinationReached에서 상태 전환
        }

        public override void OnStateExit(AgentController _controller)
        {
            base.OnStateExit(_controller);
        }

        protected override string GetStateName()
        {
            return "MOVE_TO_INTERACTABLE";
        }
    }
} 