from typing import Annotated, Any

from fastapi import APIRouter, Depends, Security
from pymongo.database import Database

from app.api.custom import RouteErrorHandler
from app.api.dependency import get_current_api_key, get_current_client, get_db
from app.models.auth.api_key import ApiKeyRead
from app.models.auth.client import ClientRead
from app.schemas.auth.api_key import (
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    GetApiKeyResponse,
    UpdateApiKeyRequest,
    UpdateApiKeyResponse,
)
from app.schemas.errors import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    TooManyRequestException,
    UnauthorizedException,
)
from app.services.auth.api_key_service import ApiKeyService

router = APIRouter(
    route_class=RouteErrorHandler,
    tags=["AUTH: API Key"],
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)


@router.post(
    "/create",
    dependencies=[
        Security(get_current_client),
    ],
    responses={
        **NotFoundException.get_response(message="Client not found"),
        **ConflictException.get_response(message="API Key already exists"),
    },
)
def create_new_api_key(
    client: Annotated[ClientRead, Depends(get_current_client)],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    request: CreateApiKeyRequest,
) -> CreateApiKeyResponse:
    """
    This endpoint creates a new API Key of the client.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `None`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `CreateApiKeyRequest`: The request body to create a new API Key.

    ### Response
    - `CreateApiKeyResponse`: The response containing the created API Key.
    """
    return ApiKeyService(db=db).create_api_key(
        client_id=client.id,
        create_request=request,
    )


@router.put("/update")
def update_api_key(
    api_key: Annotated[ApiKeyRead, Security(get_current_api_key)],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    request: UpdateApiKeyRequest,
) -> UpdateApiKeyResponse:
    """
    This endpoint updates API Key.

    ### Authentication
    - **API Key**

    ### Required Scopes
    - `None`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `UpdateApiKeyRequest`: The request body to update an API Key.

    ### Response
    - `UpdateApiKeyResponse`: The response containing the updated API Key.
    """
    return ApiKeyService(db=db).update_api_key(
        api_key_id=api_key.id,
        update_request=request,
    )


@router.get("/get")
def get_api_key(
    api_key: Annotated[ApiKeyRead, Security(get_current_api_key)],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
) -> GetApiKeyResponse:
    """
    This endpoint gets API Key details.

    ### Authentication
    - **API Key**

    ### Required Scopes
    - `None`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `None`

    ### Response
    - `GetApiKeyResponse`: The response containing the API Key.
    """
    return ApiKeyService(db=db).get_api_key(api_key_id=api_key.id)


@router.delete("/revoke")
def revoke_api_key(
    api_key: Annotated[ApiKeyRead, Security(get_current_api_key)],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
) -> None:
    """
    This endpoint revokes API Key.

    ### Authentication
    - **API Key**

    ### Required Scopes
    - `None`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `None`

    ### Response
    - `None`
    """
    ApiKeyService(db=db).delete_api_key(api_key_id=api_key.id)
