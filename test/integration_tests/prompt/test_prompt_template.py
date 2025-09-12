from loguru import logger

from app.core.config.llm import config as cfg_llm
from app.models.common.version import Version
from app.models.meal_plan import MealPlanBase
from app.prompts.context.generate_meal_plan import GenerateMealPlanPromptContext
from app.prompts.context.score_meal_plan import ScoreMealPlanPromptContext
from app.prompts.factory import PromptFactory, PromptType


def test_default_version() -> None:
    prompt = PromptFactory.render_prompt_by_type(
        prompt_type=PromptType.GENERATE_FOOD_PLAN,
        context=GenerateMealPlanPromptContext(
            meal_plan_specs="the simplist meal plan",
            meal_plan_schema=MealPlanBase.model_json_schema(),
        ),
        prompt_ver=cfg_llm.DEFAULT_PROMPT_VERSION,
    )
    logger.debug(prompt)


def test_valid_version() -> None:
    prompt = PromptFactory.render_prompt_by_type(
        prompt_type=PromptType.GENERATE_FOOD_PLAN,
        context=GenerateMealPlanPromptContext(
            meal_plan_specs="the simplist meal plan",
            meal_plan_schema=MealPlanBase.model_json_schema(),
        ),
        prompt_ver=Version(major=1, minor=0, patch=0),
    )
    logger.debug(prompt)


def test_invalid_version() -> None:
    try:
        prompt = PromptFactory.render_prompt_by_type(
            prompt_type=PromptType.GENERATE_FOOD_PLAN,
            context=GenerateMealPlanPromptContext(
                meal_plan_specs="the simplist meal plan",
                meal_plan_schema=MealPlanBase.model_json_schema(),
            ),
            prompt_ver=Version(major=2, minor=0, patch=0),
        )
        logger.debug(prompt)

        msg = "Expected ValueError"
        raise AssertionError(msg)

    except ValueError as e:
        logger.debug(e)


def test_invalid_context_type() -> None:
    try:
        # This should raise TypeError due to invalid context type
        context = ScoreMealPlanPromptContext(
            model_schema=MealPlanBase.model_json_schema(),
            error_details=[],
        )
        PromptFactory.render_prompt_by_type(
            prompt_type=PromptType.GENERATE_FOOD_PLAN,
            context=context,
            prompt_ver=Version(major=2, minor=0, patch=0),
        )

        msg = "Expected TypeError"
        raise AssertionError(msg)

    except TypeError as e:
        logger.debug(e)
