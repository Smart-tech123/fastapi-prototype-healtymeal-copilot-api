from typing import Any

import pytest
from loguru import logger
from pymongo.database import Database

from app.models.auth.common.access_policy import AccessPolicy
from app.models.auth.tenant import Tenant, TenantCRUD, TenantStatus
from app.services.auth.tenant_service import TenantService
from app.utils.rand import RandUtil
from test.conftest import config as cfg_test
from test.fixtures.mongo import MockedDB


def fill_tenant_collection(db: Database[dict[str, Any]]) -> list[Tenant]:
    logger.debug("fill tenants collection with test data")

    crud = TenantCRUD(db=db)
    crud.clear()

    obj_creates: list[Tenant] = []
    for i in range(cfg_test.TEST_ITERATION):
        tenant_name = f"tenant_{i}"
        obj_create = Tenant(
            tenant_name=tenant_name,
            status=RandUtil.get_enum(TenantStatus),
            description=RandUtil.get_str(),
            keys=[],
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
def tenant_crud(mocked_db: MockedDB) -> TenantCRUD:
    return TenantCRUD(db=mocked_db.pymongo_db)


@pytest.fixture
def tenant_service(mocked_db: MockedDB) -> TenantService:
    return TenantService(db=mocked_db.pymongo_db)


@pytest.fixture
def tenant_creates(mocked_db: MockedDB) -> list[Tenant]:
    return fill_tenant_collection(db=mocked_db.pymongo_db)
