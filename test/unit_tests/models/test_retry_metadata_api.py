import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from app.api.dependency import get_current_client
from app.api.endpoints.crud.retry_metadata import router
from app.models.retry_metadata import RetryMetadata, RetryMetadataCRUD, RetryMetadataRead
from app.utils.rand import RandUtil
from test.fixtures.dependency import mocked_get_current_client


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=router)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    return TestClient(app=app)


def test_create(
    test_http_client: TestClient, retry_metadata_crud: RetryMetadataCRUD, retry_metadata_creates: list[RetryMetadata]
) -> None:
    retry_metadata_crud.clear()
    for obj_create in retry_metadata_creates:
        resp = test_http_client.post(
            "/",
            json=obj_create.model_dump(mode="json"),
        )
        assert resp.status_code == status.HTTP_200_OK

        obj_read = RetryMetadataRead.model_validate(resp.json())
        assert obj_read.input_prompt == obj_create.input_prompt

    assert retry_metadata_crud.count() == len(retry_metadata_creates)


def test_get(
    test_http_client: TestClient, retry_metadata_crud: RetryMetadataCRUD, retry_metadata_creates: list[RetryMetadata]
) -> None:
    obj_list = retry_metadata_crud.search()

    obj_id = obj_list[RandUtil.get_int(up=len(retry_metadata_creates))].id
    resp = test_http_client.get(f"/{obj_id}")

    assert resp.status_code == status.HTTP_200_OK

    obj_read = RetryMetadataRead.model_validate(resp.json())
    assert obj_id == obj_read.id


@pytest.mark.usefixtures("retry_metadata_creates")
def test_search(test_http_client: TestClient, retry_metadata_crud: RetryMetadataCRUD) -> None:
    obj_list = retry_metadata_crud.search()

    resp = test_http_client.get("/")
    assert resp.status_code == status.HTTP_200_OK

    resp_json = resp.json()
    assert isinstance(resp_json, list)

    assert len(resp_json) == len(obj_list)

    for i in range(len(obj_list)):
        obj_read = RetryMetadataRead.model_validate(resp_json[i])
        assert obj_read.id == obj_list[i].id


@pytest.mark.usefixtures("retry_metadata_creates")
def test_update(test_http_client: TestClient, retry_metadata_crud: RetryMetadataCRUD) -> None:
    obj_list = retry_metadata_crud.search()
    obj_update = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_timestamp = RandUtil.get_timestamp()
    obj_update.created_at = new_timestamp

    # Update
    resp = test_http_client.put(
        f"/{obj_update.id}",
        json=obj_update.model_dump(mode="json"),
    )
    assert resp.status_code == status.HTTP_200_OK

    # Check update result
    obj_updated = RetryMetadataRead.model_validate(resp.json())
    assert obj_updated.created_at == new_timestamp


@pytest.mark.usefixtures("retry_metadata_creates")
def test_delete(test_http_client: TestClient, retry_metadata_crud: RetryMetadataCRUD) -> None:
    obj_list = retry_metadata_crud.search()
    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    resp = test_http_client.delete(f"/{obj_id}")
    assert resp.status_code == status.HTTP_200_OK

    try:
        retry_metadata_crud.get(obj_id=obj_id)
        msg = "RetryMetadata not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
