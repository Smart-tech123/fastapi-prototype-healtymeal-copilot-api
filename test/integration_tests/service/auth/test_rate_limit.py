import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from loguru import logger

from app.api.endpoints.auth.api_key import router as api_key_router
from app.api.endpoints.auth.client import router as client_router
from app.api.endpoints.auth.tenant import router as tenant_router
from app.api.endpoints.meal_plan_service import router as router_meal_plan
from app.api.endpoints.qdrant_service import router as qdrant_router
from app.api.endpoints.validation_service import router as validation_router
from app.core.config.auth import config as cfg_auth
from app.models.auth.api_key import ApiKeyCRUD
from app.models.auth.client import ClientCRUD
from app.models.auth.common.access_policy import AccessPolicy, AccessPolicyScope
from app.models.auth.tenant import TenantCRUD
from app.schemas.auth.token import Token
from app.services.auth.api_key_service import ApiKeyService
from app.services.auth.client_service import ClientService
from app.services.auth.tenant_service import TenantService
from app.services.rate_limit_service import RateLimiter
from test.common.auth import prepare_accounts
from test.fixtures.qdrant import MockedQdrant


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.state.limiter = RateLimiter()
    app.include_router(router=tenant_router, prefix="/tenant")
    app.include_router(router=client_router, prefix="/client")
    app.include_router(router=api_key_router, prefix="/api_key")
    app.include_router(router=router_meal_plan, prefix="/meal-plan")
    app.include_router(router=validation_router, prefix="/validate")
    app.include_router(router=qdrant_router, prefix="/qdrant")
    return TestClient(app=app)


def test_rate_limit_policy(
    app: FastAPI,
    test_http_client: TestClient,
    tenant_service: TenantService,
    tenant_crud: TenantCRUD,
    client_service: ClientService,
    client_crud: ClientCRUD,
    api_key_service: ApiKeyService,
    api_key_crud: ApiKeyCRUD,
    mocked_qdrant: MockedQdrant,
) -> None:
    # Prepare
    tenant_rate_limit = 32
    client_rate_limit = tenant_rate_limit // 2
    api_key_rate_limit = client_rate_limit // 2
    client_ip = "1.1.1.1"

    tenant_resp, client_resp, api_key_resp, tenant, client, api_key = prepare_accounts(
        tenant_service=tenant_service,
        tenant_crud=tenant_crud,
        tenant_name="test_tenant",
        tenant_description="this is a test tenant",
        tenant_policy=AccessPolicy(
            allowed_ips=["*.*.*.*"],
            scopes=[AccessPolicyScope.ALL],
            rate_limit_per_min=tenant_rate_limit,
        ),
        client_service=client_service,
        client_crud=client_crud,
        client_name="test_client",
        client_description="this is a test client",
        client_policy=AccessPolicy(
            allowed_ips=["*.*.*.*"],
            scopes=[AccessPolicyScope.ALL],
            rate_limit_per_min=client_rate_limit,
        ),
        api_key_service=api_key_service,
        api_key_crud=api_key_crud,
        api_key_name="test_api_key",
        api_key_description="this is a test api key",
        api_key_policy=AccessPolicy(
            allowed_ips=["*.*.*.*"],
            scopes=[AccessPolicyScope.ALL],
            rate_limit_per_min=api_key_rate_limit,
        ),
    )

    # ---- Check client ----
    # Login
    login_resp = test_http_client.post(
        url="/client/login",
        data={
            "client_id": str(client_resp.client_id),
            "client_secret": client_resp.client_secret_plain,
        },
        headers={
            "X-Forwarded-For": client_ip,
        },
    )
    assert login_resp.status_code == status.HTTP_200_OK
    token = Token.model_validate(login_resp.json())

    # Check rate limit
    app.state.limiter.reset_counter(client_ip)
    for i in range(tenant_rate_limit + 1):
        resp = test_http_client.get(
            url=f"/qdrant/{mocked_qdrant.collection_name}/",
            headers={
                "Authorization": f"Bearer {token.access_token}",
                "X-Forwarded-For": client_ip,
            },
        )
        logger.debug(f"[client] iteration: {i}, resp_status: {resp.status_code}")
        if i < client_rate_limit:
            assert resp.status_code == status.HTTP_200_OK
        else:
            assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    # ---- Check api key ----
    app.state.limiter.reset_counter(client_ip)
    for i in range(tenant_rate_limit + 1):
        resp = test_http_client.get(
            url=f"/qdrant/{mocked_qdrant.collection_name}",
            headers={
                cfg_auth.API_KEY_HEADER: api_key_resp.key_plain,
                "X-Forwarded-For": client_ip,
            },
        )
        logger.debug(f"[api_key] iteration: {i}, resp_status: {resp.status_code}")
        if i < api_key_rate_limit:
            assert resp.status_code == status.HTTP_200_OK
        else:
            assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS
