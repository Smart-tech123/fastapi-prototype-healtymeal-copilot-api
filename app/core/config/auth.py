from pydantic_settings import BaseSettings

from app.core.env import AuthMode
from app.core.env import config as cfg_env


class Config(BaseSettings):
    AUTH_MODE: AuthMode = cfg_env.AUTH_MODE

    SUPER_TENANT_NAME: str = "super_tenant"
    SUPER_CLIENT_NAME: str = "super_admin"

    JWT_ALGORITHM_RS256: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = cfg_env.ACCESS_TOKEN_EXPIRE_MINUTES

    CLIENT_SECRET_BYTE_LEN: int = 32
    API_KEY_BYTE_LEN: int = 64

    API_KEY_HEADER: str = "X-API-Key"
    SUPER_ADMIN_FIELD: str = "superAdminKey"
    SUPER_ADMIN_API_KEY: str = cfg_env.SUPER_ADMIN_API_KEY


config = Config()
