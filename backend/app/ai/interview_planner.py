from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from uuid import uuid4

from app.schemas.live_interview import LiveInterviewQuestion, StartLiveInterviewRequest


@dataclass(frozen=True)
class PlannedQuestion:
    question_type: str
    question_text: str


@dataclass(frozen=True)
class InterviewProfile:
    target_role: str
    mode: str
    difficulty: str
    company_style: str
    interviewer_name: str
    interviewer_persona: str
    interviewer_accent: str
    interview_duration_minutes: int
    skills: tuple[str, ...]
    projects: tuple[str, ...]
    resume_summary: str | None

    @property
    def primary_skill(self) -> str:
        return self.skills[0] if self.skills else _default_skill_for_role(self.target_role)

    @property
    def primary_project(self) -> str:
        return self.projects[0] if self.projects else "your strongest recent project"

    def as_prompt_context(self) -> dict[str, object]:
        return {
            "target_role": self.target_role,
            "mode": self.mode,
            "difficulty": self.difficulty,
            "company_style": self.company_style,
            "interviewer_name": self.interviewer_name,
            "interviewer_persona": self.interviewer_persona,
            "interviewer_accent": self.interviewer_accent,
            "interview_duration_minutes": self.interview_duration_minutes,
            "skills": list(self.skills),
            "projects": list(self.projects),
            "resume_summary": self.resume_summary,
        }


class InterviewPlanner:
    def build_profile(self, request: StartLiveInterviewRequest) -> InterviewProfile:
        resume_summary = request.resume_summary
        derived_skills = _derive_skills_from_resume(resume_summary or "")
        derived_projects = _derive_projects_from_resume(resume_summary or "")
        return InterviewProfile(
            target_role=request.target_role,
            mode=request.mode.value,
            difficulty=request.difficulty.value,
            company_style=request.target_company or "General product company",
            interviewer_name=request.interviewer_name,
            interviewer_persona=request.interviewer_persona,
            interviewer_accent=request.interviewer_accent,
            interview_duration_minutes=request.interview_duration_minutes,
            skills=tuple(_clean_items(request.candidate_skills) or derived_skills),
            projects=tuple(_clean_items(request.project_highlights) or derived_projects),
            resume_summary=resume_summary,
        )

    def generate_seed_questions(
        self,
        *,
        request: StartLiveInterviewRequest,
        session_seed: str,
    ) -> list[LiveInterviewQuestion]:
        profile = self.build_profile(request)
        rng = random.Random(_stable_seed(session_seed, profile))
        question_specs = self._question_specs(profile)
        rng.shuffle(question_specs)

        opening = self._opening_question(profile)
        selected_specs = [opening, *question_specs]
        selected_specs = selected_specs[: request.question_count]

        return [
            LiveInterviewQuestion(
                id=uuid4(),
                order_index=index,
                question_type=question_type,
                question_text=question_text,
                preparation_seconds=10 if index == 1 else 5,
                expected_answer_seconds=120 if question_type != "behavioral_signal" else 90,
            )
            for index, (question_type, question_text) in enumerate(selected_specs, start=1)
        ]

    def build_questions_from_plan(
        self,
        *,
        planned_questions: list[PlannedQuestion],
    ) -> list[LiveInterviewQuestion]:
        return [
            LiveInterviewQuestion(
                id=uuid4(),
                order_index=index,
                question_type=planned.question_type,
                question_text=planned.question_text,
                preparation_seconds=10 if index == 1 else 5,
                expected_answer_seconds=120 if planned.question_type != "behavioral" else 90,
            )
            for index, planned in enumerate(planned_questions, start=1)
        ]

    def _opening_question(self, profile: InterviewProfile) -> tuple[str, str]:
        if profile.resume_summary:
            return (
                "resume_deep_dive",
                (
                    f"I have your resume context. Let us start with {profile.primary_project}. "
                    f"What problem did it solve, what did you personally build, and where "
                    f"{profile.primary_skill} became important?"
                ),
            )

        return (
            "profile_deep_dive",
            (
                f"Let us start with {profile.primary_project}. "
                f"Walk me through the problem, your exact contribution, and where "
                f"{profile.primary_skill} mattered technically."
            ),
        )

    def _question_specs(self, profile: InterviewProfile) -> list[tuple[str, str]]:
        role = profile.target_role.lower()
        mode = profile.mode
        company = profile.company_style
        skill = profile.primary_skill
        project = profile.primary_project

        if mode == "hr" or mode == "behavioral":
            return [
                (
                    "behavioral_signal",
                    (
                        f"Tell me about a time during {project} when you were blocked. "
                        "What did you try first, and how did you decide the next step?"
                    ),
                ),
                (
                    "communication",
                    (
                        f"Explain {project} to a non-technical hiring manager in two minutes, "
                        "without losing the business impact."
                    ),
                ),
                (
                    "ownership",
                    (
                        "Tell me about a decision where you had incomplete information. "
                        "What did you do?"
                    ),
                ),
            ]

        if mode == "dsa":
            return [
                (
                    "dsa_approach",
                    (
                        "We will solve a Two Sum style problem. Before coding, explain "
                        "the brute force approach, the optimized hash-map approach, and "
                        "the edge cases you would test."
                    ),
                ),
                (
                    "dsa_complexity",
                    (
                        "After your implementation, walk me through the time and space "
                        "complexity and why the hash map gives a single-pass solution."
                    ),
                ),
                (
                    "dsa_debugging",
                    (
                        "If one test case fails for duplicate numbers, how would you debug "
                        "the map update order?"
                    ),
                ),
            ]

        if mode == "system_design":
            return [
                (
                    "system_design",
                    (
                        f"Design a production version of {project} for 100,000 users. "
                        "Start with APIs, data model, scaling bottlenecks, and failure handling."
                    ),
                ),
                (
                    "tradeoff_depth",
                    (
                        f"For a {company} interview, compare two architecture choices you could "
                        f"make around {skill}. Which one would you choose and why?"
                    ),
                ),
            ]

        if "ai" in role or "ml" in role:
            return [
                (
                    "ai_pipeline",
                    (
                        f"Suppose {project} needs an AI evaluation pipeline. How would you design "
                        "prompting, validation, retry handling, and evaluation metrics?"
                    ),
                ),
                (
                    "rag_personalization",
                    (
                        f"How would you use resume context and {skill} to generate personalized "
                        "interview questions without hallucinating candidate experience?"
                    ),
                ),
                (
                    "llm_ops",
                    (
                        f"In a {company} environment, how would you monitor LLM quality, latency, "
                        "cost, and prompt regressions?"
                    ),
                ),
                (
                    "production_ai",
                    "What failure modes can happen when an LLM evaluates candidate answers?",
                ),
            ]

        if "backend" in role or "sde" in role:
            return [
                (
                    "backend_design",
                    (
                        f"Take {project}. Design the backend APIs, database tables, and error "
                        "handling needed to ship it reliably."
                    ),
                ),
                (
                    "scaling",
                    (
                        f"If traffic to {project} grew 20x, which bottleneck would you measure "
                        "first and what would you change?"
                    ),
                ),
                (
                    "debugging",
                    (
                        f"A {skill}-related feature is slow in production. Walk me through your "
                        "debugging plan from logs to root cause."
                    ),
                ),
                (
                    "security",
                    (
                        "How would you protect user data, API keys, and uploaded resumes "
                        "in this system?"
                    ),
                ),
            ]

        if "front" in role:
            return [
                (
                    "frontend_architecture",
                    (
                        f"How would you build the live interview UI for {project} so camera, mic, "
                        "transcript, and WebSocket state stay reliable?"
                    ),
                ),
                (
                    "performance",
                    "What would you optimize if the live interview screen becomes slow on mobile?",
                ),
                (
                    "state_management",
                    "How would you prevent stale UI state during realtime follow-up questions?",
                ),
            ]

        return [
                (
                    "technical_depth",
                    (
                        f"Pick one technical decision from {project}. What alternatives "
                        "did you reject, and what tradeoff did you accept?"
                    ),
                ),
            (
                "production_readiness",
                f"How would you make a {skill}-heavy feature reliable in production?",
            ),
            (
                "debugging",
                "Tell me how you debug a live production issue from first alert to permanent fix.",
            ),
        ]


