from typing import Any

import pytest
from loguru import logger
from pymongo.database import Database

from app.models.version_log import VersionLog, VersionLogAction, VersionLogCRUD, VersionLogMetadata
from app.utils.datetime import DatetimeUtil
from app.utils.rand import RandUtil
from test.conftest import config as cfg_test
from test.fixtures.mongo import MockedDB


def fill_version_log_collection(db: Database[dict[str, Any]]) -> list[VersionLog]:
    logger.debug("fill version log collection with test data")

    crud = VersionLogCRUD(db=db)
    crud.clear()

    obj_creates: list[VersionLog] = []
    for i in range(cfg_test.TEST_ITERATION):
        client_name = f"client_{i}"
        obj_create = VersionLog(
            meal_plan_id=RandUtil.get_mongo_id(),
            client_name=client_name,
            timestamp=DatetimeUtil.get_current_timestamp(),
            message=RandUtil.get_str(),
            patch=RandUtil.get_str(),
            full_content=None,
            metadata=VersionLogMetadata(
                created_by=client_name,
                action=VersionLogAction.create,
                note=RandUtil.get_str(),
            ),
        )
        obj_creates.append(obj_create)
        crud.create(obj_create=obj_create)

    return obj_creates


@pytest.fixture
def version_log_crud(mocked_db: MockedDB) -> VersionLogCRUD:
    return VersionLogCRUD(db=mocked_db.pymongo_db)


@pytest.fixture
def version_log_creates(mocked_db: MockedDB) -> list[VersionLog]:
    return fill_version_log_collection(db=mocked_db.pymongo_db)
