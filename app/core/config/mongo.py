from loguru import logger
from pydantic import model_validator
from pydantic_settings import BaseSettings

from app.core.env import AppEnv
from app.core.env import config as cfg_env


class Config(BaseSettings):
    MONGO_URL: str = cfg_env.MONGO_URL
    DB_NAME: str = cfg_env.MONGO_DB

    @model_validator(mode="after")
    def validate_dbname(self) -> "Config":
        if cfg_env.APP_ENV is AppEnv.DEV:
            self.DB_NAME += "_" + AppEnv.DEV.value
        logger.debug(f"mongo_db > {self.MONGO_URL} > {self.DB_NAME}")

        return self


config = Config()
