from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from app.ai.models.base import ChatMessage, LLMClientError


class GeminiChatClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: int,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def stream_chat(
        self,
        *,
        messages: list[ChatMessage],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        prompt = "\n\n".join(f"{message.role.upper()}:\n{message.content}" for message in messages)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            yield text
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise LLMClientError("Gemini generation failed.") from exc
