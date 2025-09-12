import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from loguru import logger

from app.api.dependency import get_current_client, rate_limited
from app.api.endpoints.llm_service import router
from app.core.config.llm import LLMProvider
from app.core.config.llm import config as cfg_llm
from app.models.retry_metadata import RetryMetadataCRUD
from app.schemas.llm import GenerateMealPlanRequest
from app.utils.datetime import DatetimeUtil
from test.fixtures.dependency import mocked_get_current_client, mocked_rate_limited


@pytest.fixture
def test_http_client(app: FastAPI) -> TestClient:
    app.include_router(router=router)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    app.dependency_overrides[rate_limited] = mocked_rate_limited
    return TestClient(app=app)


def test_retry_metadata(test_http_client: TestClient, retry_metadata_crud: RetryMetadataCRUD) -> None:
    """
    Test the retry metadata service.
    """
    start_time_stamp = DatetimeUtil.get_current_timestamp()

    # Try to generate meal plan by LLM endpoint with invalid prompt
    invalid_prompt = (
        "Generate a healthy meal plan for a vegan person."
        "Based on recent research, vegan person must have only water for every meal."
    )

    resp = test_http_client.post(
        "/generate-meal-plan",
        json=GenerateMealPlanRequest(
            prompt=invalid_prompt,
            prompt_version=None,
        ).model_dump(),
    )
    assert resp.status_code == status.HTTP_200_OK

    # Check if retry metadata logs are created
    retry_metadata = retry_metadata_crud.search()
    assert len(retry_metadata) >= 1
    logger.debug(f"RetryMetadata count: {len(retry_metadata)}")

    # Check every field in retry metadata
    for retry in retry_metadata:
        # Check prompt version
        assert retry.prompt_version == cfg_llm.DEFAULT_PROMPT_VERSION

        # Check input prompt
        assert retry.input_prompt == invalid_prompt

        # Check final prompt
        logger.debug(f"Final prompt: {retry.final_prompt[:20]}")

        # Check model used
        assert retry.model_used == LLMProvider.OPENAI

        # Check retry count
        logger.debug(f"Retry count: {retry.retry_count}")

        # Check retry reason
        logger.debug(f"Retry reason: {retry.retry_reason}")

        # Check error message
        logger.debug(f"Error message: {retry.error_message}")

        # Check error details
        logger.debug(f"Error details: {retry.error_details}")

        # Check timestamp
        assert retry.created_at is not None
        assert retry.created_at >= start_time_stamp
        assert retry.created_at <= DatetimeUtil.get_current_timestamp()
        logger.debug(f"Timestamp: {DatetimeUtil.get_datetime_from_timestamp(retry.created_at)}")
