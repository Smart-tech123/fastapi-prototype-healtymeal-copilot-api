from typing import Any

from pymongo.database import Database

from app.models.auth.tenant import Tenant, TenantCRUD, TenantKey, TenantRead, TenantStatus, TenantUpdate
from app.models.common.object_id import PyObjectId
from app.schemas.auth.tenant import (
    CreateTenantRequest,
    CreateTenantResponse,
    GetTenantResponse,
    UpdateTenantRequest,
    UpdateTenantResponse,
)
from app.schemas.errors import ConflictException, ErrorCode409
from app.services.auth.client_service import ClientService
from app.utils.datetime import DatetimeUtil
from app.utils.key import KeyUtil


class TenantService:
    def __init__(self, db: Database[dict[str, Any]]) -> None:
        self.db = db
        self.crud = TenantCRUD(db=db)
        self.client_service = ClientService(db=db)

    def create_tenant(self, create_request: CreateTenantRequest) -> CreateTenantResponse:
        # Check if tenant already exists
        if self.crud.search(
            {
                Tenant.Field.tenant_name: create_request.tenant_name,
            }
        ):
            raise ConflictException(
                error_code=ErrorCode409.CONFLICT,
                message="Tenant already exists",
            )

        # Generate keys
        kid, jwk_pub, priv_pem = KeyUtil.new_rsa_keypair()

        # Insert tenant
        tenant_read = self.crud.create(
            obj_create=Tenant(
                tenant_name=create_request.tenant_name,
                description=create_request.description,
                status=TenantStatus.INACTIVE,
                keys=[
                    TenantKey(
                        kid=kid,
                        public_jwk=jwk_pub,
                        private_pem=priv_pem,
                        created_at=DatetimeUtil.get_current_timestamp(),
                        active=True,
                    )
                ],
                access_policy=create_request.access_policy,
            )
        )

        return CreateTenantResponse(
            tenant_id=tenant_read.id,
            tenant_name=tenant_read.tenant_name,
            description=tenant_read.description,
            status=tenant_read.status,
            access_policy=tenant_read.access_policy,
        )

    def update_tenant(self, tenant_id: PyObjectId, update_request: UpdateTenantRequest) -> UpdateTenantResponse:
        # Prepare update object
        update_dict = update_request.model_dump(exclude_unset=True)
        tenant_update = TenantUpdate.model_validate(update_dict)

        # Update
        tenant_updated = self.crud.update(obj_update=tenant_update, obj_id=tenant_id)
        return UpdateTenantResponse(
            tenant_id=tenant_updated.id,
            tenant_name=tenant_updated.tenant_name,
            description=tenant_updated.description,
            status=tenant_updated.status,
            access_policy=tenant_updated.access_policy,
        )

    def get_tenant(self, tenant_id: PyObjectId) -> GetTenantResponse:
        tenant = self.crud.get(obj_id=tenant_id)
        return GetTenantResponse(
            tenant_id=tenant.id,
            tenant_name=tenant.tenant_name,
            description=tenant.description,
            status=tenant.status,
            access_policy=tenant.access_policy,
        )

    def get_by_tenant_name(self, tenant_name: str) -> TenantRead | None:
        res = self.crud.search({Tenant.Field.tenant_name: tenant_name})
        return res[0] if res else None

    def delete_tenant(self, tenant_id: PyObjectId) -> None:
        self.crud.delete(obj_id=tenant_id)
        self.client_service.delete_tenant_clients(tenant_id=tenant_id)

    def rotate(self, tenant_id: PyObjectId) -> TenantKey:
        """
        Rotate tenant key

        Args:
            tenant_id (PyObjectId): Tenant id to rotate
            make_active (bool): Make new key active

        Returns:
            TenantKey: New tenant key
        """
        tenant = self.crud.get(obj_id=tenant_id)
        kid, jwk_pub, priv_pem = KeyUtil.new_rsa_keypair()
        new_key = TenantKey(
            kid=kid,
            public_jwk=jwk_pub,
            private_pem=priv_pem,
            created_at=DatetimeUtil.get_current_timestamp(),
        )
        self.crud.update(
            obj_update=TenantUpdate(
                keys=[
                    *tenant.keys,
                    new_key,
                ]
            ),
            obj_id=tenant_id,
        )
        return new_key
