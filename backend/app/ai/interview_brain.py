from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.ai.interview_planner import extract_answer_signals


class InterviewMoveType(StrEnum):
    clarify = "clarify"
    deepen = "deepen"
    challenge = "challenge"
    implementation = "implementation"
    scaling = "scaling"
    debugging = "debugging"
    tradeoff = "tradeoff"
    behavioral = "behavioral"
    switch_topic = "switch_topic"


@dataclass
class AnswerAnalysis:
    technologies: list[str]
    answered_topics: list[str]
    weak_areas: list[str]
    strengths: list[str]
    depth_score: int
    confidence_score: int
    is_vague: bool
    sounds_memorized: bool
    missing_tradeoffs: bool
    missing_metrics: bool
    missing_failure_modes: bool


@dataclass
class InterviewBrainState:
    candidate_strengths: list[str] = field(default_factory=list)
    weak_areas: list[str] = field(default_factory=list)
    answered_topics: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    depth_scores: list[int] = field(default_factory=list)
    confidence_scores: list[int] = field(default_factory=list)
    move_history: list[str] = field(default_factory=list)
    turn_count: int = 0
    current_strategy: str = "calibrate"
    last_interviewer_intent: str | None = None
    last_acknowledgement: str | None = None

    @property
    def average_depth(self) -> int:
        if not self.depth_scores:
            return 0
        return round(sum(self.depth_scores) / len(self.depth_scores))

    @property
    def average_confidence(self) -> int:
        if not self.confidence_scores:
            return 0
        return round(sum(self.confidence_scores) / len(self.confidence_scores))


@dataclass(frozen=True)
class InterviewMove:
    move_type: InterviewMoveType
    question: str
    acknowledgement: str
    rationale: str
    should_interrupt: bool = False


