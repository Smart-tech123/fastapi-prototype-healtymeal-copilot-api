import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.security import APIKeyHeader, APIKeyQuery, OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

from app.core.config.auth import config as cfg_auth
from app.core.env import AuthMode
from app.models.auth.common.access_policy import AccessPolicyScope
from app.models.auth.tenant import TenantKey


class AuthService:
    # Password context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # FastAPI security
    oauth2_scheme = OAuth2PasswordBearer(
        tokenUrl="/auth/client/login",
        scopes={
            AccessPolicyScope.ALL: "All Access",
            AccessPolicyScope.TENANT: "Tenant Management Access",
            AccessPolicyScope.QDRANT: "Qdrant Management Access",
            AccessPolicyScope.FOOD_PLAN: "Meal plan Management Access",
            AccessPolicyScope.GENERATE: "Meal plan generation by LLM Access",
            AccessPolicyScope.VALIDATE: "Meal plan validation Access",
            AccessPolicyScope.VERSION_SERVICE: "Version Management Access",
        },
        auto_error=False,
    )
    api_key_header = APIKeyHeader(name=cfg_auth.API_KEY_HEADER, auto_error=False)
    super_admin_key = APIKeyQuery(name=cfg_auth.SUPER_ADMIN_FIELD, auto_error=False)

    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Returns a hashed password

        Args:
            password (str): Plain password

        Returns:
            str: Hashed password
        """
        return cls.pwd_context.hash(password)  # type: ignore  # noqa: PGH003

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Returns True if the plain password matches the hashed password

        Args:
            plain_password (str): Plain password
            hashed_password (str): Hashed password

        Returns:
            bool: True if the plain password matches the hashed password
        """
        return cls.pwd_context.verify(plain_password, hashed_password)  # type: ignore  # noqa: PGH003

    @classmethod
    def create_jwt_access_token_rs256(
        cls,
        data: dict[str, Any],
        tenant_id: str,
        tenant_key: TenantKey,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Returns an access token

        Args:
            data (dict[str, Any]): Token data
            priv_pem (str): Private key
            expires_delta (timedelta | None, optional): Token expiration time. Defaults to None.

        Returns:
            str: Access token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(tz=UTC) + expires_delta
        else:
            expire = datetime.now(tz=UTC) + timedelta(minutes=cfg_auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})

        return jwt.encode(  # type: ignore  # noqa: PGH003
            to_encode,
            tenant_key.private_pem,
            algorithm=cfg_auth.JWT_ALGORITHM_RS256,
            headers={
                "tenant_id": tenant_id,
                "kid": tenant_key.kid,
            },
        )

    @classmethod
    def generate_client_secret(cls) -> str:
        """
        Generates a new client secret

        Returns:
            str: Client secret
        """
        return secrets.token_urlsafe(cfg_auth.CLIENT_SECRET_BYTE_LEN)

    @classmethod
    def generate_api_key(cls) -> str:
        """
        Generates a new API key

        Returns:
            str: API key
        """
        return secrets.token_urlsafe(cfg_auth.API_KEY_BYTE_LEN)

    @classmethod
    def hash_api_key(cls, api_key: str) -> str:
        """
        Returns a hashed API key

        Args:
            api_key (str): API key

        Returns:
            str: Hashed API key
        """
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    @classmethod
    def verify_api_key(cls, api_key: str, hashed_api_key: str) -> bool:
        """
        Returns True if the API key matches the hashed API key

        Args:
            api_key (str): API key
            hashed_api_key (str): Hashed API key

        Returns:
            bool: True if the API key matches the hashed API key
        """
        return cls.hash_api_key(api_key) == hashed_api_key

    @classmethod
    def is_api_key_auth_supported(cls) -> bool:
        return cfg_auth.AUTH_MODE in [
            AuthMode.INTERNAL,
            AuthMode.BOTH,
        ]

    @classmethod
    def is_oauth2_auth_supported(cls) -> bool:
        return cfg_auth.AUTH_MODE in [
            AuthMode.PARTNER,
            AuthMode.BOTH,
        ]
