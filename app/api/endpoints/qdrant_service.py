from typing import Annotated

from fastapi import APIRouter, Depends, Security
from qdrant_client import QdrantClient

from app.api.custom import RouteErrorHandler
from app.api.dependency import get_current_client, get_qdrant_client, rate_limited
from app.models.auth.common.access_policy import AccessPolicyScope
from app.schemas.errors import ForbiddenException, NotFoundException, TooManyRequestException, UnauthorizedException
from app.schemas.qdrant import (
    QdrantPoint,
    QdrantPointRead,
    QdrantPointUpdate,
    QdrantSearchQuery,
    QdrantSearchResult,
)
from app.services.qdrant_service import QdrantService

router = APIRouter(
    route_class=RouteErrorHandler,
    tags=["Qdrant Service"],
    dependencies=[
        Security(
            get_current_client,
            scopes=[
                AccessPolicyScope.QDRANT,
            ],
        ),
        Depends(rate_limited),
    ],
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)


@router.get("/{collection_name}")
def get_all_points(
    qdrant_client: Annotated[QdrantClient, Depends(get_qdrant_client)],
    collection_name: str,
) -> list[QdrantPointRead]:
    """
    This endpoint returns a list of all points in a collection.

    ### Authentication
    - **SuperAdmin**

    ### Request Query Parameters
    - **collection_name** (`str`): The name of the collection to retrieve points from.

    ### Request Body
    - `None`

    ### Response
    - `list[QdrantPointRead]`: A list of all points in the collection.
    """
    return QdrantService(
        qdrant_client=qdrant_client,
        collection_name=collection_name,
    ).get_all_points()


@router.get(
    "/{collection_name}/{point_id}",
    responses={
        **NotFoundException.get_response(message="Point not found"),
    },
)
def get_point(
    qdrant_client: Annotated[QdrantClient, Depends(get_qdrant_client)],
    collection_name: str,
    point_id: str,
) -> QdrantPointRead:
    """
    This endpoint returns a point by ID.

    ### Authentication
    - **SuperAdmin**

    ### Request Query Parameters
    - **collection_name** (`str`): The name of the collection to retrieve points from.
    - **point_id** (`str`): The ID of the point to retrieve.

    ### Request Body
    - `None`

    ### Response
    - `QdrantPointRead`: The point with the specified ID.
    """
    return QdrantService(
        qdrant_client=qdrant_client,
        collection_name=collection_name,
    ).get_point(point_id=point_id)


@router.post("/{collection_name}")
def create_point(
    qdrant_client: Annotated[QdrantClient, Depends(get_qdrant_client)],
    collection_name: str,
    point: QdrantPoint,
) -> QdrantPointRead:
    """
    This endpoint creates a new point in a collection.

    ### Authentication
    - **SuperAdmin**

    ### Request Query Parameters
    - **collection_name** (`str`): The name of the collection to create the point in.
    - **point** (`QdrantPoint`): The point to create.

    ### Request Body
    - `None`

    ### Response
    - `QdrantPointRead`: The created point.
    """
    return QdrantService(
        qdrant_client=qdrant_client,
        collection_name=collection_name,
    ).create_point(point_data=point)


@router.put("/{collection_name}/{point_id}")
def update_point(
    qdrant_client: Annotated[QdrantClient, Depends(get_qdrant_client)],
    collection_name: str,
    point: QdrantPointUpdate,
    point_id: str,
) -> QdrantPointRead:
    """
    This endpoint updates a point in a collection.

    ### Authentication
    - **SuperAdmin**

    ### Request Query Parameters
    - **collection_name** (`str`): The name of the collection to update the point in.
    - **point_id** (`str`): The ID of the point to update.

    ### Request Body
    - `QdrantPointUpdate`: The point to update.

    ### Response
    - `QdrantPointRead`: The updated point.
    """
    return QdrantService(
        qdrant_client=qdrant_client,
        collection_name=collection_name,
    ).update_point(
        point_id=point_id,
        point_data=point,
    )


@router.delete("/{collection_name}/{point_id}")
def delete_point(
    qdrant_client: Annotated[QdrantClient, Depends(get_qdrant_client)],
    collection_name: str,
    point_id: str,
) -> None:
    """
    This endpoint deletes a point in a collection.

    ### Authentication
    - SuperAdmin

    ### Request Query Parameters
    - **collection_name** (`str`): The name of the collection to delete the point from.
    - **point_id** (`str`): The ID of the point to delete.

    ### Request Body
    - `None`

    ### Response
    - `None`
    """
    QdrantService(
        qdrant_client=qdrant_client,
        collection_name=collection_name,
    ).delete_point(point_id=point_id)


@router.post("/{collection_name}/search")
def search_points(
    qdrant_client: Annotated[QdrantClient, Depends(get_qdrant_client)],
    collection_name: str,
    search_query: QdrantSearchQuery,
) -> list[QdrantSearchResult]:
    """
    This endpoint searches for similar points in a collection.

    ### Authentication
    - **SuperAdmin**

    ### Request Query Parameters
    - **collection_name** (`str`): The name of the collection to search in.

    ### Request Body
    - `QdrantSearchQuery`: The search query.

    ### Response
    - `list[QdrantSearchResult]`: A list of similar points.
    """
    return QdrantService(
        qdrant_client=qdrant_client,
        collection_name=collection_name,
    ).search_points(search_query=search_query)
