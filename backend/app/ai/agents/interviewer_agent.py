from __future__ import annotations

from collections.abc import AsyncIterator

from app.ai.models import ChatMessage, LLMClientError, get_interview_llm_client


class InterviewerAgent:
    async def stream_response(
        self,
        *,
        current_question: str,
        transcript: str,
        personality: str,
        memory: list[dict],
        interview_context: dict[str, object],
        planned_move: dict[str, object],
    ) -> AsyncIterator[str]:
        messages = self._build_messages(
            current_question=current_question,
            transcript=transcript,
            personality=personality,
            memory=memory,
            interview_context=interview_context,
            planned_move=planned_move,
        )
        client = get_interview_llm_client()
        try:
            async for chunk in client.stream_chat(
                messages=messages,
                temperature=0.55,
                max_tokens=180,
            ):
                yield chunk
        except LLMClientError:
            raise

    def _build_messages(
        self,
        *,
        current_question: str,
        transcript: str,
        personality: str,
        memory: list[dict],
        interview_context: dict[str, object],
        planned_move: dict[str, object],
    ) -> list[ChatMessage]:
        system_prompt = f"""
You are ViewBuddy.ai's realtime AI interviewer.

Personality: {personality}

Behavior rules:
- Act like a senior human interviewer, not a questionnaire generator.
- Ask exactly one next question.
- Follow the planned interviewer move and intent.
- Challenge vague answers without being rude.
- Reference earlier answers when useful.
- Do not score the candidate during the live interview.
- Keep responses short enough for voice output.
- Avoid generic questions like "tell me more"; ask a concrete probe.
"""
        user_prompt = f"""
Current question:
{current_question}

Candidate answer:
{transcript}

Interview context and brain state:
{interview_context}

Planned interviewer move:
{planned_move}

Recent conversation memory:
{memory[-8:]}

Write the next interviewer question only. You may include one brief transition sentence.
"""
        return [
            ChatMessage(role="system", content=system_prompt.strip()),
            ChatMessage(role="user", content=user_prompt.strip()),
        ]


interviewer_agent = InterviewerAgent()
