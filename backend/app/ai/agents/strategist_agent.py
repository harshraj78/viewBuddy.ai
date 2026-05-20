from app.ai.interview_brain import (
    AnswerAnalysis,
    InterviewBrainState,
    InterviewMove,
    interview_brain,
)


class FollowupStrategistAgent:
    def update_and_plan(
        self,
        *,
        state: InterviewBrainState,
        analysis: AnswerAnalysis,
        interview_context: dict[str, object],
    ) -> InterviewMove:
        interview_brain.update_state(state=state, analysis=analysis)
        return interview_brain.plan_next_move(
            state=state,
            analysis=analysis,
            interview_context=interview_context,
        )


followup_strategist_agent = FollowupStrategistAgent()
