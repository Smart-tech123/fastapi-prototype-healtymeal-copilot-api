from enum import StrEnum
from typing import Annotated, Any, override

from pydantic import Field
from pymongo.database import Database

from app.core.config.llm import LLMProvider
from app.models.common.base_models import TimeStampedModel
from app.models.common.filter import ComparableFilterField, FilterBase, ObjectFilterField, StringFilterField
from app.models.common.generic_crud import TimeStampedCRUDBase
from app.models.common.object_id import PyObjectId
from app.models.common.version import Version

COLLECTION_NAME = "retry_metadata"


class RetryReason(StrEnum):
    validation_failed = "validation_failed"
    llm_error = "llm_error"


class RetryMetadata(TimeStampedModel):
    prompt_version: Annotated[
        Version,
        Field(
            description="Prompt version to be used for LLM",
        ),
    ]
    input_prompt: Annotated[
        str,
        Field(description="Input prompt provided by user"),
    ]
    final_prompt: Annotated[
        str,
        Field(description="Final prompt passed to LLM"),
    ]
    model_used: Annotated[
        LLMProvider,
        Field(
            description="Model used for LLM",
            examples=[
                "openai",
                "google_gemini",
                "anthropic_claude",
            ],
        ),
    ]
    retry_count: Annotated[
        int,
        Field(ge=0, description="Number of retries"),
    ]
    retry_reason: Annotated[
        RetryReason,
        Field(description="Reason for retry"),
    ]
    error_message: Annotated[
        str,
        Field(description="Error message"),
    ]
    error_details: Annotated[
        Any,
        Field(description="Error details"),
    ]

    class Field(StrEnum):
        prompt_version = "prompt_version"
        input_prompt = "input_prompt"
        final_prompt = "final_prompt"
        model_used = "model_used"
        retry_count = "retry_count"
        retry_reason = "retry_reason"
        error_message = "error_message"
        error_details = "error_details"


class RetryMetadataRead(RetryMetadata):
    id: Annotated[PyObjectId, Field(alias="_id")]


class RetryMetadataUpdate(TimeStampedModel):
    prompt_version: Version | None = None
    input_prompt: str | None = None
    final_prompt: str | None = None
    model_used: LLMProvider | None = None
    retry_count: int | None = None
    retry_reason: RetryReason | None = None
    error_message: str | None = None
    error_details: Any | None = None


class RetryMetadataFilter(FilterBase):
    prompt_version: ObjectFilterField[dict[str, int]] | None = None
    input_prompt: StringFilterField | None = None
    final_prompt: StringFilterField | None = None
    model_used: StringFilterField | None = None
    retry_count: ComparableFilterField[int] | None = None
    retry_reason: StringFilterField | None = None
    error_message: StringFilterField | None = None
    created_at: ComparableFilterField[int] | None = None
    updated_at: ComparableFilterField[int] | None = None

    @override
    def query(self) -> dict[str, Any]:
        query = {}
        if self.prompt_version is not None:
            query[RetryMetadata.Field.prompt_version.value] = self.prompt_version.query()
        if self.input_prompt is not None:
            query[RetryMetadata.Field.input_prompt.value] = self.input_prompt.query()
        if self.final_prompt is not None:
            query[RetryMetadata.Field.final_prompt.value] = self.final_prompt.query()
        if self.model_used is not None:
            query[RetryMetadata.Field.model_used.value] = self.model_used.query()
        if self.retry_count is not None:
            query[RetryMetadata.Field.retry_count.value] = self.retry_count.query()
        if self.retry_reason is not None:
            query[RetryMetadata.Field.retry_reason.value] = self.retry_reason.query()
        if self.error_message is not None:
            query[RetryMetadata.Field.error_message.value] = self.error_message.query()
        if self.created_at is not None:
            query[TimeStampedModel.Field.created_at.value] = self.created_at.query()
        if self.updated_at is not None:
            query[TimeStampedModel.Field.updated_at.value] = self.updated_at.query()
        return query


class RetryMetadataCRUD(TimeStampedCRUDBase[RetryMetadata, RetryMetadataRead, RetryMetadataUpdate]):
    def __init__(self, db: Database[dict[str, Any]]) -> None:
        super().__init__(
            db=db,
            collection_name=COLLECTION_NAME,
            read_schema=RetryMetadataRead,
        )
