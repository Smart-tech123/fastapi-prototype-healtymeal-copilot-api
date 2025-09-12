from typing import Annotated

from pydantic import BaseModel, Field

from app.models.auth.common.access_policy import AccessPolicy
from app.models.common.object_id import PyObjectId


class ApiKeyServiceBase(BaseModel):
    key_name: Annotated[
        str,
        Field(
            min_length=3,
            description="User friendly name for key",
            examples=[
                "my_api_key",
            ],
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="Description for key",
            examples=[
                "This is my api key",
            ],
        ),
    ]
    access_policy: Annotated[AccessPolicy | None, Field(description="Access policy for api key")]


class CreateApiKeyRequest(ApiKeyServiceBase):
    pass


class CreateApiKeyResponse(ApiKeyServiceBase):
    client_id: Annotated[PyObjectId, Field(description="The id of the client the key belongs to")]
    key_id: Annotated[PyObjectId, Field(description="The id of the key")]
    key_plain: Annotated[
        str,
        Field(
            description="Plain key to be used for authentication",
            examples=[
                "<plain_api_key_to_be_used>",
            ],
        ),
    ]
    access_policy: Annotated[AccessPolicy, Field(description="Access policy for the api key")]


class UpdateApiKeyRequest(BaseModel):
    key_name: str | None = None
    description: str | None = None
    access_policy: AccessPolicy | None = None


class GetApiKeyResponse(ApiKeyServiceBase):
    client_id: Annotated[PyObjectId, Field(description="The id of the client the key belongs to")]
    key_id: Annotated[PyObjectId, Field(description="The id of the key")]
    key_secret_front: Annotated[
        str,
        Field(
            description="Partial front characters of plain key. Used for identification",
            examples=[
                "5423625",
            ],
        ),
    ]
    access_policy: Annotated[AccessPolicy, Field(description="Access policy for the api key")]


class UpdateApiKeyResponse(GetApiKeyResponse):
    pass
