# Changelog

All notable changes to AI Interview Copilot will be documented in this file.

The format follows Keep a Changelog principles, and this project aims to use semantic versioning once the first deployable release is available.

## [Unreleased]

### Added

- Initial product architecture and roadmap.
- Production-oriented README.
- Engineering progress log in `AGENTS.md`.
- Environment variable template.
- Detailed architecture, database/API, prompt, roadmap, and DevOps documentation.
- FastAPI backend skeleton with application factory.
- `/api/v1/health` endpoint.
- Pydantic settings management.
- SQLAlchemy session setup and production-shaped domain models.
- Initial Alembic schema migration.
- Backend pytest and Ruff setup.
- Streamlit placeholder frontend.
- React/Vite video interview room scaffold with camera/microphone permission flow and answer recording controls.
- Seven-screen product flow for landing, setup, waiting room, live interview, coding round, system design, and feedback report.
- Product flow documentation covering UX rules and core product modules.
- Browser-based voice MVP with speech-to-text transcript capture and text-to-speech interviewer playback.
- Live interview session API contracts for creating sessions, requesting questions, and submitting transcripts.
- Feedback report API generated from submitted transcripts and connected to the frontend report screen.
- AI evaluator abstraction with OpenAI JSON evaluation path and deterministic fallback mode.
- FastAPI WebSocket orchestration for realtime transcript-to-follow-up interview flow.
- Gemini-ready conversation engine with zero-cost fallback follow-up generation.
- Dockerfiles and Docker Compose foundation.
- WebSocket event IDs for idempotent transcript handling.
- Collapsible live transcript feed with separate interviewer and candidate turns.
- Browser voice lifecycle handling for one-speaker-at-a-time interview flow.

### Changed

- Realtime session startup now avoids racing REST question loading against WebSocket introduction state.
- Follow-up generation now includes acknowledgement pacing and more natural interviewer transitions.
- Live interview UI now uses stable active session/question refs to reduce stale state during follow-ups.

### Fixed

- Prevented duplicate transcript WebSocket events from generating duplicate follow-up questions.
- Prevented overlapping browser speech synthesis and microphone recognition during live interviews.
- Fixed early interview leave flow so sessions can transition to feedback generation cleanly.

### Security

- Documented initial security expectations for authentication, resume uploads, secrets, and LLM logging.
