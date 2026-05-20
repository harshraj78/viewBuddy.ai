from app.ai.interview_brain import AnswerAnalysis, interview_brain


class CandidateAnalyzerAgent:
    def analyze(
        self,
        *,
        current_question: str,
        transcript: str,
        interview_context: dict[str, object],
    ) -> AnswerAnalysis:
        return interview_brain.analyze_answer(
            current_question=current_question,
            transcript=transcript,
            interview_context=interview_context,
        )


candidate_analyzer_agent = CandidateAnalyzerAgent()
