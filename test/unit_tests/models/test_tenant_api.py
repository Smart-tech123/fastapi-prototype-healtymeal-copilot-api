import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from app.api.dependency import get_current_client
from app.api.endpoints.crud.tenant import router
from app.models.auth.tenant import Tenant, TenantCRUD, TenantRead
from app.utils.rand import RandUtil
from test.fixtures.dependency import mocked_get_current_client


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=router)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    return TestClient(app=app)


def test_create(test_http_client: TestClient, tenant_crud: TenantCRUD, tenant_creates: list[Tenant]) -> None:
    tenant_crud.clear()
    for obj_create in tenant_creates:
        resp = test_http_client.post(
            "/",
            json=obj_create.model_dump(mode="json"),
        )
        assert resp.status_code == status.HTTP_200_OK

        obj_read = TenantRead.model_validate(resp.json())
        assert obj_read.tenant_name == obj_create.tenant_name

    assert tenant_crud.count() == len(tenant_creates)


def test_get(test_http_client: TestClient, tenant_crud: TenantCRUD, tenant_creates: list[Tenant]) -> None:
    obj_list = tenant_crud.search()

    obj_id = obj_list[RandUtil.get_int(up=len(tenant_creates))].id
    resp = test_http_client.get(f"/{obj_id}")

    assert resp.status_code == status.HTTP_200_OK

    obj_read = TenantRead.model_validate(resp.json())
    assert obj_id == obj_read.id


@pytest.mark.usefixtures("tenant_creates")
def test_get_all(test_http_client: TestClient, tenant_crud: TenantCRUD) -> None:
    obj_list = tenant_crud.search()

    resp = test_http_client.get("/")
    assert resp.status_code == status.HTTP_200_OK

    resp_json = resp.json()
    assert isinstance(resp_json, list)

    assert len(resp_json) == len(obj_list)

    for i in range(len(obj_list)):
        obj_read = TenantRead.model_validate(resp_json[i])
        assert obj_read.id == obj_list[i].id


@pytest.mark.usefixtures("tenant_creates")
def test_update(test_http_client: TestClient, tenant_crud: TenantCRUD) -> None:
    obj_list = tenant_crud.search()
    obj_update = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_tenant_name = RandUtil.get_str()
    obj_update.tenant_name = new_tenant_name

    # Update
    resp = test_http_client.put(
        f"/{obj_update.id}",
        json=obj_update.model_dump(mode="json"),
    )
    assert resp.status_code == status.HTTP_200_OK

    # Check update result
    obj_updated = TenantRead.model_validate(resp.json())
    assert obj_updated.tenant_name == new_tenant_name


@pytest.mark.usefixtures("tenant_creates")
def test_delete(test_http_client: TestClient, tenant_crud: TenantCRUD) -> None:
    obj_list = tenant_crud.search()
    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    resp = test_http_client.delete(f"/{obj_id}")
    assert resp.status_code == status.HTTP_200_OK

    try:
        tenant_crud.get(obj_id=obj_id)
        msg = "Tenant not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
