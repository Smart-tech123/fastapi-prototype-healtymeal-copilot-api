from typing import Any

import pytest
from fastapi import status
from loguru import logger
from pymongo.database import Database

from app.core.config.llm import LLMProvider
from app.models.audit_log import AuditLog, AuditLogCRUD
from app.models.common.version import Version
from app.utils.rand import RandUtil
from test.conftest import config as cfg_test
from test.fixtures.mongo import MockedDB


def fill_audit_log_collection(db: Database[dict[str, Any]]) -> list[AuditLog]:
    logger.debug("fill version log collection with test data")

    crud = AuditLogCRUD(db=db)
    crud.clear()

    obj_creates: list[AuditLog] = []
    for i in range(cfg_test.TEST_ITERATION):
        obj_create = AuditLog(
            tenant_id=RandUtil.get_mongo_id(),
            tenant_name=RandUtil.get_str(),
            client_id=RandUtil.get_mongo_id(),
            client_name=RandUtil.get_str(),
            api_key_id=None if i % 2 == 0 else RandUtil.get_mongo_id(),
            api_key_name=None if i % 2 == 0 else RandUtil.get_str(),
            input_prompt=RandUtil.get_str(),
            prompt_version=Version(
                major=RandUtil.get_int(),
                minor=RandUtil.get_int(),
                patch=RandUtil.get_int(),
            ),
            model_used=RandUtil.get_enum(LLMProvider),
            trial_id=RandUtil.get_str(),
            request_path=RandUtil.get_str(),
            request_query=RandUtil.get_str(),
            request_method=RandUtil.get_list_item(
                [
                    "GET",
                    "POST",
                    "PUT",
                    "DELETE",
                    "PATCH",
                    "OPTIONS",
                ]
            ),
            remote_address=RandUtil.get_str(),
            response_status=RandUtil.get_list_item(
                [
                    status.HTTP_200_OK,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                ]
            ),
            latency_ms=RandUtil.get_int(),
        )
        obj_creates.append(obj_create)
        crud.create(obj_create=obj_create)

    return obj_creates


@pytest.fixture
def audit_log_crud(mocked_db: MockedDB) -> AuditLogCRUD:
    return AuditLogCRUD(db=mocked_db.pymongo_db)


@pytest.fixture
def audit_log_creates(mocked_db: MockedDB) -> list[AuditLog]:
    return fill_audit_log_collection(db=mocked_db.pymongo_db)