def extract_answer_signals(transcript: str) -> list[str]:
    lower = transcript.lower()
    signals = []
    signal_keywords = {
        "FastAPI": ("fastapi", "api", "async"),
        "PostgreSQL": ("postgres", "postgresql", "database", "sql", "index"),
        "Redis/cache": ("redis", "cache", "caching"),
        "LLM pipeline": ("llm", "prompt", "gemini", "openai", "rag"),
        "observability": ("log", "monitor", "metric", "trace", "latency"),
        "security": ("auth", "jwt", "secret", "permission", "encrypt"),
        "scaling": ("scale", "load", "queue", "worker", "traffic"),
    }
    for label, keywords in signal_keywords.items():
        if any(keyword in lower for keyword in keywords):
            signals.append(label)
    return signals


def _clean_items(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item.strip()][:8]


def _derive_skills_from_resume(resume_text: str) -> list[str]:
    lower = resume_text.lower()
    known_skills = {
        "FastAPI": ("fastapi",),
        "React": ("react", "vite", "next.js", "nextjs"),
        "PostgreSQL": ("postgres", "postgresql", "sql"),
        "Redis": ("redis", "cache", "caching"),
        "RAG": ("rag", "retrieval", "embedding", "vector"),
        "LLM applications": ("llm", "gemini", "openai", "prompt"),
        "Docker": ("docker", "container"),
        "WebSockets": ("websocket", "realtime", "real-time"),
        "Python": ("python",),
        "JavaScript": ("javascript", "typescript"),
    }
    return [
        label
        for label, keywords in known_skills.items()
        if any(keyword in lower for keyword in keywords)
    ][:8]


def _derive_projects_from_resume(resume_text: str) -> list[str]:
    lines = [
        line.strip(" -•\t")
        for line in resume_text.splitlines()
        if 8 <= len(line.strip()) <= 110
    ]
    project_markers = ("project", "built", "developed", "created", "platform", "app")
    projects = [
        line
        for line in lines
        if any(marker in line.lower() for marker in project_markers)
    ]
    if projects:
        return projects[:4]

    if resume_text.strip():
        return ["the strongest resume project"]
    return []


def _default_skill_for_role(role: str) -> str:
    lower_role = role.lower()
    if "ai" in lower_role:
        return "LLM application design"
    if "backend" in lower_role or "sde" in lower_role:
        return "backend system design"
    if "front" in lower_role:
        return "realtime frontend state management"
    return "production engineering"


def _stable_seed(session_seed: str, profile: InterviewProfile) -> int:
    seed_text = "|".join(
        [
            session_seed,
            profile.target_role,
            profile.mode,
            profile.company_style,
            ",".join(profile.skills),
            ",".join(profile.projects),
        ]
    )
    return int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:12], 16)


interview_planner = InterviewPlanner()
