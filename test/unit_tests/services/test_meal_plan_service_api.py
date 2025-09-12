import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from app.api.dependency import get_current_client
from app.api.endpoints.meal_plan_service import router
from app.models.common.version import ChangeType, Version
from app.models.meal_plan import MealPlan, MealPlanCRUD, MealPlanRead
from app.schemas.meal_plan import CreateMealPlanRequest, UpdateMealPlanRequest
from app.utils.rand import RandUtil
from test.fixtures.dependency import mocked_get_current_client


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=router)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    return TestClient(app=app)


@pytest.mark.usefixtures("meal_plan_creates")
def test_create_meal_plan(
    test_http_client: TestClient, meal_plan_crud: MealPlanCRUD, meal_plan_creates: list[MealPlan]
) -> None:
    meal_plan_crud.clear()
    for obj_create in meal_plan_creates:
        resp = test_http_client.post(
            "/",
            json=CreateMealPlanRequest.from_base(obj_create, log_message="test").model_dump(),
        )
        assert resp.status_code == status.HTTP_200_OK

        obj_read = MealPlanRead.model_validate(resp.json())
        assert obj_read.plan_name == obj_create.plan_name
        assert obj_read.version == Version.initial_version()

    assert meal_plan_crud.count() == len(meal_plan_creates)


def test_get_meal_plan(
    test_http_client: TestClient, meal_plan_crud: MealPlanCRUD, meal_plan_creates: list[MealPlan]
) -> None:
    obj_list = meal_plan_crud.search()

    obj_id = obj_list[RandUtil.get_int(up=len(meal_plan_creates))].id
    resp = test_http_client.get(f"/{obj_id}")

    assert resp.status_code == status.HTTP_200_OK

    obj_read = MealPlanRead.model_validate(resp.json())
    assert obj_id == obj_read.id


@pytest.mark.usefixtures("meal_plan_creates")
def test_get_all_meal_plans(test_http_client: TestClient, meal_plan_crud: MealPlanCRUD) -> None:
    obj_list = meal_plan_crud.search()

    resp = test_http_client.get("/")
    assert resp.status_code == status.HTTP_200_OK

    resp_json = resp.json()
    assert isinstance(resp_json, list)

    assert len(resp_json) == len(obj_list)

    for i in range(len(obj_list)):
        obj_read = MealPlanRead.model_validate(resp_json[i])
        assert obj_read.id == obj_list[i].id


@pytest.mark.usefixtures("meal_plan_creates")
def test_update_meal_plan(test_http_client: TestClient, meal_plan_crud: MealPlanCRUD) -> None:
    obj_list = meal_plan_crud.search()
    obj_target = obj_list[RandUtil.get_int(up=len(obj_list))]

    for i in range(3):
        # Set change type
        obj_update = UpdateMealPlanRequest.from_base(
            obj_target,
            change=[ChangeType.PATCH, ChangeType.MINOR, ChangeType.MAJOR][i],
            log_message="test",
        )

        # Set new name
        new_name = RandUtil.get_str()
        obj_update.plan_name = new_name

        # Store old version
        old_version = [
            obj_target.version.patch,
            obj_target.version.minor,
            obj_target.version.major,
        ][i]

        # Update
        resp = test_http_client.put(f"/{obj_target.id}", json=obj_update.model_dump())
        assert resp.status_code == status.HTTP_200_OK

        # Check update result
        obj_updated = MealPlanRead.model_validate(resp.json())
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
def test_delete_meal_plan(test_http_client: TestClient, meal_plan_crud: MealPlanCRUD) -> None:
    obj_list = meal_plan_crud.search()
    obj_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    resp = test_http_client.delete(f"/{obj_id}")
    assert resp.status_code == status.HTTP_200_OK

    try:
        meal_plan_crud.get(obj_id=obj_id)
        msg = "MealPlan not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017
