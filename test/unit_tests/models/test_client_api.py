import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from loguru import logger

from app.api.dependency import get_current_client
from app.api.endpoints.crud.client import router
from app.models.auth.client import Client, ClientCRUD, ClientRead, ClientUpdate
from app.utils.rand import RandUtil
from test.fixtures.dependency import mocked_get_current_client


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=router)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    return TestClient(app=app)


def test_create(test_http_client: TestClient, client_crud: ClientCRUD, client_creates: list[Client]) -> None:
    client_crud.clear()
    for obj_create in client_creates:
        resp = test_http_client.post(
            "/",
            json=obj_create.model_dump(mode="json"),
        )
        assert resp.status_code == status.HTTP_200_OK

        obj_out = ClientRead.model_validate(resp.json())
        assert obj_out.client_name == obj_create.client_name
        logger.debug(f"client_id: {obj_out.id}")
        logger.debug(f"client_secret: {obj_out.client_secret_hash}")

    assert client_crud.count() == len(client_creates)


def test_get(test_http_client: TestClient, client_crud: ClientCRUD, client_creates: list[Client]) -> None:
    obj_list = client_crud.search()

    client_id = obj_list[RandUtil.get_int(up=len(client_creates))].id
    resp = test_http_client.get(f"/{client_id}")

    assert resp.status_code == status.HTTP_200_OK

    obj_read = ClientRead.model_validate(resp.json())
    assert client_id == obj_read.id


@pytest.mark.usefixtures("client_creates")
def test_get_all(test_http_client: TestClient, client_crud: ClientCRUD) -> None:
    obj_list = client_crud.search()

    resp = test_http_client.get("/")
    assert resp.status_code == status.HTTP_200_OK

    resp_json = resp.json()
    assert isinstance(resp_json, list)

    assert len(resp_json) == len(obj_list)

    for i in range(len(obj_list)):
        obj_read = ClientRead.model_validate(resp_json[i])
        assert obj_read.id == obj_list[i].id


@pytest.mark.usefixtures("client_creates")
def test_update(test_http_client: TestClient, client_crud: ClientCRUD) -> None:
    obj_list = client_crud.search()
    obj_target = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_description = RandUtil.get_str()
    obj_update = ClientUpdate(description=new_description)

    # Update
    resp = test_http_client.put(
        f"/{obj_target.id}",
        json=obj_update.model_dump(mode="json", exclude_unset=True),
    )
    assert resp.status_code == status.HTTP_200_OK

    # Check update result
    obj_updated = ClientRead.model_validate(resp.json())
    assert obj_updated.description == new_description


@pytest.mark.usefixtures("client_creates")
def test_delete(test_http_client: TestClient, client_crud: ClientCRUD) -> None:
    obj_list = client_crud.search()
    client_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    resp = test_http_client.delete(f"/{client_id}")
    assert resp.status_code == status.HTTP_200_OK

    try:
        client_crud.get(obj_id=client_id)
        msg = "Client not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
