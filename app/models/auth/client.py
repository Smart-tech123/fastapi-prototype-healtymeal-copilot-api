from enum import StrEnum
from typing import Annotated, Any

from pydantic import Field
from pymongo.database import Database

from app.models.auth.common.access_policy import AccessPolicy
from app.models.common.base_models import TimeStampedModel
from app.models.common.generic_crud import TimeStampedCRUDBase
from app.models.common.object_id import PyObjectId

COLLECTION_NAME = "client"


class Client(TimeStampedModel):
    tenant_id: Annotated[
        PyObjectId,
        Field(description="The id of the tenant the client belongs to"),
    ]
    client_name: Annotated[
        str,
        Field(
            min_length=3,
            description="The name of the client",
            examples=[
                "internal_bot",
            ],
        ),
    ]
    client_secret_hash: Annotated[
        str,
        Field(
            description="OAuth2 client secret. Will store as hashed value",
            examples=[
                "<hashed_client_secret>",
            ],
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="The description of the client",
            examples=[
                "This client is used for internal work",
            ],
        ),
    ]
    access_policy: Annotated[
        AccessPolicy | None,
        Field(description="Access policy for the client"),
    ] = None

    class Field(StrEnum):
        tenant_id = "tenant_id"
        client_name = "client_name"
        client_secret_hash = "client_secret_hash"  # noqa: S105
        description = "description"
        access_policy = "access_policy"


class ClientRead(Client):
    id: Annotated[PyObjectId, Field(alias="_id")]


class ClientUpdate(TimeStampedModel):
    tenant_id: PyObjectId | None = None
    client_name: str | None = None
    client_secret_hash: str | None = None
    description: str | None = None
    access_policy: AccessPolicy | None = None


class ClientCRUD(TimeStampedCRUDBase[Client, ClientRead, ClientUpdate]):
    def __init__(self, db: Database[dict[str, Any]]) -> None:
        super().__init__(
            db=db,
            collection_name=COLLECTION_NAME,
            read_schema=ClientRead,
            indexes=[
                [
                    Client.Field.tenant_id.value,
                    Client.Field.client_name.value,
                ],
            ],
        )
