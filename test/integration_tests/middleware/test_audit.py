import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.endpoints.auth import router as router_auth
from app.api.endpoints.crud import router as router_crud
from app.api.endpoints.llm_service import router as router_llm
from app.api.middleware import AuditMiddleware
from app.core.config.auth import config as cfg_auth
from app.core.config.llm import config as cfg_llm
from app.init import init_super_admin
from app.models.audit_log import AuditLogCRUD
from app.models.auth.api_key import ApiKeyCRUD, ApiKeyRead
from app.models.auth.client import ClientCRUD, ClientRead
from app.models.auth.common.access_policy import AccessPolicy, AccessPolicyScope
from app.models.auth.tenant import TenantCRUD, TenantRead
from app.models.common.version import Version
from app.schemas.auth.api_key import CreateApiKeyResponse
from app.schemas.auth.client import CreateClientResponse
from app.schemas.auth.tenant import CreateTenantRequest
from app.schemas.auth.token import Token
from app.schemas.llm import GenerateMealPlanRequest
from app.services.auth.api_key_service import ApiKeyService
from app.services.auth.client_service import ClientService
from app.services.auth.tenant_service import TenantService
from app.services.rate_limit_service import RateLimiter
from app.utils.datetime import DatetimeUtil
from test.common.auth import prepare_accounts
from test.fixtures.mongo import MockedDB


@pytest.fixture
def test_http_client(app: FastAPI, mocked_db: MockedDB) -> TestClient:
    # No auth endpoints
    app.include_router(router=router_auth, prefix="/auth")
    # User endpoints
    app.include_router(router=router_llm, prefix="/llm")
    # Super admin endpoints
    app.include_router(router=router_crud, prefix="/crud")

    # Add middleware
    app.add_middleware(
        AuditMiddleware,  # type: ignore  # noqa: PGH003
        db=mocked_db.pymongo_db,
    )
    app.state.limiter = RateLimiter()

    return TestClient(app=app)


@pytest.fixture
def init_super_admin_account(mocked_db: MockedDB) -> tuple[TenantRead, ClientRead]:
    return init_super_admin(db=mocked_db.pymongo_db)


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


def test_audit_super_admin(
    init_super_admin_account: tuple[TenantRead, ClientRead],
    test_http_client: TestClient,
    audit_log_crud: AuditLogCRUD,
) -> None:
    start_tstamp = DatetimeUtil.get_current_timestamp()
    client_ip = "127.0.0.3"

    response = test_http_client.get(
        "/crud/tenant/",
        params={
            cfg_auth.SUPER_ADMIN_FIELD: cfg_auth.SUPER_ADMIN_API_KEY,
        },
        headers={
            "X-Forwarded-For": client_ip,
        },
    )
    assert response.status_code == status.HTTP_200_OK

    audit_logs = audit_log_crud.search()
    assert len(audit_logs) == 1

    audit_log = audit_logs[0]
    super_admin_tenant, super_admin_client = init_super_admin_account
    assert audit_log.tenant_id == super_admin_tenant.id
    assert audit_log.tenant_name == super_admin_tenant.tenant_name
    assert audit_log.client_id == super_admin_client.id
    assert audit_log.client_name == super_admin_client.client_name
    assert audit_log.api_key_id is None
    assert audit_log.api_key_name is None
    assert audit_log.input_prompt is None
    assert audit_log.prompt_version is None
    assert audit_log.model_used is None
    assert audit_log.request_path == "/crud/tenant/"
    assert audit_log.request_query == f"{cfg_auth.SUPER_ADMIN_FIELD}={cfg_auth.SUPER_ADMIN_API_KEY}"
    assert audit_log.request_method == "GET"
    assert audit_log.remote_address == client_ip
    assert audit_log.response_status == status.HTTP_200_OK
    assert audit_log.latency_ms > 0
    assert audit_log.latency_ms <= DatetimeUtil.get_current_timestamp() - start_tstamp


