from typing import Annotated

from pydantic import BaseModel, Field

from app.models.auth.common.access_policy import AccessPolicy
from app.models.common.object_id import PyObjectId


class ClientServiceBase(BaseModel):
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
    description: Annotated[
        str,
        Field(
            description="The description of the client",
            examples=[
                "This client is used for internal work",
            ],
        ),
    ]
    access_policy: Annotated[AccessPolicy | None, Field(description="Access policy for the client")]


class CreateClientRequest(ClientServiceBase):
    tenant_id: Annotated[PyObjectId, Field(description="The id of the tenant the client belongs to")]


class CreateClientResponse(ClientServiceBase):
    tenant_id: Annotated[PyObjectId, Field(description="The id of the tenant the client belongs to")]
    client_id: Annotated[PyObjectId, Field(description="The id of the client")]
    client_secret_plain: Annotated[
        str,
        Field(
            description="Client secret. Plain value",
            examples=[
                "Xdl45Fo23",
            ],
        ),
    ]


class UpdateClientRequest(BaseModel):
    client_name: Annotated[
        str | None,
        Field(
            min_length=3,
            description="The name of the client",
            examples=[
                "internal_bot",
            ],
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            description="The description of the client",
            examples=[
                "This client is used for internal work",
            ],
        ),
    ] = None
    access_policy: Annotated[
        AccessPolicy | None,
        Field(description="Access policy for the client"),
    ] = None


class GetClientResponse(ClientServiceBase):
    tenant_id: Annotated[PyObjectId, Field(description="The id of the tenant the client belongs to")]
    client_id: Annotated[PyObjectId, Field(description="The id of the client")]


class UpdateClientResponse(GetClientResponse):
    pass
