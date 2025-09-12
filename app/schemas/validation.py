from typing import Annotated, Any

from pydantic import BaseModel, Field


class ValidationErrorDetails(BaseModel):
    field: Annotated[
        list[str | int] | None,
        Field(
            description="Field path",
            examples=[
                [
                    "body",
                    "children",
                    0,
                    "name",
                ],
            ],
        ),
    ] = None
    code: Annotated[
        str | None,
        Field(
            description="Error code. You can find more info https://docs.pydantic.dev/latest/errors/validation_errors/",
            examples=[
                "missing",
            ],
        ),
    ] = None
    message: Annotated[
        str | None,
        Field(
            description="Error message",
            examples=[
                "Field required",
            ],
        ),
    ] = None
    input: Annotated[
        Any,
        Field(
            description="Object body in which the error raised",
            examples=[
                {
                    "children": [
                        {
                            "gender": "male",
                            "age": 10,
                        },
                    ],
                }
            ],
        ),
    ] = None


class ValidationResult(BaseModel):
    valid: Annotated[
        bool,
        Field(
            description="Model validation result",
            examples=[
                False,
            ],
        ),
    ]
    model_obj: Annotated[
        Any,
        Field(
            description="Validated model object",
            examples=[
                "<model_object>",
            ],
        ),
    ] = None
    errors: Annotated[
        list[ValidationErrorDetails],
        Field(
            description="Errors for invalid fields",
        ),
    ]
