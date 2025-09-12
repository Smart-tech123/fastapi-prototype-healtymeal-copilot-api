from enum import StrEnum

from loguru import logger
from pydantic_settings import BaseSettings

from app.core.env import config as cfg_env
from app.models.common.version import Version


class LLMProvider(StrEnum):
    OPENAI = "openai"
    GOOGLE_GEMINI = "google_gemini"
    ANTHROPIC_CLAUDE = "anthropic_claude"


class Config(BaseSettings):
    EMBEDDING_MODEL: str = "text-embedding-ada-002"

    # Fallback configuration
    MAX_RETRIES: int = 3

    # LLM configuration
    LLM_PROVIDER: LLMProvider = LLMProvider.OPENAI

    OPENAI_API_KEY: str = cfg_env.OPENAI_API_KEY
    OPENAI_MODEL: str = cfg_env.OPENAI_MODEL

    GEMINI_API_KEY: str = cfg_env.GEMINI_API_KEY
    GEMINI_MODEL: str = cfg_env.GEMINI_MODEL

    CLAUDE_API_KEY: str = cfg_env.CLAUDE_API_KEY
    CLAUDE_MODEL: str = cfg_env.CLAUDE_MODEL

    # Prompt configuration
    DEFAULT_PROMPT_VERSION: Version = Version(major=1, minor=0, patch=0)
    TEMPLATE_EXT: str = "j2"

    # Qdrant Context
    ADD_CONTEXT: bool = True


config = Config()

if __name__ == "__main__":
    logger.debug(config.model_dump_json(indent=2))
