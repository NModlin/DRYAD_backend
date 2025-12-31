from typing import Optional
from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    provider: str = Field(..., description="LLM Provider (openai, anthropic, mock)")
    model_name: str = Field(..., description="Model identifier (e.g. gpt-4o)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None)
    api_key: Optional[str] = Field(default=None, description="Optional override, usually from env")
