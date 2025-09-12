from collections.abc import Generator
from typing import Any

import pytest
from mongomock import MongoClient
from pymongo.database import Database

from test.conftest import config as cfg_test


class MockedDB:
    def __init__(self) -> None:
        self.database_name = f"{cfg_test.TEST_MONGO_DB}"
        self.pymongo_client: MongoClient[dict[str, Any]] = MongoClient(document_class=dict[str, Any])
        self.pymongo_db = self.pymongo_client.get_database(self.database_name)

    def clean(self) -> None:
        self.pymongo_client.drop_database(self.database_name)
        self.pymongo_client.close()

    def get_db(self) -> Generator[Database[dict[str, Any]], Any, None]:
        yield self.pymongo_db


@pytest.fixture
def mocked_db() -> Generator[MockedDB, Any, None]:
    db = MockedDB()
    yield db
    db.clean()
