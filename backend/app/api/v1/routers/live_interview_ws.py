from uuid import UUID, uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.ai.conversation import ai_conversation_engine
from app.schemas.live_interview import (
    InterviewRuntimeState,
    InterviewTurnState,
    WebSocketEvent,
    WebSocketEventType,
)
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
        if session.runtime_state in {
            InterviewRuntimeState.setup,
            InterviewRuntimeState.waiting_room,
        }:
            live_interview_service.transition_runtime_state(
                session_id,
                InterviewRuntimeState.introduction,
            )
            live_interview_service.set_turn_state(session_id, InterviewTurnState.introducing)
            await _send_state(websocket, InterviewRuntimeState.introduction)
            await _send_interviewer_text(
                websocket,
                (
                    "Welcome. I will ask one question at a time. "
                    "Answer naturally and I may ask follow-ups when I need more depth."
                ),
                message_role="introduction",
            )

        while True:
            raw_event = await websocket.receive_json()
            event = WebSocketEvent.model_validate(raw_event)
            if event.type == WebSocketEventType.transcript_delta:
                await _handle_transcript_delta(websocket, session_id, event)
            elif event.type in {
                WebSocketEventType.transcript_chunk,
                WebSocketEventType.transcript_final,
            }:
                await _handle_transcript_final(websocket, session_id, event)
            elif event.type == WebSocketEventType.interview_complete:
                await _complete_interview(websocket, session_id)
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


async def _handle_transcript_delta(
    websocket: WebSocket,
    session_id: UUID,
    event: WebSocketEvent,
) -> None:
    transcript = str(event.payload.get("transcript", "")).strip()
    if not transcript:
        return

    live_interview_service.update_live_transcript(
        session_id,
        transcript=transcript,
    )
    # Partial STT is memory-only. The interviewer must not respond until the
    # candidate answer is finalized; otherwise TTS can interrupt the candidate
    # and create duplicate overlapping generations.
    return


async def _handle_transcript_final(
    websocket: WebSocket,
    session_id: UUID,
    event: WebSocketEvent,
) -> None:
    generation_id = event.event_id or str(uuid4())
    if not live_interview_service.mark_event_processed(session_id, generation_id):
        await _send_event(
            websocket,
            WebSocketEventType.ai_response_chunk,
            {
                "text": "",
                "is_duplicate": True,
                "message_role": "dedupe",
            },
        )
        return
    if not await live_interview_service.begin_generation(session_id, generation_id):
        await _send_event(
            websocket,
            WebSocketEventType.ai_response_chunk,
            {
                "text": "",
                "is_duplicate": True,
                "message_role": "generation_locked",
            },
        )
        return

    try:
        transcript = str(event.payload.get("transcript", "")).strip()
        question_text = str(event.payload.get("question", "")).strip()
        personality = str(event.payload.get("personality", "Friendly"))
        if not transcript:
            return
        transcript = live_interview_service.update_live_transcript(
            session_id,
            transcript=transcript,
            is_final=True,
        )

        session = live_interview_service.get_runtime_session(session_id)
        live_interview_service.append_memory(
            session_id,
            speaker="candidate",
            message=transcript,
        )
        next_move = live_interview_service.process_candidate_answer(
            session_id,
            current_question=question_text,
            transcript=transcript,
        )
        live_interview_service.transition_runtime_state(session_id, InterviewRuntimeState.follow_up)
        live_interview_service.set_turn_state(session_id, InterviewTurnState.responding)
        await _send_state(websocket, InterviewRuntimeState.follow_up)

        chunks = []
        stream_message_id = str(uuid4())
        async for chunk in ai_conversation_engine.stream_followup(
            current_question=question_text,
            transcript=transcript,
            personality=personality,
            memory=session.memory,
            interview_context=live_interview_service.get_interview_context(session_id),
            planned_move={
                "move_type": next_move.move_type.value,
                "question": next_move.question,
                "rationale": next_move.rationale,
                "should_interrupt": False,
            },
        ):
            chunks.append(chunk)
            await _send_interviewer_text(
                websocket,
                chunk,
                message_role="followup_stream",
                is_final=False,
                message_id=stream_message_id,
            )

        followup = " ".join(chunks).strip() or next_move.question
        live_interview_service.append_memory(session_id, speaker="interviewer", message=followup)
        followup_question = live_interview_service.add_followup_question(
            session_id,
            followup,
            question_type=next_move.move_type.value,
        )
        live_interview_service.clear_live_transcript(session_id)
        await _send_event(
            websocket,
            WebSocketEventType.followup_question,
            {
                "question": followup,
                "question_id": str(followup_question.id),
                "question_type": followup_question.question_type,
                "message_id": stream_message_id,
                "move_type": next_move.move_type.value,
                "rationale": next_move.rationale,
                "should_interrupt": False,
            },
        )
    finally:
        live_interview_service.finish_generation(session_id, generation_id)


async def _complete_interview(websocket: WebSocket, session_id: UUID) -> None:
    session = live_interview_service.get_runtime_session(session_id)
    if session.runtime_state != InterviewRuntimeState.feedback_generation:
        live_interview_service.transition_runtime_state(
            session_id,
            InterviewRuntimeState.feedback_generation,
        )
        await _send_state(websocket, InterviewRuntimeState.feedback_generation)

    live_interview_service.transition_runtime_state(
        session_id,
        InterviewRuntimeState.completed,
    )


async def _send_state(websocket: WebSocket, state: InterviewRuntimeState) -> None:
    await _send_event(
        websocket,
        WebSocketEventType.state_transition,
        {"state": state.value},
    )


async def _send_interviewer_text(
    websocket: WebSocket,
    text: str,
    *,
    message_role: str,
    is_final: bool = False,
    message_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    payload = {
        "message_id": message_id or str(uuid4()),
        "speaker": "interviewer",
        "message_role": message_role,
        "text": text,
        "is_final": is_final,
    }
    if metadata:
        payload.update(metadata)

    await _send_event(
        websocket,
        WebSocketEventType.ai_response_chunk,
        payload,
    )


async def _send_event(websocket: WebSocket, event_type: WebSocketEventType, payload: dict) -> None:
    if websocket.client_state == WebSocketState.DISCONNECTED:
        return

    event = WebSocketEvent(type=event_type, payload=payload)
    try:
        await websocket.send_json(event.model_dump(mode="json"))
    except RuntimeError:
        return
