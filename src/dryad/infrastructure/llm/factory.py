from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage

from dryad.infrastructure.llm.providers import LLMConfig
from dryad.core.config import settings

class FakeListChatModel(BaseChatModel):
    """
    Simple mock model for testing without API keys.
    """
    responses: list[str] = ["Hello from Mock LLM!", "I am a simulation."]
    i: int = 0

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise NotImplementedError("Use async ainvoke/agenerate")
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.outputs import ChatResult, ChatGeneration
        content = self.responses[self.i % len(self.responses)]
        self.i += 1
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    @property
    def _llm_type(self) -> str:
        return "fake-list"

class LLMFactory:
    @staticmethod
    def create_model(config: LLMConfig) -> BaseChatModel:
        if config.provider == "mock":
            return FakeListChatModel()
            
        if config.provider == "openai":
            api_key = config.api_key or settings.OPENAI_API_KEY
            if not api_key:
                # Fallback to mock if no key provided in dev, or raise error
                if settings.PROJECT_NAME == "DRYAD.AI Backend": # Simple check, better use env var
                     return FakeListChatModel()
                raise ValueError("OpenAI API Key not found")
                
            return ChatOpenAI(
                model=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=api_key
            )
            
        raise ValueError(f"Unsupported provider: {config.provider}")
