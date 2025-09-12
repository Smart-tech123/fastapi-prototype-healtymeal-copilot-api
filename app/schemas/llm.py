from typing import Annotated, Any, TypeAlias

from pydantic import BaseModel, Field

from app.models.common.version import Version
from app.models.meal_plan import MealPlanBase
from app.schemas.validation import ValidationResult


class GenerateMealPlanRequest(BaseModel):
    prompt: Annotated[
        str,
        Field(
            description="LLM prompt for meal plan generation",
            examples=[
                "Generate a healthy meal plan for a vegan person",
            ],
        ),
    ]
    prompt_version: Annotated[
        Version | None,
        Field(
            None,
            description="Prompt version to be used for LLM. If not provided, the default version will be used",
        ),
    ]


class GenerateMealPlanResult(BaseModel):
    success: Annotated[
        bool,
        Field(description="Whether the meal plan generation was successful"),
    ]
    meal_plan: Annotated[
        MealPlanBase | None,
        Field(description="Generated meal plan"),
    ] = None
    raw_output: Annotated[
        dict[str, Any] | None,
        Field(description="Raw output from LLM"),
    ] = None
    errors: Annotated[
        list[ValidationResult],
        Field(description="List of validation errors"),
    ] = []


GenerateMealPlanResponse: TypeAlias = GenerateMealPlanResult
