# AI Interview Copilot - Engineering Log

This file tracks project progress, architecture decisions, learning notes, bugs, and next milestones. Treat it like a lightweight engineering notebook for a real startup project.

## Current Progress

- Project foundation initialized.
- Phase 1 backend skeleton implemented.
- Local Python virtual environment created at `.venv`.
- Backend dependencies installed.
- Initial FastAPI health endpoint verified by test.
- Initial SQLAlchemy models and Alembic migration added.
- Docker Compose foundation added for backend, frontend, PostgreSQL, and Redis.
- React/Vite video interview room scaffold added.
- Live interview API contracts added for session creation, next question, and transcript submission.
- Candidate-facing frontend refactored into seven product screens: landing, setup, waiting room, live interview, coding round, system design round, and feedback report.
- Browser voice MVP added with speech-to-text transcript capture and text-to-speech interviewer question playback.
- MVP feedback report endpoint added and connected to submitted live interview transcripts.
- AI evaluator abstraction added with OpenAI-compatible JSON evaluation path and deterministic fallback.
- FastAPI WebSocket interview orchestration added with explicit state transitions and streamed follow-up events.
- Gemini 2.5 Flash-ready follow-up engine added with zero-cost deterministic fallback.
- Realtime interview stability improved with idempotent WebSocket transcript events, safer state transitions, and duplicate-message protection.
- Live transcript UX now separates interviewer and candidate turns with collapsible transcript history.
- Browser voice flow improved to prevent overlapping speech synthesis and safely restart speech recognition during answer capture.
- Interview personalization improved with role, company style, skills, project highlights, resume summary, answer signals, and session-unique question planning.
- Stateful interview brain added to analyze each answer, track candidate strengths/weaknesses, choose interviewer intent, and drive adaptive next moves.
- Product vision defined.
- High-level architecture documented.
- Database and API design drafted.
- Prompt engineering strategy drafted.
- Development roadmap drafted.

## Product North Star

The main goal is a live video-based interview simulation, not a static question generator or text chat.

Every architecture decision should support this path:

- Candidate enters a realistic video interview room.
- Candidate camera and microphone are active during the session.
- AI interviewer asks one question at a time through voice and/or on-screen interviewer UI.
- Candidate answers naturally by voice.
- System records/transcribes answers for evaluation.
- AI evaluates silently or after each answer depending on mode.
- AI asks contextual follow-up questions like a real interviewer.
- Session has pacing, difficulty, memory, and a final interview report.
- Live mode should support WebRTC/video capture, WebSockets, streaming responses, speech-to-text, and text-to-speech.

MVP must be video-based. Streamlit can remain useful for quick internal dashboards, but the candidate-facing interview room should move toward a browser frontend that can handle camera, microphone, WebRTC/media APIs, and real-time state cleanly.
- Environment variable template added.

## Completed Tasks

- Created `README.md` with product overview, architecture, roadmap, security, testing, DevOps, and resume positioning.
- Created `CHANGELOG.md` for professional release tracking.
- Created `.env.example` with production-oriented configuration placeholders.
- Created `docs/ARCHITECTURE.md` for system architecture.
- Created `docs/DATABASE_AND_API.md` for schema and API design.
- Created `docs/PROMPTS.md` for LLM prompt templates and structured output strategy.
- Created `docs/ROADMAP.md` for phased development.
- Created `docs/DEVOPS.md` for deployment, CI/CD, observability, and operations guidance.
- Created FastAPI application factory and `/api/v1/health`.
- Created Pydantic settings management.
- Created SQLAlchemy database session setup.
- Created initial models for users, resumes, interviews, answers, scores, feedback, analytics, prompt versions, and LLM call logs.
- Created initial Alembic migration.
- Created backend test suite with health endpoint coverage.
- Created Streamlit placeholder frontend.
- Created React/Vite video interview room scaffold with camera/microphone capture and recording controls.
- Refactored React frontend to match the actual screen flow and keep analytics out of the live interview screen.
- Created `docs/PRODUCT_FLOW.md` to lock the UX and module architecture.
- Added browser speech recognition support for live answer transcripts with typed fallback.
- Added browser speech synthesis support so interviewer questions can be spoken aloud.
- Added deterministic MVP evaluation report with communication, technical, behavioral, replay, and improvement sections.
- Connected frontend feedback report screen to backend-generated report data.
- Added prompt versioning constants for answer evaluation.
- Added OpenAI provider boundary for future LLM scoring.
- Added WebSocket events for live interview session start, transcript chunks, AI response chunks, follow-up questions, state transitions, and interview completion.
- Added explicit interview runtime states: setup, waiting room, introduction, questioning, follow-up, coding, system design, feedback generation, completed.
- Added WebSocket event IDs to prevent duplicate follow-up generation from repeated transcript sends.
- Added realistic interviewer pacing with acknowledgement messages, short pauses, and contextual follow-up transitions.
- Added frontend stale-state guards for active session, active question, recording state, and speech state.
- Added collapsible live transcript feed with clear interviewer/candidate separation.
- Improved browser speech flow so interviewer playback cancels active recognition and candidate recording cancels overlapping playback.
- Added an interview planner that generates role-specific, project-aware, skill-aware question sets instead of one fixed script.
- Added setup inputs for candidate skills, project highlights, and resume summary to feed personalization.
- Added answer-signal extraction so follow-up questions can adapt to technologies and production concerns mentioned during the interview.
- Expanded Gemini follow-up prompting with interview context, prior questions, and anti-repetition guidance.
- Added answer analysis for vagueness, confidence, memorized-sounding responses, missing tradeoffs, missing metrics, and missing failure modes.
- Added dynamic interviewer moves: clarify, deepen, challenge, implementation, scaling, debugging, tradeoff, behavioral, and switch-topic.
- Changed active interview flow to start with an opening question and keep only a hidden topic roadmap while live conversation drives the next question.
- Created live interview API endpoints:
  - `POST /api/v1/live-interviews/sessions`
  - `GET /api/v1/live-interviews/sessions/{session_id}`
  - `POST /api/v1/live-interviews/sessions/{session_id}/next-question`
  - `POST /api/v1/live-interviews/sessions/{session_id}/transcript`
