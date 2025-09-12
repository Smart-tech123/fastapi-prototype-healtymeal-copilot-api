from enum import StrEnum
from typing import Annotated, Any

from pydantic import Field
from pymongo.database import Database

from app.core.config.llm import LLMProvider
from app.models.common.base_models import TimeStampedModel
from app.models.common.generic_crud import TimeStampedCRUDBase
from app.models.common.object_id import PyObjectId
from app.models.common.version import Version

COLLECTION_NAME = "audit_log"


class AuditLog(TimeStampedModel):
    # Account Info
    tenant_id: Annotated[
        PyObjectId | None,
        Field(description="Tenant id"),
    ]
    tenant_name: Annotated[
        str | None,
        Field(
            description="Tenant name",
            examples=[
                "internal_group",
            ],
        ),
    ]
    client_id: Annotated[
        PyObjectId | None,
        Field(description="Client id"),
    ]
    client_name: Annotated[
        str | None,
        Field(
            description="Client name",
            examples=[
                "internal_bot",
            ],
        ),
    ]
    api_key_id: Annotated[
        PyObjectId | None,
        Field(description="Api key id"),
    ]
    api_key_name: Annotated[
        str | None,
        Field(
            description="Api key name",
            examples=[
                "my_api_key",
            ],
        ),
    ]

    # LLM Info
    input_prompt: Annotated[
        str | None,
        Field(
            description="User LLM prompt",
            examples=[
                "Generate a healthy meal plan for a vegan person",
            ],
        ),
    ]
    prompt_version: Annotated[
        Version | None,
        Field(description="Prompt version to be used for LLM"),
    ]
    model_used: Annotated[
        LLMProvider | None,
        Field(description="Model used for LLM"),
    ]

    # Request
    request_path: Annotated[
        str,
        Field(
            description="Request URL path",
            examples=[
                "/llm/generate-meal-plan",
            ],
        ),
    ]
    request_query: Annotated[
        str,
        Field(
            description="Request query parameters",
            examples=[
                "api_key_id=1234",
            ],
        ),
    ]
    request_method: Annotated[
        str,
        Field(
            description="Request method",
            examples=[
                "POST",
            ],
        ),
    ]
    remote_address: Annotated[
        str,
        Field(
            description="Remote address of the request",
            examples=[
                "127.0.0.1",
            ],
        ),
    ]

    # Response
    response_status: Annotated[
        int,
        Field(
            description="Response status code",
            examples=[
                200,
            ],
        ),
    ]
    latency_ms: Annotated[
        int,
        Field(
            ge=0,
            description="Latency in milliseconds",
            examples=[
                1000,
            ],
        ),
    ]

    class Field(StrEnum):
        tenant_id = "tenant_id"
        tenant_name = "tenant_name"
        client_id = "client_id"
        client_name = "client_name"
        api_key_id = "api_key_id"
        api_key_name = "api_key_name"
        input_prompt = "input_prompt"
        prompt_version = "prompt_version"
        model_used = "model_used"
        request_path = "request_path"
        request_query = "request_query"
        request_method = "request_method"
        remote_address = "remote_address"
        response_status = "response_status"
        latency_ms = "latency_ms"


class AuditLogRead(AuditLog):
    id: Annotated[PyObjectId, Field(alias="_id")]


class AuditLogUpdate(TimeStampedModel):
    tenant_id: PyObjectId | None = None
    tenant_name: str | None = None
    client_id: PyObjectId | None = None
    client_name: str | None = None
    api_key_id: PyObjectId | None = None
    api_key_name: str | None = None
    input_prompt: str | None = None
    prompt_version: Version | None = None
    model_used: LLMProvider | None = None
    trial_id: str | None = None
    request_path: str | None = None
    request_query: str | None = None
    request_method: str | None = None
    remote_address: str | None = None
    response_status: int | None = None
    latency_ms: int | None = None


class AuditLogCRUD(TimeStampedCRUDBase[AuditLog, AuditLogRead, AuditLogUpdate]):
    def __init__(self, db: Database[dict[str, Any]]) -> None:
        super().__init__(
            db=db,
            collection_name=COLLECTION_NAME,
            read_schema=AuditLogRead,
        )
