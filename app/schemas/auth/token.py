from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field

from app.models.auth.common.access_policy import AccessPolicyScope


class TokenType(StrEnum):
    BEARER = "bearer"


class Token(BaseModel):
    access_token: Annotated[
        str,
        Field(
            description="The access token",
            examples=[
                "<access_token_value>",
            ],
        ),
    ]
    token_type: TokenType


class TokenData(BaseModel):
    client_id: Annotated[
        str,
        Field(
            description="The id of the client",
            examples=[
                "<client_id>",
            ],
        ),
    ]
    scopes: Annotated[
        list[str],
        Field(
            description="The scopes of the client",
            examples=[
                [
                    AccessPolicyScope.GENERATE,
                    AccessPolicyScope.FOOD_PLAN,
                ]
            ],
        ),
    ]
