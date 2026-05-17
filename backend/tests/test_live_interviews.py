from fastapi.testclient import TestClient

from app.main import app


def test_live_interview_session_flow_accepts_transcript() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/live-interviews/sessions",
        json={
            "target_role": "AI Engineer",
            "mode": "technical",
            "difficulty": "intermediate",
            "question_count": 2,
        },
    )
    assert create_response.status_code == 201
    session = create_response.json()
    assert session["media"]["camera_required"] is True
    assert session["media"]["microphone_required"] is True

    next_response = client.post(
        f"/api/v1/live-interviews/sessions/{session['session_id']}/next-question"
    )
    assert next_response.status_code == 200
    question = next_response.json()["question"]
    assert question["question_text"]

    transcript_response = client.post(
        f"/api/v1/live-interviews/sessions/{session['session_id']}/transcript",
        json={
            "question_id": question["id"],
            "transcript": (
                "I would design this with FastAPI, background workers, "
                "and LLM evaluation."
            ),
            "duration_seconds": 45,
        },
    )
    assert transcript_response.status_code == 200
    assert transcript_response.json()["evaluation_status"] == "queued"
