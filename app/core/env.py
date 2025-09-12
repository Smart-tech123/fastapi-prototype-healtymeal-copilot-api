from enum import StrEnum

from loguru import logger
from pydantic import EmailStr, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    DEV = "dev"
    PROD = "prod"


class AuthMode(StrEnum):
    INTERNAL = "internal"
    PARTNER = "partner"
    BOTH = "both"


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    APP_ENV: AppEnv = AppEnv.DEV

    # ---- Application metadata ----
    APP_TITLE: str = "Healthy Meal Copilot API"
    APP_NAME: str = "Healthy Meal Copilot"
    APP_URL: HttpUrl = HttpUrl("https://copilot.healthymeal.ai")
    APP_EMAIL: EmailStr = "admin@healthymeal.ai"
    APP_PORT: int = 8000

    # ---- Authentication ----
    AUTH_MODE: AuthMode = AuthMode.BOTH
    SUPER_ADMIN_API_KEY: str = "default_super_admin_api_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ---- MongoDB configuration ----
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB: str = "healthymeal_copilot"

    # ---- Qdrant configuration ----
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "healthymeal_copilot"

    # ---- LLM configuration ----
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = ""

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = ""

    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = ""


config = Config()

logger.debug(f"Environment variables: {config.model_dump_json(indent=2)}")
