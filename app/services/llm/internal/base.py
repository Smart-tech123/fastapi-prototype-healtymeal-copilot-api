from typing import Any


class BaseLLMService:
    def complete_text(
        self,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
    ) -> str:
        if system_prompt is None and user_prompt is None:
            msg = "Both `system_prompt` and `user_prompt` are None"
            raise ValueError(msg)

        raise NotImplementedError

    def complete_json(
        self,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
    ) -> Any:  # noqa: ANN401
        if system_prompt is None and user_prompt is None:
            msg = "Both `system_prompt` and `user_prompt` are None"
            raise ValueError(msg)

        raise NotImplementedError

    def generate_embedding(self, text: str) -> list[float]:
        raise NotImplementedError
