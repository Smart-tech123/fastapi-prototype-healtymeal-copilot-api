from typing import Any

import pytest
from loguru import logger
from pymongo.database import Database

from app.models.auth.client import Client, ClientCRUD
from app.models.auth.common.access_policy import AccessPolicy
from app.services.auth.client_service import ClientService
from app.utils.rand import RandUtil
from test.conftest import config as cfg_test
from test.fixtures.mongo import MockedDB


def fill_client_collection(db: Database[dict[str, Any]]) -> list[Client]:
    logger.debug("fill oauth client collection with test data")

    crud = ClientCRUD(db=db)
    crud.clear()

    obj_creates: list[Client] = []
    for _ in range(cfg_test.TEST_ITERATION):
        obj_create = Client(
            tenant_id=RandUtil.get_mongo_id(),
            client_id=RandUtil.get_str(),
            client_secret_hash=RandUtil.get_str(),
            client_name=RandUtil.get_str(),
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
def client_crud(mocked_db: MockedDB) -> ClientCRUD:
    return ClientCRUD(db=mocked_db.pymongo_db)


@pytest.fixture
def client_service(mocked_db: MockedDB) -> ClientService:
    return ClientService(db=mocked_db.pymongo_db)


@pytest.fixture
def client_creates(mocked_db: MockedDB) -> list[Client]:
    return fill_client_collection(db=mocked_db.pymongo_db)
