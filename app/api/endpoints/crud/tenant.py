from app.api.generic_router import GenericRouter
from app.models.auth.tenant import (
    Tenant,
    TenantCRUD,
    TenantRead,
    TenantUpdate,
)

router = GenericRouter[
    TenantCRUD,
    Tenant,
    TenantRead,
    TenantUpdate,
].create_crud_router(
    name="Tenant",
    crud=TenantCRUD,
    db_schema=Tenant,
    read_schema=TenantRead,
    update_schema=TenantUpdate,
)
