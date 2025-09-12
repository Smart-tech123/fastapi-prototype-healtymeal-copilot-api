import pytest
from fastapi import FastAPI

from app.api.dependency import get_db
from test.fixtures.mongo import MockedDB


@pytest.fixture
def app(mocked_db: MockedDB) -> FastAPI:
    app = FastAPI()
    app.dependency_overrides[get_db] = mocked_db.get_db
    return app
