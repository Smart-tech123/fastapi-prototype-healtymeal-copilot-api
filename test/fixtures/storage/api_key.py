from typing import Any

import pytest
from loguru import logger
from pymongo.database import Database

from app.models.auth.api_key import ApiKey, ApiKeyCRUD
from app.models.auth.common.access_policy import AccessPolicy
from app.services.auth.api_key_service import ApiKeyService
from app.services.auth.auth_service import AuthService
from app.utils.rand import RandUtil
from test.conftest import config as cfg_test
from test.fixtures.mongo import MockedDB


def fill_api_key_collection(db: Database[dict[str, Any]]) -> list[ApiKey]:
    logger.debug("fill api_keys collection with test data")

    crud = ApiKeyCRUD(db=db)
    crud.clear()

    obj_creates: list[ApiKey] = []
    for i in range(cfg_test.TEST_ITERATION):
        key_name = f"key_{i}"
        plain_key = RandUtil.get_str()
        obj_create = ApiKey(
            client_id=RandUtil.get_mongo_id(),
            key_name=key_name,
            key_secret_hash=AuthService.hash_password(plain_key),
            key_secret_front=plain_key[:8],
            description=RandUtil.get_str(),
            access_policy=AccessPolicy(
                allowed_ips=[],
                endpoints=[],
                scopes=[],
                rate_limit_per_min=0,
            ),
        )
        obj_creates.append(obj_create)
        crud.create(obj_create=obj_create)

    return obj_creates


@pytest.fixture
def api_key_crud(mocked_db: MockedDB) -> ApiKeyCRUD:
    return ApiKeyCRUD(db=mocked_db.pymongo_db)


@pytest.fixture
def api_key_service(mocked_db: MockedDB) -> ApiKeyService:
    return ApiKeyService(db=mocked_db.pymongo_db)


@pytest.fixture
def api_key_creates(mocked_db: MockedDB) -> list[ApiKey]:
    return fill_api_key_collection(db=mocked_db.pymongo_db)
