from typing import Any

import pytest
from fastapi import HTTPException, status
from pymongo.collection import Collection

from app.models.version_log import COLLECTION_NAME, VersionLog, VersionLogCRUD, VersionLogRead, VersionLogUpdate
from app.utils.rand import RandUtil
from test.fixtures.mongo import MockedDB


@pytest.fixture
def collection(mocked_db: MockedDB) -> Collection[dict[str, Any]]:
    return mocked_db.pymongo_db.get_collection(COLLECTION_NAME)


def read_from_db(coll: Collection[dict[str, Any]]) -> list[VersionLogRead]:
    cursor = coll.find()
    return [VersionLogRead.model_validate(doc) for doc in cursor]


def test_create(collection: Collection[dict[str, Any]], version_log_creates: list[VersionLog]) -> None:
    obj_list = read_from_db(collection)

    assert len(obj_list) == len(version_log_creates)
    for obj_create, obj in zip(version_log_creates, obj_list, strict=True):
        assert obj.message == obj_create.message


@pytest.mark.usefixtures("version_log_creates")
def test_get(version_log_crud: VersionLogCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)

    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id
    obj = version_log_crud.get(obj_id=obj_id)
    assert obj is not None
    assert obj_id == obj.id


def test_get_all(version_log_crud: VersionLogCRUD, version_log_creates: list[VersionLog]) -> None:
    obj_list = version_log_crud.search()
    assert len(obj_list) == len(version_log_creates)
    for i in range(len(version_log_creates)):
        assert obj_list[i].message == version_log_creates[i].message


@pytest.mark.usefixtures("version_log_creates")
def test_update(version_log_crud: VersionLogCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_update = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_msg = RandUtil.get_str()

    # Update
    obj_updated = version_log_crud.update(
        obj_update=VersionLogUpdate(message=new_msg),
        obj_id=obj_update.id,
    )

    # Check update result
    assert new_msg == obj_updated.message


@pytest.mark.usefixtures("version_log_creates")
def test_delete(version_log_crud: VersionLogCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    version_log_crud.delete(obj_id)
    assert len(obj_list) - 1 == version_log_crud.count()

    try:
        version_log_crud.get(obj_id=obj_id)
        msg = "VersionLog not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
