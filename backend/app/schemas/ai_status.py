from pydantic import BaseModel


class AIStatusResponse(BaseModel):
    interview_llm_provider: str
    interview_model: str
    gemini_key_configured: bool
    local_llm_base_url: str
    local_llm_model: str
    fallback_enabled: bool
