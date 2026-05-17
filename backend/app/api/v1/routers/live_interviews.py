from uuid import UUID

from fastapi import APIRouter, status

from app.schemas.live_interview import (
    AnswerTranscriptRequest,
    AnswerTranscriptResponse,
    LiveInterviewSessionResponse,
    NextQuestionResponse,
    StartLiveInterviewRequest,
)
from app.services.live_interview_service import live_interview_service

router = APIRouter(prefix="/live-interviews", tags=["live interviews"])


@router.post(
    "/sessions",
    response_model=LiveInterviewSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_live_interview(request: StartLiveInterviewRequest) -> LiveInterviewSessionResponse:
    return live_interview_service.start_session(request)


@router.get("/sessions/{session_id}", response_model=LiveInterviewSessionResponse)
def get_live_interview(session_id: UUID) -> LiveInterviewSessionResponse:
    return live_interview_service.get_session(session_id)


@router.post("/sessions/{session_id}/next-question", response_model=NextQuestionResponse)
def get_next_question(session_id: UUID) -> NextQuestionResponse:
    return live_interview_service.next_question(session_id)


@router.post("/sessions/{session_id}/transcript", response_model=AnswerTranscriptResponse)
def submit_answer_transcript(
    session_id: UUID,
    request: AnswerTranscriptRequest,
) -> AnswerTranscriptResponse:
    return live_interview_service.submit_transcript(session_id, request)

