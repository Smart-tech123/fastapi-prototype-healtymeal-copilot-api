from datetime import timedelta
from typing import Any

from loguru import logger
from pymongo.database import Database

from app.core.config.auth import config as cfg_auth
from app.models.auth.client import Client, ClientCRUD, ClientRead, ClientUpdate
from app.models.auth.tenant import TenantCRUD
from app.models.common.object_id import PyObjectId
from app.schemas.auth.client import (
    CreateClientRequest,
    CreateClientResponse,
    GetClientResponse,
    UpdateClientRequest,
    UpdateClientResponse,
)
from app.schemas.auth.token import Token, TokenType
from app.schemas.errors import (
    ConflictException,
    ErrorCode401,
    ErrorCode404,
    ErrorCode409,
    NotFoundException,
    UnauthorizedException,
)
from app.services.auth.api_key_service import ApiKeyService
from app.services.auth.auth_service import AuthService


class ClientService:
    def __init__(self, db: Database[dict[str, Any]]) -> None:
        self.db = db
        self.crud = ClientCRUD(db=db)
        self.tenant_crud = TenantCRUD(db=db)
        self.api_key_service = ApiKeyService(db=db)

    def create_client(self, create_request: CreateClientRequest) -> CreateClientResponse:
        # Check if tenant exists
        tenants = self.tenant_crud.search({"_id": create_request.tenant_id})
        if not tenants or len(tenants) > 1:
            raise NotFoundException(
                error_code=ErrorCode404.NOT_FOUND,
                message="Tenant not found",
            )
        tenant = tenants[0]

        # Restrict creation of clients for SUPER tenant
        if tenant.tenant_name == cfg_auth.SUPER_TENANT_NAME:
            raise NotFoundException(
                error_code=ErrorCode404.NOT_FOUND,
                message="Tenant not found",
            )

        # Check if client already exists
        if self.crud.search(
            {
                Client.Field.tenant_id: create_request.tenant_id,
                Client.Field.client_name: create_request.client_name,
            }
        ):
            raise ConflictException(
                error_code=ErrorCode409.CONFLICT,
                message="Client already exists",
            )

        # Generate client id and secret
        client_secret_plain = AuthService.generate_client_secret()
        client_secret_hash = AuthService.hash_password(client_secret_plain)

        # Insert client
        client_created = self.crud.create(
            Client(
                tenant_id=create_request.tenant_id,
                client_secret_hash=client_secret_hash,
                client_name=create_request.client_name,
                description=create_request.description,
                access_policy=create_request.access_policy,
            ),
        )

        return CreateClientResponse(
            tenant_id=create_request.tenant_id,
            client_id=client_created.id,
            client_secret_plain=client_secret_plain,
            client_name=create_request.client_name,
            description=create_request.description,
            access_policy=create_request.access_policy,
        )

    def login_for_access_token(
        self,
        client_id: str,
        client_secret: str,
    ) -> Token:
        credentials_exception = UnauthorizedException(
            error_code=ErrorCode401.INVALID_CREDENTIALS,
            message="Invalid credentials",
        )

        try:
            client = self.get_by_client_id(client_id=client_id)
        except Exception:
            logger.error("Client not found")
            raise credentials_exception  # noqa: B904

        if not AuthService.verify_password(client_secret, client.client_secret_hash):
            logger.error("Invalid credentials")
            raise credentials_exception

        tenant = self.tenant_crud.get(obj_id=client.tenant_id)
        if not tenant:
            logger.error("Tenant not found")
            raise credentials_exception

        # Create access token
        expires_delta = (
            timedelta(minutes=cfg_auth.ACCESS_TOKEN_EXPIRE_MINUTES) if cfg_auth.ACCESS_TOKEN_EXPIRE_MINUTES else None
        )

        # Get allowed scopes for client
        scopes = tenant.access_policy.scopes
        if client.access_policy:
            scopes = list(set(scopes) & set(client.access_policy.scopes))

        # Generate access token
        if not tenant.keys:
            logger.error("Tenant has no keys")
            raise credentials_exception

        access_token = AuthService.create_jwt_access_token_rs256(
            data={
                "sub": str(client_id),
                "scopes": [str(scope) for scope in scopes],
            },
            tenant_id=str(tenant.id),
            tenant_key=tenant.keys[-1],
            expires_delta=expires_delta,
        )

        return Token(
            access_token=access_token,
            token_type=TokenType.BEARER,
        )

    def update_client(self, client_id: PyObjectId, update_request: UpdateClientRequest) -> UpdateClientResponse:
        # Prepare update object
        update_dict = update_request.model_dump(exclude_unset=True)
        client__update = ClientUpdate.model_validate(update_dict)

        # Update
        client_updated = self.crud.update(obj_update=client__update, obj_id=client_id)
        return UpdateClientResponse(
            tenant_id=client_updated.tenant_id,
            client_id=client_updated.id,
            client_name=client_updated.client_name,
            description=client_updated.description,
            access_policy=client_updated.access_policy,
        )

    def get_client(self, client_id: PyObjectId) -> GetClientResponse:
        client = self.get_by_client_id(client_id=client_id)
        return GetClientResponse(
            tenant_id=client.tenant_id,
            client_id=client.id,
            client_name=client.client_name,
            description=client.description,
            access_policy=client.access_policy,
        )

    def get_by_client_id(self, client_id: PyObjectId | str) -> ClientRead:
        return self.crud.get(obj_id=client_id)

    def get_by_client_name(self, client_name: str) -> ClientRead | None:
        res = self.crud.search({Client.Field.client_name: client_name})
        return res[0] if res else None

    def delete_client(self, client_id: PyObjectId) -> None:
        self.crud.delete(obj_id=client_id)
        self.api_key_service.delete_client_api_keys(client_id=client_id)

    def delete_tenant_clients(self, tenant_id: PyObjectId) -> None:
        tenant_clients = self.crud.search({Client.Field.tenant_id: tenant_id})
        for client in tenant_clients:
            self.delete_client(client_id=client.id)

    def rotate(self, client_id: PyObjectId | str) -> str:
        """
        Rotate client secret.

        Args:
            client_id (str): Client id to rotate

        Returns:
            str: New plain client secret
        """
        client_secret_plain = AuthService.generate_client_secret()
        client_secret_hash = AuthService.hash_password(client_secret_plain)
        self.crud.update(
            obj_update=ClientUpdate(
                client_secret_hash=client_secret_hash,
            ),
            obj_id=client_id,
        )
        return client_secret_plain
