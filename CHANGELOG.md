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
- Role, company, skills, project, and resume-summary inputs for interview personalization.
- Interview planner for session-unique, profile-aware seed question generation.
- Answer-signal extraction for adaptive follow-up questioning.
- Stateful interview brain with answer analysis, candidate memory, weak-area tracking, and adaptive interviewer moves.
- OpenAI-compatible local/vLLM model client for open-source interviewer inference.
- Agent module boundaries for analyzer, strategist, memory manager, and interviewer response generation.
- Open-source LLM architecture documentation with vLLM and fine-tuning direction.
- AI provider status endpoint that confirms active provider and whether Gemini is configured without exposing secrets.
- AI-powered interview planner for first question and hidden roadmap generation.
- Deployment configs for Vercel frontend and Railway/Render backend.
- MVP deployment guide with backend/frontend env variables and smoke tests.
- CORS regression tests for Vercel-to-Render preflight requests.
- MockAI-style interview customization, waiting room, live room, phase rail, and interrupt UI.
- Interviewer persona/accent/candidate metadata fields for richer AI context.
- WebSocket `transcript_delta`, `transcript_final`, and `interviewer_interrupt` events for a more realtime interview loop.
- Live transcript buffering and lightweight answer-drift detection during candidate speech.
- Light/dark theme toggle and responsive mobile layout improvements for the candidate frontend.
- Premium roadmap marker for subscription-only interview capabilities.

### Changed

- Realtime session startup now avoids racing REST question loading against WebSocket introduction state.
- Follow-up generation now includes acknowledgement pacing and more natural interviewer transitions.
- Live interview UI now uses stable active session/question refs to reduce stale state during follow-ups.
- Follow-up prompts now include interview context, answer-derived signals, and anti-repetition instructions.
- CORS setup now keeps local Vite test ports while preserving environment-configured origins.
- Live interview sessions now start from an opening question plus hidden roadmap instead of treating the entire round as a pre-generated queue.
- WebSocket follow-ups now use the interview brain's planned intent before phrasing the next interviewer question.
- Live interviewer response generation now routes through a swappable model client while preserving deterministic fallback behavior.
- Settings now load `.env` from both project root and `backend/.env` so local backend startup is less fragile.
- Live interview session creation now attempts LLM-generated question planning before deterministic fallback.
- Backend Docker startup now respects cloud platform `PORT`.
- CORS origin settings now use comma-separated env parsing that works on Render.
- Candidate-facing flow now prioritizes realistic interview room interaction over dashboard-style layout.
- Browser speech recognition now streams interim transcript updates and finalizes the answer when recording stops.
- README now uses a recruiter-friendly project structure with problem statement, features, architecture, setup, APIs, challenges, and future improvements.
- Interview setup now uses a single resume upload input instead of manual skills, project highlights, and resume summary fields.
- Interview planner now derives skill/project memory from resume context when explicit profile fields are absent.

### Fixed

- Prevented duplicate transcript WebSocket events from generating duplicate follow-up questions.
- Prevented overlapping browser speech synthesis and microphone recognition during live interviews.
- Fixed early interview leave flow so sessions can transition to feedback generation cleanly.
- Fixed Gemini/local model configuration appearing as fallback when Uvicorn is started from the backend directory.
- Fixed initial interview questions still feeling hardcoded even when Gemini was configured.
- Fixed Render startup failure caused by list parsing for `BACKEND_CORS_ORIGINS`.
- Fixed Vercel `OPTIONS /api/v1/live-interviews/sessions` preflight returning 400.

### Security

- Documented initial security expectations for authentication, resume uploads, secrets, and LLM logging.
