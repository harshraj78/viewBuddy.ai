# AI Interview Copilot

AI Interview Copilot is a production-oriented interview preparation platform for candidates targeting AI Engineer, backend, and software roles. It accepts resumes, extracts skills and projects, generates personalized technical and behavioral interviews, evaluates answers with LLMs, scores performance, and tracks long-term improvement.

This repository is intentionally designed like a real SaaS AI product, not a toy tutorial. The goal is to make it deployable, extensible, recruiter-impressive, and strong enough to discuss deeply in interviews.

## 1. Project Overview

The platform helps candidates practice realistic interview rounds using AI:

- Upload a resume in PDF or DOCX format.
- Parse skills, experience, projects, education, and achievements.
- Generate interview questions from resume, target role, company, and job description.
- Support technical, HR, behavioral, DSA, and domain-specific rounds.
- Evaluate user answers with structured scoring rubrics.
- Generate actionable feedback and improvement roadmaps.
- Track progress across sessions with analytics.

Beginner view: the app behaves like an AI mock interviewer.

Industry view: the app is an AI workflow system with user management, document ingestion, structured LLM outputs, async processing, retrieval, observability, prompt versioning, and cost controls.

## 2. Product Vision

The product should feel like a serious AI interview coach for India-focused 2026 hiring. A strong v1 focuses on reliability, explainability, and useful feedback rather than flashy AI demos.

Primary users:

- Beginner-to-intermediate developers preparing for AI Engineer roles.
- Candidates applying to Indian startups, product companies, service companies, and global remote roles.
- Students who need resume-based mock interviews and progress tracking.

Recruiter value:

- Shows full-stack product thinking.
- Demonstrates AI engineering beyond simple chatbot wrappers.
- Covers backend design, database modeling, prompt engineering, async jobs, RAG, deployment, testing, and monitoring.

## 3. High-Level Architecture

```text
                       +----------------------+
                       |   React Video Room    |
                       |  live interview MVP   |
                       +----------+-----------+
                                  |
                                  | HTTPS / JSON
                                  v
+------------------+    +---------+----------+     +-------------------+
|  Reverse Proxy   | -> |   FastAPI Backend  | --> |   PostgreSQL DB   |
|  Nginx / Cloud   |    |  API + business    |     | relational state  |
+------------------+    +---------+----------+     +-------------------+
                                  |
                                  +--------------+
                                  |              |
                                  v              v
                         +--------+-----+   +----+----------------+
                         | LLM Provider |   | Vector DB           |
                         | OpenAI/Groq/ |   | ChromaDB/Pinecone   |
                         | Gemini       |   | resume/job context  |
                         +--------------+   +---------------------+
                                  |
                                  v
                         +--------+---------+
                         | Background Jobs  |
                         | Celery + Redis   |
                         +------------------+
```

Core request flow:

1. User uploads a resume.
2. Backend stores file metadata and creates a parsing job.
3. Worker extracts text, sections, skills, projects, and embeddings.
4. User starts an interview session.
5. Backend retrieves resume and job context.
6. LLM generates structured interview questions.
7. User submits answers.
8. LLM evaluates answers using a scoring rubric.
9. Scores, feedback, and analytics are stored.

Scaling principle: keep API requests fast, move heavy document parsing and AI evaluation into background jobs, and store structured AI outputs so the product can be audited and improved over time.

## 4. Backend Design

Backend stack:

- FastAPI for HTTP APIs, validation, OpenAPI docs, and dependency injection.
- SQLAlchemy 2.x ORM for PostgreSQL persistence.
- Alembic for database migrations.
- Pydantic v2 for request/response schemas and LLM structured output models.
- Celery + Redis for async parsing, embeddings, and long-running evaluations.
- Provider abstraction for OpenAI, Groq, or Gemini.
- ChromaDB for local MVP vector search; Pinecone for managed production vector search.

Recommended service layers:

