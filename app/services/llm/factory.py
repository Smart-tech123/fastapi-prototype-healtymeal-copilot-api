from app.core.config.llm import LLMProvider
from app.core.config.llm import config as cfg_llm
from app.services.llm.internal.base import BaseLLMService
from app.services.llm.internal.claude import ClaudeService
from app.services.llm.internal.gemini import GeminiService
from app.services.llm.internal.openai import OpenAIService


class LLMFactory:
    """
    Factory for LLM services.
    LLMFactory can be used to get a specific LLM service by provider.
    """

    @classmethod
    def get(cls, provider: LLMProvider) -> BaseLLMService:
        """
        Get a specific LLM service by provider.

        Args:
            provider (LLMProvider): LLM provider

        Returns:
            BaseLLMService: LLM service
        """
        if provider == LLMProvider.OPENAI:
            return OpenAIService(
                model=cfg_llm.OPENAI_MODEL,
                api_key=cfg_llm.OPENAI_API_KEY,
            )

        if provider == LLMProvider.GOOGLE_GEMINI:
            return GeminiService(
                model=cfg_llm.GEMINI_MODEL,
                api_key=cfg_llm.GEMINI_API_KEY,
            )

        if provider == LLMProvider.ANTHROPIC_CLAUDE:
            return ClaudeService(
                model=cfg_llm.CLAUDE_MODEL,
                api_key=cfg_llm.CLAUDE_API_KEY,
            )

        msg = f"Unknown LLM provider: {provider}"
        raise ValueError(msg)
