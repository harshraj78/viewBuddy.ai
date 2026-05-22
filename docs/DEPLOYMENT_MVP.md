# MVP Deployment Guide

This deployment path keeps the MVP simple:

- Frontend: Vercel
- Backend: Railway or Render
- Database: Supabase PostgreSQL
- AI: Gemini API

## 1. Backend Deployment

Deploy the `backend` folder as a Docker service.

### Required Environment Variables

```env
APP_NAME=AI Interview Copilot
APP_ENV=production
APP_DEBUG=false
API_V1_PREFIX=/api/v1

DATABASE_URL=your_supabase_postgres_url

INTERVIEW_LLM_PROVIDER=gemini
GEMINI_API_KEY=your_real_gemini_key
GEMINI_MODEL=gemini-2.5-flash

AI_EVALUATION_MODE=fallback
LLM_REQUEST_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=3

BACKEND_CORS_ORIGINS=https://your-vercel-domain.vercel.app
JWT_SECRET_KEY=replace_with_long_random_secret
```

Do not set real secrets in `.env.example`.

### Railway

1. Create a new Railway project.
2. Connect the GitHub repo.
3. Set root directory to `backend`.
4. Add the environment variables above.
5. Deploy.
6. Verify:

```text
https://your-backend-domain/api/v1/health
https://your-backend-domain/api/v1/ai/status
```

### Render

1. Create a new Web Service.
2. Select Docker.
3. Set root directory to `backend`.
4. Add environment variables.
5. Deploy.

## 2. Frontend Deployment

Deploy `frontend/video_interview_app` to Vercel.

### Vercel Settings

```text
Framework: Vite
Root Directory: frontend/video_interview_app
Build Command: npm run build
Output Directory: dist
```

### Required Frontend Environment Variable

```env
VITE_API_BASE_URL=https://your-backend-domain/api/v1
```

Redeploy frontend after setting this variable.

## 3. CORS

After Vercel gives you the frontend URL, update backend:

```env
BACKEND_CORS_ORIGINS=https://your-vercel-domain.vercel.app
```

Redeploy backend.

## 4. Smoke Test

1. Open frontend URL.
2. Start an interview.
3. Check backend:

```text
/api/v1/ai/status
```

Expected:

```json
{
  "interview_llm_provider": "gemini",
  "gemini_key_configured": true
}
```

4. Start interview with different skills/projects.
5. First question should change because the AI planner now generates the roadmap.

## 5. Current MVP Limitations

- Interview sessions are still in memory. A backend restart clears active sessions.
- PostgreSQL persistence for live sessions is the next production hardening task.
- Browser SpeechRecognition works best in Chrome-based browsers.
- Browser speech synthesis quality depends on the user's device/browser.
