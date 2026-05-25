from dataclasses import dataclass, field
from uuid import UUID, uuid4

from fastapi import status

from app.ai.agents.analyzer_agent import candidate_analyzer_agent
from app.ai.agents.memory_agent import memory_manager_agent
from app.ai.agents.planner_agent import interview_planner_agent
from app.ai.agents.strategist_agent import followup_strategist_agent
from app.ai.evaluators import interview_answer_evaluator
from app.ai.interview_brain import (
    AnswerAnalysis,
    InterviewBrainState,
    InterviewMove,
)
from app.ai.interview_planner import interview_planner
from app.ai.models import LLMClientError
from app.core.config import settings
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
    topic_roadmap: list[LiveInterviewQuestion] = field(default_factory=list)
    transcripts: dict[UUID, AnswerTranscriptRequest] = field(default_factory=dict)
    memory: list[dict[str, str]] = field(default_factory=list)
    answer_signals: list[str] = field(default_factory=list)
    brain_state: InterviewBrainState = field(default_factory=InterviewBrainState)
    latest_analysis: AnswerAnalysis | None = None
    latest_move: InterviewMove | None = None
    processed_event_ids: set[str] = field(default_factory=set)
    live_transcript_buffer: str = ""
    last_interim_transcript: str = ""
    last_interrupt_signature: str | None = None


class LiveInterviewService:
    def __init__(self) -> None:
        self._sessions: dict[UUID, LiveInterviewSession] = {}

    async def start_session(
        self,
        request: StartLiveInterviewRequest,
    ) -> LiveInterviewSessionResponse:
        session_id = uuid4()
        planned_questions = await self._generate_questions(
            request=request,
            session_seed=str(session_id),
        )
        session = LiveInterviewSession(
            session_id=session_id,
            request=request,
            questions=planned_questions[:1],
            topic_roadmap=planned_questions[1:],
        )
        self._sessions[session_id] = session
        return self._to_response(session)

    async def _generate_questions(
        self,
        *,
        request: StartLiveInterviewRequest,
        session_seed: str,
    ) -> list[LiveInterviewQuestion]:
        fallback_questions = interview_planner.generate_seed_questions(
            request=request,
            session_seed=session_seed,
        )
        if settings.interview_llm_provider.lower() == "fallback":
            return fallback_questions

        try:
            profile = interview_planner.build_profile(request)
            ai_plan = await interview_planner_agent.generate_question_plan(
                profile=profile,
                question_count=request.question_count,
            )
            ai_questions = interview_planner.build_questions_from_plan(
                planned_questions=ai_plan,
            )
        except LLMClientError:
            return fallback_questions

        if len(ai_questions) < request.question_count:
            used = {question.question_text.lower() for question in ai_questions}
            ai_questions.extend(
                question
                for question in fallback_questions
                if question.question_text.lower() not in used
            )
        return ai_questions[: request.question_count]

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
        if speaker == "candidate":
            memory_manager_agent.update_answer_signals(
                existing=session.answer_signals,
                transcript=message,
            )

    def get_interview_context(self, session_id: UUID) -> dict[str, object]:
        session = self._get_session(session_id)
        profile = interview_planner.build_profile(session.request).as_prompt_context()
        return {
            **profile,
            "answer_signals": session.answer_signals[-8:],
            "brain_state": {
                "candidate_strengths": session.brain_state.candidate_strengths[-8:],
                "weak_areas": session.brain_state.weak_areas[-8:],
                "answered_topics": session.brain_state.answered_topics[-8:],
                "technologies": session.brain_state.technologies[-8:],
                "average_depth": session.brain_state.average_depth,
                "average_confidence": session.brain_state.average_confidence,
                "current_strategy": session.brain_state.current_strategy,
                "last_interviewer_intent": session.brain_state.last_interviewer_intent,
            },
            "asked_questions": [
                item["message"]
                for item in session.memory
                if item.get("speaker") == "interviewer"
            ][-8:],
        }

    def process_candidate_answer(
        self,
        session_id: UUID,
        *,
        current_question: str,
        transcript: str,
    ) -> InterviewMove:
        session = self._get_session(session_id)
        context = self.get_interview_context(session_id)
        analysis = candidate_analyzer_agent.analyze(
            current_question=current_question,
            transcript=transcript,
            interview_context=context,
        )
        move = followup_strategist_agent.update_and_plan(
            state=session.brain_state,
            analysis=analysis,
            interview_context=context,
        )
        session.latest_analysis = analysis
        session.latest_move = move
        return move

    def mark_event_processed(self, session_id: UUID, event_id: str | None) -> bool:
        if not event_id:
            return True

        session = self._get_session(session_id)
        if event_id in session.processed_event_ids:
            return False

        session.processed_event_ids.add(event_id)
        return True

    def update_live_transcript(
        self,
        session_id: UUID,
        *,
        transcript: str,
        is_final: bool = False,
    ) -> str:
        session = self._get_session(session_id)
        cleaned = " ".join(transcript.split())
        if not cleaned:
            return session.live_transcript_buffer

        if is_final:
            session.live_transcript_buffer = cleaned
            session.last_interim_transcript = ""
            return session.live_transcript_buffer

        session.last_interim_transcript = cleaned
        if len(cleaned) > len(session.live_transcript_buffer):
            session.live_transcript_buffer = cleaned
        return session.live_transcript_buffer

    def clear_live_transcript(self, session_id: UUID) -> None:
        session = self._get_session(session_id)
        session.live_transcript_buffer = ""
        session.last_interim_transcript = ""
        session.last_interrupt_signature = None

    def plan_live_interrupt(self, session_id: UUID, transcript: str) -> dict[str, str] | None:
        session = self._get_session(session_id)
        words = transcript.split()
        if len(words) < 32:
            return None

        lowered = transcript.lower()
        vague_markers = ("basically", "kind of", "somehow", "stuff", "things", "maybe", "i think")
        structure_markers = (
            "because",
            "tradeoff",
            "latency",
            "scale",
            "metric",
            "failure",
            "debug",
        )
        vague_count = sum(marker in lowered for marker in vague_markers)
        has_structure = any(marker in lowered for marker in structure_markers)

        if vague_count >= 2:
            signature = "vague"
            message = (
                "Pause for a second. Give me one concrete implementation detail, "
                "not a high-level summary."
            )
            reason = "vague_answer"
        elif len(words) >= 80 and not has_structure:
            signature = "unstructured"
            message = (
                "Let me redirect you. What was the exact tradeoff or failure mode "
                "you handled there?"
            )
            reason = "missing_tradeoff"
        else:
            return None

        if session.last_interrupt_signature == signature:
            return None

        session.last_interrupt_signature = signature
        return {"message": message, "reason": reason}

    def add_followup_question(
        self,
        session_id: UUID,
        question_text: str,
        *,
        question_type: str = "follow_up",
    ) -> LiveInterviewQuestion:
        session = self._get_session(session_id)
        question = LiveInterviewQuestion(
            id=uuid4(),
            order_index=len(session.questions) + 1,
            question_text=question_text,
            question_type=question_type,
            expected_answer_seconds=90,
            preparation_seconds=5,
        )
        session.questions.append(question)
        session.current_index = len(session.questions)
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

        if session.current_index >= len(session.questions) and session.topic_roadmap:
            session.questions.append(session.topic_roadmap.pop(0))

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
