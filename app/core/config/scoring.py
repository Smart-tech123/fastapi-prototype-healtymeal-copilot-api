from pydantic_settings import BaseSettings


class Config(BaseSettings):
    MAX_SCORE: int = 100
    MAX_ERROR_POINT: int = 100  # Means that the score will be 0 if error point is greater than MAX_ERROR_POINT
    SEVERITY_WEIGHTS: dict[str, int] = {
        # Do not edit keys
        # The keys are predefined pydantic validation error codes
        # https://docs.pydantic.dev/latest/errors/validation_errors/
        "missing": 10,
        "enum": 8,
        "float_type": 6,
        "int_type": 6,
        "str_type": 6,
        "greater_than": 5,
        "greater_than_equal": 5,
        "less_than": 5,
        "less_than_equal": 5,
        "default": 1,  # Default weight
    }


config = Config()
