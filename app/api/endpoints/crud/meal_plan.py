from app.api.generic_router import GenericRouter
from app.models.meal_plan import (
    MealPlan,
    MealPlanCRUD,
    MealPlanRead,
    MealPlanUpdate,
)

router = GenericRouter[
    MealPlanCRUD,
    MealPlan,
    MealPlanRead,
    MealPlanUpdate,
].create_crud_router(
    name="MealPlan",
    crud=MealPlanCRUD,
    db_schema=MealPlan,
    read_schema=MealPlanRead,
    update_schema=MealPlanUpdate,
)
