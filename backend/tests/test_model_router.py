import pytest

from app.ai.models.openai_compatible import OpenAICompatibleChatClient
from app.ai.models.router import get_interview_llm_client
from app.core.config import settings


def test_interview_model_router_builds_openai_compatible_client(monkeypatch) -> None:
    monkeypatch.setattr(settings, "interview_llm_provider", "local")
    monkeypatch.setattr(settings, "local_llm_base_url", "http://localhost:8001/v1")
    monkeypatch.setattr(settings, "local_llm_api_key", "EMPTY")
    monkeypatch.setattr(settings, "local_llm_model", "interview-llm")

    client = get_interview_llm_client()

    assert isinstance(client, OpenAICompatibleChatClient)
    assert client.base_url == "http://localhost:8001/v1"
    assert client.model == "interview-llm"


@pytest.mark.asyncio
async def test_conversation_falls_back_when_local_model_is_unavailable(monkeypatch) -> None:
    from app.ai.conversation import AIConversationEngine

    monkeypatch.setattr(settings, "interview_llm_provider", "local")
    monkeypatch.setattr(settings, "local_llm_base_url", "http://127.0.0.1:9/v1")
    monkeypatch.setattr(settings, "llm_request_timeout_seconds", 1)

    chunks = [
        chunk
        async for chunk in AIConversationEngine().stream_followup(
            current_question="Tell me about your project.",
            transcript="I used Redis caching to reduce latency.",
            personality="Strict",
            memory=[],
            interview_context={
                "target_role": "Backend Engineer",
                "skills": ["Redis"],
                "projects": ["ViewBuddy.ai"],
            },
            planned_move={
                "move_type": "scaling",
                "question": "What cache metric would fail first at 100x traffic?",
            },
        )
    ]

    assert "cache metric" in " ".join(chunks).lower()
