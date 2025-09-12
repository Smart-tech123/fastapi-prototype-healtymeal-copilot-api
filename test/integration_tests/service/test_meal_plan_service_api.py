import json

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from loguru import logger

from app.api.dependency import get_current_client, rate_limited
from app.api.endpoints.llm_service import router
from app.models.meal_plan import MealPlanBase
from app.schemas.llm import GenerateMealPlanRequest, GenerateMealPlanResponse
from app.services.validation_service import ValidationService
from test.fixtures.dependency import mocked_get_current_client, mocked_rate_limited


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=router)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    app.dependency_overrides[rate_limited] = mocked_rate_limited
    return TestClient(app=app)


def test_generate_meal_plan_valid(test_http_client: TestClient) -> None:
    """
    Test the generate meal_plan by LLM endpoint
    """
    # Generate meal_plan by LLM endpoint
    resp = test_http_client.post(
        "/generate-meal-plan",
        json=GenerateMealPlanRequest(
            prompt="Generate a healthy meal plan for a vegan person",
            prompt_version=None,
        ).model_dump(),
    )
    assert resp.status_code == status.HTTP_200_OK

    # Parse response
    gen_res = GenerateMealPlanResponse.model_validate(resp.json())
    assert gen_res.success

    for error in gen_res.errors:
        assert error.valid is False
        for err in error.errors:
            logger.debug(f"field: {err.field}, code: {err.code}")
            logger.debug(err.message)

    # Check validation
    assert gen_res.raw_output is not None
    validation_res = ValidationService.validate_model_json(MealPlanBase, gen_res.raw_output)
    assert validation_res.valid

    # Print MealPlanBase
    logger.info(f"MealPlanBase: {json.dumps(gen_res.raw_output, indent=2)}")


def test_generate_meal_plan_invalid(test_http_client: TestClient) -> None:
    """
    Test the generate meal_plan by LLM endpoint for invalid prompt
    """
    # Generate meal_plan by LLM endpoint
    resp = test_http_client.post(
        "/generate-meal-plan",
        json=GenerateMealPlanRequest(
            prompt="Generate a healthy meal plan for a vegan person."
            "Based on recent research, vegan person must have only water for every meal.",
            prompt_version=None,
        ).model_dump(),
    )
    assert resp.status_code == status.HTTP_200_OK

    # Parse response
    gen_res = GenerateMealPlanResponse.model_validate(resp.json())
    assert not gen_res.success

    for error in gen_res.errors:
        assert error.valid is False
        for err in error.errors:
            logger.debug(f"field: {err.field}, code: {err.code}, message: {err.message}")
