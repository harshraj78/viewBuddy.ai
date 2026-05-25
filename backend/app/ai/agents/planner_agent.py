from __future__ import annotations

import json
import logging

from app.ai.interview_planner import InterviewProfile, PlannedQuestion
from app.ai.models import ChatMessage, LLMClientError, get_interview_llm_client

logger = logging.getLogger(__name__)


class InterviewPlannerAgent:
    async def generate_question_plan(
        self,
        *,
        profile: InterviewProfile,
        question_count: int,
    ) -> list[PlannedQuestion]:
        client = get_interview_llm_client()
        messages = self._build_messages(profile=profile, question_count=question_count)
        chunks = []
        try:
            async for chunk in client.stream_chat(
                messages=messages,
                temperature=0.7,
                max_tokens=700,
            ):
                chunks.append(chunk)
        except LLMClientError:
            raise

        raw_response = "".join(chunks)
        try:
            return self._parse_questions(raw_response, question_count)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            logger.warning("AI planner returned invalid question plan: %s", raw_response)
            raise LLMClientError("AI planner returned invalid question plan.") from exc

    def _build_messages(
        self,
        *,
        profile: InterviewProfile,
        question_count: int,
    ) -> list[ChatMessage]:
        system_prompt = """
You are ViewBuddy.ai's senior interview planner.
Create a realistic live interview roadmap, not a generic questionnaire.

Rules:
- Return only valid JSON.
- Generate one opening question and a hidden roadmap of follow-up topics.
- Questions must be specific to the candidate role, skills, projects, and company style.
- If resume_summary is present, treat it as the primary memory source and ask from it.
- Prefer project names, technologies, responsibilities, metrics, and tradeoffs
  found in resume_summary.
- Avoid generic questions like "tell me about yourself".
- Each question should test a different interviewer intent.
- The live interviewer will adapt later, so do not over-script.
"""
        user_prompt = {
            "candidate_profile": profile.as_prompt_context(),
            "question_count": question_count,
            "required_json_shape": {
                "questions": [
                    {
                        "question_type": (
                            "profile_deep_dive | implementation | scaling | debugging | "
                            "tradeoff | behavioral"
                        ),
                        "question_text": "one concise interviewer question",
                    }
                ]
            },
        }
        return [
            ChatMessage(role="system", content=system_prompt.strip()),
            ChatMessage(role="user", content=json.dumps(user_prompt, indent=2)),
        ]

    def _parse_questions(self, raw_response: str, question_count: int) -> list[PlannedQuestion]:
        data = json.loads(_strip_json_fence(raw_response))
        questions = data["questions"]
        parsed = []
        seen_text = set()
        for question in questions:
            question_text = str(question["question_text"]).strip()
            question_type = str(question.get("question_type", "ai_planned")).strip()
            if not question_text or question_text.lower() in seen_text:
                continue
            seen_text.add(question_text.lower())
            parsed.append(
                PlannedQuestion(
                    question_type=question_type[:80],
                    question_text=question_text,
                )
            )
            if len(parsed) >= question_count:
                break

        if not parsed:
            raise ValueError("AI planner returned no usable questions.")
        return parsed


def _strip_json_fence(raw_response: str) -> str:
    text = raw_response.strip()
    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
    elif text.startswith("```"):
        text = text.removeprefix("```").strip()
    if text.endswith("```"):
        text = text.removesuffix("```").strip()
    return text


interview_planner_agent = InterviewPlannerAgent()
