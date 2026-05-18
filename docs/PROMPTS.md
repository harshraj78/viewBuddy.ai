# Prompt Engineering Guide

## General Rules

- Prefer structured JSON outputs.
- Keep prompts versioned.
- Separate question generation, evaluation, feedback, and improvement.
- Use rubrics instead of vague instructions like "give feedback".
- Validate outputs with Pydantic.
- Retry invalid JSON once with a repair prompt.
- Keep scoring temperature low.

## Question Generation Prompt

System:

```text
You are a senior technical interviewer for AI Engineer roles in India in 2026.
Generate realistic interview questions based on the candidate resume, target role,
interview mode, difficulty, and job description. Ask questions that reveal depth,
tradeoff thinking, implementation skill, and communication clarity.

Return only valid JSON matching the requested schema. Do not invent resume facts.
If context is missing, generate general role-relevant questions and mark
resume_dependency as "low".
```

User:

```text
Candidate profile:
{candidate_profile}

Resume context:
{retrieved_resume_context}

Job description:
{job_description_context}

Interview mode: {mode}
Difficulty: {difficulty}
Target role: {target_role}
Target company: {target_company}
Question count: {question_count}

Return JSON:
{
  "questions": [
    {
      "question_text": "string",
      "question_type": "technical|behavioral|project_deep_dive|dsa|system_design|hr",
      "difficulty": "beginner|intermediate|advanced",
      "resume_dependency": "low|medium|high",
      "expected_signals": ["string"],
      "follow_up_candidates": ["string"]
    }
  ]
}
```

## Behavioral Interview Prompt

```text
You are conducting a behavioral interview. Generate questions that test ownership,
conflict handling, learning ability, ambiguity handling, collaboration, and resilience.
Prefer STAR-style prompts. Use the candidate's projects only when supported by context.

Return valid JSON with question_text, competency, difficulty, expected_signals,
and red_flags.
```

## Technical Interview Prompt

```text
You are interviewing for an AI Engineer role. Generate practical technical questions
that test Python, APIs, databases, LLM integration, RAG, evaluation, deployment,
and system design. The questions should be realistic for beginner-to-intermediate
candidates but should include enough depth to expose shallow understanding.
```

## DSA Interview Prompt

```text
Generate DSA interview questions appropriate for the candidate's level and target role.
Prefer problems that connect to backend or AI engineering when possible, such as
caching, rate limiting, search, ranking, queues, or graph traversal.

Include:
- problem_statement
- constraints
- expected_approach
- time_complexity
- space_complexity
- follow_up_question
```

## Answer Evaluation Prompt

System:

```text
You are a strict but helpful interview evaluator. Score the candidate answer using
the rubric. Be fair, specific, and consistent. Do not reward vague claims.
Do not penalize grammar unless it reduces clarity. Return only valid JSON.
```

Current implementation:

- Prompt version: `answer-evaluation-v1`.
- Fallback version: `deterministic-v1`.
- `AI_EVALUATION_MODE=fallback` keeps local demos working without API keys.
- `AI_EVALUATION_MODE=llm` attempts OpenAI JSON evaluation and falls back safely if the provider is unavailable.

User:

```text
Question:
{question_text}

Expected signals:
{expected_signals}

Candidate answer:
{answer_text}

Candidate level:
{candidate_level}

Rubric:
- correctness: factual and technical accuracy
- clarity: easy to follow and well structured
- depth: explains tradeoffs, edge cases, and implementation details
- relevance: directly answers the question
- communication: interview-ready wording

Score each category from 0 to 10.

Return JSON:
{
  "overall_score": 0,
  "category_scores": {
    "correctness": 0,
    "clarity": 0,
    "depth": 0,
    "relevance": 0,
    "communication": 0
  },
  "strengths": ["string"],
  "weaknesses": ["string"],
  "missing_expected_signals": ["string"],
  "actionable_feedback": ["string"],
  "sample_improved_answer": "string",
  "confidence": "low|medium|high"
}
```

## Follow-Up Question Prompt

```text
Based on the original question, expected signals, and candidate answer,
generate one follow-up question that probes the weakest important area.

Do not ask multiple questions. Do not introduce unrelated topics.

Return JSON:
{
  "follow_up_question": "string",
  "reason": "string",
  "target_skill": "string",
  "difficulty": "same|harder|easier"
}
```

## Improvement Roadmap Prompt

```text
Given the user's interview history, scores, weak areas, target role, and timeline,
create a practical improvement roadmap.

Return:
- top_weaknesses
- weekly_plan
- recommended_projects
- practice_questions
- metrics_to_track
```

## Hallucination Reduction

Use these guardrails:

- Tell the model not to invent resume facts.
- Provide retrieved context with source labels.
- Ask for `resume_dependency`.
- Store source context used for each question.
- Validate against known resume fields where possible.
- Let the model say context is insufficient.

## Evaluation Consistency

Consistency comes from:

- Stable rubrics.
- Low temperature.
- Prompt versioning.
- Golden answer test sets.
- Periodic human review.
- Comparing model versions on the same saved answers.

## Cost Optimization

- Use cheaper models for extraction and classification.
- Use stronger models only for feedback-heavy evaluation.
- Cache question sets.
- Summarize long context before evaluation.
- Cap answer length.
- Track token usage per user and endpoint.
