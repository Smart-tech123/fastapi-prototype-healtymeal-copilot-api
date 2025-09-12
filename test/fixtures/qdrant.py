from collections.abc import Generator
from typing import Any

import pytest
from loguru import logger
from qdrant_client import QdrantClient

from app.core.config.qdrant import config as cfg_qdrant
from app.schemas.qdrant import QdrantPoint
from app.services.qdrant_service import QdrantService
from app.utils.rand import RandUtil
from test.conftest import config as cfg_test


def fill_qdrant_collection(qdrant_client: QdrantClient, collection_name: str) -> list[QdrantPoint]:
    logger.debug("fill qdrant collection with test data")

    crud = QdrantService(
        qdrant_client=qdrant_client,
        collection_name=collection_name,
    )
    crud.clear()

    obj_creates: list[QdrantPoint] = []
    for _ in range(cfg_test.TEST_ITERATION):
        obj_create = QdrantPoint(
            vector=[RandUtil.get_float() for _ in range(cfg_qdrant.VECTOR_SIZE)],
            payload={
                "text": f"text_{RandUtil.get_str()}",
                "title": f"title_{RandUtil.get_str()}",
            },
        )
        obj_creates.append(obj_create)
        crud.create_point(point_data=obj_create)

    return obj_creates


class MockedQdrant:
    def __init__(self) -> None:
        self.collection_name = f"{cfg_test.TEST_QDRANT_COLLECTION}"
        self.qdrant_client = QdrantClient(url=cfg_qdrant.QDRANT_URL)

    def clean(self) -> None:
        self.qdrant_client.delete_collection(collection_name=self.collection_name)
        self.qdrant_client.close()

    def get_client(self) -> Generator[QdrantClient, Any, None]:
        yield self.qdrant_client


@pytest.fixture
def mocked_qdrant() -> Generator[MockedQdrant, Any, None]:
    qdrant = MockedQdrant()
    yield qdrant
    qdrant.clean()


@pytest.fixture
def qdrant_crud(mocked_qdrant: MockedQdrant) -> QdrantService:
    return QdrantService(
        qdrant_client=mocked_qdrant.qdrant_client,
        collection_name=mocked_qdrant.collection_name,
    )


@pytest.fixture
def qdrant_creates(mocked_qdrant: MockedQdrant) -> list[QdrantPoint]:
    return fill_qdrant_collection(
        qdrant_client=mocked_qdrant.qdrant_client,
        collection_name=mocked_qdrant.collection_name,
    )
