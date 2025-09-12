import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.endpoints.crud import router as router_crud
from app.api.endpoints.meal_plan_service import router as router_meal_plan
from app.core.config.auth import config as cfg_auth
from app.init import init_super_admin
from app.models.auth.api_key import ApiKeyCRUD
from app.models.auth.client import ClientCRUD, ClientRead
from app.models.auth.common.access_policy import AccessPolicy, AccessPolicyScope
from app.models.auth.tenant import TenantCRUD, TenantRead
from app.services.auth.api_key_service import ApiKeyService
from app.services.auth.client_service import ClientService
from app.services.auth.tenant_service import TenantService
from test.common.auth import prepare_accounts
from test.fixtures.mongo import MockedDB


@pytest.fixture(autouse=True)
def init_super_admin_account(mocked_db: MockedDB) -> tuple[TenantRead, ClientRead]:
    return init_super_admin(db=mocked_db.pymongo_db)


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    # User endpionts
    app.include_router(router=router_meal_plan, prefix="/meal-plan")
    # Super admin endpoints
    app.include_router(router=router_crud, prefix="/crud")
    return TestClient(app=app)


def test_super_admin_to_super_admin(test_http_client: TestClient) -> None:
    response = test_http_client.get(
        "/crud/tenant",
        params={
            cfg_auth.SUPER_ADMIN_FIELD: cfg_auth.SUPER_ADMIN_API_KEY,
        },
        headers={
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert response.status_code == status.HTTP_200_OK


def test_super_admin_to_user(test_http_client: TestClient) -> None:
    response = test_http_client.get(
        "/meal-plan",
        params={
            cfg_auth.SUPER_ADMIN_FIELD: cfg_auth.SUPER_ADMIN_API_KEY,
        },
        headers={
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert response.status_code == status.HTTP_200_OK


def test_user_to_super_admin(
    test_http_client: TestClient,
    tenant_service: TenantService,
    tenant_crud: TenantCRUD,
    client_service: ClientService,
    client_crud: ClientCRUD,
    api_key_service: ApiKeyService,
    api_key_crud: ApiKeyCRUD,
) -> None:
    # Create normal client with full access
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

    # Test super admin endoint with no authentication
    response = test_http_client.get(
        "/crud/tenant",
        headers={
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Test super admin endoint with authentication with full permission
    response = test_http_client.get(
        "/crud/tenant",
        headers={
            "Authorization": f"Bearer {client_resp.client_secret_plain}",
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
