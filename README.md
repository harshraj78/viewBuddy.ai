# ViewBuddy.ai - AI Interview Copilot

ViewBuddy.ai is a realtime AI mock interview platform for candidates preparing for SDE, AI Engineer, backend, frontend, and system design interviews. The product is built to feel like a live interview room, not a chatbot or static questionnaire.

## Problem Statement

Most interview preparation tools give generic question banks or text-based chat. Real interviews are different: candidates must speak clearly, handle follow-ups, explain tradeoffs, recover from weak answers, and stay calm under pressure.

ViewBuddy.ai solves this by simulating a live AI interviewer that:

- asks one question at a time through voice
- listens to candidate answers through the browser microphone
- adapts follow-up questions using role, skills, projects, resume context, and conversation memory
- challenges vague answers with implementation, scaling, debugging, and tradeoff probes
- generates a feedback report after the interview instead of distracting the candidate during the round

## Features

- MockAI-style interview setup with role, difficulty, interviewer personality, accent, and company style
- Waiting room with camera and microphone checks
- Live video interview screen with candidate panel, AI interviewer panel, timer, phase rail, interrupt control, and compact transcript
- Browser SpeechRecognition for zero-cost speech-to-text
- Browser speechSynthesis for zero-cost AI interviewer voice
- FastAPI WebSocket orchestration for live transcript deltas, final answers, AI response chunks, follow-up questions, and interview state transitions
- Stateful interview brain that tracks strengths, weak areas, answered topics, technologies, confidence, depth, and repetition
- Gemini/local/fallback model router for AI question planning and follow-up generation
- Resume/skills/project-aware personalization inputs
- Feedback report with communication, technical, behavioral, replay, and improvement suggestions
- Separate screens for coding round, system design round, and final report
- Deployment-ready frontend and backend configs for Vercel and Render/Railway

## Tech Stack

Frontend:

- React
- Vite
- Tailwind-style custom CSS
- lucide-react icons
- Browser Media APIs
- Browser SpeechRecognition
- Browser speechSynthesis

Backend:

- FastAPI
- Python 3.11
- Pydantic v2
- SQLAlchemy
- Alembic
- WebSockets

AI:

- Gemini 2.5 Flash API support
- OpenAI-compatible local model support for vLLM
- Deterministic fallback mode for zero-cost demos
- Agent-style interviewer components: planner, analyzer, strategist, memory manager, interviewer

Database and deployment:

- PostgreSQL / Supabase-ready schema direction
- Render or Railway backend deployment
- Vercel frontend deployment
- Docker and Docker Compose foundation

## Architecture

```text
Candidate browser
  -> camera + microphone
  -> SpeechRecognition transcript deltas
  -> React live interview room
  -> FastAPI WebSocket
  -> Interview Session Engine
  -> Stateful Interview Brain
  -> Gemini / local LLM / fallback model router
  -> AI response stream
  -> browser speechSynthesis voice output
```

Backend flow:

```text
POST /live-interviews/sessions
  -> create session
  -> build profile context
  -> generate opening question + hidden roadmap

WebSocket transcript_delta
  -> update live transcript buffer
  -> detect vague or drifting answers
  -> optionally send interviewer_interrupt

WebSocket transcript_final
  -> persist answer transcript
  -> analyze candidate response
  -> update interview brain state
  -> choose next interviewer strategy
  -> stream contextual follow-up

GET /live-interviews/sessions/{id}/report
  -> evaluate transcript replay
  -> return structured feedback report
```

Key design decision: the live interview screen stays minimal. Analytics, scores, and charts are intentionally moved to the final feedback report so the round feels like a real interview.

## Screenshots

Add screenshots here after the next UI pass:

- Landing page
- Customize mock interview screen
- Waiting room
- Live interview room
- Coding round
- Feedback report

Recommended filenames:

```text
docs/screenshots/landing.png
docs/screenshots/setup.png
docs/screenshots/waiting-room.png
docs/screenshots/live-interview.png
docs/screenshots/report.png
```

## Setup Instructions

### 1. Clone the repository

```powershell
git clone https://github.com/harshraj78/viewBuddy.ai.git
cd "viewBuddy.ai"
```

### 2. Backend setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd backend
pip install -e ".[dev]"
copy ..\.env.example ..\.env
```

Update `.env` with your Gemini key:

```text
INTERVIEW_LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Run the backend:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8020 --reload
```

Smoke test:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/api/v1/health
Invoke-RestMethod http://127.0.0.1:8020/api/v1/ai/status
```

### 3. Frontend setup

```powershell
cd frontend\video_interview_app
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

For deployed Vercel builds, set:

```text
VITE_API_BASE_URL=https://your-render-backend.onrender.com/api/v1
```

## API Endpoints

Health and diagnostics:

- `GET /api/v1/health`
- `GET /api/v1/ai/status`

Live interview:

- `POST /api/v1/live-interviews/sessions`
- `GET /api/v1/live-interviews/sessions/{session_id}`
- `POST /api/v1/live-interviews/sessions/{session_id}/next-question`
- `POST /api/v1/live-interviews/sessions/{session_id}/transcript`
- `GET /api/v1/live-interviews/sessions/{session_id}/report`
- `WS /api/v1/live-interviews/sessions/{session_id}/ws`

WebSocket events:

- `session_start`
- `transcript_delta`
- `transcript_final`
- `ai_response_chunk`
- `interviewer_interrupt`
- `followup_question`
- `state_transition`
- `interview_complete`
- `error`

Example session request:

```json
{
  "candidate_name": "Harsh Raj",
  "target_role": "AI Engineer",
  "mode": "technical",
  "difficulty": "beginner",
  "target_company": "Indian Product",
  "interviewer_persona": "Senior Engineer - Strict",
  "interviewer_accent": "Indian English",
  "candidate_skills": ["FastAPI", "PostgreSQL", "RAG", "React"],
  "project_highlights": ["AI Interview Copilot"],
  "resume_summary": "Built a resume-aware mock interview platform with realtime voice flow.",
  "question_count": 5
}
```

## Challenges Faced

- Making the AI feel like a real interviewer instead of a generated question list
- Avoiding duplicate WebSocket transcript events and repeated follow-ups
- Preventing overlapping browser speech synthesis and microphone recognition
- Handling Vercel-to-Render CORS preflight failures
- Supporting Gemini, local open-source models, and deterministic fallback through one model boundary
- Keeping the live interview UI focused while still supporting transcript, notes, coding, and feedback flows
- Designing a zero-cost MVP without paid realtime APIs, LiveKit, or OpenAI Realtime

## Future Improvements

- PostgreSQL-backed persistence for live sessions and interview messages
- Supabase authentication and user profiles
- Real resume upload, PDF parsing, chunking, embeddings, and pgvector retrieval
- Monaco-based coding round with sandboxed execution
- Whiteboard canvas for system design interviews
- WebRTC media transport for richer realtime audio/video architecture
- Better streaming STT/TTS once moving beyond browser-native APIs
- Prompt and model evaluation benchmark suite
- Dataset export pipeline for LoRA/QLoRA fine-tuning of interviewer behavior
- Observability with LLM latency, token usage, transcript events, and follow-up quality metrics
- GitHub Actions CI for linting, tests, frontend build, and deployment checks
