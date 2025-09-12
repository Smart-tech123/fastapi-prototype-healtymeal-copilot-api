from typing import Any

from pymongo.database import Database

from app.core.config.auth import config as cfg_auth
from app.db.mongo import pymongo_db
from app.models.auth.api_key import ApiKeyCRUD
from app.models.auth.client import Client, ClientCRUD, ClientRead
from app.models.auth.common.access_policy import AccessPolicy, AccessPolicyScope
from app.models.auth.tenant import TenantCRUD, TenantRead, TenantStatus, TenantUpdate
from app.models.meal_plan import MealPlanCRUD
from app.models.retry_metadata import RetryMetadataCRUD
from app.models.version_log import VersionLogCRUD
from app.schemas.auth.tenant import CreateTenantRequest
from app.services.auth.client_service import ClientService
from app.services.auth.tenant_service import TenantService


def init_indexes(db: Database[dict[str, Any]]) -> None:
    TenantCRUD(db=db).create_indexes()
    ClientCRUD(db=db).create_indexes()
    ApiKeyCRUD(db=db).create_indexes()
    VersionLogCRUD(db=db).create_indexes()
    RetryMetadataCRUD(db=db).create_indexes()
    MealPlanCRUD(db=db).create_indexes()


def init_super_admin(db: Database[dict[str, Any]]) -> tuple[TenantRead, ClientRead]:
    """
    Create a SUPER Tenant and corresponding SUPER Client to streamline the super administrator workflow
    """
    # Create SUPER Tenant
    tenant_service = TenantService(db=db)
    if not tenant_service.get_by_tenant_name(tenant_name=cfg_auth.SUPER_TENANT_NAME):
        tenant_service.create_tenant(
            create_request=CreateTenantRequest(
                tenant_name=cfg_auth.SUPER_TENANT_NAME,
                description="Built-in super administrator tenant",
                access_policy=AccessPolicy(
                    allowed_ips=["*.*.*.*"],
                    scopes=[AccessPolicyScope.ALL],
                    rate_limit_per_min=0,
                ),
            )
        )
    super_tenant = tenant_service.get_by_tenant_name(tenant_name=cfg_auth.SUPER_TENANT_NAME)
    if not super_tenant:
        msg = "Failed to create SUPER Tenant"
        raise RuntimeError(msg)

    # Activate SUPER Tenant
    TenantCRUD(db=db).update(
        obj_id=super_tenant.id,
        obj_update=TenantUpdate(status=TenantStatus.ACTIVE),
    )

    # Create SUPER Client
    client_service = ClientService(db=db)
    if not client_service.get_by_client_name(client_name=cfg_auth.SUPER_CLIENT_NAME):
        ClientCRUD(db=db).create(
            obj_create=Client(
                tenant_id=super_tenant.id,
                client_name=cfg_auth.SUPER_CLIENT_NAME,
                client_secret_hash="",  # Ensure OAuth2 authentication is disabled for SUPER client
                description="Built-in super administrator client",
                access_policy=None,
            )
        )
    super_client = client_service.get_by_client_name(client_name=cfg_auth.SUPER_CLIENT_NAME)
    if not super_client:
        msg = "Failed to create SUPER Client"
        raise RuntimeError(msg)

    return super_tenant, super_client


def init_data() -> None:
    init_indexes(db=pymongo_db)
    init_super_admin(db=pymongo_db)
