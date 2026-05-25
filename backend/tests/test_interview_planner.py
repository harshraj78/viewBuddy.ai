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


def test_interview_planner_derives_memory_from_resume_context() -> None:
    request = StartLiveInterviewRequest(
        target_role="AI Engineer",
        mode=InterviewMode.technical,
        difficulty=InterviewDifficulty.intermediate,
        target_company="Startup",
        resume_summary=(
            "Built ViewBuddy.ai project using FastAPI, PostgreSQL, React, "
            "WebSockets, Gemini prompts, and RAG-style resume memory."
        ),
        question_count=3,
    )

    profile = interview_planner.build_profile(request)
    questions = interview_planner.generate_seed_questions(
        request=request,
        session_seed="resume-memory",
    )
    question_text = " ".join(question.question_text for question in questions)

    assert "FastAPI" in profile.skills
    assert profile.projects
    assert "resume context" in questions[0].question_text.lower()
    assert "FastAPI" in question_text


def test_interview_planner_generates_dsa_approach_first_questions() -> None:
    request = StartLiveInterviewRequest(
        target_role="SDE",
        mode=InterviewMode.dsa,
        difficulty=InterviewDifficulty.intermediate,
        target_company="FAANG",
        question_count=3,
    )

    questions = interview_planner.generate_seed_questions(
        request=request,
        session_seed="dsa-session",
    )
    question_text = " ".join(question.question_text.lower() for question in questions)

    assert "brute force" in question_text
    assert "optimized" in question_text
    assert "edge cases" in question_text
