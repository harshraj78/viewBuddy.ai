from app.ai.interview_planner import extract_answer_signals


class MemoryManagerAgent:
    def update_answer_signals(self, *, existing: list[str], transcript: str) -> None:
        for signal in extract_answer_signals(transcript):
            if signal not in existing:
                existing.append(signal)


memory_manager_agent = MemoryManagerAgent()
