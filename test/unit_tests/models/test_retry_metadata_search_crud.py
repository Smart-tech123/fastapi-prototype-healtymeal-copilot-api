"""
test_retry_metadata_search.py

This test suite focuses on validating the search operations for `RetryMetadata`, including:

1. Field-level filtering:
   - Ensures each individual field in the `RetryMetadata` model can be queried and returns expected results.

2. Base filter field operations:
   - Validates that standard filters operate correctly across the supported field types and conditions.

Target: Ensures robust and predictable search behavior for `RetryMetadata` DB operations.
"""

import pytest

from app.core.config.llm import LLMProvider
from app.models.common.filter import (
    ComparableFilterCondition,
    ComparableFilterField,
    ObjectFilterCondition,
    ObjectFilterField,
    StringFilterCondition,
    StringFilterField,
)
from app.models.retry_metadata import RetryMetadataCRUD, RetryMetadataFilter


@pytest.mark.usefixtures("retry_metadata_creates")
def test_search_prompt_version(retry_metadata_crud: RetryMetadataCRUD) -> None:
    """
    Test prompt version search.
    Focused on object filter field.
    """
    obj_list = retry_metadata_crud.search()
    total_len = len(obj_list)

    for obj in obj_list:
        # Check eq filter
        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                prompt_version=ObjectFilterField[dict[str, int]](
                    value=obj.prompt_version.model_dump(),
                    condition=ObjectFilterCondition.EQ,
                ),
            ).query()
        )
        assert len(res) == 1

        # Check ne filter
        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                prompt_version=ObjectFilterField[dict[str, int]](
                    value=obj.prompt_version.model_dump(),
                    condition=ObjectFilterCondition.NE,
                ),
            ).query()
        )
        assert len(res) == total_len - 1


@pytest.mark.usefixtures("retry_metadata_creates")
def test_search_input_prompt(retry_metadata_crud: RetryMetadataCRUD) -> None:
    """
    Test input prompt search.
    Focused on string filter field.
    """
    obj_list = retry_metadata_crud.search()
    total_len = len(obj_list)

    for obj in obj_list:
        # Check eq filter
        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt,
                    condition=StringFilterCondition.EQ,
                ),
            ).query()
        )
        assert len(res) == 1

        # Check ne filter
        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt,
                    condition=StringFilterCondition.NE,
                ),
            ).query()
        )
        assert len(res) == total_len - 1

        # Check starts with filter
        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt[:-1],
                    condition=StringFilterCondition.STARTS_WITH,
                ),
            ).query()
        )
        assert len(res) == 1

        # Check ends with filter
        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt[1:],
                    condition=StringFilterCondition.ENDS_WITH,
                ),
            ).query()
        )
        assert len(res) == 1

        # Check contains filter
        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt[1:-1],
                    condition=StringFilterCondition.CONTAINS,
                ),
            ).query()
        )
        assert len(res) == 1

        # Check case sensitive filter
        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                input_prompt=StringFilterField(
                    value=obj.input_prompt[1:-1].upper(),
                    condition=StringFilterCondition.CONTAINS,
                    case_sensitive=True,
                ),
            ).query()
        )
        assert len(res) == 0


@pytest.mark.usefixtures("retry_metadata_creates")
def test_search_final_prompt(retry_metadata_crud: RetryMetadataCRUD) -> None:
    """
    Test final prompt search.
    """
    obj_list = retry_metadata_crud.search()

    for obj in obj_list:
        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                final_prompt=StringFilterField(
                    value=obj.final_prompt,
                    condition=StringFilterCondition.EQ,
                ),
            ).query()
        )
        assert len(res) == 1

        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                final_prompt=StringFilterField(
                    value=obj.final_prompt + "zzz",
                    condition=StringFilterCondition.EQ,
                ),
            ).query()
        )
        assert len(res) == 0


@pytest.mark.usefixtures("retry_metadata_creates")
def test_search_model_used(retry_metadata_crud: RetryMetadataCRUD) -> None:
    """
    Test model used search.
    """
    obj_list = retry_metadata_crud.search()
    total_len = len(obj_list)

    res_openai = retry_metadata_crud.search(
        RetryMetadataFilter(
            model_used=StringFilterField(
                value=LLMProvider.OPENAI.value,
                condition=StringFilterCondition.EQ,
            ),
        ).query()
    )
    res_claude = retry_metadata_crud.search(
        RetryMetadataFilter(
            model_used=StringFilterField(
                value=LLMProvider.ANTHROPIC_CLAUDE.value,
                condition=StringFilterCondition.EQ,
            ),
        ).query()
    )
    res_gemini = retry_metadata_crud.search(
        RetryMetadataFilter(
            model_used=StringFilterField(
                value=LLMProvider.GOOGLE_GEMINI.value,
                condition=StringFilterCondition.EQ,
            ),
        ).query()
    )

    assert len(res_openai) + len(res_claude) + len(res_gemini) == total_len


