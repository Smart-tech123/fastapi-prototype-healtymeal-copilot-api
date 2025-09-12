from typing import Any

from pydantic import BaseModel, ValidationError

from app.schemas.validation import ValidationErrorDetails, ValidationResult


class ValidationService:
    @classmethod
    def validate_model_json(cls, model: type[BaseModel], obj_dict: dict[str, Any]) -> ValidationResult:
        try:
            model_obj = model.model_validate(obj_dict)
            return ValidationResult(valid=True, model_obj=model_obj, errors=[])

        except ValidationError as e:
            return ValidationResult(
                valid=False,
                errors=[
                    ValidationErrorDetails(
                        field=list(err.get("loc")),  # type: ignore  # noqa: PGH003
                        code=err.get("type"),
                        message=err.get("msg"),
                        input=err.get("input"),
                    )
                    for err in e.errors()
                ],
            )
        except TypeError as e:
            return ValidationResult(
                valid=False,
                model_obj=None,
                errors=[
                    ValidationErrorDetails(
                        code="type_error",
                        field=["body"],
                        message=str(e),
                        input=obj_dict,
                    )
                ],
            )
        except ValueError as e:
            return ValidationResult(
                valid=False,
                model_obj=None,
                errors=[
                    ValidationErrorDetails(
                        code="value_error",
                        field=["body"],
                        message=str(e),
                        input=obj_dict,
                    )
                ],
            )
        except Exception as e:
            return ValidationResult(
                valid=False,
                model_obj=None,
                errors=[
                    ValidationErrorDetails(
                        code="unexpected_error",
                        field=["body"],
                        message=str(e),
                        input=obj_dict,
                    )
                ],
            )
