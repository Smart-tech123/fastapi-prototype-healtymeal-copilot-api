from pydantic_settings import BaseSettings

from app.core.env import AppEnv
from app.core.env import config as cfg_env


class Config(BaseSettings):
    DEBUG: bool = cfg_env.APP_ENV is AppEnv.DEV
    REQUEST_TIMEOUT: float = 30.0
    HISTORY_KEYFRAME_INTERVAL: int = 100


config = Config()