@pytest.mark.usefixtures("retry_metadata_creates")
def test_timestamp(retry_metadata_crud: RetryMetadataCRUD) -> None:
    """
    Test timestamp search.
    Focused on comparable filter field.
    """
    obj_list = retry_metadata_crud.search()
    obj_list = sorted(obj_list, key=lambda x: x.created_at or 0)
    total_len = len(obj_list)

    for obj in obj_list:
        # Check eq filter
        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                created_at=ComparableFilterField[int](
                    value=obj.created_at,
                    condition=ComparableFilterCondition.EQ,
                ),
            ).query()
        )
        assert len(res) == 1

        # Check ne filter
        res = retry_metadata_crud.search(
            RetryMetadataFilter(
                created_at=ComparableFilterField[int](
                    value=obj.created_at,
                    condition=ComparableFilterCondition.NE,
                ),
            ).query()
        )
        assert len(res) == total_len - 1

    # Check gt filter
    res = retry_metadata_crud.search(
        RetryMetadataFilter(
            created_at=ComparableFilterField[int](
                value=obj_list[0].created_at,
                condition=ComparableFilterCondition.GT,
            ),
        ).query()
    )
    assert len(res) == total_len - 1
    res = retry_metadata_crud.search(
        RetryMetadataFilter(
            created_at=ComparableFilterField[int](
                value=obj_list[-1].created_at,
                condition=ComparableFilterCondition.GT,
            ),
        ).query()
    )
    assert len(res) == 0

    # Check lt filter
    res = retry_metadata_crud.search(
        RetryMetadataFilter(
            created_at=ComparableFilterField[int](
                value=obj_list[-1].created_at,
                condition=ComparableFilterCondition.LT,
            ),
        ).query()
    )
    assert len(res) == total_len - 1
    res = retry_metadata_crud.search(
        RetryMetadataFilter(
            created_at=ComparableFilterField[int](
                value=obj_list[0].created_at,
                condition=ComparableFilterCondition.LT,
            ),
        ).query()
    )
    assert len(res) == 0

    # Check gte filter
    res = retry_metadata_crud.search(
        RetryMetadataFilter(
            created_at=ComparableFilterField[int](
                value=obj_list[0].created_at,
                condition=ComparableFilterCondition.GTE,
            ),
        ).query()
    )
    assert len(res) == total_len

    # Check lte filter
    res = retry_metadata_crud.search(
        RetryMetadataFilter(
            created_at=ComparableFilterField[int](
                value=obj_list[-1].created_at,
                condition=ComparableFilterCondition.LTE,
            ),
        ).query()
    )
    assert len(res) == total_len

    # Check gt_lt filter
    res = retry_metadata_crud.search(
        RetryMetadataFilter(
            created_at=ComparableFilterField[int](
                value=(obj_list[0].created_at, obj_list[-1].created_at),
                condition=ComparableFilterCondition.GT_LT,
            ),
        ).query()
    )
    assert len(res) == total_len - 2

    # Check gt_lte filter
    res = retry_metadata_crud.search(
        RetryMetadataFilter(
            created_at=ComparableFilterField[int](
                value=(obj_list[0].created_at, obj_list[-1].created_at),
                condition=ComparableFilterCondition.GT_LTE,
            ),
        ).query()
    )
    assert len(res) == total_len - 1

    # Check gte_lt filter
    res = retry_metadata_crud.search(
        RetryMetadataFilter(
            created_at=ComparableFilterField[int](
                value=(obj_list[0].created_at, obj_list[-1].created_at),
                condition=ComparableFilterCondition.GTE_LT,
            ),
        ).query()
    )
    assert len(res) == total_len - 1

    # Check gte_lte filter
    res = retry_metadata_crud.search(
        RetryMetadataFilter(
            created_at=ComparableFilterField[int](
                value=(obj_list[0].created_at, obj_list[-1].created_at),
                condition=ComparableFilterCondition.GTE_LTE,
            ),
        ).query()
    )
    assert len(res) == total_len
