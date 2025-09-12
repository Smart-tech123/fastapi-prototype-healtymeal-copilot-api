from enum import StrEnum
from typing import Annotated

from pydantic import Field

from app.models.common.version import ChangeType, Version
from app.models.meal_plan import MealPlan, MealPlanBase, MealPlanUpdate


class CreateMealPlanRequest(MealPlanBase):
    log_message: Annotated[
        str,
        Field(
            description="Message for version log",
            examples=[
                "upgraded risk management",
            ],
        ),
    ]

    class Field(StrEnum):
        log_message = "log_message"

    @classmethod
    def from_base(cls, meal_plan: MealPlanBase, log_message: str) -> "CreateMealPlanRequest":
        return cls.model_validate(
            {
                **meal_plan.model_dump(include=set(MealPlanBase.model_fields.keys())),
                cls.Field.log_message: log_message,
            }
        )

    def to_meal_plan(self, version: Version) -> MealPlan:
        return MealPlan.model_validate(
            {
                **self.model_dump(),
                MealPlan.Field.version: version,
            }
        )


class UpdateMealPlanRequest(MealPlanBase):
    change: Annotated[ChangeType, Field(description="Indicates which type of change was made")]
    log_message: Annotated[
        str,
        Field(
            description="Message for version log",
            examples=[
                "upgraded risk management",
            ],
        ),
    ]

    class Field(StrEnum):
        change = "change"
        log_message = "log_message"

    @classmethod
    def from_base(cls, meal_plan: MealPlanBase, change: ChangeType, log_message: str) -> "UpdateMealPlanRequest":
        return cls.model_validate(
            {
                **meal_plan.model_dump(include=set(MealPlanBase.model_fields.keys())),
                cls.Field.change: change,
                cls.Field.log_message: log_message,
            }
        )

    def to_meal_plan_update(self, version: Version) -> MealPlanUpdate:
        return MealPlanUpdate.model_validate(
            {
                **self.model_dump(include=set(MealPlanBase.model_fields.keys())),
                MealPlan.Field.version: version,
            }
        )
