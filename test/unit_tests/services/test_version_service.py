import time

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from loguru import logger

from app.api.dependency import get_current_client
from app.api.endpoints.meal_plan_service import router
from app.models.common.version import ChangeType
from app.models.meal_plan import MealPlan, MealPlanCRUD, MealPlanRead
from app.models.version_log import VersionLogAction, VersionLogCRUD
from app.schemas.meal_plan import CreateMealPlanRequest, UpdateMealPlanRequest
from app.services.version_log_service import VersionLogService
from app.utils.datetime import DatetimeUtil
from app.utils.rand import RandUtil
from test.fixtures.dependency import mocked_get_current_client
from test.fixtures.mongo import MockedDB


def test_version_management(
    app: FastAPI,
    mocked_db: MockedDB,
    meal_plan_crud: MealPlanCRUD,
    version_log_crud: VersionLogCRUD,
    meal_plan_creates: list[MealPlan],
) -> None:
    # Prepare test
    app.include_router(router=router)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    client = TestClient(app=app)

    meal_plan_crud.clear()
    meal_plan = meal_plan_creates[RandUtil.get_int(up=len(meal_plan_creates))]

    # Create meal_plan
    created_at = DatetimeUtil.get_current_timestamp()
    create_msg = "Initial log"
    resp = client.post(
        "/",
        json=CreateMealPlanRequest.from_base(meal_plan, log_message=create_msg).model_dump(),
    )
    assert resp.status_code == status.HTTP_200_OK
    meal_plan_read = MealPlanRead.model_validate(resp.json())

    # Update 1 - change name
    update_msg = "Name is changed"
    new_name = RandUtil.get_str()
    meal_plan_read.plan_name = new_name
    resp = client.put(
        f"/{meal_plan_read.id}",
        json=UpdateMealPlanRequest.from_base(
            meal_plan_read,
            change=ChangeType.PATCH,
            log_message=update_msg,
        ).model_dump(),
    )
    assert resp.status_code == status.HTTP_200_OK
    meal_plan_read = MealPlanRead.model_validate(resp.json())

    # Update 2 - change description
    update_msg2 = "Description is changed"
    new_desc = RandUtil.get_str()
    meal_plan_read.description = new_desc
    resp = client.put(
        f"/{meal_plan_read.id}",
        json=UpdateMealPlanRequest.from_base(
            meal_plan_read,
            change=ChangeType.PATCH,
            log_message=update_msg2,
        ).model_dump(),
    )
    assert resp.status_code == status.HTTP_200_OK
    meal_plan_read = MealPlanRead.model_validate(resp.json())

    # Check version logs
    version_logs = version_log_crud.search()
    assert len(version_logs) == 3  # means initial log + 2 updates  # noqa: PLR2004

    for i in range(len(version_logs)):
        # Check message
        assert (
            version_logs[i].message
            == [
                create_msg,
                update_msg,
                update_msg2,
            ][i]
        )

        # Check action
        if i == 0:
            assert version_logs[i].metadata.action == VersionLogAction.create
        else:
            assert version_logs[i].metadata.action == VersionLogAction.update

        logger.debug(f"version_log {i} > {version_logs[i].model_dump_json(indent=4)}")

    # Rollback
    time.sleep(3)
    updated_at = DatetimeUtil.get_current_timestamp()
    version_log_service = VersionLogService(db=mocked_db.pymongo_db)

    meal_plan_read = version_log_service.rollback(
        meal_plan_id=meal_plan_read.id,
        log_id=version_logs[1].id,
        client_name="test",
        msg="Rollback",
    )
    assert meal_plan_read.plan_name == new_name
    assert meal_plan_read.description == meal_plan.description

    # Check version logs
    version_logs = version_log_crud.search()
    assert len(version_logs) == 4  # means additional rollback log  # noqa: PLR2004

    # Check created_at and updated_at
    assert version_logs[0].created_at is not None
    assert version_logs[0].created_at >= created_at
    assert version_logs[0].created_at < created_at + 1000

    assert version_logs[-1].created_at is not None
    assert version_logs[-1].created_at >= updated_at
    assert version_logs[-1].created_at < updated_at + 1000

    # Check action
    assert version_logs[-1].metadata.action == VersionLogAction.rollback
