import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from loguru import logger

from app.api.endpoints.auth.api_key import router as api_key_router
from app.api.endpoints.auth.client import router as client_router
from app.api.endpoints.auth.tenant import router as tenant_router
from app.api.endpoints.meal_plan_service import router as router_meal_plan
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
from test.common.auth import prepare_accounts


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=tenant_router, prefix="/tenant")
    app.include_router(router=client_router, prefix="/client")
    app.include_router(router=api_key_router, prefix="/api_key")
    app.include_router(router=router_meal_plan, prefix="/meal-plan")
    app.include_router(router=validation_router, prefix="/validate")
    return TestClient(app=app)


def test_scope_policy(
    test_http_client: TestClient,
    tenant_service: TenantService,
    tenant_crud: TenantCRUD,
    client_service: ClientService,
    client_crud: ClientCRUD,
    api_key_service: ApiKeyService,
    api_key_crud: ApiKeyCRUD,
) -> None:
    # Prepare
    tenant_resp, client_resp, api_key_resp, tenant, client, api_key = prepare_accounts(
        tenant_service=tenant_service,
        tenant_crud=tenant_crud,
        tenant_name="test_tenant",
        tenant_description="this is a test tenant",
        tenant_policy=AccessPolicy(
            allowed_ips=["*.*.*.*"],
            scopes=[AccessPolicyScope.TENANT, AccessPolicyScope.FOOD_PLAN, AccessPolicyScope.VALIDATE],
            rate_limit_per_min=0,
        ),
        client_service=client_service,
        client_crud=client_crud,
        client_name="test_client",
        client_description="this is a test client",
        client_policy=AccessPolicy(
            allowed_ips=["*.*.*.*"],
            scopes=[AccessPolicyScope.TENANT, AccessPolicyScope.FOOD_PLAN],
            rate_limit_per_min=0,
        ),
        api_key_service=api_key_service,
        api_key_crud=api_key_crud,
        api_key_name="test_api_key",
        api_key_description="this is a test api key",
        api_key_policy=AccessPolicy(
            allowed_ips=["*.*.*.*"],
            scopes=[AccessPolicyScope.TENANT],
            rate_limit_per_min=0,
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
    )
    assert login_resp.status_code == status.HTTP_200_OK
    token = Token.model_validate(login_resp.json())

    # Check allowed resource
    resp = test_http_client.get(
        url="/tenant/get",
        headers={
            "Authorization": f"Bearer {token.access_token}",
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert resp.status_code == status.HTTP_200_OK

    # Check not allowed resource
    get_resp = test_http_client.post(
        url="/validate/validate-meal-plan",
        json={"plan_name": "test_meal_plan"},
        headers={
            "Authorization": f"Bearer {token.access_token}",
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert get_resp.status_code == status.HTTP_403_FORBIDDEN
    logger.debug(f"error: {get_resp.json()}")

    # ---- Check api key ----
    # Check allowed resource
    resp = test_http_client.get(
        url="/tenant/get",
        headers={
            cfg_auth.API_KEY_HEADER: api_key_resp.key_plain,
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert resp.status_code == status.HTTP_200_OK

    # Check not allowed resource
    get_resp = test_http_client.get(
        url="/meal-plan",
        headers={
            cfg_auth.API_KEY_HEADER: api_key_resp.key_plain,
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert get_resp.status_code == status.HTTP_403_FORBIDDEN
    logger.debug(f"error: {get_resp.json()}")


def test_ip_policy(
    test_http_client: TestClient,
    tenant_service: TenantService,
    tenant_crud: TenantCRUD,
    client_service: ClientService,
    client_crud: ClientCRUD,
    api_key_service: ApiKeyService,
    api_key_crud: ApiKeyCRUD,
) -> None:
    # Prepare
    tenant_resp, client_resp, api_key_resp, tenant, client, api_key = prepare_accounts(
        tenant_service=tenant_service,
        tenant_crud=tenant_crud,
        tenant_name="test_tenant",
        tenant_description="this is a test tenant",
        tenant_policy=AccessPolicy(
            allowed_ips=["127.0.0.1", "127.0.0.2", "127.0.0.3"],
            scopes=[AccessPolicyScope.ALL],
            rate_limit_per_min=0,
        ),
        client_service=client_service,
        client_crud=client_crud,
        client_name="test_client",
        client_description="this is a test client",
        client_policy=AccessPolicy(
            allowed_ips=["127.0.0.1", "127.0.0.2"],
            scopes=[AccessPolicyScope.ALL],
            rate_limit_per_min=0,
        ),
        api_key_service=api_key_service,
        api_key_crud=api_key_crud,
        api_key_name="test_api_key",
        api_key_description="this is a test api key",
        api_key_policy=AccessPolicy(
            allowed_ips=["127.0.0.1"],
            scopes=[AccessPolicyScope.ALL],
            rate_limit_per_min=0,
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
    )
    assert login_resp.status_code == status.HTTP_200_OK
    token = Token.model_validate(login_resp.json())

    # Check allowed ip
    resp = test_http_client.get(
        url="/tenant/get",
        headers={
            "Authorization": f"Bearer {token.access_token}",
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert resp.status_code == status.HTTP_200_OK

    # Check not allowed ip
    get_resp = test_http_client.get(
        url="/tenant/get",
        headers={
            "Authorization": f"Bearer {token.access_token}",
            "X-Forwarded-For": "127.0.0.3",
        },
    )
    assert get_resp.status_code == status.HTTP_403_FORBIDDEN
    logger.debug(f"error: {get_resp.json()}")

    # ---- Check api key ----
    # Check allowed resource
    resp = test_http_client.get(
        url="/tenant/get",
        headers={
            cfg_auth.API_KEY_HEADER: api_key_resp.key_plain,
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert resp.status_code == status.HTTP_200_OK

    # Check not allowed resource
    get_resp = test_http_client.get(
        url="/tenant/get",
        headers={
            cfg_auth.API_KEY_HEADER: api_key_resp.key_plain,
            "X-Forwarded-For": "127.0.0.2",
        },
    )
    assert get_resp.status_code == status.HTTP_403_FORBIDDEN
    logger.debug(f"error: {get_resp.json()}")
