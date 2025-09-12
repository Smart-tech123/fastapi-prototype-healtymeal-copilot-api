from collections.abc import Generator
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, Request
from fastapi.security import SecurityScopes
from jose import jwt
from loguru import logger
from pymongo.database import Database
from qdrant_client import QdrantClient

from app.core.config.auth import config as cfg_auth
from app.core.config.mongo import config as cfg_mongo
from app.db.mongo import pymongo_client
from app.db.qdrant import qdrant_client
from app.models.auth.api_key import ApiKeyCRUD, ApiKeyRead
from app.models.auth.client import Client, ClientCRUD, ClientRead
from app.models.auth.common.access_policy import AccessPolicy, AccessPolicyScope
from app.models.auth.tenant import TenantCRUD, TenantKey, TenantRead, TenantStatus
from app.schemas.auth.token import TokenData
from app.schemas.errors import (
    ErrorCode401,
    ErrorCode403,
    ForbiddenException,
    UnauthorizedException,
)
from app.services.auth.auth_service import AuthService
from app.services.ipfilter import IPFilterService
from app.utils.http import HttpUtil

if TYPE_CHECKING:
    from app.services.rate_limit_service import RateLimiter


def get_db() -> Generator[Database[dict[str, Any]], Any, None]:
    pymongo_db: Database[dict[str, Any]] = pymongo_client.get_database(cfg_mongo.DB_NAME)
    try:
        yield pymongo_db
    finally:
        pass


def get_qdrant_client() -> Generator[QdrantClient, Any, None]:
    try:
        yield qdrant_client
    finally:
        pass


def get_super_admin_client(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    super_admin_query: Annotated[str, Depends(AuthService.super_admin_key)],
) -> ClientRead:
    if super_admin_query != cfg_auth.SUPER_ADMIN_API_KEY:
        raise UnauthorizedException(
            error_code=ErrorCode401.INVALID_SUPER_ADMIN_KEY,
            message="Invalid super admin key",
        )

    res = ClientCRUD(db=db).search({Client.Field.client_name: cfg_auth.SUPER_CLIENT_NAME})
    if not res or len(res) > 1:
        raise UnauthorizedException(
            error_code=ErrorCode401.INVALID_SUPER_ADMIN_KEY,
            message="Super admin client error",
        )

    return res[0]


def get_current_tenant(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    request: Request,
    security_scopes: SecurityScopes,
    super_admin_query: Annotated[str, Depends(AuthService.super_admin_key)],
    token: Annotated[str | None, Depends(AuthService.oauth2_scheme)],
    api_key_header: Annotated[str | None, Depends(AuthService.api_key_header)],
) -> TenantRead:
    client = get_current_client(
        request=request,
        security_scopes=security_scopes,
        super_admin_qeury=super_admin_query,
        token=token,
        api_key_header=api_key_header,
        db=db,
    )

    tenant = TenantCRUD(db=db).get(obj_id=client.tenant_id)
    if tenant.status is TenantStatus.INACTIVE:
        raise ForbiddenException(
            error_code=ErrorCode403.TENANT_INACTIVE,
            message="Tenant is not active",
        )
    return tenant


def get_current_client(
    request: Request,
    security_scopes: SecurityScopes,
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    super_admin_qeury: Annotated[str | None, Depends(AuthService.super_admin_key)],
    token: Annotated[str | None, Depends(AuthService.oauth2_scheme)],
    api_key_header: Annotated[str | None, Depends(AuthService.api_key_header)],
) -> ClientRead:
    # Check if token or API key is provided
    if not token and not api_key_header and not super_admin_qeury:
        logger.error("No token or API key provided")
        raise UnauthorizedException(
            error_code=ErrorCode401.MISSING_CREDENTIALS,
            message="No authentication credentials are provided",
        )

    tenant_crud = TenantCRUD(db=db)
    client_crud = ClientCRUD(db=db)

    policies: list[AccessPolicy | None] = []

    if super_admin_qeury:
        client = get_super_admin_client(
            db=db,
            super_admin_query=super_admin_qeury,
        )
        tenant = tenant_crud.get(obj_id=client.tenant_id)

    elif token and AuthService.is_oauth2_auth_supported():
        try:
            # Get tenant
            header = jwt.get_unverified_header(token)
            tenant_id = header.get("tenant_id")
            kid = header.get("kid")
            tenant = tenant_crud.get(obj_id=tenant_id)
        except Exception:
            raise UnauthorizedException(  # noqa: B904
                error_code=ErrorCode401.INVALID_TOKEN,
                message="Provided token is invalid",
            )

        # Get public key
        tenant_key: TenantKey | None = None
        for key in tenant.keys:
            if key.kid == kid:
                tenant_key = key
                break
        if not tenant_key:
            raise UnauthorizedException(
                error_code=ErrorCode401.INVALID_TOKEN,
                message="Tenant key is not found",
            )

        try:
            # Decode JWT
            payload = jwt.decode(token, tenant_key.public_jwk, algorithms=[cfg_auth.JWT_ALGORITHM_RS256])
        except Exception:
            raise UnauthorizedException(  # noqa: B904
                error_code=ErrorCode401.INVALID_TOKEN,
                message="Provided token is invalid",
            )

        client_id: str | None = payload.get("sub")
        if client_id is None:
            raise UnauthorizedException(
                error_code=ErrorCode401.INVALID_TOKEN,
                message="Client id is not found",
            )

        token_scopes = payload.get("scopes", [])
        token_data = TokenData(client_id=client_id, scopes=token_scopes)

        # Verify access policy
        client = client_crud.get(obj_id=token_data.client_id)
        if tenant.id != client.tenant_id:
            raise UnauthorizedException(
                error_code=ErrorCode401.INVALID_TOKEN,
                message="Tenants mismatched",
            )

    elif api_key_header and AuthService.is_api_key_auth_supported():
        api_key = get_current_api_key(
            request=request,
            security_scopes=security_scopes,
            api_key_header=api_key_header,
            db=db,
        )
        client = client_crud.get(obj_id=api_key.client_id)
        tenant = tenant_crud.get(obj_id=client.tenant_id)

        # Append access policy for api key
        policies.append(api_key.access_policy)
    else:
        raise UnauthorizedException(
            error_code=ErrorCode401.MISSING_CREDENTIALS,
            message="No authentication credentials are provided",
        )

    # Check if tenant is active
    if tenant.status is TenantStatus.INACTIVE:
        raise ForbiddenException(
            error_code=ErrorCode403.TENANT_INACTIVE,
            message="Tenant is not active",
        )

    # Append access policy for client and tenant
    policies.append(client.access_policy)
    policies.append(tenant.access_policy)

    # Verify access policy
    verify_access_policy(
        request=request,
        security_scopes=security_scopes,
        policies=policies,
    )

    return client


def get_current_api_key(
    request: Request,
    security_scopes: SecurityScopes,
    api_key_header: Annotated[str, Depends(AuthService.api_key_header)],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
) -> ApiKeyRead:
    try:
        # Parse API key
        key_id = api_key_header.split(".")[0]
        key_secret_plain = api_key_header.split(".")[1]

        # Verify API Key
        api_key = ApiKeyCRUD(db=db).get(obj_id=key_id)
        if not AuthService.verify_api_key(key_secret_plain, api_key.key_secret_hash):
            msg = "Invalid API key"
            raise ValueError(msg)  # noqa: TRY301

        # Verify access policy
        client = ClientCRUD(db=db).get(obj_id=api_key.client_id)
        tenant = TenantCRUD(db=db).get(obj_id=client.tenant_id)

    except Exception:
        raise UnauthorizedException(  # noqa: B904
            error_code=ErrorCode401.INVALID_API_KEY,
            message="Provided api key is invalid",
        )

    # Check if tenant is active
    if tenant.status is TenantStatus.INACTIVE:
        raise ForbiddenException(
            error_code=ErrorCode403.TENANT_INACTIVE,
            message="Tenant is not active",
        )

    verify_access_policy(
        security_scopes=security_scopes,
        request=request,
        policies=[
            api_key.access_policy,
            client.access_policy,
            tenant.access_policy,
        ],
    )

    return api_key


