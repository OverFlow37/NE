using UnityEngine;
using System;
using OhMAIGod.Agent;
using OhMAIGod.Perceive;

namespace OhMAIGod.Agent
{
    public class WaitStateHandler : AgentStateHandler
    {
        private int WAIT_TIME_THRESHOLD = 10;
        public override void OnStateEnter(AgentController _controller)
        {
            _controller.animator.SetBool("isMoving", false);
            _controller.mWaitTIme = TimeManager.Instance.GetCurrentGameTime();
        }

        public override void OnStateExecute(AgentController _controller)
        {
            // 임계치 이상 대기하면 반응 생성
            TimeSpan elapsed = TimeManager.Instance.GetCurrentGameTime() - _controller.mWaitTIme;
            if (elapsed >= TimeSpan.FromMinutes(WAIT_TIME_THRESHOLD))
            {
                PerceiveEvent perceiveEvent = new PerceiveEvent();
                perceiveEvent.event_type = PerceiveEventType.AGENT_NO_TASK;
                perceiveEvent.event_location = "";
                perceiveEvent.event_description = "";
                perceiveEvent.event_is_save = false;
                perceiveEvent.event_role = "";
                _controller.ReactToResponse(true, perceiveEvent); // 호출하고 싶은 함수명으로 변경
            }
        }

        protected override string GetStateName()
        {
            return "WAIT";
        }
    }
} 