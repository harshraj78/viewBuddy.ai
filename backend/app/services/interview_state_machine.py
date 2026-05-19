from app.schemas.live_interview import InterviewRuntimeState

ALLOWED_TRANSITIONS: dict[InterviewRuntimeState, set[InterviewRuntimeState]] = {
    InterviewRuntimeState.setup: {
        InterviewRuntimeState.waiting_room,
        InterviewRuntimeState.introduction,
    },
    InterviewRuntimeState.waiting_room: {
        InterviewRuntimeState.introduction,
        InterviewRuntimeState.questioning,
    },
    InterviewRuntimeState.introduction: {InterviewRuntimeState.questioning},
    InterviewRuntimeState.questioning: {
        InterviewRuntimeState.follow_up,
        InterviewRuntimeState.coding_round,
        InterviewRuntimeState.system_design,
        InterviewRuntimeState.feedback_generation,
    },
    InterviewRuntimeState.follow_up: {
        InterviewRuntimeState.questioning,
        InterviewRuntimeState.feedback_generation,
    },
    InterviewRuntimeState.coding_round: {
        InterviewRuntimeState.questioning,
        InterviewRuntimeState.feedback_generation,
    },
    InterviewRuntimeState.system_design: {
        InterviewRuntimeState.questioning,
        InterviewRuntimeState.feedback_generation,
    },
    InterviewRuntimeState.feedback_generation: {InterviewRuntimeState.completed},
    InterviewRuntimeState.completed: set(),
}


class InvalidStateTransition(ValueError):
    pass


class InterviewStateMachine:
    def transition(
        self,
        current_state: InterviewRuntimeState,
        next_state: InterviewRuntimeState,
    ) -> InterviewRuntimeState:
        if current_state == next_state:
            return current_state
        if next_state not in ALLOWED_TRANSITIONS[current_state]:
            raise InvalidStateTransition(f"Cannot transition from {current_state} to {next_state}.")
        return next_state


interview_state_machine = InterviewStateMachine()
