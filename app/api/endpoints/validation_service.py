from typing import Any

from fastapi import APIRouter, Security

from app.api.custom import RouteErrorHandler
from app.api.dependency import get_current_client
from app.models.auth.common.access_policy import AccessPolicyScope
from app.models.meal_plan import MealPlanBase
from app.schemas.errors import ForbiddenException, TooManyRequestException, UnauthorizedException
from app.schemas.validation import ValidationResult
from app.services.validation_service import ValidationService

router = APIRouter(
    route_class=RouteErrorHandler,
    tags=["MealPlan Validation Service"],
    dependencies=[
        Security(
            get_current_client,
            scopes=[
                AccessPolicyScope.VALIDATE,
            ],
        ),
    ],
    responses={
        **UnauthorizedException.get_response(),
        **ForbiddenException.get_response(),
        **TooManyRequestException.get_response(),
    },
)


@router.post("/validate-meal-plan")
def validate_meal_plan_json(
    obj_dict: dict[str, Any],
) -> ValidationResult:
    """
    This endpoint validates a meal plan json.

    ### Authentication
    - **API Key**
    - **OAuth2**

    ### OAuth2 Scopes
    - `validate`

    ### Request Query Parameters
    - `None`

    ### Request Body
    - `dict[str, Any]`: The meal plan json to validate.

    ### Response
    - `ValidationResult`: The validation result.
    """
    return ValidationService.validate_model_json(MealPlanBase, obj_dict)
