from dataclasses import dataclass, field
from uuid import UUID, uuid4

from fastapi import status

from app.core.errors import AppError
from app.schemas.live_interview import (
    AnswerTranscriptRequest,
    AnswerTranscriptResponse,
    FeedbackReportResponse,
    LiveInterviewQuestion,
    LiveInterviewSessionResponse,
    LiveInterviewStatus,
    MediaRequirement,
    NextQuestionResponse,
    ReportSection,
    StartLiveInterviewRequest,
    TranscriptReplayItem,
)


@dataclass
class LiveInterviewSession:
    session_id: UUID
    request: StartLiveInterviewRequest
    status: LiveInterviewStatus = LiveInterviewStatus.created
    current_index: int = 0
    questions: list[LiveInterviewQuestion] = field(default_factory=list)
    transcripts: dict[UUID, AnswerTranscriptRequest] = field(default_factory=dict)


class LiveInterviewService:
    def __init__(self) -> None:
        self._sessions: dict[UUID, LiveInterviewSession] = {}

    def start_session(self, request: StartLiveInterviewRequest) -> LiveInterviewSessionResponse:
        session_id = uuid4()
        session = LiveInterviewSession(
            session_id=session_id,
            request=request,
            questions=self._generate_seed_questions(request),
        )
        self._sessions[session_id] = session
        return self._to_response(session)

    def get_session(self, session_id: UUID) -> LiveInterviewSessionResponse:
        return self._to_response(self._get_session(session_id))

    def next_question(self, session_id: UUID) -> NextQuestionResponse:
        session = self._get_session(session_id)
        session.status = LiveInterviewStatus.in_progress

        if session.current_index >= len(session.questions):
            session.status = LiveInterviewStatus.completed
            return NextQuestionResponse(
                session_id=session.session_id,
                status=session.status,
                question=None,
                remaining_questions=0,
            )

        question = session.questions[session.current_index]
        session.current_index += 1
        return NextQuestionResponse(
            session_id=session.session_id,
            status=session.status,
            question=question,
            remaining_questions=len(session.questions) - session.current_index,
        )

    def submit_transcript(
        self,
        session_id: UUID,
        request: AnswerTranscriptRequest,
    ) -> AnswerTranscriptResponse:
        session = self._get_session(session_id)
        question_ids = {question.id for question in session.questions}
        if request.question_id not in question_ids:
            raise AppError(
                code="QUESTION_NOT_IN_SESSION",
                message="The submitted question does not belong to this live interview session.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        session.transcripts[request.question_id] = request
        return AnswerTranscriptResponse(
            session_id=session.session_id,
            question_id=request.question_id,
            accepted=True,
            evaluation_status="ready_for_report",
            next_action="request_next_question",
        )

    def generate_report(self, session_id: UUID) -> FeedbackReportResponse:
        session = self._get_session(session_id)
        replay = self._build_replay(session)
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
            session_id=session.session_id,
            overall_score=overall_score,
            communication=communication,
            technical=technical,
            behavioral=behavioral,
            replay=replay,
            improvement_suggestions=suggestions,
        )

    def _get_session(self, session_id: UUID) -> LiveInterviewSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise AppError(
                code="LIVE_INTERVIEW_SESSION_NOT_FOUND",
                message="Live interview session was not found.",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return session

    def _to_response(self, session: LiveInterviewSession) -> LiveInterviewSessionResponse:
        current_question = None
        if 0 <= session.current_index - 1 < len(session.questions):
            current_question = session.questions[session.current_index - 1]

        return LiveInterviewSessionResponse(
            session_id=session.session_id,
            status=session.status,
            target_role=session.request.target_role,
            mode=session.request.mode,
            difficulty=session.request.difficulty,
            media=MediaRequirement(),
            websocket_path=f"/api/v1/live-interviews/sessions/{session.session_id}/ws",
            current_question=current_question,
        )

    def _generate_seed_questions(
        self,
        request: StartLiveInterviewRequest,
    ) -> list[LiveInterviewQuestion]:
        base_questions = [
            (
                "project_deep_dive",
                (
                    "Walk me through one project that proves you are ready for a "
                    f"{request.target_role} role."
                ),
            ),
            (
                "technical_depth",
                (
                    "Explain how you would design the AI evaluation pipeline for "
                    "this interview product."
                ),
            ),
            (
                "tradeoffs",
                "What tradeoffs would you consider when choosing between OpenAI, Groq, and Gemini?",
            ),
            (
                "production_readiness",
                "How would you make an LLM-powered interview system reliable in production?",
            ),
            (
                "behavioral",
                "Tell me about a time you had to learn a difficult technical topic quickly.",
            ),
        ]

        return [
            LiveInterviewQuestion(
                id=uuid4(),
                order_index=index,
                question_type=question_type,
                question_text=question_text,
                preparation_seconds=10,
                expected_answer_seconds=120,
            )
            for index, (question_type, question_text) in enumerate(
                base_questions[: request.question_count],
                start=1,
            )
        ]

    def _build_replay(self, session: LiveInterviewSession) -> list[TranscriptReplayItem]:
        questions_by_id = {question.id: question for question in session.questions}
        replay = []
        for question_id, answer in session.transcripts.items():
            question = questions_by_id[question_id]
            replay.append(
                TranscriptReplayItem(
                    question_id=question_id,
                    question_text=question.question_text,
                    transcript=answer.transcript,
                    duration_seconds=answer.duration_seconds,
                )
            )
        return replay

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


live_interview_service = LiveInterviewService()
