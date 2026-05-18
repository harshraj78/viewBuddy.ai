# Product Flow

The product is a realistic live interview platform. It should feel closer to Google Meet, Zoom, LeetCode, and an interview debrief than a dashboard-heavy AI app.

## Screen 1 - Landing Page

Goal: convert visitor to start interview.

Sections:

- Hero.
- Demo preview.
- Interview types.
- Testimonials.
- CTA.

Keep it simple. The landing page should sell the experience, not explain every backend feature.

## Screen 2 - Interview Setup

Goal: configure interview context.

Layout:

- Left: interview settings.
- Right: live preview of interviewer personality.

Inputs:

- Role: SDE, AI Engineer, Backend, Frontend.
- Experience: Fresher, Mid-level.
- Interview type: Technical, HR, System Design.
- Company style: FAANG, Startup, Indian Product.
- Personality: Friendly, Strict, FAANG pressure.
- Resume upload.
- Start interview button.

## Screen 3 - Waiting Room

Goal: create psychological realism before the interview starts.

Features:

- Camera test.
- Mic test.
- AI interviewer intro.
- Interview tips.

This screen matters because real interviews have a pre-call readiness moment.

## Screen 4 - Live Interview

Goal: only focus on conversation.

Layout:

```text
+------------------------------+
|     AI Interviewer Video      |
+------------------------------+

+------------------------------+
|   Current Question Card       |
+------------------------------+

+------------------------------+
|  Live Transcript Collapsible  |
+------------------------------+

mic | cam | leave | notes
```

Rules:

- No analytics.
- No charts.
- No report cards.
- No coding panel.
- No dashboard clutter.

The interview screen must stay minimal and pressure-realistic.

MVP voice behavior:

- Browser text-to-speech reads the current interviewer question.
- Browser speech recognition captures candidate answers into the transcript where supported.
- Typed transcript remains the fallback.
- OpenAI Realtime API and LiveKit are the production target after the local MVP flow is stable.

## Screen 5 - Coding Round

Goal: separate LeetCode-style experience from conversation mode.

Layout:

```text
+--------------+---------------+
| Problem      | AI Interviewer |
| Description  | voice/chat     |
+--------------+---------------+
|                              |
|        Monaco Editor         |
|                              |
+------------------------------+
```

The AI can:

- Observe pauses.
- Offer hints.
- Ask optimization questions.
- Evaluate complexity and code quality.

## Screen 6 - System Design Round

Goal: immersive whiteboard mode.

Layout:

```text
+-----------------------------+
| AI interviewer question      |
+-----------------------------+

+-----------------------------+
| Whiteboard / Architecture    |
| canvas                       |
+-----------------------------+
```

## Screen 7 - Feedback Report

Goal: put analytics after the interview.

Sections:

- Communication: confidence, filler words, pace.
- Technical: depth, correctness.
- Behavioral: structure, leadership.
- Replay: recording and transcript.
- Improvement suggestions.

MVP behavior:

- Report is generated from submitted answer transcripts.
- Scores are deterministic for now so the product is demoable without an LLM key.
- The evaluator returns communication, technical, behavioral, replay, and improvement sections.
- Production version should replace the deterministic evaluator with versioned LLM rubric evaluation.
- Set `AI_EVALUATION_MODE=llm` and configure `OPENAI_API_KEY` to route report generation through the LLM evaluator.

## Core Product Modules

1. Authentication Service: signup, login, sessions.
2. Interview Session Engine: state, question flow, follow-up logic, interruptions, timing.
3. AI Conversation Engine: realtime voice, reasoning, dynamic responses.
4. Resume Intelligence Engine: upload, extraction, chunking, embeddings, pgvector, question generation.
5. Evaluation Engine: transcript, technical depth, communication, scorecard.
6. Coding Engine: Monaco editor, code execution sandbox, test cases, AI review.
7. Voice Engine: STT, TTS, interruptions, latency optimization.
8. Reporting Engine: feedback report, replay, transcript, improvement roadmap.

Current MVP voice layer:

- Browser Web Speech API for local speech-to-text.
- Browser SpeechSynthesis for local interviewer text-to-speech.
- This keeps the MVP fast and demoable before adding paid realtime infrastructure.

## Recommended Scalable Stack

- Frontend: Next.js, TailwindCSS, shadcn/ui.
- Backend: FastAPI.
- Realtime: WebRTC and LiveKit.
- AI: OpenAI Realtime API.
- Database: PostgreSQL.
- Vector search: pgvector.
- Coding: Monaco Editor and Docker sandbox execution.

## Product Decisions

Do not build:

- Fake 3D avatars.
- Metaverse UI.
- Overly animated screens.
- Massive dashboards during interviews.

Build:

- Minimal screens.
- Realistic interview pacing.
- Fast voice interaction.
- Separate modes for conversation, coding, system design, and report.
