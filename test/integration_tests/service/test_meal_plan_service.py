import json

from loguru import logger

from app.core.config.llm import config as cfg_llm
from app.core.config.qdrant import config as cfg_qdrant
from app.schemas.qdrant import QdrantPoint
from app.services.llm.factory import LLMFactory
from app.services.meal_plan import MealPlanService
from app.services.qdrant_service import QdrantService
from test.conftest import config as cfg_test
from test.fixtures.mongo import MockedDB
from test.fixtures.qdrant import MockedQdrant


def test_meal_plan_generation(mocked_db: MockedDB) -> None:
    user_prompt = """
- entry conditions:
    - use sma indicator
    - use recommended operator for entry conditions
    - value is 1500
- trigger interval is 1 minute
- exit conditions:
    - use ema indicator
    - use recommended operator for exit conditions
    - value is 2000
- risk management:
    - stop loss is 1%
    - take profit is 2%"""

    resp = MealPlanService(db=mocked_db.pymongo_db).generate_meal_plan(
        meal_plan_specs=user_prompt,
        prompt_version=None,
        qdrant_client=None,
        add_context=False,
    )

    logger.info(f"user_prompt: {user_prompt}")
    logger.info(f"response: {json.dumps(resp.raw_output, indent=2)}")


def test_meal_plan_generation_with_context(
    mocked_db: MockedDB,
    mocked_qdrant: MockedQdrant,
    qdrant_crud: QdrantService,
) -> None:
    user_prompt = "Generate a meal plan for a sports man"

    cfg_qdrant.COLLECTION_NAME = cfg_test.TEST_QDRANT_COLLECTION

    # Prepare context
    qdrant_crud.clear()
    contexts = [
        "Based on latest research result, sports man must have only water for every meal",  # Related, but fraud
        "The rocket goes to Mars",  # Unrelated
    ]
    for context in contexts:
        vector = LLMFactory.get(cfg_llm.LLM_PROVIDER).generate_embedding(context)
        qdrant_crud.create_point(
            QdrantPoint(
                vector=vector,
                payload={"text": context},
            )
        )

    # Try without context
    resp_no_context = MealPlanService(db=mocked_db.pymongo_db).generate_meal_plan(
        meal_plan_specs=user_prompt,
        prompt_version=None,
        qdrant_client=None,
        add_context=False,
    )

    # Try with context
    resp_context = MealPlanService(db=mocked_db.pymongo_db).generate_meal_plan(
        meal_plan_specs=user_prompt,
        prompt_version=None,
        qdrant_client=mocked_qdrant.qdrant_client,
        add_context=True,
    )

    logger.debug(f"response without context: {json.dumps(resp_no_context.raw_output, indent=2)}")
    logger.debug(f"response with context: {json.dumps(resp_context.raw_output, indent=2)}")
