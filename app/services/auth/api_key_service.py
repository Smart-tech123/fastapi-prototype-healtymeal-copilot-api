from typing import Any

from pymongo.database import Database

from app.core.config.auth import config as cfg_auth
from app.models.auth.api_key import ApiKey, ApiKeyCRUD, ApiKeyUpdate
from app.models.auth.client import ClientCRUD
from app.models.common.object_id import PyObjectId
from app.schemas.auth.api_key import (
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    GetApiKeyResponse,
    UpdateApiKeyRequest,
    UpdateApiKeyResponse,
)
from app.schemas.errors import ConflictException, ErrorCode404, ErrorCode409, NotFoundException
from app.services.auth.auth_service import AuthService


class ApiKeyService:
    def __init__(self, db: Database[dict[str, Any]]) -> None:
        self.db = db
        self.crud = ApiKeyCRUD(db=db)
        self.client_crud = ClientCRUD(db=db)

    def create_api_key(self, client_id: PyObjectId, create_request: CreateApiKeyRequest) -> CreateApiKeyResponse:
        # Check if client exists
        clients = self.client_crud.search({"_id": client_id})
        if not clients or len(clients) > 1:
            raise NotFoundException(
                error_code=ErrorCode404.NOT_FOUND,
                message="Client not found",
            )

        # Restrict creation of api keys for SUPER client
        if clients[0].client_name == cfg_auth.SUPER_CLIENT_NAME:
            raise NotFoundException(
                error_code=ErrorCode404.NOT_FOUND,
                message="Client not found",
            )

        # Check if api key already exists
        if self.crud.search(
            {
                ApiKey.Field.client_id: client_id,
                ApiKey.Field.key_name: create_request.key_name,
            }
        ):
            raise ConflictException(
                error_code=ErrorCode409.CONFLICT,
                message="API key already exists",
            )

        # Create api key
        key_secret_plain = AuthService.generate_api_key()
        key_hash = AuthService.hash_api_key(key_secret_plain)
        api_key_created = self.crud.create(
            obj_create=ApiKey(
                client_id=client_id,
                key_name=create_request.key_name,
                key_secret_hash=key_hash,
                key_secret_front=key_secret_plain[:8],
                description=create_request.description,
                access_policy=create_request.access_policy,
            )
        )

        return CreateApiKeyResponse(
            client_id=api_key_created.client_id,
            key_id=api_key_created.id,
            key_name=api_key_created.key_name,
            key_plain=f"{api_key_created.id}.{key_secret_plain}",
            description=api_key_created.description,
            access_policy=api_key_created.access_policy,
        )

    def update_api_key(self, api_key_id: PyObjectId, update_request: UpdateApiKeyRequest) -> UpdateApiKeyResponse:
        # Prepare update object
        update_dict = update_request.model_dump(exclude_unset=True)
        api_key_update = ApiKeyUpdate.model_validate(update_dict)

        # Update
        api_key_updated = self.crud.update(obj_update=api_key_update, obj_id=api_key_id)
        return UpdateApiKeyResponse(
            client_id=api_key_updated.client_id,
            key_id=api_key_updated.id,
            key_name=api_key_updated.key_name,
            key_secret_front=api_key_updated.key_secret_front,
            description=api_key_updated.description,
            access_policy=api_key_updated.access_policy,
        )

    def get_api_key(self, api_key_id: PyObjectId) -> GetApiKeyResponse:
        api_key = self.crud.get(obj_id=api_key_id)
        return GetApiKeyResponse(
            client_id=api_key.client_id,
            key_id=api_key.id,
            key_name=api_key.key_name,
            key_secret_front=api_key.key_secret_front,
            description=api_key.description,
            access_policy=api_key.access_policy,
        )

    def get_by_key_name(self, key_name: str) -> ApiKey | None:
        res = self.crud.search({ApiKey.Field.key_name: key_name})
        return res[0] if res else None

    def delete_api_key(self, api_key_id: PyObjectId) -> None:
        self.crud.delete(obj_id=api_key_id)

    def delete_client_api_keys(self, client_id: PyObjectId) -> None:
        self.crud.delete_many({ApiKey.Field.client_id: client_id})
