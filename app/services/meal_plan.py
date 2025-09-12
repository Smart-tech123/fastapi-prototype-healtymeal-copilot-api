import json
from typing import TYPE_CHECKING, Any

from loguru import logger
from pymongo.database import Database
from qdrant_client import QdrantClient

from app.core.config.fs import config as cfg_fs
from app.core.config.llm import config as cfg_llm
from app.core.config.qdrant import config as cfg_qdrant
from app.models.common.object_id import PyObjectId
from app.models.common.version import ChangeType, Version
from app.models.meal_plan import MealPlan, MealPlanCRUD, MealPlanRead
from app.models.retry_metadata import RetryMetadata, RetryReason
from app.prompts.context.generate_meal_plan import GenerateMealPlanPromptContext
from app.prompts.factory import PromptFactory, PromptType
from app.schemas.llm import GenerateMealPlanResult
from app.schemas.meal_plan import CreateMealPlanRequest, UpdateMealPlanRequest
from app.schemas.qdrant import QdrantSearchQuery
from app.services.llm.factory import LLMFactory
from app.services.qdrant_service import QdrantService
from app.services.retry_metadata_service import RetryMetadataService
from app.services.validation_service import ValidationService
from app.services.version_log_service import VersionLogService
from app.utils.datetime import DatetimeUtil

if TYPE_CHECKING:
    from pydantic import BaseModel

    from app.schemas.validation import ValidationResult


