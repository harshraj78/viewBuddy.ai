from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app


def test_cors_origins_accept_comma_separated_env_value() -> None:
    settings = Settings(
        backend_cors_origins=(
            "https://view-buddy-ai.vercel.app, https://custom.example.com/"
        )
    )

    assert settings.cors_origins == [
        "https://view-buddy-ai.vercel.app",
        "https://custom.example.com",
    ]


def test_vercel_origin_preflight_is_allowed_by_default_regex() -> None:
    client = TestClient(app)

    response = client.options(
        "/api/v1/live-interviews/sessions",
        headers={
            "Origin": "https://view-buddy-ai.vercel.app",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
