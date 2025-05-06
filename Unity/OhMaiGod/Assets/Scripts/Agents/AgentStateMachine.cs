using System.Collections.Generic;
using UnityEngine;

namespace OhMAIGod.Agent
{
    public class AgentStateMachine
    {
        private AgentController mController;
        private Dictionary<AgentState, AgentStateHandler> mStates;
        private AgentStateHandler mCurrentState;
        private AgentStateHandler mPreviousState;
        private AgentState mCurrentStateType;
        private AgentState mPreviousStateType;

        public AgentState CurrentStateType {get { return mCurrentStateType; }}
        public AgentState PreviousStateType {get { return mPreviousStateType; }}

        public AgentStateMachine(AgentController _controller)
        {
            mController = _controller;
            mStates = new Dictionary<AgentState, AgentStateHandler>();
            InitializeStates();
        }

        private void InitializeStates()
        {
            // 모든 상태 등록
            // RegisterState(AgentState.WAIT_FOR_AI_RESPONSE, new WaitingForAIResponseState());
            // RegisterState(AgentState.WAIT, new WaitingForScheduleState());
            // RegisterState(AgentState.WAIT, new WaitingForConditionState());
            // RegisterState(AgentState.MOVE_TO_LOCATION, new MovingToLocationState());
            // RegisterState(AgentState.MOVE_TO_INTERACTABLE, new MovingToInteractableState());
            // RegisterState(AgentState.INTERACTION, new InteractionState());
        }

        private void RegisterState(AgentState _stateType, AgentStateHandler _stateClass)
        {
            mStates[_stateType] = _stateClass;
        }

        public void ChangeState(AgentState _newStateType)
        {
            if (mCurrentStateType == _newStateType)     return;

            // 디버깅
            Debug.Log($"{mController.AgentName}: 상태 변경 {mCurrentStateType} -> {_newStateType}");

            // 이전 상태 종료
            if (mCurrentState != null)
            {
                mCurrentState.Exit(mController);
            }

            // 상태 변경
            mPreviousState = mCurrentState;
            mPreviousStateType = mCurrentStateType;
            mCurrentStateType = _newStateType;
            mCurrentState = mStates[_newStateType];

            // 새 상태 진입
            if (mCurrentState != null)
            {
                mCurrentState.Enter(mController);
            }
        }

        public void Update()
        {
            if (mCurrentState != null)
            {
                mCurrentState.Update(mController);
            }
        }

        public void Initialize(AgentState _initialState)
        {
            mCurrentStateType = _initialState;
            mCurrentState = mStates[_initialState];
            mCurrentState.Enter(mController);
        }
    }  
}


