from loguru import logger
from pydantic_settings import BaseSettings

# Do not change plugin order
pytest_plugins = (
    "test.fixtures.mongo",
    "test.fixtures.app",
    "test.fixtures.qdrant",
    "test.fixtures.storage.tenant",
    "test.fixtures.storage.client",
    "test.fixtures.storage.api_key",
    "test.fixtures.storage.meal_plan",
    "test.fixtures.storage.version_log",
    "test.fixtures.storage.retry_metadata",
    "test.fixtures.storage.audit_log",
)


class Config(BaseSettings):
    TEST_ITERATION: int = 8

    TEST_MONGO_DB: str = "healthymeal_copilot_test"
    TEST_QDRANT_COLLECTION: str = "healthymeal_copilot_test"

    TEST_COSINE_DISTANCE_THRESHOLD: float = 0.1


config = Config()

if __name__ == "__main__":
    logger.debug(config.model_dump_json(indent=2))
