using UnityEngine;

namespace OhMAIGod.Agent
{
    public class WaitForAIResponseStateHandler : AgentStateHandler
    {
        public override void OnStateEnter(AgentController _controller)
        {
            base.OnStateEnter(_controller);
            _controller.AllowStateChange = false;
        }

         public override void OnStateExecute(AgentController _controller)
         {
            // Debug.Log("WaitForAIResponseStateHandler Update Calling");

            // TODO: AI 응답 대기 상태일 때 로직 필요
            // _controller.UpdateWaitTime();
         }

         public override void OnStateExit(AgentController _controller)
         {
            base.OnStateExit(_controller);
            _controller.AllowStateChange = true;
            _controller.mAgentUI.ShowReact("", false);
         }

        protected override string GetStateName()
        {
            return "AI 응답 대기";
        }
    }
}

