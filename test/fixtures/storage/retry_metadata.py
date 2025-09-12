import time
from typing import Any

import pytest
from loguru import logger
from pymongo.database import Database

from app.core.config.llm import LLMProvider
from app.models.common.version import Version
from app.models.retry_metadata import RetryMetadata, RetryMetadataCRUD, RetryReason
from app.utils.rand import RandUtil
from test.conftest import config as cfg_test
from test.fixtures.mongo import MockedDB


def fill_retry_metadata_collection(db: Database[dict[str, Any]]) -> list[RetryMetadata]:
    logger.debug("fill version log collection with test data")

    crud = RetryMetadataCRUD(db=db)
    crud.clear()

    obj_creates: list[RetryMetadata] = []
    for _ in range(cfg_test.TEST_ITERATION):
        obj_create = RetryMetadata(
            prompt_version=Version(
                major=RandUtil.get_int(),
                minor=RandUtil.get_int(),
                patch=RandUtil.get_int(),
            ),
            input_prompt=RandUtil.get_str(),
            final_prompt=RandUtil.get_str(),
            model_used=RandUtil.get_enum(LLMProvider),
            retry_count=RandUtil.get_int(),
            retry_reason=RandUtil.get_enum(RetryReason),
            error_message=RandUtil.get_str(),
            error_details=RandUtil.get_str(),
            timestamp=RandUtil.get_timestamp(),
        )
        obj_creates.append(obj_create)
        crud.create(obj_create=obj_create)

        time.sleep(1 / 1_000)

    return obj_creates


@pytest.fixture
def retry_metadata_crud(mocked_db: MockedDB) -> RetryMetadataCRUD:
    return RetryMetadataCRUD(db=mocked_db.pymongo_db)


@pytest.fixture
def retry_metadata_creates(mocked_db: MockedDB) -> list[RetryMetadata]:
    return fill_retry_metadata_collection(db=mocked_db.pymongo_db)
