from app.api.generic_router import GenericRouter
from app.models.retry_metadata import (
    RetryMetadata,
    RetryMetadataCRUD,
    RetryMetadataFilter,
    RetryMetadataRead,
    RetryMetadataUpdate,
)

router = GenericRouter[
    RetryMetadataCRUD,
    RetryMetadata,
    RetryMetadataRead,
    RetryMetadataUpdate,
].create_crud_router(
    name="RetryMetadata",
    crud=RetryMetadataCRUD,
    db_schema=RetryMetadata,
    read_schema=RetryMetadataRead,
    update_schema=RetryMetadataUpdate,
    filter_schema=RetryMetadataFilter,
)
