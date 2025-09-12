from typing import Annotated, Any

from fastapi import APIRouter, Depends, Security
from pymongo.database import Database

from app.api.custom import RouteErrorHandler
from app.api.dependency import get_current_client, get_db
from app.models.auth.client import ClientRead
from app.models.auth.common.access_policy import AccessPolicyScope
from app.models.common.object_id import PyObjectId
from app.models.meal_plan import MealPlanRead
from app.models.version_log import VersionLog, VersionLogCRUD, VersionLogRead
from app.schemas.errors import ForbiddenException, TooManyRequestException, UnauthorizedException
from app.schemas.version_log import VersionLogRollbackRequest
from app.services.version_log_service import VersionLogService

router = APIRouter(
    route_class=RouteErrorHandler,
    tags=["Version Management Service"],
    dependencies=[
        Security(
            get_current_client,
            scopes=[
                AccessPolicyScope.VERSION_SERVICE,
            ],
        ),
    ],
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)


@router.get("/meal-plan/{meal_plan_id}")
def get_logs_for_meal_plan(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    meal_plan_id: str,
) -> list[VersionLogRead]:
    """
    This endpoint returns a list of logs for a meal_plan.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `version_service`

    ### Request Query Parameters
    - **meal_plan_id** (`str`): The ID of the meal_plan to retrieve logs for.

    ### Request Body
    - `None`

    ### Response
    - `list[VersionLogRead]`: A list of logs for the meal_plan.
    """
    cursor = VersionLogCRUD(db=db).coll.find({VersionLog.Field.meal_plan_id: PyObjectId(meal_plan_id)})
    return [VersionLogRead.model_validate(doc) for doc in cursor]


@router.get("/meal_plan/{meal_plan_id}/{log_id}")
def get_meal_plan_for_log(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    meal_plan_id: str,
    log_id: str,
) -> MealPlanRead:
    """
    This endpoint returns a meal_plan for a log.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `version_service`

    ### Request Query Parameters
    - **meal_plan_id** (`str`): The ID of the meal_plan to retrieve.
    - **log_id** (`str`): The ID of the log to retrieve.

    ### Request Body
    - `None`

    ### Response
    - `MealPlanRead`: The meal_plan for the log.
    """
    return VersionLogService(db=db).get_by_log_id(
        meal_plan_id=PyObjectId(meal_plan_id),
        log_id=PyObjectId(log_id),
    )


@router.get("/log/{log_id}")
def get_log(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    log_id: str,
) -> VersionLogRead:
    """
    This endpoint returns a log.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `version_service`

    ### Request Query Parameters
    - **log_id** (`str`): The ID of the log to retrieve.

    ### Request Body
    - `None`

    ### Response
    - `VersionLogRead`: The requested log.
    """
    return VersionLogCRUD(db=db).get(obj_id=PyObjectId(log_id))


@router.post("/rollback/{meal_plan_id}/{log_id}")
def rollback_meal_plan_to(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    client: Annotated[ClientRead, Depends(get_current_client)],
    meal_plan_id: str,
    log_id: str,
    request: VersionLogRollbackRequest,
) -> MealPlanRead:
    """
    This endpoint rolls back a meal_plan to a specific log.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `version_service`

    ### Request Query Parameters
    - **meal_plan_id** (`str`): The ID of the meal_plan to rollback.
    - **log_id** (`str`): The ID of the log to rollback to.

    ### Request Body
    - `VersionLogRollbackRequest`: The rollback request.

    ### Response
    - `MealPlanRead`: The rolled back meal_plan.
    """
    return VersionLogService(db=db).rollback(
        meal_plan_id=PyObjectId(meal_plan_id),
        log_id=PyObjectId(log_id),
        client_name=client.client_name,
        msg=request.msg,
    )