- API routers: HTTP boundary only.
- Schemas: request/response validation.
- Services: business use cases such as create interview session or evaluate answer.
- Repositories: database access.
- AI services: prompts, provider clients, evaluators, parsers, embeddings.
- Workers: background task orchestration.
- Core: config, logging, security, errors.

Beginner mistake to avoid: putting all logic inside FastAPI route functions. That becomes painful to test and impossible to scale.

## 5. Frontend Design

MVP frontend: React/Vite video interview room.

Why React/Vite for the candidate-facing MVP:

- Direct browser camera and microphone access.
- Better control over recording and interview-room UX.
- WebSocket-ready for live session events.
- Easier migration path to Next.js when the SaaS UI grows.

Streamlit role:

- Useful for internal dashboards, demos, analytics views, and quick admin tools.
- Not ideal as the main live video interview room.

Migration path:

- MVP: React/Vite video interview room.
- Support tool: Streamlit admin/demo dashboard.
- V2: Next.js frontend consuming the same FastAPI API.
- Keep backend API stable so frontend migration does not rewrite core product logic.

Expected screens:

- Login/register.
- Resume upload and parsed profile view.
- Interview setup.
- Live interview session.
- Answer evaluation.
- Session history.
- Analytics dashboard.
- Improvement roadmap.

## 6. Database Schema

See [docs/DATABASE_AND_API.md](docs/DATABASE_AND_API.md) for detailed schema and endpoint examples.

Major entities:

- `users`
- `resumes`
- `resume_skills`
- `resume_projects`
- `job_descriptions`
- `interview_sessions`
- `questions`
- `answers`
- `answer_scores`
- `feedback_items`
- `conversation_history`
- `analytics_snapshots`
- `prompt_versions`
- `llm_calls`

Design principle: store the raw AI response, structured parsed output, prompt version, provider, model, token usage, latency, and cost estimate. This makes the project interview-worthy because you can discuss auditability and AI evaluation quality.

## 7. API Design

API groups:

- `/api/v1/auth`
- `/api/v1/resumes`
- `/api/v1/interviews`
- `/api/v1/answers`
- `/api/v1/analytics`
- `/api/v1/reports`
- `/api/v1/jobs`

Example endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/resumes/upload`
- `GET /api/v1/resumes/{resume_id}`
- `POST /api/v1/interviews/sessions`
- `POST /api/v1/interviews/sessions/{session_id}/questions`
- `POST /api/v1/answers/evaluate`
- `GET /api/v1/analytics/me`

API rules:

- Return typed response models.
- Use predictable error shapes.
- Validate file size and MIME type.
- Protect user-owned resources.
- Never trust client-provided user IDs; derive identity from JWT.

## 8. Authentication Design

MVP:

- Email and password authentication.
- Password hashing with Argon2 or bcrypt.
- JWT access tokens.
- Refresh token support after MVP.

Production:

- Short-lived access tokens.
- Refresh token rotation.
- Rate limiting on login.
- Email verification.
- Password reset.
- Optional OAuth later.

Auth flow:

```text
User -> POST /auth/login -> FastAPI verifies password -> JWT issued
User -> Authorization: Bearer token -> Protected API route
Route -> get_current_user dependency -> service layer receives user context
```

Beginner mistake to avoid: storing passwords directly or using unsalted hashes. Always use a password hashing library.

## 9. AI/LLM Pipeline

AI workflows:

- Resume parsing and skill extraction.
- Question generation.
- Answer evaluation.
- Feedback generation.
- Follow-up question generation.
- Improvement roadmap generation.
- Resume-job description matching.

Production pattern:

```text
Input validation
-> context selection
-> prompt template
-> LLM call
-> structured output validation
-> retry or repair if invalid
-> persistence
-> analytics update
```

Avoid building a simple "send text to model and display response" app. The recruiter-impressive part is structured AI behavior, scoring consistency, observability, and continuous improvement.

## 10. Prompt Engineering

See [docs/PROMPTS.md](docs/PROMPTS.md).

Prompt principles:

- Use structured JSON outputs.
- Use explicit scoring rubrics.
- Separate generation from evaluation.
- Store prompt versions.
- Include constraints and refusal rules.
- Keep prompts deterministic where scoring matters.
- Evaluate against role level, not generic correctness.

## 11. RAG Architecture

RAG is used for personalized interviews from resume, projects, and job descriptions.

Pipeline:

```text
Resume text
-> clean and section
-> chunk by semantic sections
-> embed chunks
-> store vectors with metadata
-> retrieve top relevant chunks per question generation/evaluation
-> pass retrieved context into prompt
```

ChromaDB is good for local MVP. Pinecone is better when you want managed hosting, scaling, and production operations.

## 12. Folder Structure

Planned production folder structure:

```text
ai-interview-copilot/
  backend/
    app/
      api/
        v1/
          routers/
      core/
      db/
      models/
      schemas/
      repositories/
      services/
      ai/
        providers/
        prompts/
        pipelines/
        evaluators/
        embeddings/
      workers/
      observability/
      tests/
    alembic/
    Dockerfile
    pyproject.toml
  frontend/
    video_interview_app/
      src/
      package.json
    streamlit_app/
      app.py
      pages/
      components/
      services/
    Dockerfile
  docs/
  infra/
    docker/
    nginx/
    github-actions/
  scripts/
  README.md
  AGENTS.md
  CHANGELOG.md
  .env.example
