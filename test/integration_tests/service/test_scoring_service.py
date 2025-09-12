from loguru import logger

from app.core.config.llm import config as cfg_llm
from app.core.config.scoring import config as cfg_scoring
from app.models.meal_plan import MealPlanBase
from app.services.scoring_service import ScoringService
from test.common.validation import get_valid_meal_plan_json


def test_valid() -> None:
    meal_plan_json = get_valid_meal_plan_json()
    res = ScoringService.score_meal_plan(meal_plan_json, prompt_ver=cfg_llm.DEFAULT_PROMPT_VERSION)
    logger.debug(res.model_dump_json(indent=2))

    assert res.score == cfg_scoring.MAX_SCORE


def test_missing() -> None:
    meal_plan_json = get_valid_meal_plan_json()
    meal_plan_json.pop(MealPlanBase.Field.plan_name.value, None)
    res = ScoringService.score_meal_plan(meal_plan_json, prompt_ver=cfg_llm.DEFAULT_PROMPT_VERSION)
    logger.debug(res.model_dump_json(indent=2))

    assert res.score >= 0
    assert res.score < cfg_scoring.MAX_SCORE


def test_invalid_type() -> None:
    meal_plan_json = get_valid_meal_plan_json()
    meal_plan_json[MealPlanBase.Field.plan_name.value] = 123
    res = ScoringService.score_meal_plan(meal_plan_json, prompt_ver=cfg_llm.DEFAULT_PROMPT_VERSION)
    logger.debug(res.model_dump_json(indent=2))

    assert res.score >= 0
    assert res.score < cfg_scoring.MAX_SCORE


def test_invalid_enum() -> None:
    meal_plan_json = get_valid_meal_plan_json()
    meal_plan_json[MealPlanBase.Field.day.value] = "zzz"
    res = ScoringService.score_meal_plan(meal_plan_json, prompt_ver=cfg_llm.DEFAULT_PROMPT_VERSION)
    logger.debug(res.model_dump_json(indent=2))

    assert res.score >= 0
    assert res.score < cfg_scoring.MAX_SCORE
