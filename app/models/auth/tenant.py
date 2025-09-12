from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field
from pymongo.database import Database

from app.models.auth.common.access_policy import AccessPolicy
from app.models.common.base_models import TimeStampedModel
from app.models.common.generic_crud import TimeStampedCRUDBase
from app.models.common.object_id import PyObjectId

COLLECTION_NAME = "tenant"


class TenantStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class TenantKey(BaseModel):
    kid: Annotated[
        str,
        Field(
            description="The id of the tenant key",
            examples=[
                "12345678-1234-1234-1234-123456789012",
            ],
        ),
    ]
    public_jwk: Annotated[
        dict[str, Any],
        Field(
            description="The public jwk of the tenant key",
            examples=[
                "{...}",
            ],
        ),
    ]
    private_pem: Annotated[
        str,
        Field(
            description="The private pem of the tenant key",
            examples=[
                "<private_pem>",
            ],
        ),
    ]
    created_at: Annotated[
        int,
        Field(
            description="Unix timestamp in milliseconds",
            examples=[
                "<timestamp_ms>",
            ],
        ),
    ]

    class Field(StrEnum):
        kid = "kid"
        public_jwk = "public_jwk"
        private_pem = "private_pem"
        created_at = "created_at"


class Tenant(TimeStampedModel):
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
    status: Annotated[
        TenantStatus,
        Field(description="The status of the tenant"),
    ]
    keys: Annotated[
        list[TenantKey],
        Field(description="The keys of the tenant for JWT authentication"),
    ]
    access_policy: Annotated[
        AccessPolicy,
        Field(description="Access policy for tenant"),
    ]

    class Field(StrEnum):
        tenant_name = "tenant_name"
        description = "description"
        status = "status"
        keys = "keys"
        access_policy = "access_policy"


class TenantRead(Tenant):
    id: Annotated[PyObjectId, Field(alias="_id")]


class TenantUpdate(TimeStampedModel):
    tenant_name: str | None = None
    description: str | None = None
    status: TenantStatus | None = None
    keys: list[TenantKey] | None = None
    access_policy: AccessPolicy | None = None


class TenantCRUD(TimeStampedCRUDBase[Tenant, TenantRead, TenantUpdate]):
    def __init__(self, db: Database[dict[str, Any]]) -> None:
        super().__init__(
            db=db,
            collection_name=COLLECTION_NAME,
            read_schema=TenantRead,
            indexes=[
                [
                    Tenant.Field.tenant_name.value,
                ]
            ],
        )
