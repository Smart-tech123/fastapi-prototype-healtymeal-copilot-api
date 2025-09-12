from typing import Any

import pytest
from fastapi import HTTPException, status
from pymongo.collection import Collection

from app.models.auth.client import (
    COLLECTION_NAME,
    Client,
    ClientCRUD,
    ClientRead,
    ClientUpdate,
)
from app.utils.rand import RandUtil
from test.fixtures.mongo import MockedDB


@pytest.fixture
def collection(mocked_db: MockedDB) -> Collection[dict[str, Any]]:
    return mocked_db.pymongo_db.get_collection(COLLECTION_NAME)


def read_from_db(coll: Collection[dict[str, Any]]) -> list[ClientRead]:
    cursor = coll.find()
    return [ClientRead.model_validate(doc) for doc in cursor]


def test_create(collection: Collection[dict[str, Any]], client_creates: list[Client]) -> None:
    cursor = collection.find()
    obj_list = [ClientRead.model_validate(doc) for doc in cursor]

    assert len(obj_list) == len(client_creates)
    for obj_create, obj in zip(client_creates, obj_list, strict=True):
        assert obj.client_name == obj_create.client_name


@pytest.mark.usefixtures("client_creates")
def test_get(client_crud: ClientCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)

    client_id = obj_list[RandUtil.get_int(up=len(obj_list))].id
    obj = client_crud.get(obj_id=client_id)
    assert obj is not None
    assert client_id == obj.id


def test_get_all(client_crud: ClientCRUD, client_creates: list[Client]) -> None:
    obj_list = client_crud.search()
    assert len(obj_list) == len(client_creates)
    for i in range(len(client_creates)):
        assert obj_list[i].description == client_creates[i].description


@pytest.mark.usefixtures("client_creates")
def test_update(client_crud: ClientCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_update = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_description = RandUtil.get_str()

    # Update
    obj_updated = client_crud.update(
        obj_update=ClientUpdate(description=new_description),
        obj_id=obj_update.id,
    )

    # Check update result
    assert new_description == obj_updated.description


@pytest.mark.usefixtures("client_creates")
def test_delete(client_crud: ClientCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    client_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    client_crud.delete(client_id)
    assert len(obj_list) - 1 == client_crud.count()

    try:
        client_crud.get(client_id)
        msg = "Client not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
