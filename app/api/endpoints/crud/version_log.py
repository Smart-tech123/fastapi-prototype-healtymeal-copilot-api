from app.api.generic_router import GenericRouter
from app.models.version_log import (
    VersionLog,
    VersionLogCRUD,
    VersionLogRead,
    VersionLogUpdate,
)

router = GenericRouter[
    VersionLogCRUD,
    VersionLog,
    VersionLogRead,
    VersionLogUpdate,
].create_crud_router(
    name="VersionLog",
    crud=VersionLogCRUD,
    db_schema=VersionLog,
    read_schema=VersionLogRead,
    update_schema=VersionLogUpdate,
)
