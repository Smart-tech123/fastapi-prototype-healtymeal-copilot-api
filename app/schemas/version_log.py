from typing import Annotated

from pydantic import BaseModel, Field


class VersionLogRollbackRequest(BaseModel):
    msg: Annotated[
        str,
        Field(
            min_length=3,
            description="Rollback message",
            examples=[
                "rollback to latest stable version",
            ],
        ),
    ]
