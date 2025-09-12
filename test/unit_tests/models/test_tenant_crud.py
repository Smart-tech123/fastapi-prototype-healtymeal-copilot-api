from typing import Any

import pytest
from fastapi import HTTPException, status
from pymongo.collection import Collection

from app.models.auth.tenant import COLLECTION_NAME, Tenant, TenantCRUD, TenantRead, TenantUpdate
from app.utils.rand import RandUtil
from test.fixtures.mongo import MockedDB


@pytest.fixture
def collection(mocked_db: MockedDB) -> Collection[dict[str, Any]]:
    return mocked_db.pymongo_db.get_collection(COLLECTION_NAME)


def read_from_db(coll: Collection[dict[str, Any]]) -> list[TenantRead]:
    cursor = coll.find()
    return [TenantRead.model_validate(doc) for doc in cursor]


def test_create(collection: Collection[dict[str, Any]], tenant_creates: list[Tenant]) -> None:
    obj_list = read_from_db(collection)

    assert len(obj_list) == len(tenant_creates)
    for obj_create, obj in zip(tenant_creates, obj_list, strict=True):
        assert obj.tenant_name == obj_create.tenant_name


@pytest.mark.usefixtures("tenant_creates")
def test_get(tenant_crud: TenantCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)

    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id
    obj = tenant_crud.get(obj_id=obj_id)
    assert obj is not None
    assert obj_id == obj.id


def test_get_all(tenant_crud: TenantCRUD, tenant_creates: list[Tenant]) -> None:
    obj_list = tenant_crud.search()
    assert len(obj_list) == len(tenant_creates)
    for i in range(len(tenant_creates)):
        assert obj_list[i].tenant_name == tenant_creates[i].tenant_name


@pytest.mark.usefixtures("tenant_creates")
def test_update(tenant_crud: TenantCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_update = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_tenant_name = RandUtil.get_str()

    # Update
    obj_updated = tenant_crud.update(
        obj_update=TenantUpdate(tenant_name=new_tenant_name),
        obj_id=obj_update.id,
    )

    # Check update result
    assert new_tenant_name == obj_updated.tenant_name


@pytest.mark.usefixtures("tenant_creates")
def test_delete(tenant_crud: TenantCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    tenant_crud.delete(obj_id)
    assert len(obj_list) - 1 == tenant_crud.count()

    try:
        tenant_crud.get(obj_id=obj_id)
        msg = "Tenant not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
