from typing import Annotated

from pydantic import BaseModel, Field

from app.models.auth.common.access_policy import AccessPolicy
from app.models.auth.tenant import TenantStatus
from app.models.common.object_id import PyObjectId


class TenantServiceBase(BaseModel):
    tenant_name: Annotated[
        str,
        Field(
            min_length=3,
            description="The name of the tenant",
            examples=[
                "internal_group",
            ],
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="The description of the tenant",
            examples=[
                "This is an Internal group",
            ],
        ),
    ]
    access_policy: Annotated[
        AccessPolicy,
        Field(description="Access policy for tenant"),
    ]


class CreateTenantRequest(TenantServiceBase):
    pass


class CreateTenantResponse(TenantServiceBase):
    tenant_id: Annotated[PyObjectId, Field(description="Unique id of the tenant")]
    status: Annotated[TenantStatus, Field(description="Status of the tenant")]


class UpdateTenantRequest(BaseModel):
    tenant_name: Annotated[
        str | None,
        Field(
            min_length=3,
            description="The name of the tenant",
            examples=[
                "internal_group",
            ],
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            description="The description of the tenant",
            examples=[
                "This is an Internal group",
            ],
        ),
    ] = None
    access_policy: Annotated[
        AccessPolicy | None,
        Field(description="Access policy for tenant"),
    ] = None


class GetTenantResponse(TenantServiceBase):
    tenant_id: Annotated[PyObjectId, Field(description="Unique id of the tenant")]
    status: Annotated[TenantStatus, Field(description="Status of the tenant")]


class UpdateTenantResponse(GetTenantResponse):
    pass
