import asyncio

import httpx

from app.core.config import settings


class AIConversationEngine:
    async def stream_followup(
        self,
        *,
        current_question: str,
        transcript: str,
        personality: str,
        memory: list[dict],
    ):
        if settings.gemini_api_key:
            try:
                async for chunk in self._stream_gemini_followup(
                    current_question=current_question,
                    transcript=transcript,
                    personality=personality,
                    memory=memory,
                ):
                    yield chunk
                return
            except (httpx.HTTPError, KeyError, TypeError, ValueError):
                pass

        async for chunk in self._stream_fallback_followup(
            current_question=current_question,
            transcript=transcript,
            personality=personality,
            memory=memory,
        ):
            yield chunk

    async def _stream_gemini_followup(
        self,
        *,
        current_question: str,
        transcript: str,
        personality: str,
        memory: list[dict],
    ):
        prompt = self._build_followup_prompt(current_question, transcript, personality, memory)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.45,
                "maxOutputTokens": 160,
            },
        }

        async with httpx.AsyncClient(timeout=settings.llm_request_timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        for chunk in self._chunk_text(text):
            await asyncio.sleep(0)
            yield chunk

    async def _stream_fallback_followup(
        self,
        *,
        current_question: str,
        transcript: str,
        personality: str,
        memory: list[dict],
    ):
        lower_transcript = transcript.lower()
        recent_interviewer_questions = [
            item["message"].lower()
            for item in memory[-8:]
            if item.get("speaker") == "interviewer"
        ]
        if "redis" in lower_transcript or "cache" in lower_transcript:
            response = "What cache invalidation strategy did you use, and how did you test it?"
        elif "api" in lower_transcript or "fastapi" in lower_transcript:
            response = "How would you handle authentication, rate limits, and failures in that API?"
        elif "database" in lower_transcript or "postgres" in lower_transcript:
            response = "What indexes or schema choices would matter most as usage grows?"
        elif len(transcript.split()) < 35:
            response = (
                "Your answer is a little high level. "
                "Can you give me one concrete implementation detail?"
            )
        else:
            response = (
                "Good. Now tell me the main tradeoff you made and "
                "what you would improve next."
            )

        if any(response.lower()[:45] in question for question in recent_interviewer_questions):
            response = (
                "Let us go one level deeper. What was the hardest failure case, "
                "and how would you detect it in production?"
            )

        if personality == "FAANG pressure":
            response = f"Be specific and keep it structured. {response}"
        elif personality == "Strict":
            response = f"I want a precise answer. {response}"
        elif personality == "Friendly":
            response = f"That is a good start. {response}"

        for chunk in self._chunk_text(response):
            await asyncio.sleep(0.05)
            yield chunk

    def _build_followup_prompt(
        self,
        current_question: str,
        transcript: str,
        personality: str,
        memory: list[dict],
    ) -> str:
        return f"""
You are a professional AI interviewer.
Personality: {personality}

Ask exactly one concise follow-up question based on the candidate answer.
Challenge vague responses. Avoid repeating recent questions. Do not give feedback yet.
Use a natural interviewer transition, then ask the follow-up.

Current question:
{current_question}

Candidate answer:
{transcript}

Recent memory:
{memory[-6:]}
"""

    def _chunk_text(self, text: str, size: int = 18) -> list[str]:
        words = text.split()
        return [" ".join(words[index : index + size]) for index in range(0, len(words), size)]


ai_conversation_engine = AIConversationEngine()
