import asyncio
import logging

from app.ai.agents.interviewer_agent import interviewer_agent
from app.ai.models import LLMClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIConversationEngine:
    async def stream_followup(
        self,
        *,
        current_question: str,
        transcript: str,
        personality: str,
        memory: list[dict],
        interview_context: dict[str, object] | None = None,
        planned_move: dict[str, object] | None = None,
    ):
        context = interview_context or {}
        move = planned_move or {}
        if settings.interview_llm_provider.lower() != "fallback":
            try:
                async for chunk in interviewer_agent.stream_response(
                    current_question=current_question,
                    transcript=transcript,
                    personality=personality,
                    memory=memory,
                    interview_context=context,
                    planned_move=move,
                ):
                    yield chunk
                return
            except LLMClientError as exc:
                logger.warning(
                    "Interview LLM provider '%s' failed; using deterministic fallback. Reason: %s",
                    settings.interview_llm_provider,
                    exc,
                )

        async for chunk in self._stream_fallback_followup(
            current_question=current_question,
            transcript=transcript,
            personality=personality,
            memory=memory,
            interview_context=context,
            planned_move=move,
        ):
            yield chunk

    async def _stream_fallback_followup(
        self,
        *,
        current_question: str,
        transcript: str,
        personality: str,
        memory: list[dict],
        interview_context: dict[str, object],
        planned_move: dict[str, object],
    ):
        if planned_move.get("question"):
            response = str(planned_move["question"])
            if personality == "FAANG pressure":
                response = f"Good, I am going to raise the bar a bit. {response}"
            elif personality == "Strict":
                response = f"I am going to hold you to the implementation detail here. {response}"
            elif personality == "Friendly":
                response = f"That direction makes sense. {response}"
            for chunk in self._chunk_text(response):
                await asyncio.sleep(0.05)
                yield chunk
            return

        lower_transcript = transcript.lower()
        role = str(interview_context.get("target_role", "candidate"))
        company_style = str(interview_context.get("company_style", "product company"))
        skills = [str(skill) for skill in interview_context.get("skills", [])]
        projects = [str(project) for project in interview_context.get("projects", [])]
        answer_signals = [str(signal) for signal in interview_context.get("answer_signals", [])]
        has_resume_memory = bool(interview_context.get("resume_summary"))
        primary_skill = skills[0] if skills else "your main technical skill"
        primary_project = projects[0] if projects else "that project"
        recent_interviewer_questions = [
            item["message"].lower()
            for item in memory[-8:]
            if item.get("speaker") == "interviewer"
        ]
        if "redis" in lower_transcript or "cache" in lower_transcript:
            response = (
                f"For {primary_project}, what cache invalidation strategy did you use, "
                "and what metric proved it was safe?"
            )
        elif has_resume_memory and len(transcript.split()) < 35:
            response = (
                f"I want this grounded in your resume. Pick one concrete decision from "
                f"{primary_project} and explain the tradeoff, not just the outcome."
            )
        elif "api" in lower_transcript or "fastapi" in lower_transcript:
            response = (
                f"As a {role}, why choose that API approach over a simpler framework, "
                "and how would you handle auth, rate limits, and failure cases?"
            )
        elif "database" in lower_transcript or "postgres" in lower_transcript:
            response = (
                f"In {primary_project}, which query or table would become slow first, "
                "and what index or schema change would you make?"
            )
        elif "llm" in lower_transcript or "prompt" in lower_transcript or "rag" in lower_transcript:
            response = (
                f"How would you evaluate whether the {primary_skill} AI behavior is actually "
                "improving candidate outcomes instead of only sounding better?"
            )
        elif any(term in lower_transcript for term in ("async", "worker", "queue")):
            response = (
                f"What should run synchronously versus in the background for a {company_style} "
                "production launch, and how would you recover failed jobs?"
            )
        elif len(transcript.split()) < 35:
            response = (
                f"Your answer is still high level for a {role} round. "
                f"Give me one concrete implementation detail from {primary_project}."
            )
        elif answer_signals:
            response = (
                f"You mentioned {answer_signals[-1]}. What was the hardest edge case there, "
                "and how did you know your solution worked?"
            )
        else:
            response = (
                f"Good. Now connect that answer to {primary_skill}: what tradeoff did you make, "
                "and what would you improve if you rebuilt it?"
            )

        if any(response.lower()[:45] in question for question in recent_interviewer_questions):
            response = (
                "Let us shift from the happy path. What was the hardest failure case, "
                "and how would you detect it in production?"
            )

        if personality == "FAANG pressure":
            response = f"Keep it tight and specific. {response}"
        elif personality == "Strict":
            response = f"I am looking for the exact reasoning. {response}"
        elif personality == "Friendly":
            response = f"That is a reasonable start. {response}"

        for chunk in self._chunk_text(response):
            await asyncio.sleep(0.05)
            yield chunk

    def _chunk_text(self, text: str, size: int = 18) -> list[str]:
        words = text.split()
        return [" ".join(words[index : index + size]) for index in range(0, len(words), size)]


ai_conversation_engine = AIConversationEngine()
