import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.dependency import get_current_client
from app.api.endpoints.validation_service import router
from app.models.meal_plan import MealPlanBase
from app.schemas.validation import ValidationResult
from test.common.validation import get_valid_meal_plan_json
from test.fixtures.dependency import mocked_get_current_client


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=router)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    return TestClient(app=app)


def test_validation_meal_plan_json_valid(test_http_client: TestClient) -> None:
    # Check valid json
    obj_dict = get_valid_meal_plan_json()

    resp = test_http_client.post("/validate-meal-plan", json=obj_dict)
    assert resp.status_code == status.HTTP_200_OK

    validation_res = ValidationResult.model_validate(resp.json())
    assert validation_res.valid


def test_validation_meal_plan_json_invalid(test_http_client: TestClient) -> None:
    # Check invalid json
    obj_dict = get_valid_meal_plan_json()
    obj_dict.pop(MealPlanBase.Field.plan_name.value, None)

    resp = test_http_client.post("/validate-meal-plan", json=obj_dict)
    assert resp.status_code == status.HTTP_200_OK

    validation_res = ValidationResult.model_validate(resp.json())
    assert not validation_res.valid
