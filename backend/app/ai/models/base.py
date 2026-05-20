from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class LLMClientError(RuntimeError):
    pass


class LLMClient(Protocol):
    async def stream_chat(
        self,
        *,
        messages: list[ChatMessage],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        raise NotImplementedError
