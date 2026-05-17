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


class MediaRequirement(BaseModel):
    camera_required: bool = True
    microphone_required: bool = True
    recording_required: bool = True
    transcription_required: bool = True


class StartLiveInterviewRequest(BaseModel):
    target_role: str = Field(default="AI Engineer", min_length=2, max_length=120)
    mode: InterviewMode = InterviewMode.technical
    difficulty: InterviewDifficulty = InterviewDifficulty.intermediate
    target_company: str | None = Field(default=None, max_length=120)
    resume_id: UUID | None = None
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

