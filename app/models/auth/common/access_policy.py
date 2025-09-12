from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


class AccessPolicyScope(StrEnum):
    ALL = "all"
    TENANT = "tenant"
    QDRANT = "qdrant"
    FOOD_PLAN = "meal_plan"
    GENERATE = "generate"
    VALIDATE = "validate"
    VERSION_SERVICE = "version_service"


class AccessPolicy(BaseModel):
    allowed_ips: Annotated[
        list[str],
        Field(
            description="List of allowed IPs",
            examples=[
                [
                    "127.0.0.1",
                    "192.168.8.*",
                    "192.168.9.*",
                    "169.254.*.*",
                    "192.168.10.1-192.168.10.10",
                    "192.168.11.0/24",
                ],
                ["1.2.3.4"],
                ["*.*.*.*"],
            ],
        ),
    ]
    scopes: Annotated[
        list[AccessPolicyScope],
        Field(
            description="List of allowed scopes",
            examples=[
                [
                    AccessPolicyScope.GENERATE,
                    AccessPolicyScope.FOOD_PLAN,
                ]
            ],
        ),
    ]
    rate_limit_per_min: Annotated[
        int,
        Field(
            ge=0,
            description="Rate limit per minute. 0 means no limit",
            examples=[
                60,
                120,
                0,
            ],
        ),
    ]

    class Field(StrEnum):
        allowed_ips = "allowed_ips"
        endpoints = "endpoints"
        scopes = "scopes"
        rate_limit_per_min = "rate_limit_per_min"
