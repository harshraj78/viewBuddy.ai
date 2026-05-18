import json
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings


class LLMProviderError(RuntimeError):
    pass


class LLMProvider(ABC):
    @abstractmethod
    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        raise NotImplementedError


class OpenAIChatProvider(LLMProvider):
    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not settings.openai_api_key:
            raise LLMProviderError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": settings.openai_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=settings.llm_request_timeout_seconds) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code >= 400:
            raise LLMProviderError(f"OpenAI request failed with status {response.status_code}.")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "openai":
        return OpenAIChatProvider()
    raise LLMProviderError(f"Unsupported LLM provider: {settings.llm_provider}")
