from typing import Any

from app.schemas.errors import ErrorCode429, TooManyRequestException
from app.utils.datetime import DatetimeUtil


class RateLimiter:
    def __init__(self) -> None:
        self.storage: dict[str, Any] = {}

    def increase_counter(self, key: str, limit_min: int, window_min: int = 1) -> None:
        """
        Increase the counter for the given key.

        Args:
            key (str): The key to increase the counter for.
            limit_min (int): The limit in minutes. If 0, no limit.
            window_min (int, optional): The window in minutes. Defaults to 1.
        """
        if limit_min == 0:
            return

        now_tstamp = DatetimeUtil.get_current_timestamp()
        if key in self.storage:
            self.storage[key].append(now_tstamp)
        else:
            self.storage[key] = [now_tstamp]

        for tstamp in self.storage[key]:
            if tstamp + window_min * 60_000 < now_tstamp:
                self.storage[key].remove(tstamp)

        if len(self.storage[key]) > limit_min:
            raise TooManyRequestException(
                error_code=ErrorCode429.TOO_MANY_REQUESTS,
                message="Rate limit exceeded",
            )

    def reset_counter(self, key: str) -> None:
        """
        Reset the counter for the given key.

        Args:
            key (str): The key to reset the counter for.
        """
        if key in self.storage:
            del self.storage[key]
