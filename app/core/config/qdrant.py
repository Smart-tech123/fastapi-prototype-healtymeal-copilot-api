from loguru import logger
from pydantic_settings import BaseSettings

from app.core.env import config as cfg_env


class Config(BaseSettings):
    QDRANT_URL: str = cfg_env.QDRANT_URL
    COLLECTION_NAME: str = cfg_env.QDRANT_COLLECTION
    VECTOR_SIZE: int = 1536
    QUERY_LIMIT: int = 5
    QUERY_SCORE_THRESHOLD: float = 0.5


config = Config()

if __name__ == "__main__":
    logger.debug(config.model_dump_json(indent=2))
