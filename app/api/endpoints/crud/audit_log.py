from app.api.generic_router import GenericRouter
from app.models.audit_log import (
    AuditLog,
    AuditLogCRUD,
    AuditLogRead,
    AuditLogUpdate,
)

router = GenericRouter[
    AuditLogCRUD,
    AuditLog,
    AuditLogRead,
    AuditLogUpdate,
].create_crud_router(
    name="AuditLog",
    crud=AuditLogCRUD,
    db_schema=AuditLog,
    read_schema=AuditLogRead,
    update_schema=AuditLogUpdate,
)
