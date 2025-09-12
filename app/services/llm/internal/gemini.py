from typing import Any, override

from loguru import logger

from app.services.llm.internal.base import BaseLLMService


class GeminiService(BaseLLMService):
    def __init__(
        self,
        model: str,
        api_key: str,
    ) -> None:
        """
        Initialize Gemini service

        Args:
            model (str): Gemini model
            api_key (str): Gemini API key
        """
        logger.debug(f"model: {model}")
        logger.debug(f"api_key: {api_key}")

        raise NotImplementedError

    @override
    def complete_text(
        self,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
    ) -> str:
        """
        Get response from Gemini.

        If both `system_prompt` and `user_prompt` are None, raise ValueError.

        Args:
            sys_prompt (str): System prompt
            user_prompt (str): User prompt

        Returns:
            str: Raw Gemini response
        """
        if system_prompt is None and user_prompt is None:
            msg = "Both `system_prompt` and `user_prompt` are None"
            raise ValueError(msg)

        raise NotImplementedError

    @override
    def complete_json(
        self,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
    ) -> Any:
        """
        Get JSON response from Gemini.

        If both `system_prompt` and `user_prompt` are None, raise ValueError.

        Args:
            sys_prompt (str): System prompt
            user_prompt (str): User prompt

        Returns:
            Any: JSON response. e.g. dict, list ...
        """
        if system_prompt is None and user_prompt is None:
            msg = "Both `system_prompt` and `user_prompt` are None"
            raise ValueError(msg)

        raise NotImplementedError
