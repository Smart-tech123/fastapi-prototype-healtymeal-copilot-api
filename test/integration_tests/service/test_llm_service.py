import json

from loguru import logger

from app.core.config.llm import config as cfg_llm
from app.services.llm.factory import LLMFactory


def test_complete_text() -> None:
    llm = LLMFactory.get(cfg_llm.LLM_PROVIDER)

    system_prompt = "answer the question"
    user_prompt = "what is openai?"

    resp = llm.complete_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    logger.info(f"system_prompt: {system_prompt}")
    logger.info(f"user_prompt: {user_prompt}")
    logger.info(f"response: {resp}")


def test_complete_json() -> None:
    llm = LLMFactory.get(cfg_llm.LLM_PROVIDER)

    system_prompt = "create JSON for user with the fields."
    user_prompt = "required fields are username, age, gender"

    resp = llm.complete_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    logger.info(f"system_prompt: {system_prompt}")
    logger.info(f"user_prompt: {user_prompt}")
    logger.info(f"response: {json.dumps(resp, indent=2)}")
