from enum import StrEnum

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config.fs import config as cfg_fs
from app.core.config.llm import config as cfg_llm
from app.models.common.version import Version
from app.prompts.context.base import PromptContextBase
from app.prompts.context.generate_meal_plan import GenerateMealPlanPromptContext
from app.prompts.context.score_meal_plan import ScoreMealPlanPromptContext


class PromptType(StrEnum):
    GENERATE_FOOD_PLAN = "generate_meal_plan"
    SCORE_FOOD_PLAN = "score_meal_plan"


TEMPLATE_FILENAMES: dict[PromptType, str] = {
    PromptType.GENERATE_FOOD_PLAN: "generate_meal_plan.j2",
    PromptType.SCORE_FOOD_PLAN: "score_meal_plan.j2",
}

PROMPT_CONTEXT_TYPES: dict[PromptType, type] = {
    PromptType.GENERATE_FOOD_PLAN: GenerateMealPlanPromptContext,
    PromptType.SCORE_FOOD_PLAN: ScoreMealPlanPromptContext,
}


class PromptFactory:
    @classmethod
    def render_prompt_by_type(
        cls,
        prompt_type: PromptType,
        context: PromptContextBase,
        prompt_ver: Version,
    ) -> str:
        """
        Render prompt using Jinja2 template.

        `context` type should match the prompt type.
        For example, if prompt type is `generate_meal_plan`, `context` should be `GenerateMealPlanPromptContext`

        Args:
            prompt_type (PromptType): Type of prompt to render.
            context (PromptContextBase): Jinja2 template context.
            prompt_ver (Version): Version of prompt to render.

        Returns:
            str: Rendered prompt.

        Raises:
            ValueError: If context type is invalid for given prompt type.
            ValueError: If template file does not exist.
        """
        # Check if context is proper for given prompt type
        expected_context_type = PROMPT_CONTEXT_TYPES[prompt_type]
        if not isinstance(context, expected_context_type):
            msg = f"Invalid context type. Expected: {expected_context_type}, received: {type(context)}"
            raise TypeError(msg)

        # Get template dir with version
        template_dir = cfg_fs.TEMPLATE_DIR / (prompt_ver.to_str())

        # Get template filename
        template_filename = TEMPLATE_FILENAMES[prompt_type]

        # Check template file existence
        template_filepath = template_dir / template_filename
        if not template_filepath.exists():
            msg = f"Invalid template filepath. Template file not found: {template_filepath}"
            raise ValueError(msg)

        # Load template
        jinja2_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(
                disabled_extensions=(cfg_llm.TEMPLATE_EXT,),
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = jinja2_env.get_template(template_filename)

        # Render and return
        return template.render(context.model_dump())
