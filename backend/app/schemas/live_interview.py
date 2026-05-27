from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class InterviewMode(StrEnum):
    technical = "technical"
    behavioral = "behavioral"
    hr = "hr"
    dsa = "dsa"
    system_design = "system_design"


class InterviewDifficulty(StrEnum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class LiveInterviewStatus(StrEnum):
    created = "created"
    in_progress = "in_progress"
    completed = "completed"


class InterviewRuntimeState(StrEnum):
    setup = "SETUP"
    waiting_room = "WAITING_ROOM"
    introduction = "INTRODUCTION"
    questioning = "QUESTIONING"
    follow_up = "FOLLOW_UP"
    coding_round = "CODING_ROUND"
    system_design = "SYSTEM_DESIGN"
    feedback_generation = "FEEDBACK_GENERATION"
    completed = "COMPLETED"


class InterviewTurnState(StrEnum):
    idle = "IDLE"
    introducing = "INTRODUCING"
    asking_question = "ASKING_QUESTION"
    listening = "LISTENING"
    processing = "PROCESSING"
    responding = "RESPONDING"
    followup = "FOLLOWUP"
    ending = "ENDING"


class MediaRequirement(BaseModel):
    camera_required: bool = True
    microphone_required: bool = True
    recording_required: bool = True
    transcription_required: bool = True


class StartLiveInterviewRequest(BaseModel):
    candidate_name: str = Field(default="Candidate", min_length=1, max_length=120)
    target_role: str = Field(default="AI Engineer", min_length=2, max_length=120)
    mode: InterviewMode = InterviewMode.technical
    difficulty: InterviewDifficulty = InterviewDifficulty.intermediate
    target_company: str | None = Field(default=None, max_length=120)
    interviewer_name: str = Field(default="Sarah", min_length=1, max_length=80)
    interviewer_persona: str = Field(default="Basic Interviewer", max_length=120)
    interviewer_accent: str = Field(default="US American", max_length=80)
    interview_duration_minutes: int = Field(default=45, ge=5, le=120)
    resume_id: UUID | None = None
    candidate_skills: list[str] = Field(default_factory=list, max_length=12)
    project_highlights: list[str] = Field(default_factory=list, max_length=8)
    resume_summary: str | None = Field(default=None, max_length=12000)
    question_count: int = Field(default=5, ge=1, le=12)


class LiveInterviewQuestion(BaseModel):
    id: UUID
    order_index: int
    question_text: str
    question_type: str
    expected_answer_seconds: int
    preparation_seconds: int


class LiveInterviewSessionResponse(BaseModel):
    session_id: UUID
    status: LiveInterviewStatus
    target_role: str
    mode: InterviewMode
    difficulty: InterviewDifficulty
    media: MediaRequirement
    websocket_path: str
    current_question: LiveInterviewQuestion | None = None


class NextQuestionResponse(BaseModel):
    session_id: UUID
    status: LiveInterviewStatus
    question: LiveInterviewQuestion | None
    remaining_questions: int


class AnswerTranscriptRequest(BaseModel):
    question_id: UUID
    transcript: str = Field(min_length=1, max_length=8000)
    duration_seconds: int = Field(ge=1, le=900)


class AnswerTranscriptResponse(BaseModel):
    session_id: UUID
    question_id: UUID
    accepted: bool
    evaluation_status: str
    next_action: str


class ReportSection(BaseModel):
    score: int = Field(ge=0, le=100)
    strengths: list[str]
    improvements: list[str]


class TranscriptReplayItem(BaseModel):
    question_id: UUID
    question_text: str
    transcript: str
    duration_seconds: int


class FeedbackReportResponse(BaseModel):
    session_id: UUID
    overall_score: int = Field(ge=0, le=100)
    communication: ReportSection
    technical: ReportSection
    behavioral: ReportSection
    replay: list[TranscriptReplayItem]
    improvement_suggestions: list[str]
    evaluator: str
    prompt_version: str


class WebSocketEventType(StrEnum):
    session_start = "session_start"
    transcript_delta = "transcript_delta"
    transcript_final = "transcript_final"
    transcript_chunk = "transcript_chunk"
    ai_response_chunk = "ai_response_chunk"
    interviewer_interrupt = "interviewer_interrupt"
    interviewer_question = "interviewer_question"
    followup_question = "followup_question"
    state_transition = "state_transition"
    interview_complete = "interview_complete"
    error = "error"


class WebSocketEvent(BaseModel):
    type: WebSocketEventType
    payload: dict = Field(default_factory=dict)
    event_id: str | None = None
