from typing import Any

import jsonpatch
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from app.core.config.api import config as cfg_api
from app.models.common.base_models import TimeStampedModel
from app.models.common.object_id import PyObjectId
from app.models.meal_plan import MealPlanBase, MealPlanCRUD, MealPlanRead, MealPlanUpdate
from app.models.version_log import VersionLog, VersionLogAction, VersionLogCRUD, VersionLogMetadata, VersionLogRead
from app.utils.datetime import DatetimeUtil


class VersionLogService:
    """
    Version history management service.

    * Role:
        * Log version change with current timestamp, client name and message
        * Rollback meal_plan to the given log id
    """

    def __init__(self, db: Database[dict[str, Any]]) -> None:
        self.db = db
        self.meal_plan_crud = MealPlanCRUD(db=db)
        self.version_log_crud = VersionLogCRUD(db=db)

    def save_meal_plan_version_log(
        self,
        meal_plan: MealPlanRead,
        client_name: str,
        msg: str,
        action: VersionLogAction | None = None,
    ) -> VersionLogRead:
        """
        Saves the meal_plan version log with current timestamp.

        Args:
            meal_plan (MealPlanRead): MealPlan to save version log
            client_name (str): Client name who made the change
            msg (str): Log message
            action (VersionLogAction | None): Change action.
                If not provided, it will be determined based on the log count

        Returns:
            PyObjectId: Generated version log id
        """
        # Set patch
        patch = None
        latest_meal_plan = self.get_latest(meal_plan_id=meal_plan.id)
        if latest_meal_plan is not None:
            json_patch = jsonpatch.make_patch(
                latest_meal_plan.model_dump(include=set(MealPlanBase.model_fields.keys())),
                meal_plan.model_dump(include=set(MealPlanBase.model_fields.keys())),
            )
            patch = json_patch.patch

        # Set key frame
        log_count = self.version_log_crud.count({VersionLog.Field.meal_plan_id: meal_plan.id})
        full_content = meal_plan if log_count % cfg_api.HISTORY_KEYFRAME_INTERVAL == 0 else None

        # Set action
        action = action or (VersionLogAction.create if log_count == 0 else VersionLogAction.update)

        # Save version log
        return self.version_log_crud.create(
            obj_create=VersionLog(
                meal_plan_id=meal_plan.id,
                client_name=client_name,
                timestamp=DatetimeUtil.get_current_timestamp(),
                message=msg,
                patch=patch,
                full_content=full_content,
                metadata=VersionLogMetadata(
                    created_by=client_name,
                    action=action,
                    note=msg,
                ),
            )
        )

    def get_by_log_id(
        self,
        meal_plan_id: PyObjectId,
        log_id: PyObjectId,
    ) -> MealPlanRead:
        """
        Returns the meal_plan at the given log id.

        Args:
            meal_plan_id (PyObjectId): MealPlan id
            log_id (PyObjectId): Log id

        Returns:
            MealPlanRead: MealPlan
        """
        version_log = self.version_log_crud.get(obj_id=log_id)
        if version_log.meal_plan_id != meal_plan_id:
            msg = "MealPlan id mismatch"
            raise ValueError(msg)

        # Get last full log
        doc = self.version_log_crud.coll.find_one(
            {
                VersionLog.Field.meal_plan_id: meal_plan_id,
                VersionLog.Field.full_content: {"$ne": None},
                TimeStampedModel.Field.created_at: {"$lte": version_log.created_at},
            },
            sort=[(TimeStampedModel.Field.created_at, DESCENDING)],
        )
        last_full_log = VersionLogRead.model_validate(doc)
        if last_full_log.full_content is None:
            msg = "Last full log not found"
            raise ValueError(msg)

        # Get all diff logs
        logs_cursor = self.version_log_crud.coll.find(
            {
                VersionLog.Field.meal_plan_id: meal_plan_id,
                TimeStampedModel.Field.created_at: {"$gt": last_full_log.created_at, "$lte": version_log.created_at},
            },
            sort=[(TimeStampedModel.Field.created_at, ASCENDING)],
        )

        # Merge diff logs
        full_content_dict = last_full_log.full_content.model_dump()
        for log_doc in logs_cursor:
            log = VersionLogRead.model_validate(log_doc)
            full_content_dict = jsonpatch.apply_patch(full_content_dict, log.patch)

        return MealPlanRead.model_validate(
            {
                "_id": meal_plan_id,
                **full_content_dict,
            }
        )

    def get_latest(
        self,
        meal_plan_id: PyObjectId,
    ) -> MealPlanRead | None:
        """
        Returns the last version of the meal_plan.

        Args:
            meal_plan_id (PyObjectId): MealPlan id to get the latest version

        Returns:
            MealPlanRead: MealPlan
        """

        # Get last full log
        doc = self.version_log_crud.coll.find_one(
            {
                VersionLog.Field.meal_plan_id: meal_plan_id,
            },
            sort=[(TimeStampedModel.Field.created_at, DESCENDING)],
        )
        if doc is None:
            ret = None
        else:
            last_log = VersionLogRead.model_validate(doc)
            ret = self.get_by_log_id(meal_plan_id=meal_plan_id, log_id=last_log.id)

        return ret

    def rollback(
        self,
        meal_plan_id: PyObjectId,
        log_id: PyObjectId,
        client_name: str,
        msg: str,
    ) -> MealPlanRead:
        """
        Rollback the meal_plan to the given log id.

        Args:
            meal_plan_id (PyObjectId): MealPlan id to rollback
            log_id (PyObjectId): Log id to rollback to

        Returns:
            MealPlanRead: MealPlan
        """

        # Update meal_plan
        meal_plan_rollback = self.get_by_log_id(meal_plan_id=meal_plan_id, log_id=log_id)
        meal_plan_read = self.meal_plan_crud.update(
            obj_update=MealPlanUpdate.model_validate(meal_plan_rollback.model_dump()),
            obj_id=meal_plan_id,
        )

        # Save version log
        self.save_meal_plan_version_log(
            meal_plan=meal_plan_read,
            client_name=client_name,
            msg=msg,
            action=VersionLogAction.rollback,
        )

        return meal_plan_read

    def drop_logs(self, meal_plan_id: PyObjectId) -> None:
        """
        Drop all version logs of the meal_plan.

        Args:
            meal_plan_id (PyObjectId): MealPlan id

        Returns:
            None
        """
        self.version_log_crud.coll.delete_many({VersionLog.Field.meal_plan_id: meal_plan_id})

    def created_at(self, meal_plan_id: PyObjectId) -> int | None:
        """
        Returns the creation time of the meal_plan.

        Args:
            meal_plan_id (PyObjectId): MealPlan id to get the creation time

        Returns:
            int: Creation timestamp in milliseconds Unix epoch
        """
        doc = self.version_log_crud.coll.find_one(
            {VersionLog.Field.meal_plan_id: meal_plan_id},
            sort=[(TimeStampedModel.Field.created_at, ASCENDING)],
        )
        if doc is None:
            return None
        return VersionLogRead.model_validate(doc).created_at

    def updated_at(self, meal_plan_id: PyObjectId) -> int | None:
        """
        Returns the last update time of the meal_plan.

        Args:
            meal_plan_id (PyObjectId): MealPlan id to get the update time

        Returns:
            int: Update timestamp in milliseconds Unix epoch
        """
        doc = self.version_log_crud.coll.find_one(
            {VersionLog.Field.meal_plan_id: meal_plan_id},
            sort=[(TimeStampedModel.Field.created_at, DESCENDING)],
        )
        if doc is None:
            return None
        return VersionLogRead.model_validate(doc).created_at
