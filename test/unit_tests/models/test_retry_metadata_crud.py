from typing import Any

import pytest
from fastapi import HTTPException, status
from pymongo.collection import Collection

from app.models.retry_metadata import (
    COLLECTION_NAME,
    RetryMetadata,
    RetryMetadataCRUD,
    RetryMetadataRead,
    RetryMetadataUpdate,
)
from app.utils.rand import RandUtil
from test.fixtures.mongo import MockedDB


@pytest.fixture
def collection(mocked_db: MockedDB) -> Collection[dict[str, Any]]:
    return mocked_db.pymongo_db.get_collection(COLLECTION_NAME)


def read_from_db(coll: Collection[dict[str, Any]]) -> list[RetryMetadataRead]:
    cursor = coll.find()
    return [RetryMetadataRead.model_validate(doc) for doc in cursor]


def test_create(collection: Collection[dict[str, Any]], retry_metadata_creates: list[RetryMetadata]) -> None:
    obj_list = read_from_db(collection)

    assert len(obj_list) == len(retry_metadata_creates)
    for obj_create, obj in zip(retry_metadata_creates, obj_list, strict=True):
        assert obj.input_prompt == obj_create.input_prompt


@pytest.mark.usefixtures("retry_metadata_creates")
def test_get(retry_metadata_crud: RetryMetadataCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)

    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id
    obj = retry_metadata_crud.get(obj_id=obj_id)
    assert obj is not None
    assert obj_id == obj.id


def test_get_all(retry_metadata_crud: RetryMetadataCRUD, retry_metadata_creates: list[RetryMetadata]) -> None:
    obj_list = retry_metadata_crud.search()
    assert len(obj_list) == len(retry_metadata_creates)
    for i in range(len(retry_metadata_creates)):
        assert obj_list[i].input_prompt == retry_metadata_creates[i].input_prompt


@pytest.mark.usefixtures("retry_metadata_creates")
def test_update(retry_metadata_crud: RetryMetadataCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_update = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_timestamp = RandUtil.get_timestamp()
    obj_update.created_at = new_timestamp

    # Update
    obj_updated = retry_metadata_crud.update(
        obj_update=RetryMetadataUpdate(created_at=new_timestamp),
        obj_id=obj_update.id,
    )

    # Check update result
    assert new_timestamp == obj_updated.created_at


@pytest.mark.usefixtures("retry_metadata_creates")
def test_delete(retry_metadata_crud: RetryMetadataCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    retry_metadata_crud.delete(obj_id)
    assert len(obj_list) - 1 == retry_metadata_crud.count()

    try:
        retry_metadata_crud.get(obj_id=obj_id)
        msg = "RetryMetadata not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
