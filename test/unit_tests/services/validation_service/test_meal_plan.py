from app.models.meal_plan import MealPlanBase
from app.services.validation_service import ValidationService
from test.common.validation import check_meal_plan_validation_error, get_valid_meal_plan_json


def test_valid_meal_plan_json() -> None:
    obj_dict = get_valid_meal_plan_json()
    res = ValidationService.validate_model_json(MealPlanBase, obj_dict)
    assert res.valid


def test_invalid_meal_plan_name() -> None:
    # Check missing name
    obj_dict = get_valid_meal_plan_json()
    obj_dict.pop(MealPlanBase.Field.plan_name.value, None)
    check_meal_plan_validation_error(obj_dict, [([MealPlanBase.Field.plan_name.value], "missing")])

    # Check None name
    obj_dict = get_valid_meal_plan_json()
    obj_dict[MealPlanBase.Field.plan_name.value] = None
    check_meal_plan_validation_error(obj_dict, [([MealPlanBase.Field.plan_name.value], "string_type")])

    # Check invalid name
    obj_dict = get_valid_meal_plan_json()
    obj_dict[MealPlanBase.Field.plan_name.value] = ""
    check_meal_plan_validation_error(obj_dict, [([MealPlanBase.Field.plan_name.value], "string_too_short")])
