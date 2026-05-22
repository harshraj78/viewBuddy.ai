from app.ai.agents.planner_agent import InterviewPlannerAgent


def test_planner_agent_parses_json_fenced_question_plan() -> None:
    raw_response = """
```json
{
  "questions": [
    {
      "question_type": "profile_deep_dive",
      "question_text": "Walk me through ViewBuddy.ai and the exact AI component you owned."
    },
    {
      "question_type": "scaling",
      "question_text": "At 100 concurrent live interviews, what bottleneck appears first?"
    }
  ]
}
```
"""

    questions = InterviewPlannerAgent()._parse_questions(raw_response, 2)

    assert len(questions) == 2
    assert questions[0].question_type == "profile_deep_dive"
    assert "ViewBuddy.ai" in questions[0].question_text
