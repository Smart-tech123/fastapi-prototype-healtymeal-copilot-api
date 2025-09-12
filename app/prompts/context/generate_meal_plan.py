from typing import Any

from app.prompts.context.base import PromptContextBase


class GenerateMealPlanPromptContext(PromptContextBase):
    meal_plan_specs: str
    meal_plan_schema: dict[str, Any]