- Created Dockerfiles and Docker Compose.

## Pending Tasks

- Implement authentication endpoints.
- Implement resume upload and parsing pipeline.
- Replace in-memory live interview service with PostgreSQL-backed session persistence.
- Add real speech-to-text provider.
- Add production text-to-speech provider once moving beyond the zero-cost browser MVP.
- Replace browser-only voice with OpenAI Realtime API and/or LiveKit when moving from MVP to production realtime.
- Replace coding round placeholder with Monaco editor.
- Replace system design placeholder with whiteboard canvas.
- Connect feedback report to real evaluation output.
- Replace deterministic MVP evaluator with LLM rubric evaluation once provider keys are configured.
- Add LLM call logging for provider, model, latency, token usage, and errors.
- Persist WebSocket transcript and state transitions into PostgreSQL-backed `interview_messages`.
- Implement first LLM provider abstraction.
- Implement question generation and answer evaluation endpoints.
- Build the production candidate-facing video interview MVP.
- Add API and service tests.
- Add GitHub Actions CI.

## Architecture Decisions

### ADR-001: FastAPI for Backend

Decision: Use FastAPI for the backend API.

Why:

- Strong Python ecosystem for AI products.
- Excellent OpenAPI support.
- Pydantic validation helps with structured request and response contracts.
- Async-friendly for I/O-heavy LLM calls.

Tradeoff:

- Requires careful separation of route handlers and business logic to avoid messy code.

### ADR-002: PostgreSQL as System of Record

Decision: Use PostgreSQL for users, sessions, answers, scores, feedback, analytics, prompt versions, and LLM call logs.

Why:

- Reliable relational data model.
- Strong indexing and query capabilities.
- Recruiter-friendly backend choice.
- Works well with analytics and auditability.

Tradeoff:

- Vector search still needs ChromaDB or Pinecone for semantic retrieval.

### ADR-003: Streamlit First, React Later

Decision: Use Streamlit for MVP frontend and keep APIs frontend-agnostic for a later React/Next.js migration.

Why:

- Fast AI demo development.
- Lets the project prioritize backend and AI pipeline quality first.

Tradeoff:

- Streamlit is less suitable for highly polished production SaaS UX.

### ADR-004: Structured LLM Outputs

Decision: Require JSON outputs validated by Pydantic schemas for question generation, evaluation, and feedback.

Why:

- Reduces hallucinated formatting.
- Makes outputs easier to store, test, compare, and visualize.
- Supports prompt regression testing.

Tradeoff:

- Requires retry/repair handling when models return invalid JSON.

## Bugs / Issues

- Git reports dubious repository ownership for this workspace. Use per-command safe directory override:

```powershell
git -c safe.directory='C:/Users/Utkarsh Raj/Documents/New project 2' status
```

- Background server launch from the Codex desktop shell did not persist reliably. Verified commands should be run directly in a user terminal when an interactive local server is needed.

## Next Milestone

Milestone 2: Authentication and video interview foundation.

Deliverables:

- User registration.
- User login.
- Password hashing.
- JWT access tokens.
- Auth dependencies.
- Protected `/users/me` endpoint.
- Interview session lifecycle endpoints.
- One-question-at-a-time video interview API shape.
- Conversation history storage for interviewer/candidate turns.
- Frontend decision for video MVP: React/Next.js preferred, or Streamlit with `streamlit-webrtc` only if speed matters more than production UX.
- Media capture plan for camera and microphone.
- Speech-to-text provider abstraction.
- Text-to-speech provider abstraction.
- WebSocket event contract for live session state.
- API tests for auth success and failure paths.

## Learning Notes

- A serious AI project is not just prompts. It needs data modeling, evaluation, observability, and failure handling.
- PostgreSQL stores trusted system state. Vector DB stores semantic retrieval context.
- Prompt versions and LLM call logs are important for debugging and explaining AI behavior in interviews.
- Background jobs prevent slow AI/document-processing tasks from blocking API responsiveness.
- Migrations are not optional in production projects; they are how schema changes become reviewable and deployable.
- A realistic interview product needs camera/mic UX, session state, conversation memory, live pacing, transcription, and follow-up behavior. Static question generation is useful, but video interview realism is the differentiator.

## Optimization Ideas

- Cache generated question sets per resume, role, difficulty, and company.
- Use cheaper models for classification and extraction, stronger models for evaluation and feedback.
- Batch embeddings during resume ingestion.
- Store token usage and latency per provider to compare cost-performance.
- Add feature flags for prompt experiments.
