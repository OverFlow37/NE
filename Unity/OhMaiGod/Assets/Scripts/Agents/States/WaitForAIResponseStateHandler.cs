using UnityEngine;

namespace OhMAIGod.Agent
{
    public class WaitForAIResponseStateHandler : AgentStateHandler
    {
         public override void OnStateExecute(AgentController _controller)
         {
            // Debug.Log("WaitForAIResponseStateHandler Update Calling");

            // TODO: AI 응답 대기 상태일 때 로직 필요
            // _controller.UpdateWaitTime();
         }

        protected override string GetStateName()
        {
            return "AI 응답 대기";
        }
    }
}

