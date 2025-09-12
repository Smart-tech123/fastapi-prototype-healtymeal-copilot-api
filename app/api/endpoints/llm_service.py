from typing import Annotated, Any

from fastapi import APIRouter, Depends, Security
from pymongo.database import Database
from qdrant_client import QdrantClient

from app.api.custom import RouteErrorHandler
from app.api.dependency import get_current_client, get_db, get_qdrant_client, rate_limited
from app.core.config.llm import config as cfg_llm
from app.models.auth.common.access_policy import AccessPolicyScope
from app.schemas.errors import ForbiddenException, TooManyRequestException, UnauthorizedException
from app.schemas.llm import GenerateMealPlanRequest, GenerateMealPlanResponse
from app.services.meal_plan import MealPlanService

router = APIRouter(
    route_class=RouteErrorHandler,
    tags=["LLM Service"],
)


@router.post(
    "/generate-meal-plan",
    dependencies=[
        Security(
            get_current_client,
            scopes=[
                AccessPolicyScope.GENERATE,
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
def generate_meal_plan_json(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    qdrant_client: Annotated[QdrantClient, Depends(get_qdrant_client)],
    request: GenerateMealPlanRequest,
) -> GenerateMealPlanResponse:
    """
    This endpoint generates a meal plan by LLM.

    ### Authentication
    - **OAuth2**
    - **API Key**

    ### Required Scopes
    - `generate`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `GenerateMealPlanRequest`: The request body containing the LLM prompt and prompt version.

    ### Response
    - `GenerateMealPlanResponse`: The response containing the generated meal plan and other metadata.
    """
    return MealPlanService(db=db).generate_meal_plan(
        meal_plan_specs=request.prompt,
        prompt_version=request.prompt_version,
        qdrant_client=qdrant_client,
        add_context=cfg_llm.ADD_CONTEXT,
    )
