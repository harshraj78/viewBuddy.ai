# DevOps and Production Readiness

## Local Docker Compose

Planned services:

- `backend`: FastAPI API.
- `frontend`: Streamlit UI.
- `postgres`: relational database.
- `redis`: cache and Celery broker.
- `worker`: Celery worker.
- `chroma`: local vector database.

## Dockerization Principles

- Use slim Python images.
- Install dependencies with lockfiles.
- Run as non-root user in production images.
- Keep secrets out of images.
- Add health checks.
- Separate dev and prod commands.

## CI/CD with GitHub Actions

Pipeline stages:

1. Lint and format check.
2. Type check.
3. Unit tests.
4. API integration tests.
5. Docker build.
6. Security scan.
7. Deploy to staging or production.

## Cloud Deployment

Simple path:

- Backend + worker + frontend on a cloud VM with Docker Compose.
- Managed PostgreSQL.
- Redis container or managed Redis.
- Nginx reverse proxy.
- HTTPS via cloud certificates or Let's Encrypt.

More scalable path:

- Backend on container service.
- Worker autoscaling by queue depth.
- Managed PostgreSQL.
- Managed Redis.
- Pinecone for vector DB.
- Object storage for resumes.
- CDN for frontend assets if migrating to Next.js.

## Logging

Use structured JSON logs with:

- request_id
- user_id when safe
- endpoint
- status_code
- latency_ms
- error_code
- llm_provider
- llm_model
- token_usage
- cost_estimate

Do not log:

- passwords
- JWTs
- API keys
- full resume text
- sensitive answer content unless explicitly needed in a secure debug mode

## Monitoring

Track:

- API p95 latency.
- API error rate.
- Background job failure rate.
- LLM provider latency.
- LLM cost per user.
- Resume parsing failure rate.
- Evaluation invalid JSON rate.

## Secrets Management

Development:

- `.env` file ignored by Git.

Production:

- Cloud secret manager.
- Environment variables injected at runtime.
- Rotate keys periodically.
- Separate keys per environment.

## Rate Limiting

Important limits:

- Login attempts.
- Resume uploads.
- Question generation.
- Answer evaluation.
- Report generation.

Why:

- Protects from abuse.
- Controls AI cost.
- Prevents one user from exhausting provider quota.

## Fallback Strategy

LLM providers fail. Design for it:

- Retry transient failures.
- Use provider fallback for critical flows.
- Return user-friendly "try again" errors.
- Persist failed job state.
- Let users resume sessions.

