import pytest
from fastapi import HTTPException, status

from app.models.common.version import ChangeType, Version
from app.models.meal_plan import MealPlan, MealPlanCRUD
from app.schemas.meal_plan import CreateMealPlanRequest, UpdateMealPlanRequest
from app.services.meal_plan import MealPlanService
from app.utils.rand import RandUtil


def test_create_meal_plan(
    meal_plan_crud: MealPlanCRUD,
    meal_plan_service: MealPlanService,
    meal_plan_creates: list[MealPlan],
) -> None:
    meal_plan_crud.clear()
    for obj_create in meal_plan_creates:
        obj_created = meal_plan_service.create_meal_plan(
            create_request=CreateMealPlanRequest.from_base(obj_create, log_message="test"),
            client_name="test_client",
        )

        assert obj_created.plan_name == obj_create.plan_name
        assert obj_created.version == Version.initial_version()

    assert meal_plan_crud.count() == len(meal_plan_creates)


def test_get_meal_plan(
    meal_plan_crud: MealPlanCRUD,
    meal_plan_service: MealPlanService,
    meal_plan_creates: list[MealPlan],
) -> None:
    obj_list = meal_plan_crud.search()

    obj_id = obj_list[RandUtil.get_int(up=len(meal_plan_creates))].id
    obj_got = meal_plan_service.get_meal_plan(meal_plan_id=obj_id)

    assert obj_got is not None
    assert obj_id == obj_got.id


def test_get_all_meal_plans(
    meal_plan_service: MealPlanService,
    meal_plan_creates: list[MealPlan],
) -> None:
    obj_list = meal_plan_service.get_all_meal_plans()
    assert len(meal_plan_creates) == len(obj_list)
    for i in range(len(obj_list)):
        assert obj_list[i].plan_name == meal_plan_creates[i].plan_name


@pytest.mark.usefixtures("meal_plan_creates")
def test_update_meal_plan(
    meal_plan_crud: MealPlanCRUD,
    meal_plan_service: MealPlanService,
) -> None:
    obj_list = meal_plan_crud.search()
    obj_target = obj_list[RandUtil.get_int(up=len(obj_list))]

    for i in range(3):
        # Set change type
        update_request = UpdateMealPlanRequest.from_base(
            obj_target,
            change=[ChangeType.PATCH, ChangeType.MINOR, ChangeType.MAJOR][i],
            log_message="test",
        )

        # Set new name
        new_name = RandUtil.get_str()
        update_request.plan_name = new_name

        # Store old version
        old_version = [
            obj_target.version.patch,
            obj_target.version.minor,
            obj_target.version.major,
        ][i]

        # Update
        obj_updated = meal_plan_service.update_meal_plan(
            update_request=update_request,
            meal_plan_id=obj_target.id,
            client_name="test_client",
        )

        # Check update result
        assert obj_updated.plan_name == new_name
        assert (
            old_version + 1
            == [
                obj_updated.version.patch,
                obj_updated.version.minor,
                obj_updated.version.major,
            ][i]
        )


@pytest.mark.usefixtures("meal_plan_creates")
def test_delete_meal_plan(
    meal_plan_crud: MealPlanCRUD,
    meal_plan_service: MealPlanService,
) -> None:
    obj_list = meal_plan_crud.search()
    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    meal_plan_service.delete_meal_plan(meal_plan_id=obj_id)
    assert len(obj_list) - 1 == meal_plan_crud.count()

    try:
        meal_plan_crud.get(obj_id=obj_id)
        msg = "MealPlan not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
