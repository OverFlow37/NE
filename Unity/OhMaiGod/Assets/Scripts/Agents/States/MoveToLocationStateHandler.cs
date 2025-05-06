using UnityEngine;
using OhMAIGod.Agent;

namespace OhMAIGod.Agent
{
    public class MoveToLocationStateHandler : AgentStateHandler
    {
        public override void OnStateEnter(AgentController _controller)
        {
            base.OnStateEnter(_controller);
            
            // 이동 시작
            _controller.StartMovingToAction();
        }

        public override void OnStateExecute(AgentController _controller)
        {
            // 이동 중 도착 여부는 MovementController의 이벤트로 처리됨
            // 도착 시 HandleDestinationReached에서 상태 전환
        }

        protected override string GetStateName()
        {
            return "MOVE_TO_LOCATION";
        }
    }
} 