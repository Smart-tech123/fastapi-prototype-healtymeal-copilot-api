import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from scipy.spatial.distance import cosine

from app.api.dependency import get_current_client, rate_limited
from app.api.endpoints.qdrant_service import router
from app.schemas.qdrant import QdrantPoint, QdrantPointRead
from app.services.qdrant_service import QdrantService
from app.utils.rand import RandUtil
from test.conftest import config as cfg_test
from test.fixtures.dependency import mocked_get_current_client, mocked_rate_limited
from test.fixtures.qdrant import MockedQdrant


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=router)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    app.dependency_overrides[rate_limited] = mocked_rate_limited
    return TestClient(app=app)


def test_create(
    test_http_client: TestClient,
    mocked_qdrant: MockedQdrant,
    qdrant_crud: QdrantService,
    qdrant_creates: list[QdrantPoint],
) -> None:
    qdrant_crud.clear()
    for obj_create in qdrant_creates:
        resp = test_http_client.post(
            f"/{mocked_qdrant.collection_name}",
            json=obj_create.model_dump(mode="json"),
        )
        assert resp.status_code == status.HTTP_200_OK

        obj_read = QdrantPointRead.model_validate(resp.json())
        assert obj_read.payload == obj_create.payload

    assert qdrant_crud.count_points() == len(qdrant_creates)


@pytest.mark.usefixtures("qdrant_creates")
def test_get(test_http_client: TestClient, mocked_qdrant: MockedQdrant, qdrant_crud: QdrantService) -> None:
    obj_list = qdrant_crud.get_all_points()

    obj_idx = RandUtil.get_int(up=len(obj_list))
    obj_id = obj_list[obj_idx].id
    obj_vector = obj_list[obj_idx].vector
    obj_payload = obj_list[obj_idx].payload

    resp = test_http_client.get(f"/{mocked_qdrant.collection_name}/{obj_id}")

    assert resp.status_code == status.HTTP_200_OK

    obj = QdrantPointRead.model_validate(resp.json())

    assert obj is not None
    assert obj_id == obj.id
    assert cosine(obj_vector, obj.vector) < cfg_test.TEST_COSINE_DISTANCE_THRESHOLD
    assert obj_payload == obj.payload


@pytest.mark.usefixtures("qdrant_creates")
def test_get_all(test_http_client: TestClient, mocked_qdrant: MockedQdrant, qdrant_crud: QdrantService) -> None:
    obj_list = qdrant_crud.get_all_points()

    resp = test_http_client.get(f"/{mocked_qdrant.collection_name}")

    assert resp.status_code == status.HTTP_200_OK

    resp_json = resp.json()
    assert isinstance(resp_json, list)

    assert len(resp_json) == len(obj_list)

    for i in range(len(obj_list)):
        obj_read = QdrantPointRead.model_validate(resp_json[i])

        assert obj_read.id == obj_list[i].id
        assert cosine(obj_list[i].vector, obj_read.vector) < cfg_test.TEST_COSINE_DISTANCE_THRESHOLD
        assert obj_read.payload == obj_list[i].payload


@pytest.mark.usefixtures("qdrant_creates")
def test_update(test_http_client: TestClient, mocked_qdrant: MockedQdrant, qdrant_crud: QdrantService) -> None:
    obj_list = qdrant_crud.get_all_points()
    obj_update = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_msg = RandUtil.get_str()
    obj_update.payload["text"] = new_msg

    # Update
    resp = test_http_client.put(
        f"/{mocked_qdrant.collection_name}/{obj_update.id}",
        json=obj_update.model_dump(mode="json"),
    )
    assert resp.status_code == status.HTTP_200_OK

    # Check update result
    obj_updated = QdrantPointRead.model_validate(resp.json())
    assert new_msg == obj_updated.payload["text"]


@pytest.mark.usefixtures("qdrant_creates")
def test_delete(test_http_client: TestClient, mocked_qdrant: MockedQdrant, qdrant_crud: QdrantService) -> None:
    obj_list = qdrant_crud.get_all_points()
    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    resp = test_http_client.delete(f"/{mocked_qdrant.collection_name}/{obj_id}")
    assert resp.status_code == status.HTTP_200_OK

    try:
        qdrant_crud.get_point(point_id=obj_id)
        msg = "Qdrant not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
