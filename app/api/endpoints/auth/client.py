from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Security
from pymongo.database import Database

from app.api.custom import RouteErrorHandler
from app.api.dependency import get_current_client, get_db
from app.models.auth.client import ClientRead
from app.schemas.auth.client import (
    CreateClientRequest,
    CreateClientResponse,
    GetClientResponse,
    UpdateClientRequest,
    UpdateClientResponse,
)
from app.schemas.auth.token import Token
from app.schemas.errors import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    TooManyRequestException,
    UnauthorizedException,
)
from app.services.auth.client_service import ClientService

router = APIRouter(route_class=RouteErrorHandler, tags=["AUTH: Client"])


@router.post(
    "/register",
    responses={
        **NotFoundException.get_response(message="Tenant not found"),
        **ConflictException.get_response(message="Client already exists"),
    },
)
def register_new_client(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    request: CreateClientRequest,
) -> CreateClientResponse:
    """
    This endpoint registers a new client.

    ### Authentication
    - `None`

    ### Required Scopes
    - `None`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `CreateClientRequest`: The request body to create a new client.

    ### Response
    - `CreateClientResponse`: The response containing the created client.
    """
    return ClientService(db=db).create_client(create_request=request)


@router.post(
    "/login",
    responses={
        **UnauthorizedException.get_response(),
    },
)
def login_for_access_token(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    client_id: Annotated[str, Form()],
    client_secret: Annotated[str, Form()],
) -> Token:
    """
    This endpoint logs in for an access token.

    ### Authentication
    - `None`

    ### Required Scopes
    - `None`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - **client_id** (`str`): The client ID.
    - **client_secret** (`str`): The client secret.

    ### Response
    - `Token`: The response containing the access token.
    """
    return ClientService(db=db).login_for_access_token(
        client_id=client_id,
        client_secret=client_secret,
    )


@router.put(
    "/update",
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)
def update_client(
    client: Annotated[ClientRead, Security(get_current_client)],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    request: UpdateClientRequest,
) -> UpdateClientResponse:
    """
    This endpoint updates client.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `None`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `UpdateClientRequest`: The request body to update a client.

    ### Response
    - `UpdateClientResponse`: The response containing the updated client.
    """
    return ClientService(db=db).update_client(
        client_id=client.id,
        update_request=request,
    )


@router.get(
    "/get",
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)
def get_client(
    client: Annotated[ClientRead, Security(get_current_client)],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
) -> GetClientResponse:
    """
    This endpoint gets client details.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `None`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `None`

    ### Response
    - `GetClientResponse`: The response containing the client.
    """
    return ClientService(db=db).get_client(client_id=client.id)


@router.delete(
    "/revoke",
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)
def revoke_client(
    client: Annotated[ClientRead, Security(get_current_client)],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
) -> None:
    """
    This endpoint revokes client.

    ### Authentication
    - **OAuth2**
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
    ClientService(db=db).delete_client(client_id=client.id)


@router.get(
    "/rotate",
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)
def rotate_client_secret(
    client: Annotated[ClientRead, Security(get_current_client)],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
) -> str:
    """
    This endpoint rotates client secret.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `None`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `None`

    ### Response
    - `str`: The response containing the rotated client secret.
    """
    return ClientService(db=db).rotate(client_id=client.id)