class InterviewBrain:
    def analyze_answer(
        self,
        *,
        current_question: str,
        transcript: str,
        interview_context: dict[str, object],
    ) -> AnswerAnalysis:
        words = transcript.split()
        lower = transcript.lower()
        technologies = extract_answer_signals(transcript)
        answered_topics = self._extract_topics(current_question, transcript)
        weak_areas = []
        strengths = []

        has_specifics = any(char.isdigit() for char in transcript) or any(
            term in lower
            for term in (
                "because",
                "tradeoff",
                "latency",
                "throughput",
                "index",
                "metric",
                "failure",
                "tested",
                "measured",
            )
        )
        missing_tradeoffs = not any(term in lower for term in ("tradeoff", "because", "chose"))
        missing_metrics = not any(
            term in lower for term in ("ms", "latency", "metric", "measured", "reduced", "%")
        )
        missing_failure_modes = not any(
            term in lower for term in ("fail", "fallback", "retry", "error", "edge case")
        )
        is_vague = len(words) < 35 or not has_specifics
        sounds_memorized = len(words) > 80 and transcript.count(".") <= 1

        depth_score = 35
        if len(words) >= 45:
            depth_score += 15
        if technologies:
            depth_score += 10
        if not missing_tradeoffs:
            depth_score += 15
        if not missing_metrics:
            depth_score += 10
        if not missing_failure_modes:
            depth_score += 10
        if sounds_memorized:
            depth_score -= 10
        depth_score = max(10, min(depth_score, 95))

        confidence_score = 45
        if any(term in lower for term in ("i built", "i designed", "i implemented", "i chose")):
            confidence_score += 20
        if any(term in lower for term in ("maybe", "probably", "i think", "not sure")):
            confidence_score -= 15
        if is_vague:
            confidence_score -= 10
        confidence_score = max(10, min(confidence_score, 95))

        if is_vague:
            weak_areas.append("specificity")
        if missing_tradeoffs:
            weak_areas.append("tradeoff reasoning")
        if missing_metrics:
            weak_areas.append("measurement")
        if missing_failure_modes:
            weak_areas.append("failure handling")
        if sounds_memorized:
            weak_areas.append("natural explanation")
        if technologies:
            strengths.append(f"mentions {technologies[-1]}")
        if not missing_tradeoffs:
            strengths.append("explains reasoning")
        if not missing_metrics:
            strengths.append("uses metrics")

        return AnswerAnalysis(
            technologies=technologies,
            answered_topics=answered_topics,
            weak_areas=weak_areas,
            strengths=strengths,
            depth_score=depth_score,
            confidence_score=confidence_score,
            is_vague=is_vague,
            sounds_memorized=sounds_memorized,
            missing_tradeoffs=missing_tradeoffs,
            missing_metrics=missing_metrics,
            missing_failure_modes=missing_failure_modes,
        )

    def update_state(
        self,
        *,
        state: InterviewBrainState,
        analysis: AnswerAnalysis,
    ) -> InterviewBrainState:
        state.turn_count += 1
        state.depth_scores.append(analysis.depth_score)
        state.confidence_scores.append(analysis.confidence_score)
        self._append_unique(state.technologies, analysis.technologies)
        self._append_unique(state.answered_topics, analysis.answered_topics)
        self._append_unique(state.weak_areas, analysis.weak_areas)
        self._append_unique(state.candidate_strengths, analysis.strengths)

        if state.average_depth < 55:
            state.current_strategy = "probe fundamentals and specifics"
        elif analysis.missing_failure_modes:
            state.current_strategy = "test production maturity"
        elif analysis.missing_tradeoffs:
            state.current_strategy = "test decision quality"
        else:
            state.current_strategy = "increase difficulty"
        return state

    def plan_next_move(
        self,
        *,
        state: InterviewBrainState,
        analysis: AnswerAnalysis,
        interview_context: dict[str, object],
    ) -> InterviewMove:
        role = str(interview_context.get("target_role", "candidate"))
        company = str(interview_context.get("company_style", "product company"))
        skills = [str(skill) for skill in interview_context.get("skills", [])]
        projects = [str(project) for project in interview_context.get("projects", [])]
        skill = state.technologies[-1] if state.technologies else (skills[0] if skills else "this")
        project = projects[0] if projects else "that project"
        earlier_tech = state.technologies[0] if len(state.technologies) > 1 else skill

        if analysis.is_vague:
            return self._move(
                state,
                InterviewMoveType.clarify,
                self._ack(
                    state,
                    [
                        "I follow the direction, but it is still too broad.",
                        "Okay, let us make that more specific.",
                        "That gives me the outline. I want the implementation detail now.",
                    ],
                ),
                (
                    f"You earlier touched on {earlier_tech}. In {project}, name the exact "
                    "component you built, one design choice you made, and the production "
                    "issue it prevented."
                ),
                "Candidate answer lacked concrete implementation detail.",
                should_interrupt=True,
            )
        if analysis.sounds_memorized:
            return self._move(
                state,
                InterviewMoveType.challenge,
                self._ack(
                    state,
                    [
                        "I want to move away from the polished version.",
                        "Let us make this more real.",
                        "That sounds prepared; I want the actual engineering story.",
                    ],
                ),
                (
                    "Drop the polished version. What actually went wrong while building it, "
                    "and what did you personally change?"
                ),
                "Candidate answer sounded memorized.",
                should_interrupt=True,
            )
        if analysis.missing_tradeoffs:
            return self._move(
                state,
                InterviewMoveType.tradeoff,
                self._ack(
                    state,
                    [
                        "Interesting, let us test the decision behind that.",
                        "Got it. Now I want to understand the tradeoff.",
                        "That makes sense at a high level. Let us compare alternatives.",
                    ],
                ),
                (
                    f"Why did you choose {skill} for this problem, and what alternative "
                    "would become better if constraints changed?"
                ),
                "Candidate did not explain tradeoffs.",
            )
        if analysis.missing_failure_modes:
            return self._move(
                state,
                InterviewMoveType.debugging,
                self._ack(
                    state,
                    [
                        "Good. Now let us put it under production pressure.",
                        "That is reasonable. Let us talk about what breaks.",
                        "Okay, now imagine this fails in front of users.",
                    ],
                ),
                (
                    f"Assume this breaks during a {company} production launch. "
                    "What would fail first, what would you log, and how would you recover?"
                ),
                "Candidate did not discuss failure modes.",
            )
        if analysis.missing_metrics:
            return self._move(
                state,
                InterviewMoveType.scaling,
                self._ack(
                    state,
                    [
                        "That is a useful direction. Let us quantify it.",
                        "Good, now let us attach a measurable signal to it.",
                        "I understand the design. Now tell me how you would measure it.",
                    ],
                ),
                (
                    f"If traffic becomes 100x, which metric tells you {skill} is the "
                    "bottleneck, and what is your first optimization?"
                ),
                "Candidate did not provide measurable evidence.",
            )
        if state.turn_count >= 4 and InterviewMoveType.behavioral not in state.move_history:
            return self._move(
                state,
                InterviewMoveType.behavioral,
                self._ack(
                    state,
                    [
                        "I am going to switch gears briefly.",
                        "Before we continue technically, one collaboration question.",
                        "Let us briefly cover how you communicate technical decisions.",
                    ],
                ),
                (
                    f"You earlier mentioned {earlier_tech}. Tell me about a moment where "
                    "you had to defend that technical decision to someone else."
                ),
                "Interview should sample behavioral communication after technical depth.",
            )

        return self._move(
            state,
            InterviewMoveType.deepen,
            self._ack(
                state,
                [
                    "Good, let us go one level deeper.",
                    "That is a solid start. I want to push one layer further.",
                    "Okay, now connect that to the earlier design choice.",
                ],
            ),
            (
                f"Connect your earlier {earlier_tech} point to this answer. "
                f"What assumption would a senior {role} interviewer challenge?"
            ),
            "Candidate gave enough substance; increase difficulty with continuity.",
        )

    def _move(
        self,
        state: InterviewBrainState,
        move_type: InterviewMoveType,
        acknowledgement: str,
        question: str,
        rationale: str,
        *,
        should_interrupt: bool = False,
    ) -> InterviewMove:
        state.move_history.append(move_type.value)
        state.last_interviewer_intent = rationale
        state.last_acknowledgement = acknowledgement
        return InterviewMove(
            move_type=move_type,
            acknowledgement=acknowledgement,
            question=question,
            rationale=rationale,
            should_interrupt=should_interrupt,
        )

    def _ack(self, state: InterviewBrainState, options: list[str]) -> str:
        for option in options:
            if option != state.last_acknowledgement:
                return option
        return options[0]

    def _extract_topics(self, current_question: str, transcript: str) -> list[str]:
        text = f"{current_question} {transcript}".lower()
        topics = []
        topic_keywords = {
            "architecture": ("architecture", "design", "system"),
            "api": ("api", "endpoint", "fastapi"),
            "database": ("database", "postgres", "sql", "schema"),
            "ai": ("llm", "rag", "prompt", "gemini", "model"),
            "scaling": ("scale", "traffic", "latency", "throughput"),
            "security": ("auth", "jwt", "secret", "permission"),
        }
        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                topics.append(topic)
        return topics or ["project depth"]

    def _append_unique(self, target: list[str], values: list[str]) -> None:
        for value in values:
            if value not in target:
                target.append(value)


interview_brain = InterviewBrain()
