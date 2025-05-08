using UnityEngine;
using OhMAIGod.Agent;

namespace OhMAIGod.Agent
{
    public class WaitStateHandler : AgentStateHandler
    {
        public override void OnStateEnter(AgentController _controller)
        {
            _controller.animator.SetBool("isMoving", false);
        }

        public override void OnStateExecute(AgentController _controller)
        {
            // 대기 시간 감소 및 대기 종료 시 상태 전환
            // _controller.UpdateWaitTime();
        }

        protected override string GetStateName()
        {
            return "WAIT";
        }
    }
} 