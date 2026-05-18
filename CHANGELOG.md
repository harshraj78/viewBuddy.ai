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
- Dockerfiles and Docker Compose foundation.

### Changed

- Nothing yet.

### Fixed

- Nothing yet.

### Security

- Documented initial security expectations for authentication, resume uploads, secrets, and LLM logging.
