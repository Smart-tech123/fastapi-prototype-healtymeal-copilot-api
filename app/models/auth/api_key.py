from enum import StrEnum
from typing import Annotated, Any

from pydantic import Field
from pymongo.database import Database

from app.models.auth.common.access_policy import AccessPolicy
from app.models.common.base_models import TimeStampedModel
from app.models.common.generic_crud import TimeStampedCRUDBase
from app.models.common.object_id import PyObjectId

COLLECTION_NAME = "api_key"


class ApiKey(TimeStampedModel):
    client_id: Annotated[
        PyObjectId,
        Field(description="The id of the client the key belongs to"),
    ]
    key_name: Annotated[
        str,
        Field(
            min_length=3,
            description="User friendly name of the api key",
            examples=[
                "my_api_key",
            ],
        ),
    ]
    key_secret_hash: Annotated[
        str,
        Field(
            description="Hashed key",
            examples=[
                "<hashed_api_key>",
            ],
        ),
    ]
    key_secret_front: Annotated[
        str,
        Field(
            description="Partial front characters of plain key. Used for identification",
            examples=[
                "5423625",
            ],
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="Description for the api key",
            examples=[
                "This is my api key",
            ],
        ),
    ]
    access_policy: Annotated[
        AccessPolicy | None,
        Field(description="Access policy for api key"),
    ] = None

    class Field(StrEnum):
        client_id = "client_id"
        key_name = "key_name"
        key_secret_hash = "key_secret_hash"  # noqa: S105
        key_secret_front = "key_secret_front"  # noqa: S105
        description = "description"
        access_policy = "access_policy"


class ApiKeyRead(ApiKey):
    id: Annotated[PyObjectId, Field(alias="_id")]


class ApiKeyUpdate(TimeStampedModel):
    client_id: PyObjectId | None = None
    key_name: str | None = None
    key_secret_hash: str | None = None
    key_secret_front: str | None = None
    description: str | None = None
    access_policy: AccessPolicy | None = None


class ApiKeyCRUD(TimeStampedCRUDBase[ApiKey, ApiKeyRead, ApiKeyUpdate]):
    def __init__(self, db: Database[dict[str, Any]]) -> None:
        super().__init__(
            db=db,
            collection_name=COLLECTION_NAME,
            read_schema=ApiKeyRead,
            indexes=[
                [
                    ApiKey.Field.client_id.value,
                    ApiKey.Field.key_name.value,
                ]
            ],
        )
