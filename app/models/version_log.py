from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field
from pymongo.database import Database

from app.models.common.base_models import TimeStampedModel
from app.models.common.generic_crud import TimeStampedCRUDBase
from app.models.common.object_id import PyObjectId
from app.models.meal_plan import MealPlan

COLLECTION_NAME = "version_log"


class VersionLogAction(StrEnum):
    create = "create"
    update = "update"
    rollback = "rollback"


class VersionLogMetadata(BaseModel):
    created_by: Annotated[str, Field(min_length=3, description="Client name who made the change")]
    action: Annotated[VersionLogAction, Field(min_length=3, description="Performed change action")]
    note: Annotated[str, Field(min_length=3, description="Log message")]

    class Field(StrEnum):
        created_by = "created_by"
        action = "action"
        note = "note"


class VersionLog(TimeStampedModel):
    """
    VersionLog scheme for meal_plan version management
    """

    meal_plan_id: Annotated[
        PyObjectId,
        Field(description="MealPlan id to track changes"),
    ]

    client_name: Annotated[
        str,
        Field(
            min_length=3,
            description="Client name who made the change",
            examples=[
                "internal_bot",
            ],
        ),
    ]
    message: Annotated[
        str,
        Field(
            min_length=3,
            description="Log message",
            examples=[
                "upgraded risk management",
            ],
        ),
    ]

    patch: Annotated[
        Any,
        Field(
            description="Difference between current and previous meal_plan",
            examples=[
                "{...}",
            ],
        ),
    ]
    full_content: Annotated[
        MealPlan | None,
        Field(description="Full meal_plan content for keyframe"),
    ] = None

    metadata: Annotated[
        VersionLogMetadata,
        Field(description="Version log metadata"),
    ]

    class Field(StrEnum):
        meal_plan_id = "meal_plan_id"
        client_name = "client_name"
        message = "message"
        patch = "patch"
        full_content = "full_content"
        metadata = "metadata"


class VersionLogRead(VersionLog):
    id: Annotated[PyObjectId, Field(alias="_id")]


class VersionLogUpdate(TimeStampedModel):
    meal_plan_id: PyObjectId | None = None
    client_name: str | None = None
    message: str | None = None
    patch: Any | None = None
    full_content: MealPlan | None = None
    metadata: VersionLogMetadata | None = None


class VersionLogCRUD(TimeStampedCRUDBase[VersionLog, VersionLogRead, VersionLogUpdate]):
    def __init__(self, db: Database[dict[str, Any]]) -> None:
        super().__init__(
            db=db,
            collection_name=COLLECTION_NAME,
            read_schema=VersionLogRead,
        )
