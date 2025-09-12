import json

import pytest
from fastapi import HTTPException, status
from scipy.spatial.distance import cosine

from app.core.config.qdrant import config as cfg_qdrant
from app.schemas.qdrant import QdrantPoint, QdrantPointUpdate
from app.services.qdrant_service import QdrantService
from app.utils.rand import RandUtil
from test.conftest import config as cfg_test
from test.fixtures.qdrant import MockedQdrant


def test_create(mocked_qdrant: MockedQdrant, qdrant_crud: QdrantService) -> None:
    qdrant_crud.clear()
    point_create = QdrantPoint(
        vector=[RandUtil.get_float() for _ in range(cfg_qdrant.VECTOR_SIZE)],
        payload={
            "text": f"text_{RandUtil.get_str()}",
            "title": f"title_{RandUtil.get_str()}",
        },
    )

    qdrant_crud.create_point(point_data=point_create)

    points, _ = mocked_qdrant.qdrant_client.scroll(
        collection_name=mocked_qdrant.collection_name,
        limit=100,  # Number of points per batch
        with_payload=True,
        with_vectors=True,
    )

    assert len(points) == 1
    assert cosine(point_create.vector, points[0].vector) < cfg_test.TEST_COSINE_DISTANCE_THRESHOLD
    assert point_create.payload == points[0].payload


@pytest.mark.usefixtures("qdrant_creates")
def test_get(qdrant_crud: QdrantService) -> None:
    obj_list = qdrant_crud.get_all_points()

    obj_idx = RandUtil.get_int(up=len(obj_list))
    obj_id = obj_list[obj_idx].id
    obj_vector = obj_list[obj_idx].vector
    obj = qdrant_crud.get_point(point_id=obj_id)
    assert obj is not None
    assert obj_id == obj.id
    assert cosine(obj_vector, obj.vector) < cfg_test.TEST_COSINE_DISTANCE_THRESHOLD


def test_get_all(qdrant_crud: QdrantService, qdrant_creates: list[QdrantPoint]) -> None:
    obj_list = qdrant_crud.get_all_points()
    assert len(obj_list) == len(qdrant_creates)

    obj_list = sorted(obj_list, key=lambda x: json.dumps(x.payload))
    qdrant_creates = sorted(qdrant_creates, key=lambda x: json.dumps(x.payload))

    for obj_create, obj_read in zip(qdrant_creates, obj_list, strict=True):
        assert obj_create.payload == obj_read.payload
        assert cosine(obj_create.vector, obj_read.vector) < cfg_test.TEST_COSINE_DISTANCE_THRESHOLD


@pytest.mark.usefixtures("qdrant_creates")
def test_update(qdrant_crud: QdrantService) -> None:
    obj_list = qdrant_crud.get_all_points()
    obj_update = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_msg = RandUtil.get_str()
    obj_update.payload["text"] = new_msg

    # Update
    obj_updated = qdrant_crud.update_point(
        point_id=obj_update.id,
        point_data=QdrantPointUpdate(
            payload={
                "text": new_msg,
            },
        ),
    )

    # Check update result
    assert new_msg == obj_updated.payload["text"]


@pytest.mark.usefixtures("qdrant_creates")
def test_delete(qdrant_crud: QdrantService) -> None:
    obj_list = qdrant_crud.get_all_points()
    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    qdrant_crud.delete_point(point_id=obj_id)
    assert len(obj_list) - 1 == qdrant_crud.count_points()

    try:
        qdrant_crud.get_point(point_id=obj_id)
        msg = "Qdrant not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
