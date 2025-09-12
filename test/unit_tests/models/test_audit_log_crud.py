from typing import Any

import pytest
from fastapi import HTTPException, status
from pymongo.collection import Collection

from app.models.audit_log import COLLECTION_NAME, AuditLog, AuditLogCRUD, AuditLogRead, AuditLogUpdate
from app.utils.rand import RandUtil
from test.fixtures.mongo import MockedDB


@pytest.fixture
def collection(mocked_db: MockedDB) -> Collection[dict[str, Any]]:
    return mocked_db.pymongo_db.get_collection(COLLECTION_NAME)


def read_from_db(coll: Collection[dict[str, Any]]) -> list[AuditLogRead]:
    cursor = coll.find()
    return [AuditLogRead.model_validate(doc) for doc in cursor]


def test_create(collection: Collection[dict[str, Any]], audit_log_creates: list[AuditLog]) -> None:
    obj_list = read_from_db(collection)

    assert len(obj_list) == len(audit_log_creates)
    for obj_create, obj in zip(audit_log_creates, obj_list, strict=True):
        assert obj.tenant_id == obj_create.tenant_id


@pytest.mark.usefixtures("audit_log_creates")
def test_get(audit_log_crud: AuditLogCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)

    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id
    obj = audit_log_crud.get(obj_id=obj_id)
    assert obj is not None
    assert obj_id == obj.id


def test_get_all(audit_log_crud: AuditLogCRUD, audit_log_creates: list[AuditLog]) -> None:
    obj_list = audit_log_crud.search()
    assert len(obj_list) == len(audit_log_creates)
    for i in range(len(audit_log_creates)):
        assert obj_list[i].tenant_id == audit_log_creates[i].tenant_id


@pytest.mark.usefixtures("audit_log_creates")
def test_update(audit_log_crud: AuditLogCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_update = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_tenant_id = RandUtil.get_mongo_id()

    # Update
    obj_updated = audit_log_crud.update(
        obj_update=AuditLogUpdate(tenant_id=new_tenant_id),
        obj_id=obj_update.id,
    )

    # Check update result
    assert new_tenant_id == obj_updated.tenant_id


@pytest.mark.usefixtures("audit_log_creates")
def test_delete(audit_log_crud: AuditLogCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    audit_log_crud.delete(obj_id)
    assert len(obj_list) - 1 == audit_log_crud.count()

    try:
        audit_log_crud.get(obj_id=obj_id)
        msg = "AuditLog not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
