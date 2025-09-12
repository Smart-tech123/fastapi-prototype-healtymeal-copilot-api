from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.validation import ValidationErrorDetails


class ScoringResult(BaseModel):
    score: Annotated[int, Field(ge=0, le=100, description="Score number between 0 and 100. 100 means perfect")]
    flags: Annotated[list[str], Field(description="List of flags that indicates issues with the object")]
    suggestions: Annotated[list[str], Field(description="List of suggestions to improve the object")]
    errors: Annotated[list[ValidationErrorDetails], Field(description="List of validation detailed errors")]

    class Field(StrEnum):
        score = "score"
        flags = "flags"
        suggestions = "suggestions"
        errors = "errors"
