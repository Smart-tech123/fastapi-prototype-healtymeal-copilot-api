from datetime import UTC, datetime

from loguru import logger


class DatetimeUtil:
    @classmethod
    def get_current_timestamp(cls) -> int:
        """Returns current timestamp in milliseconds"""
        return int(datetime.now(tz=UTC).timestamp() * 1000)

    @classmethod
    def get_datetime_from_timestamp(cls, timestamp: int) -> datetime:
        return datetime.fromtimestamp(timestamp / 1000, tz=UTC)


if __name__ == "__main__":
    tstamp = DatetimeUtil.get_current_timestamp()
    logger.debug(f"tstamp: {tstamp}")

    dt = DatetimeUtil.get_datetime_from_timestamp(tstamp)
    logger.debug(f"parsed dt: {dt} ")
    logger.debug(f"current dt: {datetime.now(tz=UTC)}")
