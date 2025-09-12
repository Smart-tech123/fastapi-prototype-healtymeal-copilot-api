import json
import re
from typing import Any, override

from loguru import logger
from openai import OpenAI

from app.core.config.llm import config as cfg_llm
from app.services.llm.internal.base import BaseLLMService


class OpenAIService(BaseLLMService):
    def __init__(
        self,
        model: str,
        api_key: str,
    ) -> None:
        """
        Initialize OpenAI service

        Args:
            model (str): OpenAI model
            api_key (str): OpenAI API key
        """
        self.model = model
        self.client = OpenAI(api_key=api_key)

    @override
    def complete_text(
        self,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
    ) -> str:
        """
        Get response from OpenAI.

        Args:
            sys_prompt (str): System prompt
            user_prompt (str): User prompt

        Returns:
            str: Raw OpenAI response

        Exceptions:
            ValueError: If both `system_prompt` and `user_prompt` are None
            Exception: If OpenAI API request fails
        """
        if system_prompt is None and user_prompt is None:
            msg = "Both `system_prompt` and `user_prompt` are None"
            raise ValueError(msg)

        for i in range(cfg_llm.MAX_RETRIES):
            try:
                # Build messages
                messages: list[dict[str, str]] = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt.strip()})
                if user_prompt:
                    messages.append({"role": "user", "content": user_prompt.strip()})
                logger.debug(f"OpenAI Prompts:\n[system]: {system_prompt}\n[user]: {user_prompt}")

                # Get LLM response
                response = self.client.chat.completions.create(model=self.model, messages=messages)  # type: ignore  # noqa: PGH003

                # Check response
                if not response or not hasattr(response, "choices") or not response.choices:
                    logger.warning(f"Invalid response from OpenAI ({i + 1}/{cfg_llm.MAX_RETRIES})")
                    continue

                choice = response.choices[0]
                if not hasattr(choice, "message"):
                    logger.warning(f"Invalid message from OpenAI ({i + 1}/{cfg_llm.MAX_RETRIES})")
                    continue

                # Check response
                raw_resp = choice.message.content
                if raw_resp:
                    logger.debug(f"OpenAI response:\n{raw_resp}")
                    return raw_resp

                logger.warning(f"OpenAI response is empty ({i + 1}/{cfg_llm.MAX_RETRIES})")
            except Exception as e:
                logger.warning(f"OpenAI request failed ({i + 1}/{cfg_llm.MAX_RETRIES}): {e}")

        msg = f"OpenAI request failed after max {cfg_llm.MAX_RETRIES} retries"
        raise RuntimeError(msg)

    @override
    def complete_json(
        self,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
    ) -> Any:
        """
        Get JSON response from OpenAI.

        Args:
            sys_prompt (str): System prompt
            user_prompt (str): User prompt

        Returns:
            Any: JSON response. e.g. dict, list ...

        Exceptions:
            ValueError: If both `system_prompt` and `user_prompt` are None
            Exception: If all retries failed
        """
        if system_prompt is None and user_prompt is None:
            msg = "Both `system_prompt` and `user_prompt` are None"
            raise ValueError(msg)

        for i in range(cfg_llm.MAX_RETRIES):
            try:
                # Get raw response
                raw_response = self.complete_text(system_prompt=system_prompt, user_prompt=user_prompt)

                # Cleanup raw response
                cleaned = self.cleanup_raw_response(raw_response=raw_response)
                logger.debug(f"Cleaned response:\n{cleaned}")

                # Try to load JSON
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"Failed to load JSON from LLM response ({i + 1}/{cfg_llm.MAX_RETRIES}): {e}\n"
                        f"Response was:\n{cleaned}"
                    )
            except Exception as e:
                logger.warning(f"Getting raw response from LLM failed ({i + 1}/{cfg_llm.MAX_RETRIES}): {e}")

        msg = f"Failed to load JSON from LLM response after max {cfg_llm.MAX_RETRIES} retries"
        raise RuntimeError(msg)

    def cleanup_raw_response(self, raw_response: str) -> str:
        """
        Sometimes OpenAI raw response contains unexpected descriptions not only expected JSON. We should remove them.
        """
        match = re.search(r"```json\s*(.*?)\s*```", raw_response, flags=re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else raw_response.strip()

    @override
    def generate_embedding(self, text: str) -> list[float]:
        """
        Get embedding from OpenAI

        Args:
            text (str): Text to get embedding vector

        Returns:
            list[float]: Generated embedding vector

        Exceptions:
            Exception: If all retries failed
        """
        for i in range(cfg_llm.MAX_RETRIES):
            try:
                # Get embedding from OpenAI
                resp = self.client.embeddings.create(input=text, model=cfg_llm.EMBEDDING_MODEL)

                # Check response
                if not resp or not hasattr(resp, "data") or not resp.data:
                    logger.warning(f"Invalid response from OpenAI ({i + 1}/{cfg_llm.MAX_RETRIES})")
                    continue

                # Return embeddings
                return resp.data[0].embedding if isinstance(text, str) else [x.embedding for x in resp.data]

            except Exception as e:
                logger.warning(f"OpenAI embedding request failed ({i + 1}/{cfg_llm.MAX_RETRIES}): {e}")

        msg = f"OpenAI embedding request failed after max {cfg_llm.MAX_RETRIES} retries"
        raise RuntimeError(msg)
