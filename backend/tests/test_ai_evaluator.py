from uuid import uuid4

from app.ai.evaluators import InterviewAnswerEvaluator
from app.schemas.live_interview import TranscriptReplayItem


def test_fallback_evaluator_returns_scorecard() -> None:
    evaluator = InterviewAnswerEvaluator()
    session_id = uuid4()

    report = evaluator.evaluate_with_fallback(
        session_id=session_id,
        replay=[
            TranscriptReplayItem(
                question_id=uuid4(),
                question_text="How would you design this product?",
                transcript=(
                    "I would use FastAPI APIs, Postgres database storage, Redis queues, "
                    "RAG with vector search, prompt versioning, tests, and deployment safeguards."
                ),
                duration_seconds=90,
            )
        ],
    )

    assert report.session_id == session_id
    assert report.overall_score > 0
    assert report.technical.score > report.behavioral.score
    assert report.evaluator == "fallback"
