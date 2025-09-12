"""
test_retry_metadata_search.py

This test module focuses on validating the search endpoint behavior of the
RetryMetadata component, specifically its integration with the CRUD.

Scope:
- This test suite ensures that the RetryMetadata search endpoint correctly
    routes and processes requests to the CRUD service.
- It does *not* cover field-level search behavior (e.g., filters or
    conditions), as that is tested separately in the CRUD component's own search tests.
- The emphasis here is on verifying the presence, correctness,
    and routing of search-related API calls made to the RetryMetadata CRUD endpoint.
"""

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.dependency import get_current_client
from app.api.endpoints.crud.retry_metadata import router
from app.models.common.filter import StringFilterCondition, StringFilterField
from app.models.retry_metadata import RetryMetadataCRUD, RetryMetadataFilter, RetryMetadataRead
from test.fixtures.dependency import mocked_get_current_client


@pytest.mark.usefixtures("retry_metadata_creates")
def test_search_input_prompt(app: FastAPI, retry_metadata_crud: RetryMetadataCRUD) -> None:
    """
    Test input prompt search.
    Focused on string filter field.
    """
    app.include_router(router=router)
    app.dependency_overrides[get_current_client] = mocked_get_current_client
    client = TestClient(app=app)

    obj_list = retry_metadata_crud.search()
    total_len = len(obj_list)

    for obj in obj_list:
        # Check eq filter
        resp = client.post(
            "/search",
            json=RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt,
                    condition=StringFilterCondition.EQ,
                ),
            ).model_dump(mode="json"),
        )
        assert resp.status_code == status.HTTP_200_OK

        resp_json = resp.json()
        assert isinstance(resp_json, list)

        res = [RetryMetadataRead.model_validate(x) for x in resp_json]
        assert len(res) == 1

        # Check ne filter
        resp = client.post(
            "/search",
            json=RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt,
                    condition=StringFilterCondition.NE,
                ),
            ).model_dump(mode="json"),
        )
        assert resp.status_code == status.HTTP_200_OK

        resp_json = resp.json()
        assert isinstance(resp_json, list)

        res = [RetryMetadataRead.model_validate(x) for x in resp_json]
        assert len(res) == total_len - 1

        # Check starts with filter
        resp = client.post(
            "/search",
            json=RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt[:-1],
                    condition=StringFilterCondition.STARTS_WITH,
                ),
            ).model_dump(mode="json"),
        )
        assert resp.status_code == status.HTTP_200_OK

        resp_json = resp.json()
        assert isinstance(resp_json, list)

        res = [RetryMetadataRead.model_validate(x) for x in resp_json]
        assert len(res) == 1

        # Check ends with filter
        resp = client.post(
            "/search",
            json=RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt[1:],
                    condition=StringFilterCondition.ENDS_WITH,
                ),
            ).model_dump(mode="json"),
        )
        assert resp.status_code == status.HTTP_200_OK

        resp_json = resp.json()
        assert isinstance(resp_json, list)

        res = [RetryMetadataRead.model_validate(x) for x in resp_json]
        assert len(res) == 1

        # Check contains filter
        resp = client.post(
            "/search",
            json=RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt[1:-1],
                    condition=StringFilterCondition.CONTAINS,
                ),
            ).model_dump(mode="json"),
        )
        assert resp.status_code == status.HTTP_200_OK

        resp_json = resp.json()
        assert isinstance(resp_json, list)

        res = [RetryMetadataRead.model_validate(x) for x in resp_json]
        assert len(res) == 1

        # Check case sensitive filter
        resp = client.post(
            "/search",
            json=RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt[1:-1].upper(),
                    condition=StringFilterCondition.CONTAINS,
                    case_sensitive=True,
                ),
            ).model_dump(mode="json"),
        )
        assert resp.status_code == status.HTTP_200_OK

        resp_json = resp.json()
        assert isinstance(resp_json, list)

        res = [RetryMetadataRead.model_validate(x) for x in resp_json]
        assert len(res) == 0
