import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from loguru import logger

from app.api.dependency import get_current_client
from app.api.endpoints.crud.api_key import router
from app.models.auth.api_key import ApiKey, ApiKeyCRUD, ApiKeyRead, ApiKeyUpdate
from app.utils.rand import RandUtil
from test.fixtures.dependency import mocked_get_current_client


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=router)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    return TestClient(app=app)


def test_create(test_http_client: TestClient, api_key_crud: ApiKeyCRUD, api_key_creates: list[ApiKey]) -> None:
    api_key_crud.clear()
    for obj_create in api_key_creates:
        resp = test_http_client.post(
            "/",
            json=obj_create.model_dump(mode="json"),
        )
        assert resp.status_code == status.HTTP_200_OK

        obj_out = ApiKeyRead.model_validate(resp.json())
        assert obj_out.key_name == obj_create.key_name
        logger.debug(f"api_key_id: {obj_out.id}")
        logger.debug(f"api_key_hash: {obj_out.key_secret_hash}")

    assert api_key_crud.count() == len(api_key_creates)


def test_get(test_http_client: TestClient, api_key_crud: ApiKeyCRUD, api_key_creates: list[ApiKey]) -> None:
    obj_list = api_key_crud.search()

    api_key_id = obj_list[RandUtil.get_int(up=len(api_key_creates))].id
    resp = test_http_client.get(f"/{api_key_id}")

    assert resp.status_code == status.HTTP_200_OK

    obj_read = ApiKeyRead.model_validate(resp.json())
    assert api_key_id == obj_read.id


@pytest.mark.usefixtures("api_key_creates")
def test_get_all(test_http_client: TestClient, api_key_crud: ApiKeyCRUD) -> None:
    obj_list = api_key_crud.search()

    resp = test_http_client.get("/")
    assert resp.status_code == status.HTTP_200_OK

    resp_json = resp.json()
    assert isinstance(resp_json, list)

    assert len(resp_json) == len(obj_list)

    for i in range(len(obj_list)):
        obj_read = ApiKeyRead.model_validate(resp_json[i])
        assert obj_read.id == obj_list[i].id


@pytest.mark.usefixtures("api_key_creates")
def test_update(test_http_client: TestClient, api_key_crud: ApiKeyCRUD) -> None:
    obj_list = api_key_crud.search()
    obj_target = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_key_name = RandUtil.get_str()
    obj_update = ApiKeyUpdate(key_name=new_key_name)

    # Update
    resp = test_http_client.put(
        f"/{obj_target.id}",
        json=obj_update.model_dump(mode="json", exclude_unset=True),
    )
    assert resp.status_code == status.HTTP_200_OK

    # Check update result
    obj_updated = ApiKeyRead.model_validate(resp.json())
    assert obj_updated.key_name == new_key_name


@pytest.mark.usefixtures("api_key_creates")
def test_delete(test_http_client: TestClient, api_key_crud: ApiKeyCRUD) -> None:
    obj_list = api_key_crud.search()
    api_key_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    resp = test_http_client.delete(f"/{api_key_id}")
    assert resp.status_code == status.HTTP_200_OK

    try:
        api_key_crud.get(obj_id=api_key_id)
        msg = "ApiKey not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
