import datetime
import secrets
import string
from enum import StrEnum
from typing import Any

from loguru import logger

from app.core.env import AppEnv
from app.models.common.object_id import PyObjectId


class RandUtil:
    @classmethod
    def get_str(cls, strlen: int = 32) -> str:
        """Return a secure random string of the given length."""
        characters = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
        return "".join(secrets.choice(characters) for _ in range(strlen))

    @classmethod
    def get_hex(cls, strlen: int = 32) -> str:
        """Return a secure random hex string of the given length."""
        return secrets.token_hex(strlen // 2)

    @classmethod
    def get_int(cls, lo: int = 0, up: int = 65536) -> int:
        """Return a secure random integer in the range [lower_limit, upper_limit)."""
        return secrets.randbelow(up - lo) + lo

    @classmethod
    def get_float(cls) -> float:
        """Return a secure random float in the range [0.0, 1.0)."""
        return cls.get_int(0, 65536) / 65536

    @classmethod
    def get_enum(cls, enum_type: type[StrEnum]) -> StrEnum:
        return list(enum_type)[cls.get_int(0, len(enum_type))]

    @classmethod
    def get_datetime(cls) -> datetime.datetime:
        """Return random datetime which rounded microseconds."""
        # Generate a random date
        random_year = cls.get_int(2020, 2024)
        random_month = cls.get_int(1, 12)
        random_day = cls.get_int(1, 28)  # 28 is safe for all months
        random_date = datetime.datetime(random_year, random_month, random_day, tzinfo=datetime.UTC)

        # Generate a random time (HH:MM:SS)
        random_hour = cls.get_int(0, 23)
        random_minute = cls.get_int(0, 59)
        random_second = cls.get_int(0, 59)
        random_microsecond = cls.get_int(0, 999) * 1000
        random_time = datetime.time(random_hour, random_minute, random_second, random_microsecond)

        # Combine date and time
        return datetime.datetime.combine(random_date, random_time)

    @classmethod
    def get_timestamp(cls) -> int:
        return int(cls.get_datetime().timestamp() * 1000)

    @classmethod
    def get_mongo_id(cls) -> PyObjectId:
        return PyObjectId(cls.get_hex(24))

    @classmethod
    def get_list_item(cls, items: list[Any]) -> Any:  # noqa: ANN401
        return items[cls.get_int(0, len(items))]


if __name__ == "__main__":
    logger.debug(f"str: {RandUtil.get_str(32)}")
    logger.debug(f"hex: {RandUtil.get_hex(32)}")
    logger.debug(f"int: {RandUtil.get_int(0, 65535)}")
    logger.debug(f"float: {RandUtil.get_float()}")
    logger.debug(f"enum: {RandUtil.get_enum(AppEnv)}")
    logger.debug(f"datetime: {RandUtil.get_datetime()}")
    logger.debug(f"timestamp: {RandUtil.get_timestamp()}")
    logger.debug(f"mongo_id: {RandUtil.get_mongo_id()}")
