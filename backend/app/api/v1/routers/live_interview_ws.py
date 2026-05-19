from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ai.conversation import ai_conversation_engine
from app.schemas.live_interview import InterviewRuntimeState, WebSocketEvent, WebSocketEventType
from app.services.live_interview_service import live_interview_service

router = APIRouter(prefix="/live-interviews", tags=["live interview websocket"])


@router.websocket("/sessions/{session_id}/ws")
async def live_interview_websocket(websocket: WebSocket, session_id: UUID) -> None:
    await websocket.accept()
    try:
        session = live_interview_service.get_runtime_session(session_id)
        await _send_event(
            websocket,
            WebSocketEventType.session_start,
            {
                "session_id": str(session.session_id),
                "state": session.runtime_state.value,
            },
        )
        live_interview_service.transition_runtime_state(
            session_id,
            InterviewRuntimeState.introduction,
        )
        await _send_event(
            websocket,
            WebSocketEventType.state_transition,
            {"state": InterviewRuntimeState.introduction.value},
        )
        await _send_event(
            websocket,
            WebSocketEventType.ai_response_chunk,
            {
                "text": (
                    "Welcome. I will ask one question at a time. "
                    "Answer naturally and I may ask follow-ups."
                )
            },
        )

        while True:
            raw_event = await websocket.receive_json()
            event = WebSocketEvent.model_validate(raw_event)
            if event.type == WebSocketEventType.transcript_chunk:
                await _handle_transcript_chunk(websocket, session_id, event)
            elif event.type == WebSocketEventType.interview_complete:
                live_interview_service.transition_runtime_state(
                    session_id,
                    InterviewRuntimeState.feedback_generation,
                )
                await _send_event(
                    websocket,
                    WebSocketEventType.state_transition,
                    {"state": InterviewRuntimeState.feedback_generation.value},
                )
                live_interview_service.transition_runtime_state(
                    session_id,
                    InterviewRuntimeState.completed,
                )
                await _send_event(
                    websocket,
                    WebSocketEventType.interview_complete,
                    {"state": InterviewRuntimeState.completed.value},
                )
                return
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await _send_event(
            websocket,
            WebSocketEventType.error,
            {"message": str(exc)},
        )


async def _handle_transcript_chunk(
    websocket: WebSocket,
    session_id: UUID,
    event: WebSocketEvent,
) -> None:
    transcript = str(event.payload.get("transcript", "")).strip()
    question_text = str(event.payload.get("question", "")).strip()
    personality = str(event.payload.get("personality", "Friendly"))
    if not transcript:
        return

    session = live_interview_service.get_runtime_session(session_id)
    live_interview_service.append_memory(
        session_id,
        speaker="candidate",
        message=transcript,
    )
    live_interview_service.transition_runtime_state(session_id, InterviewRuntimeState.follow_up)
    await _send_event(
        websocket,
        WebSocketEventType.state_transition,
        {"state": InterviewRuntimeState.follow_up.value},
    )

    chunks = []
    async for chunk in ai_conversation_engine.stream_followup(
        current_question=question_text,
        transcript=transcript,
        personality=personality,
        memory=session.memory,
    ):
        chunks.append(chunk)
        await _send_event(websocket, WebSocketEventType.ai_response_chunk, {"text": chunk})

    followup = " ".join(chunks).strip()
    live_interview_service.append_memory(session_id, speaker="interviewer", message=followup)
    followup_question = live_interview_service.add_followup_question(session_id, followup)
    await _send_event(
        websocket,
        WebSocketEventType.followup_question,
        {
            "question": followup,
            "question_id": str(followup_question.id),
            "question_type": followup_question.question_type,
        },
    )


async def _send_event(websocket: WebSocket, event_type: WebSocketEventType, payload: dict) -> None:
    event = WebSocketEvent(type=event_type, payload=payload)
    await websocket.send_json(event.model_dump(mode="json"))
