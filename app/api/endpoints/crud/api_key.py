from app.api.generic_router import GenericRouter
from app.models.auth.api_key import (
    ApiKey,
    ApiKeyCRUD,
    ApiKeyRead,
    ApiKeyUpdate,
)

router = GenericRouter[
    ApiKeyCRUD,
    ApiKey,
    ApiKeyRead,
    ApiKeyUpdate,
].create_crud_router(
    name="ApiKey",
    crud=ApiKeyCRUD,
    db_schema=ApiKey,
    read_schema=ApiKeyRead,
    update_schema=ApiKeyUpdate,
)