class MealPlanService:
    """Service for generating meal plan JSON based on LLM specification."""

    def __init__(self, db: Database[dict[str, Any]]) -> None:
        self.retry_metadata_service = RetryMetadataService(db=db)
        self.meal_plan_crud = MealPlanCRUD(db=db)
        self.version_log_service = VersionLogService(db=db)

    def generate_meal_plan(
        self,
        meal_plan_specs: str,
        prompt_version: Version | None,
        qdrant_client: QdrantClient | None,
        add_context: bool,  # noqa: FBT001
    ) -> GenerateMealPlanResult:
        """
        Generate meal plan JSON based on LLM specification.

        Args:
            db (Database[dict[str, Any]]): MongoDB database. Will be used to log retry metadata
            meal_plan_specs (str): LLM prompt for meal plan generation
            prompt_version (Version | None): Prompt version to be used for LLM.
                If not provided, the default version will be used
            qdrant_client (QdrantClient): Qdrant client for context retrieval
            add_context (bool): Whether to add context

        Returns:
            GenerateMealPlanResult
        """

        model: type[BaseModel] = MealPlan

        # Validate version
        valid_prompt_ver = cfg_llm.DEFAULT_PROMPT_VERSION
        if prompt_version is None:  # No prompt version provided
            logger.debug("No prompt version provided. Using default version.")
        else:  # Prompt version provided
            if not isinstance(prompt_version, Version):  # Invalid type of prompt version
                logger.warning("Invalid prompt version type. Using default version.")
            else:  # Valid type of prompt version
                ver_dir = cfg_fs.TEMPLATE_DIR / (prompt_version.to_str())
                if not ver_dir.exists():  # Template version does not exist
                    logger.warning("Template version does not exist. Using default version.")
                else:
                    valid_prompt_ver = prompt_version

        # Add Vector DB context
        prompt = meal_plan_specs
        if qdrant_client and add_context:
            prompt = self.add_context(qdrant_client=qdrant_client, prompt=prompt)

        # Render prompt
        prompt = PromptFactory.render_prompt_by_type(
            prompt_type=PromptType.GENERATE_FOOD_PLAN,
            context=GenerateMealPlanPromptContext(
                meal_plan_specs=prompt,
                meal_plan_schema=model.model_json_schema(),
            ),
            prompt_ver=valid_prompt_ver,
        )

        # Generate JSON Loop
        errors: list[ValidationResult] = []
        for i in range(cfg_llm.MAX_RETRIES):
            # Generate JSON from LLM
            try:
                json_data: dict[str, Any] = LLMFactory.get(cfg_llm.LLM_PROVIDER).complete_json(user_prompt=prompt)
            except Exception as e:
                # Log error
                msg = f"Failed to generate JSON from LLM: {e}"
                logger.error(msg)

                # Log retry metadata
                self.retry_metadata_service.add_retry_metadata(
                    RetryMetadata(
                        prompt_version=valid_prompt_ver,
                        input_prompt=meal_plan_specs,
                        final_prompt=prompt,
                        model_used=cfg_llm.LLM_PROVIDER,
                        retry_count=i + 1,
                        retry_reason=RetryReason.llm_error,
                        error_message=msg,
                        error_details=None,
                        timestamp=DatetimeUtil.get_current_timestamp(),
                    )
                )
                continue

            # Check validation of JSON for given model schema
            res = ValidationService.validate_model_json(model, json_data)
            if res.valid:
                meal_plan = MealPlan.model_validate(json_data)
                return GenerateMealPlanResult(
                    success=True,
                    meal_plan=meal_plan,
                    raw_output=meal_plan.model_dump(),
                )

            # Log errors
            logger.warning(f"JSON validation failed ({i + 1}/{cfg_llm.MAX_RETRIES}): {json.dumps(json_data, indent=2)}")
            for j, err in enumerate(res.errors):
                logger.warning(
                    f"Error {j + 1}/{len(res.errors)}:\nfield: {err.field}\ncode: {err.code}\nmessage: {err.message}"
                )

            # Add error to return value
            errors.append(res)

            # Log retry metadata
            self.retry_metadata_service.add_retry_metadata(
                RetryMetadata(
                    prompt_version=valid_prompt_ver,
                    input_prompt=meal_plan_specs,
                    final_prompt=prompt,
                    model_used=cfg_llm.LLM_PROVIDER,
                    retry_count=i + 1,
                    retry_reason=RetryReason.validation_failed,
                    error_message="Validation failed",
                    error_details=res.errors,
                    timestamp=DatetimeUtil.get_current_timestamp(),
                )
            )

        # Log error
        logger.error(f"JSON validation failed after max {cfg_llm.MAX_RETRIES} retries")

        return GenerateMealPlanResult(
            success=False,
            errors=errors,
        )

    def add_context(self, qdrant_client: QdrantClient, prompt: str) -> str:
        query_vector = LLMFactory.get(cfg_llm.LLM_PROVIDER).generate_embedding(prompt)

        for i in range(cfg_llm.MAX_RETRIES):
            try:
                points = QdrantService(
                    qdrant_client=qdrant_client,
                    collection_name=cfg_qdrant.COLLECTION_NAME,
                ).search_points(
                    search_query=QdrantSearchQuery(
                        vector=query_vector,
                        limit=cfg_qdrant.QUERY_LIMIT,
                        score_threshold=None,
                        filter_conditions=None,
                        with_payload=True,
                        with_vector=True,
                    )
                )
                if not points:
                    logger.warning("No context found. Skipping context addition.")
                    return prompt

                payloads = [pt.payload for pt in points]

                ret = prompt + "\n\n# Reference Context:\n\n"

                for payload in payloads:
                    ret += "\n" + json.dumps(payload)

                return ret  # noqa: TRY300

            except Exception as e:
                # Log error
                msg = f"Failed to generate Vector DB context from LLM ({i + 1}/{cfg_llm.MAX_RETRIES}): {e}"
                logger.warning(msg)

        msg = f"Failed to add context after max {cfg_llm.MAX_RETRIES} retries"
        logger.error(msg)
        raise RuntimeError(msg)

    def get_all_meal_plans(self) -> list[MealPlanRead]:
        return self.meal_plan_crud.search()

    def get_meal_plan(self, meal_plan_id: PyObjectId) -> MealPlanRead:
        return self.meal_plan_crud.get(obj_id=meal_plan_id)

    def create_meal_plan(
        self,
        create_request: CreateMealPlanRequest,
        client_name: str,
    ) -> MealPlanRead:
        # Create object
        meal_plan_created = self.meal_plan_crud.create(
            obj_create=create_request.to_meal_plan(
                version=Version.initial_version(),
            )
        )

        # Save meal plan version log
        self.version_log_service.save_meal_plan_version_log(
            meal_plan=meal_plan_created,
            client_name=client_name,
            msg=create_request.log_message,
        )

        return meal_plan_created

    def update_meal_plan(
        self,
        update_request: UpdateMealPlanRequest,
        meal_plan_id: PyObjectId,
        client_name: str,
    ) -> MealPlanRead:
        old_meal_plan = self.meal_plan_crud.get(obj_id=meal_plan_id)
        ver = old_meal_plan.version

        # Adjust version
        if update_request.change is ChangeType.MAJOR:
            ver.major += 1
            ver.minor = 0
            ver.patch = 0
        elif update_request.change is ChangeType.MINOR:
            ver.minor += 1
            ver.patch = 0
        elif update_request.change is ChangeType.PATCH:
            ver.patch += 1
        elif update_request.change is None:
            pass
        else:
            msg = f"Invalid update type: {update_request.change}"
            raise ValueError(msg)

        # Update object
        obj_updated = self.meal_plan_crud.update(
            obj_update=update_request.to_meal_plan_update(version=ver),
            obj_id=meal_plan_id,
        )

        # Save version log
        self.version_log_service.save_meal_plan_version_log(
            meal_plan=obj_updated,
            client_name=client_name,
            msg=update_request.log_message,
        )

        return obj_updated

    def delete_meal_plan(self, meal_plan_id: PyObjectId) -> None:
        # Delete object
        self.meal_plan_crud.delete(obj_id=meal_plan_id)

        # Delete version logs
        self.version_log_service.drop_logs(meal_plan_id=meal_plan_id)
