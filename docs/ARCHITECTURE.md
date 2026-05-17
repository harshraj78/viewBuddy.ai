# Architecture Blueprint

## Product Architecture

AI Interview Copilot has four major planes:

- User experience plane: React/Vite video interview room, Streamlit admin/demo screens, and future Next.js app.
- Application plane: FastAPI services, authentication, session management, analytics.
- AI plane: prompt templates, provider abstraction, RAG, structured evaluation, model observability.
- Operations plane: Docker, CI/CD, logging, metrics, tracing, monitoring, secrets.

## Backend Architecture

```text
FastAPI Routers
  -> Pydantic Schemas
  -> Service Layer
  -> Repositories
  -> SQLAlchemy Models
  -> PostgreSQL

Service Layer
  -> AI Pipelines
  -> LLM Providers
  -> Vector Store
  -> Background Jobs
```

Why this matters:

- Routers stay thin and easy to read.
- Services are testable without HTTP.
- Repositories isolate database access.
- AI pipelines are replaceable and measurable.

## AI Pipeline Architecture

```text
Resume Upload
  -> file validation
  -> text extraction
  -> section detection
  -> skill/project extraction
  -> embedding
  -> vector storage
  -> structured profile storage

Interview Generation
  -> choose interview mode
  -> retrieve resume/job context
  -> load prompt version
  -> generate structured questions
  -> validate JSON
  -> persist questions

Answer Evaluation
  -> fetch question + answer + context
  -> apply scoring rubric
  -> structured LLM evaluation
  -> validate output
  -> persist score + feedback
  -> update analytics
```

## Background Job Architecture

Use Celery + Redis when work is slow, retryable, or expensive:

- Resume parsing.
- Embedding generation.
- Bulk question generation.
- Long interview summary generation.
- Analytics snapshot generation.
- Email/report generation later.

Tradeoff:

- Celery adds operational complexity, but it prevents the API from timing out and makes failures retryable.

## Caching Strategy

MVP:

- Cache nothing except basic in-process config and prompt templates.

Intermediate:

- Redis cache for question generation inputs.
- Cache model provider metadata.
- Cache analytics summaries.

Production:

- Per-user LLM quota cache.
- Prompt result cache for identical resume-role-company requests.
- Rate-limit counters in Redis.

Do not cache sensitive raw resume text casually. Cache derived outputs only when you have clear privacy rules.

## Scaling Strategy

First 100 users:

- Single VM or container platform.
- Managed PostgreSQL preferred.
- Local ChromaDB acceptable for demo.

1,000+ users:

- Separate API, worker, and frontend containers.
- Managed Redis.
- Managed vector database.
- Horizontal workers for parsing/evaluation.
- Queue-based backpressure.

10,000+ users:

- Provider routing and fallback models.
- Read replicas for analytics.
- Dedicated observability stack.
- Feature flags and quotas.
- Separate online interview path from offline analytics path.

## Frontend Strategy

Keep Streamlit thin:

- It calls backend APIs.
- It does not own business logic.
- It does not directly call LLM providers.
- It does not directly access the database.

Use React/Vite for the candidate-facing video MVP:

- Browser camera and microphone access.
- Answer recording.
- WebSocket-ready session state.
- Future speech-to-text and text-to-speech integration.

This makes migration to Next.js practical because the backend remains the product brain.
