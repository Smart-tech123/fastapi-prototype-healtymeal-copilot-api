from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, Request, Response
from fastapi.security import SecurityScopes
from loguru import logger
from pymongo.database import Database
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.dependency import get_current_api_key, get_current_client, get_super_admin_client
from app.api.router import RouterPrefix
from app.core.config.auth import config as cfg_auth
from app.core.config.llm import LLMProvider
from app.core.config.llm import config as cfg_llm
from app.models.audit_log import AuditLog, AuditLogCRUD
from app.models.auth.client import ClientCRUD, ClientRead
from app.models.auth.tenant import TenantCRUD
from app.models.common.version import Version
from app.utils.datetime import DatetimeUtil
from app.utils.http import HttpUtil

if TYPE_CHECKING:
    from app.models.auth.api_key import ApiKeyRead
    from app.models.auth.tenant import TenantRead


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, db: Database[dict[str, Any]]) -> None:
        super().__init__(app=app)
        self.db = db

    async def dispatch(self, request: Request, call_next) -> Response:  # type:ignore  # noqa: ANN001, PGH003
        start_tstamp = DatetimeUtil.get_current_timestamp()

        # Parse authentication parameters
        api_key_header: str | None = request.headers.get(cfg_auth.API_KEY_HEADER)  # custom header
        super_admin_key: str | None = request.query_params.get(
            cfg_auth.SUPER_ADMIN_FIELD
        )  # query param ?superAdminKey=...
        auth_header: str | None = request.headers.get("authorization")  # will be "Bearer <token>"

        bearer_token = None
        if auth_header and auth_header.startswith("Bearer "):
            bearer_token = auth_header.split(" ", 1)[1]

        # Ignore if no authentication parameters are provided
        if not api_key_header and not bearer_token and not super_admin_key:
            logger.warning("No authentication parameters provided. Skipping audit middleware.")
            response: Response = await call_next(request)
            return response

        # Prepare CRUD instances
        client_crud = ClientCRUD(db=self.db)
        tenant_crud = TenantCRUD(db=self.db)

        current_tenant: TenantRead | None = None
        current_client: ClientRead | None = None
        current_api_key: ApiKeyRead | None = None

        # Try to get current client from api key
        if api_key_header:
            try:
                current_api_key = get_current_api_key(
                    request=request,
                    security_scopes=SecurityScopes(scopes=[]),
                    api_key_header=api_key_header,
                    db=self.db,
                )
                current_client = client_crud.get(obj_id=current_api_key.client_id)
            except:  # noqa: E722
                logger.error(f"Failed to get client from API key: {api_key_header}")

        # Try to get current client from authorization token
        if bearer_token:
            try:
                current_client = get_current_client(
                    request=request,
                    security_scopes=SecurityScopes(scopes=[]),
                    db=self.db,
                    super_admin_qeury=super_admin_key,
                    token=bearer_token,
                    api_key_header=api_key_header,
                )
            except:  # noqa: E722
                logger.error(f"Failed to get client from authorization token: {bearer_token}")

        # Try to get current client from super admin query
        if super_admin_key:
            try:
                current_client = get_super_admin_client(db=self.db, super_admin_query=super_admin_key)
            except:  # noqa: E722
                logger.error(f"Failed to get super admin client from key: {super_admin_key}")

        # Try to get current tenant
        if current_client:
            current_tenant = tenant_crud.get(obj_id=current_client.tenant_id)
            if not current_tenant:
                logger.error(f"Failed to get tenant from client ({current_client.id}): {current_client.tenant_id}")

        # Parse LLM info
        input_prompt: str | None = None
        prompt_version: Version | None = None
        model_used: LLMProvider | None = None
        if request.url.path.startswith(RouterPrefix.llm.value):
            request_json = await request.json()
            if isinstance(request_json, dict):
                input_prompt = request_json.get("prompt")
                prompt_version_dict = request_json.get("prompt_version")
                if prompt_version_dict:
                    prompt_version = Version.model_validate(prompt_version_dict)
                model_used = cfg_llm.LLM_PROVIDER
                prompt_version = cfg_llm.DEFAULT_PROMPT_VERSION

        # Call next
        response = await call_next(request)

        # Create audit log
        audit_log_crud = AuditLogCRUD(db=self.db)
        audit_log_crud.create(
            obj_create=AuditLog(
                # who
                tenant_id=current_tenant.id if current_tenant else None,
                tenant_name=current_tenant.tenant_name if current_tenant else None,
                client_id=current_client.id if current_client else None,
                client_name=current_client.client_name if current_client else None,
                api_key_id=current_api_key.id if current_api_key else None,
                api_key_name=current_api_key.key_name if current_api_key else None,
                # llm
                input_prompt=input_prompt,
                prompt_version=prompt_version,
                model_used=model_used,
                # request
                request_path=str(request.url.path),
                request_query=str(request.url.query),
                request_method=request.method,
                remote_address=HttpUtil.get_remote_address(request),
                # response
                response_status=response.status_code,
                latency_ms=DatetimeUtil.get_current_timestamp() - start_tstamp,
            )
        )

        return response
