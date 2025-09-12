import math
from typing import Any

from loguru import logger

from app.core.config.llm import config as cfg_llm
from app.core.config.scoring import config as cfg_scoring
from app.models.common.version import Version
from app.models.meal_plan import MealPlanBase
from app.prompts.context.score_meal_plan import ScoreMealPlanPromptContext
from app.prompts.factory import PromptFactory, PromptType
from app.schemas.scoring import ScoringResult
from app.schemas.validation import ValidationErrorDetails
from app.services.llm.factory import LLMFactory
from app.services.validation_service import ValidationService


class ScoringService:
    @classmethod
    def exponential_decay(cls, a: float, k: float, x: float) -> float:
        return a * math.exp(-k * x)

    @classmethod
    def calculate_error_point(cls, errors: list[ValidationErrorDetails]) -> float:
        error_point = 0
        for err in errors:
            if err.code in cfg_scoring.SEVERITY_WEIGHTS:
                error_point += cfg_scoring.SEVERITY_WEIGHTS[err.code]
            else:
                logger.warning(f"Non-weighted error code: {err.code}")
                error_point += cfg_scoring.SEVERITY_WEIGHTS["default"]
        return error_point

    @classmethod
    def calculate_score(cls, errors: list[ValidationErrorDetails]) -> int:
        """
        Calculate a score based on a list of validation errors using exponential decay.
        """
        error_point = cls.calculate_error_point(errors)
        if error_point < 0:
            msg = "Error point cannot be negative"
            raise ValueError(msg)

        k = math.log(cfg_scoring.MAX_ERROR_POINT) / cfg_scoring.MAX_ERROR_POINT
        return int(cls.exponential_decay(cfg_scoring.MAX_SCORE, k, error_point))

    @classmethod
    def score_meal_plan(cls, meal_plan_json: dict[str, Any], prompt_ver: Version) -> ScoringResult:
        ret = ScoringResult(score=0, flags=[], suggestions=[], errors=[])

        # Validate JSON based on Schema
        validation_res = ValidationService.validate_model_json(MealPlanBase, meal_plan_json)

        if validation_res.valid:
            ret.score = 100

        else:
            # Generate suggestions by LLM
            error_details = [err.model_dump() for err in validation_res.errors]

            # Render prompt
            prompt = PromptFactory.render_prompt_by_type(
                prompt_type=PromptType.SCORE_FOOD_PLAN,
                context=ScoreMealPlanPromptContext(
                    model_schema=MealPlanBase.model_json_schema(),
                    error_details=error_details,
                ),
                prompt_ver=prompt_ver,
            )
            suggestions: list[str] = LLMFactory.get(cfg_llm.LLM_PROVIDER).complete_json(user_prompt=prompt)

            # Check if suggestions are valid
            if not isinstance(suggestions, list) or not suggestions:
                # Use default suggestion
                suggestions = ["Please fix errors in the meal_plan JSON and try again."]

            # Set result
            ret.score = cls.calculate_score(validation_res.errors)
            ret.flags = []
            for err in validation_res.errors:
                field_path = ".".join([f"{f}" for f in err.field or []])
                flag = f"Error in '{field_path or 'body'}'. {err.message}"
                ret.flags.append(flag)
            ret.suggestions = suggestions
            ret.errors = validation_res.errors

        return ret


if __name__ == "__main__":
    k = math.log(cfg_scoring.MAX_ERROR_POINT) / cfg_scoring.MAX_ERROR_POINT
    for ep in range(cfg_scoring.MAX_ERROR_POINT + 10):
        ed = ScoringService.exponential_decay(cfg_scoring.MAX_SCORE, k, ep)
        logger.debug(f"error_point: {ep} > {int(ed)}")
