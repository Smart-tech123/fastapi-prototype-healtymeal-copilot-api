import time

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from loguru import logger

from app.api.dependency import get_current_client
from app.api.endpoints.crud import RouterPrefix as RouterPrefixStorage
from app.api.endpoints.crud.version_log import router as router_version_log
from app.api.endpoints.meal_plan_service import router as router_meal_plan
from app.api.endpoints.version_service import router as router_version_service
from app.api.router import RouterPrefix
from app.models.common.version import ChangeType
from app.models.meal_plan import MealPlan, MealPlanCRUD, MealPlanRead
from app.models.version_log import VersionLogAction, VersionLogRead
from app.schemas.meal_plan import CreateMealPlanRequest, UpdateMealPlanRequest
from app.schemas.version_log import VersionLogRollbackRequest
from app.utils.datetime import DatetimeUtil
from app.utils.rand import RandUtil
from test.fixtures.dependency import mocked_get_current_client


def test_version_management(
    app: FastAPI,
    meal_plan_crud: MealPlanCRUD,
    meal_plan_creates: list[MealPlan],
) -> None:
    # Prepare test
    app.include_router(router=router_meal_plan, prefix=RouterPrefix.meal_plan.value)
    app.include_router(router=router_version_log, prefix=RouterPrefixStorage.version_log.value)
    app.include_router(router=router_version_service, prefix=RouterPrefix.version_service.value)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    client = TestClient(app=app)

    meal_plan_crud.clear()
    meal_plan = meal_plan_creates[0]
    meal_plan_other = meal_plan_creates[1]

    # Create meal_plan
    created_at = DatetimeUtil.get_current_timestamp()
    create_msg = "Initial log"
    resp = client.post(
        f"{RouterPrefix.meal_plan.value}/",
        json=CreateMealPlanRequest.from_base(meal_plan, log_message=create_msg).model_dump(),
    )
    assert resp.status_code == status.HTTP_200_OK
    meal_plan_read = MealPlanRead.model_validate(resp.json())

    resp = client.post(
        f"{RouterPrefix.meal_plan.value}/",
        json=CreateMealPlanRequest.from_base(meal_plan_other, log_message=create_msg).model_dump(),
    )
    assert resp.status_code == status.HTTP_200_OK
    # meal_plan_read_other = MealPlanRead.model_validate(resp.json())  # noqa: ERA001

    # Update 1 - change name
    update_msg = "Name is changed"
    new_name = RandUtil.get_str()
    meal_plan_read.plan_name = new_name
    resp = client.put(
        f"{RouterPrefix.meal_plan.value}/{meal_plan_read.id}",
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
        f"{RouterPrefix.meal_plan.value}/{meal_plan_read.id}",
        json=UpdateMealPlanRequest.from_base(
            meal_plan_read,
            change=ChangeType.PATCH,
            log_message=update_msg2,
        ).model_dump(),
    )
    assert resp.status_code == status.HTTP_200_OK
    meal_plan_read = MealPlanRead.model_validate(resp.json())

    # Check version logs by API
    resp = client.get(f"{RouterPrefix.version_service.value}/meal-plan/{meal_plan_read.id}")
    assert resp.status_code == status.HTTP_200_OK

    resp_json = resp.json()
    assert isinstance(resp_json, list)

    version_logs = [VersionLogRead.model_validate(log_dict) for log_dict in resp_json]
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
            assert version_logs[i].metadata.action is VersionLogAction.create
        else:
            assert version_logs[i].metadata.action is VersionLogAction.update

        logger.debug(f"version_log {i} > {version_logs[i].model_dump_json(indent=4)}")

    # Rollback by API
    time.sleep(3)
    updated_at = DatetimeUtil.get_current_timestamp()

    resp = client.post(
        f"{RouterPrefix.version_service.value}/rollback/{meal_plan_read.id}/{version_logs[1].id}",
        json=VersionLogRollbackRequest(msg="Rollback test").model_dump(mode="json"),
    )
    assert resp.status_code == status.HTTP_200_OK
    meal_plan_read = MealPlanRead.model_validate(resp.json())

    assert meal_plan_read.plan_name == new_name
    assert meal_plan_read.description == meal_plan.description

    # Check version logs for the meal_plan by API
    resp = client.get(f"{RouterPrefix.version_service.value}/meal-plan/{meal_plan_read.id}")
    assert resp.status_code == status.HTTP_200_OK

    resp_json = resp.json()
    assert isinstance(resp_json, list)
    version_logs = [VersionLogRead.model_validate(log_dict) for log_dict in resp_json]
    assert len(version_logs) == 4  # means additional rollback log  # noqa: PLR2004

    # Check created_at and updated_at
    assert version_logs[0].created_at is not None
    assert version_logs[0].created_at >= created_at
    assert version_logs[0].created_at < created_at + 1000

    assert version_logs[-1].created_at is not None
    assert version_logs[-1].created_at >= updated_at
    assert version_logs[-1].created_at < updated_at + 1000

    # Check rollback action
    assert version_logs[-1].metadata.action is VersionLogAction.rollback

    # Check all version logs
    resp = client.get(f"{RouterPrefixStorage.version_log.value}/")
    assert resp.status_code == status.HTTP_200_OK

    resp_json = resp.json()
    assert isinstance(resp_json, list)
    version_logs = [VersionLogRead.model_validate(log_dict) for log_dict in resp_json]
    assert len(version_logs) == 5  # addtional 1 log for meal_plan_other  # noqa: PLR2004
