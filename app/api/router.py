from enum import StrEnum

from fastapi import APIRouter

from app.api.custom import RouteErrorHandler
from app.api.endpoints.auth import router as router_auth
from app.api.endpoints.crud import router as router_crud
from app.api.endpoints.llm_service import router as router_llm
from app.api.endpoints.meal_plan_service import router as router_meal_plan
from app.api.endpoints.qdrant_service import router as router_qdrant
from app.api.endpoints.validation_service import router as router_validate
from app.api.endpoints.version_service import router as router_version_service

router = APIRouter(route_class=RouteErrorHandler)


class RouterPrefix(StrEnum):
    auth = "/auth"
    llm = "/llm"
    validate = "/validate"
    meal_plan = "/meal_plan"
    version_service = "/version-service"
    qdrant = "/qdrant"
    crud = "/crud"


router.include_router(router=router_auth, prefix=RouterPrefix.auth.value)
router.include_router(router=router_llm, prefix=RouterPrefix.llm.value)
router.include_router(router=router_validate, prefix=RouterPrefix.validate.value)
router.include_router(router=router_meal_plan, prefix=RouterPrefix.meal_plan.value)
router.include_router(router=router_version_service, prefix=RouterPrefix.version_service.value)
router.include_router(router=router_qdrant, prefix=RouterPrefix.qdrant.value)
router.include_router(router=router_crud, prefix=RouterPrefix.crud.value)
