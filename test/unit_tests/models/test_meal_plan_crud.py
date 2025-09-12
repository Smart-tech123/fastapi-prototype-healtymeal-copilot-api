from typing import Any

import pytest
from fastapi import HTTPException, status
from pymongo.collection import Collection

from app.models.meal_plan import COLLECTION_NAME, MealPlan, MealPlanCRUD, MealPlanRead, MealPlanUpdate
from app.utils.rand import RandUtil
from test.fixtures.mongo import MockedDB


@pytest.fixture
def collection(mocked_db: MockedDB) -> Collection[dict[str, Any]]:
    return mocked_db.pymongo_db.get_collection(COLLECTION_NAME)


def read_from_db(coll: Collection[dict[str, Any]]) -> list[MealPlanRead]:
    cursor = coll.find()
    return [MealPlanRead.model_validate(doc) for doc in cursor]


def test_create(collection: Collection[dict[str, Any]], meal_plan_creates: list[MealPlan]) -> None:
    obj_list = read_from_db(collection)

    assert len(obj_list) == len(meal_plan_creates)
    for obj_create, obj in zip(meal_plan_creates, obj_list, strict=True):
        assert obj.description == obj_create.description


@pytest.mark.usefixtures("meal_plan_creates")
def test_get(meal_plan_crud: MealPlanCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)

    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id
    obj = meal_plan_crud.get(obj_id=obj_id)
    assert obj is not None
    assert obj_id == obj.id


def test_get_all(meal_plan_crud: MealPlanCRUD, meal_plan_creates: list[MealPlan]) -> None:
    obj_list = meal_plan_crud.search()
    assert len(obj_list) == len(meal_plan_creates)
    for i in range(len(meal_plan_creates)):
        assert obj_list[i].description == meal_plan_creates[i].description


@pytest.mark.usefixtures("meal_plan_creates")
def test_update(meal_plan_crud: MealPlanCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_update = obj_list[RandUtil.get_int(up=len(obj_list))]

    # Set new message
    new_desc = RandUtil.get_str()

    # Update
    obj_updated = meal_plan_crud.update(
        obj_update=MealPlanUpdate(description=new_desc),
        obj_id=obj_update.id,
    )

    # Check update result
    assert new_desc == obj_updated.description


@pytest.mark.usefixtures("meal_plan_creates")
def test_delete(meal_plan_crud: MealPlanCRUD, collection: Collection[dict[str, Any]]) -> None:
    obj_list = read_from_db(collection)
    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    meal_plan_crud.delete(obj_id)
    assert len(obj_list) - 1 == meal_plan_crud.count()

    try:
        meal_plan_crud.get(obj_id=obj_id)
        msg = "MealPlan not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
