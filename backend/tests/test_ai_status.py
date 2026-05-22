from fastapi.testclient import TestClient

from app.main import app


def test_ai_status_does_not_expose_secret_values() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai/status")

    assert response.status_code == 200
    payload = response.json()
    assert "gemini_key_configured" in payload
    assert "GEMINI_API_KEY" not in payload
    assert "api_key" not in payload
