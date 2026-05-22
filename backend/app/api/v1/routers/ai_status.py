from fastapi import APIRouter

from app.core.config import settings
from app.schemas.ai_status import AIStatusResponse

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status", response_model=AIStatusResponse)
def get_ai_status() -> AIStatusResponse:
    return AIStatusResponse(
        interview_llm_provider=settings.interview_llm_provider,
        interview_model=_active_interview_model(),
        gemini_key_configured=bool(settings.gemini_api_key),
        local_llm_base_url=settings.local_llm_base_url,
        local_llm_model=settings.local_llm_model,
        fallback_enabled=True,
    )


def _active_interview_model() -> str:
    provider = settings.interview_llm_provider.lower()
    if provider == "gemini":
        return settings.gemini_model
    if provider in {"local", "vllm", "openai_compatible"}:
        return settings.local_llm_model
    return "deterministic-fallback"
