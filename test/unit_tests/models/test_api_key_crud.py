from typing import Any

import pytest
from fastapi import HTTPException, status
from pymongo.collection import Collection

from app.models.auth.api_key import (
    COLLECTION_NAME,
    ApiKey,
    ApiKeyCRUD,
    ApiKeyRead,
    ApiKeyUpdate,
)
from app.utils.rand import RandUtil
from test.fixtures.mongo import MockedDB


@pytest.fixture
def collection(mocked_db: MockedDB) -> Collection[dict[str, Any]]:
    return mocked_db.pymongo_db.get_collection(COLLECTION_NAME)


def read_from_db(coll: Collection[dict[str, Any]]) -> list[ApiKeyRead]:
    cursor = coll.find()
    return [ApiKeyRead.model_validate(doc) for doc in cursor]


def test_create(collection: Collection[dict[str, Any]], api_key_creates: list[ApiKey]) -> None:
    cursor = collection.find()
    obj_list = [ApiKeyRead.model_validate(doc) for doc in cursor]

    assert len(obj_list) == len(api_key_creates)
    for obj_create, obj in zip(api_key_creates, obj_list, strict=True):
        assert obj.key_name == obj_create.key_name


@pytest.mark.usefixtures("api_key_creates")
def test_get(api_key_crud: ApiKeyCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)

    api_key_id = obj_list[RandUtil.get_int(up=len(obj_list))].id
    obj = api_key_crud.get(obj_id=api_key_id)
    assert obj is not None
    assert api_key_id == obj.id


def test_get_all(api_key_crud: ApiKeyCRUD, api_key_creates: list[ApiKey]) -> None:
    obj_list = api_key_crud.search()
    assert len(obj_list) == len(api_key_creates)
    for i in range(len(api_key_creates)):
        assert obj_list[i].key_name == api_key_creates[i].key_name


@pytest.mark.usefixtures("api_key_creates")
def test_update(api_key_crud: ApiKeyCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_update = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_key_name = RandUtil.get_str()

    # Update
    obj_updated = api_key_crud.update(
        obj_id=obj_update.id,
        obj_update=ApiKeyUpdate(key_name=new_key_name),
    )

    # Check update result
    assert new_key_name == obj_updated.key_name


@pytest.mark.usefixtures("api_key_creates")
def test_delete(api_key_crud: ApiKeyCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    api_key_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    api_key_crud.delete(api_key_id)
    assert len(obj_list) - 1 == api_key_crud.count()

    try:
        api_key_crud.get(api_key_id)
        msg = "ApiKey not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
