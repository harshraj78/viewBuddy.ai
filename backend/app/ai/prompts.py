ANSWER_EVALUATION_PROMPT_VERSION = "answer-evaluation-v1"

ANSWER_EVALUATION_SYSTEM_PROMPT = """You are a strict but helpful AI interview evaluator.
Evaluate the candidate's interview answers using a consistent rubric.
Return only valid JSON matching the requested schema.
Do not invent details not present in the transcript.
Reward concrete architecture, tradeoffs, production thinking, and clear communication.
"""


def build_answer_evaluation_prompt(transcript: str, target_role: str, difficulty: str) -> str:
    return f"""
Target role: {target_role}
Difficulty: {difficulty}

Candidate transcript:
{transcript}

Return JSON with this exact shape:
{{
  "overall_score": 0,
  "communication": {{
    "score": 0,
    "strengths": ["string"],
    "improvements": ["string"]
  }},
  "technical": {{
    "score": 0,
    "strengths": ["string"],
    "improvements": ["string"]
  }},
  "behavioral": {{
    "score": 0,
    "strengths": ["string"],
    "improvements": ["string"]
  }},
  "improvement_suggestions": ["string"]
}}
Scores must be integers from 0 to 100.
"""

