from app.ai.models.base import LLMClient, LLMClientError
from app.ai.models.gemini import GeminiChatClient
from app.ai.models.openai_compatible import OpenAICompatibleChatClient
from app.core.config import settings


def get_interview_llm_client() -> LLMClient:
    provider = settings.interview_llm_provider.lower()
    if provider in {"local", "vllm", "openai_compatible"}:
        return OpenAICompatibleChatClient(
            base_url=settings.local_llm_base_url,
            api_key=settings.local_llm_api_key,
            model=settings.local_llm_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise LLMClientError("GEMINI_API_KEY is not configured.")
        return GeminiChatClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )
    raise LLMClientError(f"Unsupported interview LLM provider: {settings.interview_llm_provider}")
