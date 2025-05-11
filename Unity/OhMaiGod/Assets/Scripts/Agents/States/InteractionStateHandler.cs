using UnityEngine;
using OhMAIGod.Agent;

namespace OhMAIGod.Agent
{
    public class InteractionStateHandler : AgentStateHandler
    {
        public override void OnStateEnter(AgentController _controller)
        {
            base.OnStateEnter(_controller);
            
            // 상호작용 시작
            _controller.StartInteraction();
        }

        public override void OnStateExecute(AgentController _controller)
        {
            // 상호작용 시간 관리 및 완료 처리
            //_controller.UpdateActionTime();
        }

        public override void OnStateExit(AgentController _controller)
        {
            base.OnStateExit(_controller);
            // 상호작용 UI 종료
            if (_controller.mAgentUI != null)
            {
                _controller.mAgentUI.EndInteractionUI();
            }
        }

        protected override string GetStateName()
        {
            return "INTERACTION";
        }
    }
} 