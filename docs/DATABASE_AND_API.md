# Database and API Design

## Database Schema

Use UUID primary keys for public-facing resources. Keep `created_at` and `updated_at` on most tables.

### users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role_target TEXT,
    experience_level TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_email ON users(email);
```

### resumes

```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    raw_text TEXT,
    parsed_profile JSONB,
    parsing_status TEXT NOT NULL DEFAULT 'pending',
    parsing_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_resumes_user_id_created_at ON resumes(user_id, created_at DESC);
CREATE INDEX idx_resumes_parsing_status ON resumes(parsing_status);
```

### resume_skills

```sql
CREATE TABLE resume_skills (
    id UUID PRIMARY KEY,
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    skill_category TEXT,
    confidence NUMERIC(4,3),
    evidence TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_resume_skills_resume_id ON resume_skills(resume_id);
CREATE INDEX idx_resume_skills_name ON resume_skills(skill_name);
```

### resume_projects

```sql
CREATE TABLE resume_projects (
    id UUID PRIMARY KEY,
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    tech_stack JSONB,
    impact TEXT,
    extracted_facts JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_resume_projects_resume_id ON resume_projects(resume_id);
```

### job_descriptions

```sql
CREATE TABLE job_descriptions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name TEXT,
    role_title TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    extracted_requirements JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_job_descriptions_user_id_created_at ON job_descriptions(user_id, created_at DESC);
```

### interview_sessions

```sql
CREATE TABLE interview_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
    job_description_id UUID REFERENCES job_descriptions(id) ON DELETE SET NULL,
    mode TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    target_company TEXT,
    target_role TEXT,
    status TEXT NOT NULL DEFAULT 'created',
    summary JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sessions_user_id_created_at ON interview_sessions(user_id, created_at DESC);
CREATE INDEX idx_sessions_status ON interview_sessions(status);
```

### questions

```sql
CREATE TABLE questions (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    expected_signals JSONB,
    source_context JSONB,
    order_index INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_questions_session_order ON questions(session_id, order_index);
```

### answers

```sql
CREATE TABLE answers (
    id UUID PRIMARY KEY,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    duration_seconds INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_answers_question_id ON answers(question_id);
CREATE INDEX idx_answers_user_id_created_at ON answers(user_id, created_at DESC);
```

### answer_scores

```sql
CREATE TABLE answer_scores (
    id UUID PRIMARY KEY,
    answer_id UUID NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    overall_score NUMERIC(4,2) NOT NULL,
    correctness_score NUMERIC(4,2),
    clarity_score NUMERIC(4,2),
    depth_score NUMERIC(4,2),
    structure_score NUMERIC(4,2),
    confidence_score NUMERIC(4,2),
    rubric JSONB NOT NULL,
    model_name TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_answer_scores_answer_id ON answer_scores(answer_id);
```

### feedback_items

```sql
CREATE TABLE feedback_items (
    id UUID PRIMARY KEY,
    answer_id UUID NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    feedback_text TEXT NOT NULL,
    suggested_improvement TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_feedback_answer_id ON feedback_items(answer_id);
```

### conversation_history

```sql
CREATE TABLE conversation_history (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_conversation_session_created_at ON conversation_history(session_id, created_at);
```

### analytics_snapshots

```sql
CREATE TABLE analytics_snapshots (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    metrics JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_analytics_user_period ON analytics_snapshots(user_id, period_start, period_end);
```

### prompt_versions

```sql
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    template TEXT NOT NULL,
    output_schema JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(name, version)
);
```

### llm_calls

```sql
CREATE TABLE llm_calls (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT,
    input_tokens INT,
    output_tokens INT,
    latency_ms INT,
    estimated_cost_usd NUMERIC(10,6),
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_llm_calls_user_created_at ON llm_calls(user_id, created_at DESC);
CREATE INDEX idx_llm_calls_provider_model ON llm_calls(provider, model);
```

## Normalization Decisions

- Users, resumes, sessions, questions, answers, and scores are separate because they have different lifecycles.
- `parsed_profile`, `rubric`, and `summary` are JSONB because AI outputs evolve quickly.
- Skills and projects are normalized because they are queried often.
- Prompt versions and LLM calls are stored for auditability.

## API Design

Base path: `/api/v1`

### Auth

`POST /auth/register`

Request:

```json
{
  "email": "candidate@example.com",
  "password": "StrongPassword123!",
  "full_name": "Utkarsh Raj"
}
```

Response `201`:

```json
{
  "id": "uuid",
  "email": "candidate@example.com",
  "full_name": "Utkarsh Raj"
}
```

`POST /auth/login`

Response `200`:

```json
{
  "access_token": "jwt",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Resume Upload

`POST /resumes/upload`

Request:

- `multipart/form-data`
- field: `file`

Response `202`:

```json
{
  "resume_id": "uuid",
  "parsing_status": "pending",
  "message": "Resume uploaded and parsing job queued."
}
```

Errors:

- `400`: unsupported file type.
- `413`: file too large.
- `401`: unauthenticated.

### Create Interview Session

`POST /interviews/sessions`

Request:

```json
{
  "resume_id": "uuid",
  "job_description_id": "uuid",
  "mode": "technical",
  "difficulty": "intermediate",
  "target_role": "AI Engineer",
  "target_company": "Indian product startup",
  "question_count": 8
}
```

Response `201`:

```json
{
  "session_id": "uuid",
  "status": "created"
}
```

### Generate Questions

`POST /interviews/sessions/{session_id}/questions`

Response `200`:

```json
{
  "session_id": "uuid",
  "questions": [
    {
      "id": "uuid",
      "question_text": "Walk me through your resume project involving LLMs.",
      "question_type": "project_deep_dive",
      "difficulty": "intermediate",
      "expected_signals": ["architecture clarity", "tradeoff awareness"]
    }
  ]
}
```

### Evaluate Answer

`POST /answers/evaluate`

Request:

```json
{
  "question_id": "uuid",
  "answer_text": "I built the system using FastAPI..."
}
```

Response `200`:

```json
{
  "answer_id": "uuid",
  "overall_score": 7.5,
  "scores": {
    "correctness": 8,
    "clarity": 7,
    "depth": 7,
    "structure": 8
  },
  "strengths": ["Clear architecture explanation"],
  "improvements": ["Add specific metrics and failure handling"],
  "sample_improved_answer": "A stronger answer would be..."
}
```

### Analytics

`GET /analytics/me`

Response `200`:

```json
{
  "sessions_completed": 12,
  "average_score": 7.2,
  "strongest_categories": ["system design", "project explanation"],
  "weakest_categories": ["DSA", "behavioral structure"],
  "trend": [
    {"date": "2026-05-01", "average_score": 6.4},
    {"date": "2026-05-15", "average_score": 7.2}
  ]
}
```

## Error Shape

Use one consistent error response:

```json
{
  "error": {
    "code": "RESUME_UNSUPPORTED_TYPE",
    "message": "Only PDF and DOCX resumes are supported.",
    "details": {}
  }
}
```

