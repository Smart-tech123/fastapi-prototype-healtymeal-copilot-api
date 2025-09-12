from typing import Annotated, Any

from fastapi import APIRouter, Depends, Security
from pymongo.database import Database

from app.api.custom import RouteErrorHandler
from app.api.dependency import get_current_tenant, get_db
from app.models.auth.common.access_policy import AccessPolicyScope
from app.models.auth.tenant import TenantRead
from app.schemas.auth.tenant import (
    CreateTenantRequest,
    CreateTenantResponse,
    GetTenantResponse,
    UpdateTenantRequest,
    UpdateTenantResponse,
)
from app.schemas.errors import (
    ConflictException,
    ForbiddenException,
    TooManyRequestException,
    UnauthorizedException,
)
from app.services.auth.tenant_service import TenantService

router = APIRouter(route_class=RouteErrorHandler, tags=["AUTH: Tenant"])


@router.post(
    "/register",
    responses={
        **ConflictException.get_response(message="Tenant already exists"),
    },
)
def register_new_tenant(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    request: CreateTenantRequest,
) -> CreateTenantResponse:
    """
    This endpoint registers a new tenant.

    ### Authentication
    - `None`

    ### Required Scopes
    - `None`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `CreateTenantRequest`: The request body to create a new tenant.

    ### Response
    - `CreateTenantResponse`: The response containing the created tenant.
    """
    return TenantService(db=db).create_tenant(create_request=request)


@router.put(
    "/update",
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)
def update_tenant(
    tenant: Annotated[
        TenantRead,
        Security(
            get_current_tenant,
            scopes=[
                AccessPolicyScope.TENANT,
            ],
        ),
    ],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    request: UpdateTenantRequest,
) -> UpdateTenantResponse:
    """
    This endpoint updates tenant.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `tenant`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `UpdateTenantRequest`: The request body to update a tenant.

    ### Response
    - `UpdateTenantResponse`: The response containing the updated tenant.
    """
    return TenantService(db=db).update_tenant(
        tenant_id=tenant.id,
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
def get_tenant(
    tenant: Annotated[
        TenantRead,
        Security(
            get_current_tenant,
            scopes=[
                AccessPolicyScope.TENANT,
            ],
        ),
    ],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
) -> GetTenantResponse:
    """
    This endpoint gets tenant.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `tenant`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `None`

    ### Response
    - `GetTenantResponse`: The response containing the tenant.
    """
    return TenantService(db=db).get_tenant(tenant_id=tenant.id)


@router.delete(
    "/revoke",
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)
def revoke_tenant(
    tenant: Annotated[
        TenantRead,
        Security(
            get_current_tenant,
            scopes=[
                AccessPolicyScope.TENANT,
            ],
        ),
    ],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
) -> None:
    """
    This endpoint revokes tenant.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `tenant`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `None`

    ### Response
    - `None`
    """
    TenantService(db=db).delete_tenant(tenant_id=tenant.id)


@router.get(
    "/rotate",
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)
def rotate_tenant_key(
    tenant: Annotated[
        TenantRead,
        Security(
            get_current_tenant,
            scopes=[
                AccessPolicyScope.TENANT,
            ],
        ),
    ],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
) -> None:
    """
    This endpoint rotates tenant key without down-time.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `tenant`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `None`

    ### Response
    - `None`
    """
    TenantService(db=db).rotate(tenant_id=tenant.id)
