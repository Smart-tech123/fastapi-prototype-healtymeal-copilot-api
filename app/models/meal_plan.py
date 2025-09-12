from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator
from pymongo.database import Database

from app.models.common.base_models import TimeStampedModel
from app.models.common.generic_crud import TimeStampedCRUDBase
from app.models.common.object_id import PyObjectId
from app.models.common.version import Version

COLLECTION_NAME = "meal_plan"


class DayOfWeek(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class Meal(BaseModel):
    name: Annotated[
        str,
        Field(description="Name of the meal"),
    ]
    calories: Annotated[
        float,
        Field(ge=0, description="Calories per serving"),
    ]
    ingredients: Annotated[
        list[str],
        Field(
            description="List of ingredients",
            examples=[
                ["eggs", "milk"],
                ["chicken", "broccoli"],
            ],
        ),
    ]


class MealPlanBase(BaseModel):
    plan_name: Annotated[
        str,
        Field(min_length=3, description="Name of the meal plan"),
    ]
    description: Annotated[
        str,
        Field(description="Description of the meal plan"),
    ]
    day: Annotated[
        DayOfWeek,
        Field(description="Day of the week"),
    ]
    breakfast: Annotated[
        Meal | None,
        Field(description="Breakfast planned for the day"),
    ]
    lunch: Annotated[
        Meal | None,
        Field(description="Lunch planned for the day"),
    ]
    dinner: Annotated[
        Meal | None,
        Field(description="Dinner planned for the day"),
    ]

    class Field(StrEnum):
        plan_name = "plan_name"
        description = "description"
        day = "day"
        breakfast = "breakfast"
        lunch = "lunch"
        dinner = "dinner"

    @model_validator(mode="after")
    def validate_dbname(self) -> "MealPlanBase":
        if self.total_calories() <= 0:
            msg = "Total calories must be greater than 0"
            raise ValueError(msg)

        return self

    def total_calories(self) -> float:
        """
        Calculate the total calories for the day
        """
        ret = 0.0
        if self.breakfast is not None:
            ret += self.breakfast.calories
        if self.lunch is not None:
            ret += self.lunch.calories
        if self.dinner is not None:
            ret += self.dinner.calories
        return ret


class MealPlan(MealPlanBase, TimeStampedModel):
    """
    Versioned meal plan schema
    """

    version: Annotated[Version, Field(description="Version of the object")]

    class Field(StrEnum):
        version = "version"


class MealPlanRead(MealPlan):
    id: Annotated[PyObjectId, Field(alias="_id")]


class MealPlanUpdate(TimeStampedModel):
    plan_name: str | None = None
    description: str | None = None
    day: DayOfWeek | None = None
    breakfast: Meal | None = None
    lunch: Meal | None = None
    dinner: Meal | None = None
    version: Version | None = None


class MealPlanCRUD(TimeStampedCRUDBase[MealPlan, MealPlanRead, MealPlanUpdate]):
    def __init__(self, db: Database[dict[str, Any]]) -> None:
        super().__init__(
            db=db,
            collection_name=COLLECTION_NAME,
            read_schema=MealPlanRead,
            indexes=[
                [
                    MealPlanBase.Field.plan_name.value,
                ],
            ],
        )
