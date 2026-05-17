# Development Roadmap

## Phase 1 - Foundation

Goals:

- Create repo structure and documentation.
- Set up FastAPI foundation.
- Add database, config, migrations, tests, and Docker Compose.

Tasks:

- Create backend app skeleton.
- Add `pyproject.toml`.
- Add health endpoint.
- Add settings management.
- Add PostgreSQL connection.
- Add Alembic.
- Add Docker Compose.
- Add pytest setup.

Deliverables:

- Running backend at `localhost:8000`.
- OpenAPI docs at `/docs`.
- Passing test suite.

Learning:

- FastAPI structure.
- Environment configs.
- Database migrations.
- Clean architecture basics.

Recruiter value:

- Shows professional backend foundation instead of script-style coding.

## Phase 2 - Video MVP

Goals:

- Implement the first live video interview flow without overbuilding advanced AI complexity.

Tasks:

- User registration and login.
- Resume upload.
- Resume text extraction.
- Basic skill/project extraction.
- Interview session creation.
- Browser-based interview room with camera preview.
- Microphone capture and answer recording.
- Speech-to-text transcription.
- One-question-at-a-time AI interviewer flow.
- Basic question generation.
- Voice or on-screen AI interviewer question delivery.
- Answer evaluation from transcript.
- Session history.
- Candidate-facing video UI.
- Streamlit only for internal/admin demo screens if needed.

Deliverables:

- End-to-end demo: upload resume -> start video interview -> answer by voice -> get transcript, score, and feedback.

Learning:

- API design.
- Auth.
- File upload security.
- LLM integration basics.
- Browser media APIs.
- Real-time session state.
- Speech-to-text integration.

Recruiter value:

- Demonstrates a differentiated AI product loop that feels closer to a real interview platform than a chatbot.

## Phase 3 - AI Integration

Goals:

- Improve AI quality and reliability.

Tasks:

- LLM provider abstraction.
- Structured JSON output validation.
- Prompt versioning.
- LLM call logging.
- Better evaluation rubrics.
- Follow-up question generation.
- Improvement roadmap.

Deliverables:

- Reliable, explainable AI evaluation pipeline.

Learning:

- Prompt engineering.
- Model reliability.
- AI observability.

Recruiter value:

- Shows modern AI engineering instead of plain API calls.

## Phase 4 - Advanced Features

Goals:

- Add personalization and richer interview modes.

Tasks:

- RAG over resume and job description.
- Company-specific interviews.
- Behavioral rounds.
- DSA rounds.
- Adaptive difficulty.
- Resume-job description matching.
- Interview summary generation.
- Better analytics dashboard.

Deliverables:

- Personalized interview experience.

Learning:

- Embeddings.
- Vector search.
- Retrieval quality.
- Analytics design.

Recruiter value:

- Strong AI systems story.

## Phase 5 - Production Readiness

Goals:

- Make it deployable and maintainable.

Tasks:

- Dockerize backend and frontend.
- Add CI/CD.
- Add structured logging.
- Add error monitoring.
- Add rate limiting.
- Add secure upload handling.
- Add deployment docs.
- Add API tests and integration tests.

Deliverables:

- Public demo deployment.
- GitHub Actions pipeline.
- Production README.

Learning:

- DevOps.
- Security.
- Testing.
- Observability.

Recruiter value:

- Shows maturity beyond feature coding.

## Phase 6 - Scaling and Optimization

Goals:

- Prepare for higher traffic, lower latency, and lower cost.

Tasks:

- Celery workers.
- Redis caching.
- Provider fallback.
- Token and cost dashboards.
- Feature flags.
- Prompt experiments.
- Higher-quality voice interview mode.
- WebSocket live interview simulation.
- WebRTC-ready media architecture.
- Next.js frontend migration.

Deliverables:

- Scalable AI SaaS architecture.

Learning:

- Distributed systems.
- Queue design.
- AI cost optimization.
- Real-time systems.

Recruiter value:

- Gives you advanced talking points for staff-level architecture discussions.