```

## 13. Development Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

Short version:

- Phase 1: Foundation, docs, repo structure, local environment.
- Phase 2: video-based MVP interview room.
- Phase 3: AI integration and structured evaluation.
- Phase 4: RAG, adaptive interviews, analytics.
- Phase 5: production hardening, auth, deployment, CI/CD.
- Phase 6: scaling, observability, voice, real-time interviews.

## 14. GitHub Workflow

Branching:

- `main`: stable deployable branch.
- `dev`: integration branch if needed.
- `feature/<area>-<short-name>`: feature work.
- `fix/<area>-<short-name>`: bug fixes.

Commit style:

- `feat: add resume upload endpoint`
- `fix: validate resume file size`
- `docs: add architecture blueprint`
- `test: cover answer evaluation scoring`
- `chore: configure docker compose`

PR expectations:

- Clear summary.
- Screenshots for UI changes.
- API examples for backend changes.
- Tests listed.
- Known limitations.

## 15. DevOps + Deployment

MVP deployment:

- Docker Compose with FastAPI, React video frontend, Streamlit, PostgreSQL, Redis, and ChromaDB.
- Deploy backend and frontend on a cloud VM or container platform.
- Use managed PostgreSQL for production when possible.

Production deployment:

- Nginx reverse proxy.
- HTTPS with managed certificates.
- GitHub Actions CI.
- Separate dev/staging/prod configs.
- Secrets stored in cloud secret manager, not committed.
- Structured logs and health checks.

## 16. Monitoring + Logging

Track:

- API latency and error rate.
- LLM latency, token usage, provider errors, and estimated cost.
- Job queue duration and failures.
- Resume parsing failures.
- Evaluation consistency issues.

Recommended tools:

- Python structured logging.
- OpenTelemetry for traces.
- Sentry for exceptions.
- Prometheus + Grafana for metrics.
- Langfuse or Helicone for LLM observability and prompt tracking.

## 17. Security Best Practices

Security concerns:

- Resume files contain personal data.
- LLM prompts may contain sensitive content.
- User answers and feedback are private.

Practices:

- Hash passwords.
- Validate file type and size.
- Store uploads outside public web root.
- Use signed URLs if object storage is added.
- Enforce authorization on every user resource.
- Rate-limit login, upload, and LLM-heavy endpoints.
- Do not log full resume text or secrets.
- Keep provider API keys in environment variables.

## 18. Testing Strategy

Testing layers:

- Unit tests for parsers, scoring helpers, repositories, and services.
- API tests using FastAPI TestClient or httpx.
- Integration tests with test PostgreSQL.
- Contract tests for response schemas.
- Prompt regression tests with saved cases.
- Smoke tests for Docker Compose.

AI-specific testing:

- Golden datasets for answer evaluation.
- Prompt version comparisons.
- JSON schema validation.
- Rubric consistency checks.
- Human review samples.

## 19. Resume Positioning

Strong resume bullet examples:

- Built a live video-based AI interview preparation SaaS using FastAPI, PostgreSQL, React, browser media APIs, and LLM APIs to simulate realistic interview sessions.
- Designed a structured LLM evaluation pipeline with rubric-based scoring, JSON validation, prompt versioning, and feedback generation for consistent answer assessment.
- Implemented resume parsing, skill extraction, interview session history, analytics tracking, and asynchronous AI workflows using Celery and Redis.
- Architected a RAG-based personalization layer with vector search over resume and job-description context to improve relevance of generated interview questions.
- Containerized the platform with Docker Compose and planned production deployment with CI/CD, observability, rate limiting, and secure secret management.

## 20. Interview Questions Recruiters May Ask

Common questions:

- Why did you choose FastAPI?
- How do you prevent LLM hallucinations?
- How does your scoring system stay consistent?
- Why PostgreSQL instead of only a vector database?
- How would you scale the system for 10,000 users?
- How do you handle sensitive resume data?
- What happens if the LLM provider is down?
- How do you reduce AI costs?
- How would you migrate from Streamlit to React?

Short sample answer:

> I separated the system into API, service, repository, and AI pipeline layers. The backend stores structured interview state in PostgreSQL, while vector search is used only for semantic retrieval. LLM calls are validated with Pydantic schemas, logged with prompt versions, and moved to async jobs when latency is high. This lets the product remain reliable even though the AI layer is probabilistic.

## 21. Scaling Considerations

Scale bottlenecks:

- LLM latency and cost.
- Resume parsing CPU time.
- Vector search performance.
- Database query patterns for analytics.
- Long-running interview sessions.

Scaling strategies:

- Background jobs for heavy work.
- Caching common prompts and generated question sets.
- Rate limiting and per-user quotas.
- Database indexes on user, session, and created timestamps.
- Model fallback strategy.
- Async streaming for live interview responses.
- Separate read-heavy analytics from transactional writes later.

## 22. Future Improvements

High-impact improvements:

- Voice interviews with speech-to-text and text-to-speech.
- WebSocket-based live interview simulation.
- Company-specific interview packs.
- Multi-agent interview panel.
- Prompt evaluation dashboard.
- Feature flags for AI experiments.
- Benchmark set for scoring quality.
- Next.js frontend.
- Mobile-responsive candidate dashboard.
- Deployment to a public cloud with demo credentials.

## Local Development Status

Current status: Phase 1 backend foundation is initialized. Product direction has been tightened: the MVP should be a live video-based interview simulation, not a text-first mock interview.

Run backend locally:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".\backend[dev]"
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health"
```

Run Streamlit locally:

```powershell
$env:API_BASE_URL="http://127.0.0.1:8000/api/v1"
.\.venv\Scripts\python.exe -m streamlit run frontend\streamlit_app\app.py
```

Run the video interview room locally:

```powershell
cd frontend\video_interview_app
npm install
$env:VITE_API_BASE_URL="http://127.0.0.1:8020/api/v1"
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Important MVP direction:

- Streamlit is useful for quick admin/demo screens.
- The candidate-facing MVP should become a live video interview room.
- React/Next.js is preferred for camera, microphone, recording, WebSocket state, and a polished interview experience.
- Backend APIs should support live sessions, transcripts, evaluation, and follow-up questions.

Quality checks:

```powershell
cd backend
..\.venv\Scripts\python.exe -m ruff check .
..\.venv\Scripts\python.exe -m pytest tests
```
