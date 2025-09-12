from enum import StrEnum

from fastapi import APIRouter

from app.api.custom import RouteErrorHandler
from app.api.endpoints.auth.api_key import router as router_api_key
from app.api.endpoints.auth.client import router as router_client
from app.api.endpoints.auth.tenant import router as router_tenant

router = APIRouter(route_class=RouteErrorHandler)


class RouterPrefix(StrEnum):
    tenant = "/tenant"
    client = "/client"
    api_key = "/api_key"


router.include_router(router=router_tenant, prefix=RouterPrefix.tenant.value)
router.include_router(router=router_client, prefix=RouterPrefix.client.value)
router.include_router(router=router_api_key, prefix=RouterPrefix.api_key.value)
