from dataclasses import dataclass, field
from uuid import UUID, uuid4

from fastapi import status

from app.ai.evaluators import interview_answer_evaluator
from app.core.errors import AppError
from app.schemas.live_interview import (
    AnswerTranscriptRequest,
    AnswerTranscriptResponse,
    FeedbackReportResponse,
    InterviewRuntimeState,
    LiveInterviewQuestion,
    LiveInterviewSessionResponse,
    LiveInterviewStatus,
    MediaRequirement,
    NextQuestionResponse,
    StartLiveInterviewRequest,
    TranscriptReplayItem,
)
from app.services.interview_state_machine import interview_state_machine


@dataclass
class LiveInterviewSession:
    session_id: UUID
    request: StartLiveInterviewRequest
    status: LiveInterviewStatus = LiveInterviewStatus.created
    runtime_state: InterviewRuntimeState = InterviewRuntimeState.setup
    current_index: int = 0
    questions: list[LiveInterviewQuestion] = field(default_factory=list)
    transcripts: dict[UUID, AnswerTranscriptRequest] = field(default_factory=dict)
    memory: list[dict[str, str]] = field(default_factory=list)
    processed_event_ids: set[str] = field(default_factory=set)


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

    def get_runtime_session(self, session_id: UUID) -> LiveInterviewSession:
        return self._get_session(session_id)

    def transition_runtime_state(
        self,
        session_id: UUID,
        next_state: InterviewRuntimeState,
    ) -> InterviewRuntimeState:
        session = self._get_session(session_id)
        session.runtime_state = interview_state_machine.transition(
            session.runtime_state,
            next_state,
        )
        return session.runtime_state

    def append_memory(self, session_id: UUID, *, speaker: str, message: str) -> None:
        session = self._get_session(session_id)
        session.memory.append({"speaker": speaker, "message": message})

    def mark_event_processed(self, session_id: UUID, event_id: str | None) -> bool:
        if not event_id:
            return True

        session = self._get_session(session_id)
        if event_id in session.processed_event_ids:
            return False

        session.processed_event_ids.add(event_id)
        return True

    def add_followup_question(self, session_id: UUID, question_text: str) -> LiveInterviewQuestion:
        session = self._get_session(session_id)
        question = LiveInterviewQuestion(
            id=uuid4(),
            order_index=len(session.questions) + 1,
            question_text=question_text,
            question_type="follow_up",
            expected_answer_seconds=90,
            preparation_seconds=5,
        )
        session.questions.append(question)
        return question

    def next_question(self, session_id: UUID) -> NextQuestionResponse:
        session = self._get_session(session_id)
        session.status = LiveInterviewStatus.in_progress
        if session.runtime_state == InterviewRuntimeState.setup:
            session.runtime_state = interview_state_machine.transition(
                session.runtime_state,
                InterviewRuntimeState.introduction,
            )
        if session.runtime_state in {
            InterviewRuntimeState.waiting_room,
            InterviewRuntimeState.introduction,
            InterviewRuntimeState.follow_up,
        }:
            session.runtime_state = interview_state_machine.transition(
                session.runtime_state,
                InterviewRuntimeState.questioning,
            )

        if session.current_index >= len(session.questions):
            session.status = LiveInterviewStatus.completed
            session.runtime_state = InterviewRuntimeState.feedback_generation
            return NextQuestionResponse(
                session_id=session.session_id,
                status=session.status,
                question=None,
                remaining_questions=0,
            )

        question = session.questions[session.current_index]
        session.memory.append({"speaker": "interviewer", "message": question.question_text})
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

    async def generate_report(self, session_id: UUID) -> FeedbackReportResponse:
        session = self._get_session(session_id)
        replay = self._build_replay(session)
        return await interview_answer_evaluator.evaluate(
            session_id=session.session_id,
            target_role=session.request.target_role,
            difficulty=session.request.difficulty,
            replay=replay,
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


live_interview_service = LiveInterviewService()