def verify_access_policy(
    request: Request,
    security_scopes: SecurityScopes,
    policies: list[AccessPolicy | None],
) -> None:
    for policy in policies:
        if not policy:
            continue

        # Verify scopes
        if AccessPolicyScope.ALL.value not in policy.scopes:
            for scope in security_scopes.scopes:
                if scope not in policy.scopes:
                    raise ForbiddenException(
                        error_code=ErrorCode403.SCOPE_DENIED,
                        message="Not enough permissions",
                    )

        # Verify ip address
        if not request.client:
            raise ForbiddenException(
                error_code=ErrorCode403.IP_NOT_ALLOWED,
                message="Remote IP address is not allowed",
            )

        ip_address = HttpUtil.get_remote_address(request)
        if not IPFilterService(allow_patterns=policy.allowed_ips).is_allowed(ip_address):
            raise ForbiddenException(
                error_code=ErrorCode403.IP_NOT_ALLOWED,
                message="Remote IP address not allowed",
            )


def rate_limited(
    request: Request,
    security_scopes: SecurityScopes,
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    super_admin_query: Annotated[str | None, Depends(AuthService.super_admin_key)],
    token: Annotated[str | None, Depends(AuthService.oauth2_scheme)],
    api_key_header: Annotated[str | None, Depends(AuthService.api_key_header)],
) -> Any:  # noqa: ANN401
    rate_limit = float("inf")
    if super_admin_query:
        client = get_super_admin_client(
            db=db,
            super_admin_query=super_admin_query,
        )
        if client.access_policy and client.access_policy.rate_limit_per_min:
            rate_limit = min(
                client.access_policy.rate_limit_per_min,
                rate_limit,
            )
    elif token and AuthService.is_oauth2_auth_supported():
        client = get_current_client(
            request=request,
            security_scopes=security_scopes,
            super_admin_qeury=super_admin_query,
            token=token,
            api_key_header=api_key_header,
            db=db,
        )
        if client.access_policy and client.access_policy.rate_limit_per_min:
            rate_limit = min(
                client.access_policy.rate_limit_per_min,
                rate_limit,
            )
    elif api_key_header and AuthService.is_api_key_auth_supported():
        # Get API key rate limit
        api_key = get_current_api_key(
            request=request,
            security_scopes=security_scopes,
            api_key_header=api_key_header,
            db=db,
        )
        if api_key.access_policy and api_key.access_policy.rate_limit_per_min:
            rate_limit = min(
                api_key.access_policy.rate_limit_per_min,
                rate_limit,
            )

        # Get client rate limit
        client = ClientCRUD(db=db).get(obj_id=api_key.client_id)
        if client.access_policy and client.access_policy.rate_limit_per_min:
            rate_limit = min(
                rate_limit,
                client.access_policy.rate_limit_per_min,
            )
    else:
        raise UnauthorizedException(
            error_code=ErrorCode401.MISSING_CREDENTIALS,
            message="No authentication credentials are provided",
        )

    tenant = TenantCRUD(db=db).get(obj_id=client.tenant_id)
    if tenant.access_policy.rate_limit_per_min:
        rate_limit = min(
            rate_limit,
            tenant.access_policy.rate_limit_per_min,
        )

    # Apply rate limit
    if rate_limit == float("inf"):
        rate_limit = 0

    limiter: RateLimiter = request.app.state.limiter
    limiter.increase_counter(
        key=HttpUtil.get_remote_address(request),
        limit_min=int(rate_limit),
    )
