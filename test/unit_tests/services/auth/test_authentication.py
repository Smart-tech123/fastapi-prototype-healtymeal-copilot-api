import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from loguru import logger

from app.api.endpoints.auth.client import router
from app.models.auth.common.access_policy import AccessPolicy
from app.schemas.auth.client import CreateClientRequest, CreateClientResponse
from app.schemas.auth.tenant import CreateTenantRequest
from app.services.auth.auth_service import AuthService
from app.services.auth.client_service import ClientService
from app.services.auth.tenant_service import TenantService
from app.utils.rand import RandUtil
from test.fixtures.mongo import MockedDB


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=router)
    return TestClient(app=app)


def test_register(test_http_client: TestClient, mocked_db: MockedDB, client_service: ClientService) -> None:
    # Create tenant
    tenant_resp = TenantService(db=mocked_db.pymongo_db).create_tenant(
        create_request=CreateTenantRequest(
            tenant_name=RandUtil.get_str(),
            description=RandUtil.get_str(),
            access_policy=AccessPolicy(
                allowed_ips=[],
                endpoints=[],
                scopes=[],
                rate_limit_per_min=0,
            ),
        )
    )

    # Client info
    client_name = RandUtil.get_str()
    description = RandUtil.get_str()
    access_policy = AccessPolicy(
        allowed_ips=[],
        endpoints=[],
        scopes=[],
        rate_limit_per_min=0,
    )

    # ---- Test OAuth client creation ----
    response = test_http_client.post(
        url="/register",
        json=CreateClientRequest(
            tenant_id=tenant_resp.tenant_id,
            client_name=client_name,
            description=description,
            access_policy=access_policy,
        ).model_dump(mode="json"),
    )
    assert response.status_code == status.HTTP_200_OK

    client_out = CreateClientResponse.model_validate(response.json())

    # Check response
    client_id = client_out.client_id
    logger.debug(f"client_id: {client_id}")
    logger.debug(f"client_secret: {client_out.client_secret_plain}")
    assert client_out.client_name == client_name
    assert client_out.description == description
    assert client_out.access_policy == access_policy

    # Check database fields
    client_read = client_service.get_by_client_id(client_id=client_id)
    assert client_read is not None
    assert client_read.id == client_id
    assert client_read.client_name == client_name
    assert client_read.description == description
    assert client_read.access_policy == access_policy

    # Check client secret
    assert AuthService.verify_password(client_out.client_secret_plain, client_read.client_secret_hash)

    # ---- Test oauth client already exists ----
    response = test_http_client.post(
        url="/register",
        json=CreateClientRequest(
            tenant_id=tenant_resp.tenant_id,
            client_name=client_name,
            description=description,
            access_policy=access_policy,
        ).model_dump(mode="json"),
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    logger.debug(f"response: {response.json()}")


def test_login(test_http_client: TestClient, mocked_db: MockedDB) -> None:
    # Create tenant
    tenant_resp = TenantService(db=mocked_db.pymongo_db).create_tenant(
        create_request=CreateTenantRequest(
            tenant_name=RandUtil.get_str(),
            description=RandUtil.get_str(),
            access_policy=AccessPolicy(
                allowed_ips=[],
                endpoints=[],
                scopes=[],
                rate_limit_per_min=0,
            ),
        )
    )

    # Client info
    client_name = RandUtil.get_str()
    description = "test"
    access_policy = AccessPolicy(
        allowed_ips=[],
        endpoints=[],
        scopes=[],
        rate_limit_per_min=0,
    )

    # Register new oauth client
    response = test_http_client.post(
        url="/register",
        json=CreateClientRequest(
            tenant_id=tenant_resp.tenant_id,
            client_name=client_name,
            description=description,
            access_policy=access_policy,
        ).model_dump(mode="json"),
    )
    assert response.status_code == status.HTTP_200_OK

    client_out = CreateClientResponse.model_validate(response.json())
    client_id = client_out.client_id
    client_secret = client_out.client_secret_plain

    # Check normal login
    response = test_http_client.post(
        url="/login",
        data={
            "client_id": str(client_id),
            "client_secret": client_secret,
        },
    )
    assert response.status_code == status.HTTP_200_OK

    # Check invalid client secret
    response = test_http_client.post(
        url="/login",
        data={
            "client_id": str(client_id),
            "client_secret": "invalid_client_secret",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Check invalid client id
    response = test_http_client.post(
        url="/login",
        data={
            "client_id": str(RandUtil.get_mongo_id()),
            "client_secret": client_secret,
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
