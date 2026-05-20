from app.ai.interview_brain import InterviewBrainState, InterviewMoveType, interview_brain


def test_interview_brain_challenges_vague_answers() -> None:
    analysis = interview_brain.analyze_answer(
        current_question="Walk me through your AI project.",
        transcript="I used FastAPI and it was good.",
        interview_context={
            "target_role": "AI Engineer",
            "skills": ["FastAPI", "RAG"],
            "projects": ["ViewBuddy.ai"],
        },
    )
    state = interview_brain.update_state(state=InterviewBrainState(), analysis=analysis)
    move = interview_brain.plan_next_move(
        state=state,
        analysis=analysis,
        interview_context={
            "target_role": "AI Engineer",
            "company_style": "Indian Product",
            "skills": ["FastAPI", "RAG"],
            "projects": ["ViewBuddy.ai"],
        },
    )

    assert analysis.is_vague is True
    assert "specificity" in state.weak_areas
    assert move.move_type == InterviewMoveType.clarify
    assert move.should_interrupt is True


def test_interview_brain_remembers_prior_technology_for_later_probe() -> None:
    state = InterviewBrainState(technologies=["Redis/cache"], turn_count=4)
    analysis = interview_brain.analyze_answer(
        current_question="How would you scale it?",
        transcript=(
            "I designed the API with retries, measured latency, and chose the queue "
            "because request spikes could overload synchronous processing."
        ),
        interview_context={"target_role": "Backend Engineer"},
    )
    state = interview_brain.update_state(state=state, analysis=analysis)
    move = interview_brain.plan_next_move(
        state=state,
        analysis=analysis,
        interview_context={
            "target_role": "Backend Engineer",
            "company_style": "Startup",
            "skills": ["FastAPI"],
            "projects": ["ViewBuddy.ai"],
        },
    )

    assert "Redis/cache" in move.question or "FastAPI" in move.question
    assert move.move_type in {
        InterviewMoveType.clarify,
        InterviewMoveType.deepen,
        InterviewMoveType.behavioral,
    }
