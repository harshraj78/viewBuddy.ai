# Open-Source Interview LLM Architecture

ViewBuddy.ai is evolving from prompt-only follow-up generation into a model-centric
realtime interviewer. The backend now separates deterministic interview state from the
model that phrases the next interviewer turn.

## Runtime Flow

```text
Candidate voice
  -> transcript event
  -> MemoryManagerAgent
  -> CandidateAnalyzerAgent
  -> FollowupStrategistAgent
  -> InterviewerAgent
  -> LLMClient
  -> streamed interviewer response
```

The `InterviewBrainState` remains the source of truth for strategy, strengths, weak
areas, answered topics, and interviewer intent. The LLM is used to express the selected
move naturally, not to own the whole interview state.

## Local Model Serving

Use vLLM or any OpenAI-compatible server:

```powershell
vllm serve Qwen/Qwen2.5-7B-Instruct --host 0.0.0.0 --port 8001 --served-model-name interview-llm
```

Environment:

```env
INTERVIEW_LLM_PROVIDER=local
LOCAL_LLM_BASE_URL=http://localhost:8001/v1
LOCAL_LLM_API_KEY=EMPTY
LOCAL_LLM_MODEL=interview-llm
```

The backend calls:

```text
POST /v1/chat/completions
stream=true
```

## Model Swap Boundary

Model implementations live under:

```text
backend/app/ai/models/
  base.py
  openai_compatible.py
  gemini.py
  router.py
```

Supported interview providers:

- `fallback`: deterministic no-cost behavior
- `local`, `vllm`, `openai_compatible`: OpenAI-compatible local/self-hosted model
- `gemini`: Gemini fallback for hosted experimentation

## Agent Boundaries

```text
backend/app/ai/agents/
  memory_agent.py        # updates answer signals
  analyzer_agent.py      # answer analysis
  strategist_agent.py    # chooses next interviewer move
  interviewer_agent.py   # phrases the move with an LLM
```

This keeps the system debuggable. If the model says something weak, we can inspect:

- answer analysis
- brain state
- planned move
- interviewer prompt
- model response

## Fine-Tuning Direction

Training data should teach the model to turn structured interview state into realistic
interviewer responses.

Example JSONL row:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a senior AI interviewer. Ask one concise, adaptive follow-up."
    },
    {
      "role": "user",
      "content": "{\"candidate_profile\":{\"role\":\"AI Engineer\",\"skills\":[\"FastAPI\",\"RAG\"]},\"brain_state\":{\"weak_areas\":[\"missing metrics\"],\"answered_topics\":[\"Redis caching\"]},\"planned_move\":{\"move_type\":\"scaling\",\"question\":\"If traffic becomes 100x, which metric tells you Redis is the bottleneck?\"},\"candidate_answer\":\"I used Redis caching to improve performance.\"}"
    },
    {
      "role": "assistant",
      "content": "You mentioned Redis caching. If traffic becomes 100x, which metric would tell you Redis is the bottleneck, and what would you change first?"
    }
  ],
  "metadata": {
    "task_type": "followup_generation",
    "move_type": "scaling",
    "quality_score": 5
  }
}
```

Recommended first fine-tune:

- Qwen2.5 1.5B or 3B Instruct
- LoRA or QLoRA
- TRL `SFTTrainer`
- Unsloth for faster low-cost training

Do not fine-tune until we have a few hundred curated examples from real interview
turns and synthetic edge cases.