def test_audit_client(
    init_user: tuple[
        TenantRead,
        ClientRead,
        CreateClientResponse,
        ApiKeyRead,
        CreateApiKeyResponse,
    ],
    test_http_client: TestClient,
    audit_log_crud: AuditLogCRUD,
) -> None:
    input_prompt = "Generate a meal plan for sports enthusiasts"
    prompt_version = Version(major=1, minor=0, patch=0)
    client_ip = "127.0.0.3"
    start_tstamp = DatetimeUtil.get_current_timestamp()

    tenant, client, client_resp, api_key, _ = init_user

    # Login
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

    # Try to generate meal plan
    response = test_http_client.post(
        "/llm/generate-meal-plan",
        headers={
            "Authorization": f"Bearer {token.access_token}",
            "X-Forwarded-For": client_ip,
        },
        json=GenerateMealPlanRequest(
            prompt=input_prompt,
            prompt_version=prompt_version,
        ).model_dump(mode="json"),
    )

    assert response.status_code == status.HTTP_200_OK

    audit_logs = audit_log_crud.search()
    assert len(audit_logs) == 1

    audit_log = audit_logs[0]
    assert audit_log.tenant_id == tenant.id
    assert audit_log.tenant_name == tenant.tenant_name
    assert audit_log.client_id == client.id
    assert audit_log.client_name == client.client_name
    assert audit_log.api_key_id is None
    assert audit_log.api_key_name is None
    assert audit_log.input_prompt == input_prompt
    assert audit_log.prompt_version == prompt_version
    assert audit_log.model_used == cfg_llm.LLM_PROVIDER
    assert audit_log.request_path == "/llm/generate-meal-plan"
    assert audit_log.request_query == ""
    assert audit_log.request_method == "POST"
    assert audit_log.remote_address == client_ip
    assert audit_log.response_status == status.HTTP_200_OK
    assert audit_log.latency_ms > 0
    assert audit_log.latency_ms <= DatetimeUtil.get_current_timestamp() - start_tstamp


def test_audit_api_key(
    init_user: tuple[
        TenantRead,
        ClientRead,
        CreateClientResponse,
        ApiKeyRead,
        CreateApiKeyResponse,
    ],
    test_http_client: TestClient,
    audit_log_crud: AuditLogCRUD,
) -> None:
    client_ip = "127.0.0.3"

    tenant, client, _, api_key, api_key_resp = init_user
    start_tstamp = DatetimeUtil.get_current_timestamp()

    response = test_http_client.get(
        "/auth/tenant/get",
        headers={
            "X-Forwarded-For": client_ip,
            cfg_auth.API_KEY_HEADER: api_key_resp.key_plain,
        },
    )
    assert response.status_code == status.HTTP_200_OK

    audit_logs = audit_log_crud.search()
    assert len(audit_logs) == 1

    audit_log = audit_logs[0]
    assert audit_log.tenant_id == tenant.id
    assert audit_log.tenant_name == tenant.tenant_name
    assert audit_log.client_id == client.id
    assert audit_log.client_name == client.client_name
    assert audit_log.api_key_id == api_key.id
    assert audit_log.api_key_name == api_key.key_name
    assert audit_log.input_prompt is None
    assert audit_log.prompt_version is None
    assert audit_log.model_used is None
    assert audit_log.request_path == "/auth/tenant/get"
    assert audit_log.request_query == ""
    assert audit_log.request_method == "GET"
    assert audit_log.remote_address == client_ip
    assert audit_log.response_status == status.HTTP_200_OK
    assert audit_log.latency_ms > 0
    assert audit_log.latency_ms <= DatetimeUtil.get_current_timestamp() - start_tstamp


def test_no_auth(
    test_http_client: TestClient,
    audit_log_crud: AuditLogCRUD,
) -> None:
    response = test_http_client.post(
        "/auth/tenant/register",
        json=CreateTenantRequest(
            tenant_name="test_tenant",
            description="this is a test tenant",
            access_policy=AccessPolicy(
                allowed_ips=["*.*.*.*"],
                scopes=[AccessPolicyScope.ALL],
                rate_limit_per_min=0,
            ),
        ).model_dump(mode="json"),
    )
    assert response.status_code == status.HTTP_200_OK

    assert len(audit_log_crud.search()) == 0
