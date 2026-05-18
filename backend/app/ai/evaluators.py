from app.ai.prompts import (
    ANSWER_EVALUATION_PROMPT_VERSION,
    ANSWER_EVALUATION_SYSTEM_PROMPT,
    build_answer_evaluation_prompt,
)
from app.ai.providers import LLMProviderError, get_llm_provider
from app.core.config import settings
from app.schemas.live_interview import FeedbackReportResponse, ReportSection, TranscriptReplayItem


class InterviewAnswerEvaluator:
    async def evaluate(
        self,
        *,
        session_id,
        target_role: str,
        difficulty: str,
        replay: list[TranscriptReplayItem],
    ) -> FeedbackReportResponse:
        transcript = " ".join(item.transcript for item in replay)
        if settings.ai_evaluation_mode == "llm":
            try:
                return await self._evaluate_with_llm(
                    session_id=session_id,
                    target_role=target_role,
                    difficulty=difficulty,
                    replay=replay,
                    transcript=transcript,
                )
            except (LLMProviderError, KeyError, ValueError, TypeError):
                return self.evaluate_with_fallback(session_id=session_id, replay=replay)

        return self.evaluate_with_fallback(session_id=session_id, replay=replay)

    async def _evaluate_with_llm(
        self,
        *,
        session_id,
        target_role: str,
        difficulty: str,
        replay: list[TranscriptReplayItem],
        transcript: str,
    ) -> FeedbackReportResponse:
        provider = get_llm_provider()
        user_prompt = build_answer_evaluation_prompt(transcript, target_role, difficulty)
        data = await provider.generate_json(ANSWER_EVALUATION_SYSTEM_PROMPT, user_prompt)

        return FeedbackReportResponse(
            session_id=session_id,
            overall_score=int(data["overall_score"]),
            communication=ReportSection(**data["communication"]),
            technical=ReportSection(**data["technical"]),
            behavioral=ReportSection(**data["behavioral"]),
            replay=replay,
            improvement_suggestions=data["improvement_suggestions"],
            evaluator="llm",
            prompt_version=ANSWER_EVALUATION_PROMPT_VERSION,
        )

    def evaluate_with_fallback(
        self,
        *,
        session_id,
        replay: list[TranscriptReplayItem],
    ) -> FeedbackReportResponse:
        combined_transcript = " ".join(item.transcript for item in replay)
        word_count = len(combined_transcript.split())
        answered_count = len(replay)

        communication = self._score_communication(combined_transcript, answered_count)
        technical = self._score_technical(combined_transcript, answered_count)
        behavioral = self._score_behavioral(combined_transcript)
        overall_score = round(
            (communication.score * 0.35) + (technical.score * 0.45) + (behavioral.score * 0.20)
        )

        suggestions = [
            "Use a clear structure: context, approach, tradeoffs, result.",
            "Add concrete metrics or implementation details when explaining projects.",
            "Mention failure modes and production safeguards for AI systems.",
        ]
        if word_count < 80:
            suggestions.insert(0, "Give fuller answers; most responses are currently too short.")

        return FeedbackReportResponse(
            session_id=session_id,
            overall_score=overall_score,
            communication=communication,
            technical=technical,
            behavioral=behavioral,
            replay=replay,
            improvement_suggestions=suggestions,
            evaluator="fallback",
            prompt_version="deterministic-v1",
        )

    def _score_communication(self, transcript: str, answered_count: int) -> ReportSection:
        filler_words = ["um", "uh", "like", "basically", "actually", "you know"]
        lower_transcript = transcript.lower()
        filler_count = sum(lower_transcript.count(word) for word in filler_words)
        word_count = len(transcript.split())
        score = min(90, 45 + answered_count * 10 + min(word_count // 20, 20) - filler_count * 2)
        score = max(score, 20 if answered_count else 0)

        return ReportSection(
            score=score,
            strengths=[
                "Maintained interview flow with submitted responses.",
                "Provided enough signal for a first-pass communication review.",
            ],
            improvements=[
                "Reduce filler words and long pauses.",
                "Answer in a structured way so the interviewer can follow your thinking.",
            ],
        )

    def _score_technical(self, transcript: str, answered_count: int) -> ReportSection:
        technical_signals = [
            "api",
            "database",
            "postgres",
            "redis",
            "queue",
            "latency",
            "scal",
            "test",
            "deploy",
            "model",
            "prompt",
            "rag",
            "vector",
            "tradeoff",
        ]
        lower_transcript = transcript.lower()
        signal_hits = sum(1 for signal in technical_signals if signal in lower_transcript)
        score = min(95, 35 + answered_count * 8 + signal_hits * 5)

        return ReportSection(
            score=score,
            strengths=[
                "Touched relevant engineering concepts."
                if signal_hits
                else "Completed at least one technical response.",
            ],
            improvements=[
                "Discuss concrete architecture components, data flow, and failure handling.",
                "Use tradeoffs instead of only listing tools.",
            ],
        )

    def _score_behavioral(self, transcript: str) -> ReportSection:
        lower_transcript = transcript.lower()
        star_signals = ["situation", "task", "action", "result", "learned", "impact"]
        signal_hits = sum(1 for signal in star_signals if signal in lower_transcript)
        score = min(90, 45 + signal_hits * 8)

        return ReportSection(
            score=score,
            strengths=[
                "Shows potential for structured storytelling."
                if signal_hits
                else "Behavioral signal is limited but can improve quickly.",
            ],
            improvements=[
                "Use STAR: situation, task, action, result.",
                "Add what you learned and how it changed your next decision.",
            ],
        )


interview_answer_evaluator = InterviewAnswerEvaluator()

