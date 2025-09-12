from typing import Any

from app.prompts.context.base import PromptContextBase
from app.schemas.validation import ValidationErrorDetails


class ScoreMealPlanPromptContext(PromptContextBase):
    model_schema: dict[str, Any]
    error_details: list[ValidationErrorDetails]
