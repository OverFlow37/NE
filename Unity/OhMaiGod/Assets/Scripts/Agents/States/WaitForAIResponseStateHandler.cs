using UnityEngine;

namespace OhMAIGod.Agent
{
    public class WaitForAIResponseStateHandler : AgentStateHandler
    {
         public override void Update(AgentController controller)
         {
            Debug.Log("WaitForAIResponseStateHandler Update Calling");
         }

        protected override string GetStateName()
        {
            return "AI 응답 대기";
        }
    }
}

