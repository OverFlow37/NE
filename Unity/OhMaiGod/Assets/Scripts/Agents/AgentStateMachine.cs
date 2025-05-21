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
        private bool mAllowStateChange = true;

        public AgentState CurrentStateType {get {return mCurrentStateType;} }
        public AgentState PreviousStateType { get {return mPreviousStateType;} }
        public bool AllowStateChange { get {return mAllowStateChange;} set {mAllowStateChange = value;} }

        public AgentStateMachine(AgentController _controller)
        {
            mController = _controller;
            mCurrentStateType = AgentState.WAITING;
            mStates = new Dictionary<AgentState, AgentStateHandler>();
            InitializeStates();
        }

        private void InitializeStates()
        {
            // 모든 상태 등록
            RegisterState(AgentState.WAITING_FOR_AI_RESPONSE, new WaitForAIResponseStateHandler());
            RegisterState(AgentState.WAITING, new WaitStateHandler());
            RegisterState(AgentState.MOVING_TO_LOCATION, new MoveToLocationStateHandler());
            RegisterState(AgentState.MOVING_TO_INTERACTABLE, new MoveToInteractableStateHandler());
            RegisterState(AgentState.INTERACTING, new InteractionStateHandler());
        }

        private void RegisterState(AgentState _stateType, AgentStateHandler _state)
        {
            mStates[_stateType] = _state;
        }

        public void ChangeState(AgentState _newStateType)
        {
            if (mCurrentStateType == _newStateType)  return;
            //if (!mAllowStateChange && mCurrentStateType == AgentState.WAITING_FOR_AI_RESPONSE) return;
            // 디버깅용
            LogManager.Log("Agent", $"{mController.AgentName}: 상태 변경 {mCurrentStateType} -> {_newStateType}", 2);

            // 이전 상태 종료
            if (mCurrentState != null)
            {
                mCurrentState.OnStateExit(mController);
            }

            // 상태 변경
            mPreviousState = mCurrentState;
            mPreviousStateType = mCurrentStateType;
            mCurrentStateType = _newStateType;
            mCurrentState = mStates[_newStateType];

            // 새 상태 진입
            if (mCurrentState != null)
            {
                mCurrentState.OnStateEnter(mController);
            }
        }

        public void ProcessStateUpdate()
        {
            if (mCurrentState != null)
            {
                mCurrentState.OnStateExecute(mController);
            }
        }

        public void Initialize(AgentState _initialState)
        {
            mCurrentStateType = _initialState;
            mCurrentState = mStates[_initialState];
            mCurrentState.OnStateEnter(mController);
        }
        
        // AI 응답 완료 후 이전 상태로 돌아가기
        public void ReturnToPreviousState()
        {
            if (mPreviousState != null)
            {
                ChangeState(mPreviousStateType);
            }
        }
    }
}