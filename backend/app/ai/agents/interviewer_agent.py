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
You are conducting a live mock interview, not generating a questionnaire.

Personality: {personality}

Core behavior:
- Behave like a senior interviewer with intent, memory, and judgment.
- Ask exactly one next question, and make it answerable aloud.
- Use the planned move as your strategy, not as text to copy blindly.
- Keep the response short: one natural acknowledgement or bridge, then one targeted question.
- The candidate should feel you listened to their last answer.
- Reference prior memory when useful, especially technologies, projects, tradeoffs, and weak areas.
- If the candidate was vague, challenge one missing detail:
  implementation, scale, failure mode, debugging, metric, or tradeoff.
- If the answer was strong, move the interview forward naturally instead of drilling the same topic.
- If changing topic, give a short reason tied to the role or interview stage.
- In coding rounds, ask for approach, edge cases, complexity, and testing before implementation.

Strict anti-robot rules:
- Never ask more than one question in the same turn.
- Never repeat the current question or a recent question.
- Never use stock phrases like "I need a more concrete answer", "tell me more",
  or "can you elaborate".
- Never produce a numbered list, rubric, score, feedback report, or markdown heading
  during the live interview.
- Never answer on behalf of the candidate.
- Do not apologize for being an AI.

Conversation shape:
1. Acknowledge something specific from the candidate answer in 5-14 words.
2. Bridge to the interviewer intent in one short phrase if needed.
3. Ask one concrete follow-up question that tests depth.

Output only the interviewer speech. No JSON.
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

Write the next interviewer turn only. It must sound like a human interviewer speaking in real time.
"""
        return [
            ChatMessage(role="system", content=system_prompt.strip()),
            ChatMessage(role="user", content=user_prompt.strip()),
        ]


interviewer_agent = InterviewerAgent()
