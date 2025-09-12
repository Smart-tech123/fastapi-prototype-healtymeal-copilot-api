import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.endpoints.auth import router as router_auth
from app.api.endpoints.meal_plan_service import router as router_meal_plan
from app.core.config.auth import config as cfg_auth
from app.core.env import AuthMode
from app.models.auth.api_key import ApiKeyCRUD, ApiKeyRead
from app.models.auth.client import ClientCRUD, ClientRead
from app.models.auth.common.access_policy import AccessPolicy, AccessPolicyScope
from app.models.auth.tenant import TenantCRUD, TenantRead
from app.schemas.auth.api_key import CreateApiKeyResponse
from app.schemas.auth.client import CreateClientResponse
from app.schemas.auth.token import Token
from app.services.auth.api_key_service import ApiKeyService
from app.services.auth.client_service import ClientService
from app.services.auth.tenant_service import TenantService
from test.common.auth import prepare_accounts


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=router_auth, prefix="/auth")
    app.include_router(router=router_meal_plan, prefix="/meal-plan")

    return TestClient(app=app)


@pytest.fixture
def init_user(
    tenant_service: TenantService,
    tenant_crud: TenantCRUD,
    client_service: ClientService,
    client_crud: ClientCRUD,
    api_key_service: ApiKeyService,
    api_key_crud: ApiKeyCRUD,
) -> tuple[
    TenantRead,
    ClientRead,
    CreateClientResponse,
    ApiKeyRead,
    CreateApiKeyResponse,
]:
    tenant_resp, client_resp, api_key_resp, tenant, client, api_key = prepare_accounts(
        tenant_service=tenant_service,
        tenant_crud=tenant_crud,
        tenant_name="test_tenant",
        tenant_description="this is a test tenant",
        tenant_policy=AccessPolicy(
            allowed_ips=["*.*.*.*"],
            scopes=[AccessPolicyScope.ALL],
            rate_limit_per_min=0,
        ),
        client_service=client_service,
        client_crud=client_crud,
        client_name="test_client",
        client_description="this is a test client",
        client_policy=AccessPolicy(
            allowed_ips=["*.*.*.*"],
            scopes=[AccessPolicyScope.ALL],
            rate_limit_per_min=0,
        ),
        api_key_service=api_key_service,
        api_key_crud=api_key_crud,
        api_key_name="test_api_key",
        api_key_description="this is a test api key",
        api_key_policy=AccessPolicy(
            allowed_ips=["*.*.*.*"],
            scopes=[AccessPolicyScope.ALL],
            rate_limit_per_min=0,
        ),
    )

    return tenant, client, client_resp, api_key, api_key_resp


def test_auth_mode_both(
    init_user: tuple[
        TenantRead,
        ClientRead,
        CreateClientResponse,
        ApiKeyRead,
        CreateApiKeyResponse,
    ],
    test_http_client: TestClient,
) -> None:
    tenant, client, client_resp, api_key, api_key_resp = init_user
    client_ip = "127.0.0.3"
    cfg_auth.AUTH_MODE = AuthMode.BOTH

    # Check OAuth authentication
    login_resp = test_http_client.post(
        url="/auth/client/login",
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

    response = test_http_client.get(
        "/meal-plan",
        headers={
            "Authorization": f"Bearer {token.access_token}",
            "X-Forwarded-For": client_ip,
        },
    )
    assert response.status_code == status.HTTP_200_OK

    # Check Api Key authentication
    response = test_http_client.get(
        "/auth/tenant/get",
        headers={
            "X-Forwarded-For": client_ip,
            cfg_auth.API_KEY_HEADER: api_key_resp.key_plain,
        },
    )
    assert response.status_code == status.HTTP_200_OK


def test_auth_mode_internal(
    init_user: tuple[
        TenantRead,
        ClientRead,
        CreateClientResponse,
        ApiKeyRead,
        CreateApiKeyResponse,
    ],
    test_http_client: TestClient,
) -> None:
    tenant, client, client_resp, api_key, api_key_resp = init_user
    client_ip = "127.0.0.3"
    old_auth_mode = cfg_auth.AUTH_MODE
    cfg_auth.AUTH_MODE = AuthMode.INTERNAL

    # Check OAuth authentication
    login_resp = test_http_client.post(
        url="/auth/client/login",
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

    response = test_http_client.get(
        "/meal-plan",
        headers={
            "Authorization": f"Bearer {token.access_token}",
            "X-Forwarded-For": client_ip,
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Check Api Key authentication
    response = test_http_client.get(
        "/auth/tenant/get",
        headers={
            "X-Forwarded-For": client_ip,
            cfg_auth.API_KEY_HEADER: api_key_resp.key_plain,
        },
    )
    assert response.status_code == status.HTTP_200_OK

    cfg_auth.AUTH_MODE = old_auth_mode


def test_auth_mode_partner(
    init_user: tuple[
        TenantRead,
        ClientRead,
        CreateClientResponse,
        ApiKeyRead,
        CreateApiKeyResponse,
    ],
    test_http_client: TestClient,
) -> None:
    tenant, client, client_resp, api_key, api_key_resp = init_user
    client_ip = "127.0.0.3"
    old_auth_mode = cfg_auth.AUTH_MODE
    cfg_auth.AUTH_MODE = AuthMode.PARTNER

    # Check OAuth authentication
    login_resp = test_http_client.post(
        url="/auth/client/login",
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

    response = test_http_client.get(
        "/meal-plan",
        headers={
            "Authorization": f"Bearer {token.access_token}",
            "X-Forwarded-For": client_ip,
        },
    )
    assert response.status_code == status.HTTP_200_OK

    # Check Api Key authentication
    response = test_http_client.get(
        "/auth/tenant/get",
        headers={
            "X-Forwarded-For": client_ip,
            cfg_auth.API_KEY_HEADER: api_key_resp.key_plain,
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    cfg_auth.AUTH_MODE = old_auth_mode
