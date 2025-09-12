from typing import Any

from loguru import logger

from app.models.meal_plan import MealPlanBase
from app.services.validation_service import ValidationService


def get_valid_meal_plan_json() -> dict[str, Any]:
    return {
        "plan_name": "Vegan Healthy Weekly Meal Plan",
        "description": "A balanced vegan meal plan with nutrient-dense breakfasts, lunches, and dinners to support a healthy lifestyle.",  # noqa: E501
        "day": "monday",
        "breakfast": {
            "name": "Overnight Oats with Berries and Chia Seeds",
            "calories": 350,
            "ingredients": ["rolled oats", "almond milk", "chia seeds", "blueberries", "maple syrup"],
        },
        "lunch": {
            "name": "Chickpea Salad Bowl",
            "calories": 480,
            "ingredients": ["chickpeas", "mixed greens", "cucumber", "cherry tomatoes", "olive oil", "lemon juice"],
        },
        "dinner": {
            "name": "Quinoa and Roasted Vegetable Stir-fry",
            "calories": 520,
            "ingredients": ["quinoa", "broccoli", "bell peppers", "zucchini", "garlic", "tamari sauce", "sesame seeds"],
        },
    }


def check_meal_plan_validation_error(obj_dict: dict[str, Any], exp_res: list[tuple[list[str | int], str]]) -> None:
    res = ValidationService.validate_model_json(MealPlanBase, obj_dict)

    assert res.valid is False
    assert len(res.errors) == len(exp_res)

    for err, exp_err in zip(res.errors, exp_res, strict=True):
        logger.debug(f"field: {err.field}, code: {err.code}")
        logger.debug(err.message)
        logger.debug(err.input)

        assert err.field == exp_err[0]
        assert err.code == exp_err[1]
