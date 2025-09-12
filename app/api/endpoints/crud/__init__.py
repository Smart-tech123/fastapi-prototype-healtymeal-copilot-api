from enum import StrEnum

from fastapi import APIRouter, Security

from app.api.custom import RouteErrorHandler
from app.api.dependency import get_super_admin_client
from app.api.endpoints.crud.api_key import router as router_api_key
from app.api.endpoints.crud.audit_log import router as router_audit_log
from app.api.endpoints.crud.client import router as router_client
from app.api.endpoints.crud.meal_plan import router as router_meal_plan
from app.api.endpoints.crud.retry_metadata import router as router_retry_metadata
from app.api.endpoints.crud.tenant import router as router_tenant
from app.api.endpoints.crud.version_log import router as router_version_log
from app.schemas.errors import ErrorCode401, UnauthorizedException

router = APIRouter(
    route_class=RouteErrorHandler,
    dependencies=[Security(get_super_admin_client)],
    responses={
        **UnauthorizedException.get_response(
            error_code=ErrorCode401.INVALID_SUPER_ADMIN_KEY,
            message="Unauthorized SuperAdmin",
        ),
    },
)


class RouterPrefix(StrEnum):
    tenant = "/tenant"
    client = "/client"
    api_key = "/api_key"
    version_log = "/version-log"
    retry_metadata = "/retry-metadata"
    audit_log = "/audit-log"
    meal_plan = "/meal_plan"


router.include_router(router=router_tenant, prefix=RouterPrefix.tenant.value)
router.include_router(router=router_client, prefix=RouterPrefix.client.value)
router.include_router(router=router_api_key, prefix=RouterPrefix.api_key.value)
router.include_router(router=router_version_log, prefix=RouterPrefix.version_log.value)
router.include_router(router=router_retry_metadata, prefix=RouterPrefix.retry_metadata.value)
router.include_router(router=router_audit_log, prefix=RouterPrefix.audit_log.value)
router.include_router(router=router_meal_plan, prefix=RouterPrefix.meal_plan.value)
