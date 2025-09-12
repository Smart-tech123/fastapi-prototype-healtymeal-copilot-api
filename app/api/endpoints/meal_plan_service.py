from typing import Annotated, Any

from fastapi import APIRouter, Depends, Security
from pymongo.database import Database

from app.api.custom import RouteErrorHandler
from app.api.dependency import get_current_client, get_db
from app.models.auth.client import ClientRead
from app.models.auth.common.access_policy import AccessPolicyScope
from app.models.common.object_id import PyObjectId
from app.models.meal_plan import MealPlanRead
from app.schemas.errors import ForbiddenException, TooManyRequestException, UnauthorizedException
from app.schemas.meal_plan import CreateMealPlanRequest, UpdateMealPlanRequest
from app.services.meal_plan import MealPlanService

router = APIRouter(
    route_class=RouteErrorHandler,
    tags=["MealPlan Service"],
    dependencies=[
        Security(
            get_current_client,
            scopes=[
                AccessPolicyScope.FOOD_PLAN,
            ],
        ),
    ],
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)


@router.get("/")
def get_all_meal_plans(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
) -> list[MealPlanRead]:
    """
    This endpoint returns all meal plans.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `meal_plan`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `None`

    ### Response
    - `list[MealPlanRead]`: A list of all meal plans.
    """
    return MealPlanService(db=db).get_all_meal_plans()


@router.get("/{meal_plan_id}")
def get_meal_plan(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    meal_plan_id: PyObjectId,
) -> MealPlanRead:
    """
    This endpoint returns a meal_plan.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `meal_plan`

    ### Request Query Parameters
    - **meal_plan_id** (`str`): The ID of the meal_plan to get.

    ### Request Body
    - `None`

    ### Response
    - `MealPlanRead`: The meal_plan.
    """
    return MealPlanService(db=db).get_meal_plan(meal_plan_id=meal_plan_id)


@router.post("/")
def create_meal_plan(
    oauth_client: Annotated[ClientRead, Depends(get_current_client)],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    request: CreateMealPlanRequest,
) -> MealPlanRead:
    """
    This endpoint creates a new meal_plan.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `meal_plan`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `MealPlanCreateRequest`: The new meal_plan data to create.

    ### Response
    - `MealPlanRead`: The newly created meal_plan.
    """
    return MealPlanService(db=db).create_meal_plan(
        create_request=request,
        client_name=oauth_client.client_name,
    )


@router.put("/{meal_plan_id}")
def update_meal_plan(
    oauth_client: Annotated[ClientRead, Depends(get_current_client)],
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    request: UpdateMealPlanRequest,
    meal_plan_id: PyObjectId,
) -> MealPlanRead:
    """
    This endpoint updates a meal_plan.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `meal_plan`

    ### Request Query Parameters
    - **meal_plan_id** (`str`): The ID of the meal_plan to update.

    ### Request Body
    - `MealPlanUpdateRequest`: The updated meal_plan data.

    ### Response
    - `MealPlanRead`: The updated meal_plan.
    """
    return MealPlanService(db=db).update_meal_plan(
        update_request=request,
        meal_plan_id=meal_plan_id,
        client_name=oauth_client.client_name,
    )


@router.delete("/{meal_plan_id}")
def delete_meal_plan(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    meal_plan_id: PyObjectId,
) -> None:
    """
    This endpoint deletes a meal_plan.

    ### Authentication
    - **API Key**
    - **OAuth2**

    ### Required Scopes
    - `meal_plan`

    ### Request Query Parameters
    - **meal_plan_id** (`str`): The ID of the meal_plan to delete.

    ### Request Body
    - `None`

    ### Response
    - `None`
    """
    MealPlanService(db=db).delete_meal_plan(meal_plan_id=meal_plan_id)
