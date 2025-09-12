from typing import Any

import pytest
from loguru import logger
from pymongo.database import Database

from app.models.common.version import Version
from app.models.meal_plan import DayOfWeek, Meal, MealPlan, MealPlanCRUD
from app.services.meal_plan import MealPlanService
from app.utils.rand import RandUtil
from test.conftest import config as cfg_test
from test.fixtures.mongo import MockedDB


def fill_meal_plan_collection(db: Database[dict[str, Any]]) -> list[MealPlan]:
    logger.debug("fill version log collection with test data")

    crud = MealPlanCRUD(db=db)
    crud.clear()

    obj_creates: list[MealPlan] = []
    for i in range(cfg_test.TEST_ITERATION):
        breakfast = Meal(
            name=RandUtil.get_str(),
            calories=RandUtil.get_int(),
            ingredients=[
                RandUtil.get_str(),
                RandUtil.get_str(),
            ],
        )
        lunch = Meal(
            name=RandUtil.get_str(),
            calories=RandUtil.get_int(),
            ingredients=[
                RandUtil.get_str(),
                RandUtil.get_str(),
            ],
        )
        dinner = Meal(
            name=RandUtil.get_str(),
            calories=RandUtil.get_int(),
            ingredients=[
                RandUtil.get_str(),
                RandUtil.get_str(),
            ],
        )
        obj_create = MealPlan(
            plan_name=f"plan_{i}",
            description=RandUtil.get_str(),
            day=RandUtil.get_enum(DayOfWeek),
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            total_calories=breakfast.calories + lunch.calories + dinner.calories,
            version=Version.initial_version(),
        )
        obj_creates.append(obj_create)
        crud.create(obj_create=obj_create)

    return obj_creates


@pytest.fixture
def meal_plan_crud(mocked_db: MockedDB) -> MealPlanCRUD:
    return MealPlanCRUD(db=mocked_db.pymongo_db)


@pytest.fixture
def meal_plan_service(mocked_db: MockedDB) -> MealPlanService:
    return MealPlanService(db=mocked_db.pymongo_db)


@pytest.fixture
def meal_plan_creates(mocked_db: MockedDB) -> list[MealPlan]:
    return fill_meal_plan_collection(db=mocked_db.pymongo_db)
