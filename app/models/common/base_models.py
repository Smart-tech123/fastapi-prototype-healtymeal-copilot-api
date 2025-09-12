from enum import StrEnum

from pydantic import BaseModel


class TimeStampedModel(BaseModel):
    created_at: int | None = None
    updated_at: int | None = None

    class Field(StrEnum):
        created_at = "created_at"
        updated_at = "updated_at"
