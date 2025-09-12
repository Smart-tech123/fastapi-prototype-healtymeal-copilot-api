from typing import Any

from pymongo.database import Database

from app.models.retry_metadata import RetryMetadata, RetryMetadataCRUD


class RetryMetadataService:
    def __init__(self, db: Database[dict[str, Any]]) -> None:
        self.db = db
        self.retry_metadata_crud = RetryMetadataCRUD(db=db)

    def add_retry_metadata(self, retry_metadata: RetryMetadata) -> None:
        self.retry_metadata_crud.create(obj_create=retry_metadata)
