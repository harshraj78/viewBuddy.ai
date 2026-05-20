import pytest

from app.ai.conversation import AIConversationEngine
from app.schemas.live_interview import InterviewRuntimeState
from app.services.interview_state_machine import interview_state_machine


def test_interview_state_machine_allows_core_realtime_flow() -> None:
    state = InterviewRuntimeState.setup
    state = interview_state_machine.transition(state, InterviewRuntimeState.introduction)
    state = interview_state_machine.transition(state, InterviewRuntimeState.questioning)
    state = interview_state_machine.transition(state, InterviewRuntimeState.follow_up)
    state = interview_state_machine.transition(state, InterviewRuntimeState.feedback_generation)
    state = interview_state_machine.transition(state, InterviewRuntimeState.completed)

    assert state == InterviewRuntimeState.completed


@pytest.mark.asyncio
async def test_fallback_conversation_engine_generates_cache_followup() -> None:
    engine = AIConversationEngine()
    chunks = [
        chunk
        async for chunk in engine.stream_followup(
            current_question="Tell me about your backend project.",
            transcript="I used Redis caching to reduce API latency.",
            personality="Strict",
            memory=[],
            interview_context={
                "target_role": "Backend Engineer",
                "company_style": "Startup",
                "skills": ["Redis", "FastAPI"],
                "projects": ["ViewBuddy.ai"],
            },
        )
    ]

    followup = " ".join(chunks).lower()
    assert "cache" in followup
    assert "strategy" in followup
