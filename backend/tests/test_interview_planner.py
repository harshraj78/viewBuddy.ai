from app.ai.interview_planner import interview_planner
from app.schemas.live_interview import InterviewDifficulty, InterviewMode, StartLiveInterviewRequest


def test_interview_planner_generates_role_and_project_specific_questions() -> None:
    request = StartLiveInterviewRequest(
        target_role="AI Engineer",
        mode=InterviewMode.technical,
        difficulty=InterviewDifficulty.intermediate,
        target_company="Indian Product",
        candidate_skills=["FastAPI", "RAG", "PostgreSQL"],
        project_highlights=["ViewBuddy.ai live interview platform"],
        question_count=4,
    )

    questions = interview_planner.generate_seed_questions(
        request=request,
        session_seed="test-session",
    )

    question_text = " ".join(question.question_text for question in questions)
    assert len(questions) == 4
    assert "ViewBuddy.ai live interview platform" in question_text
    assert "FastAPI" in question_text
    assert len({question.question_text for question in questions}) == 4
