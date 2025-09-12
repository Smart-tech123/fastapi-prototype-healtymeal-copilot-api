from app.models.auth.api_key import ApiKeyCRUD, ApiKeyRead
from app.models.auth.client import ClientCRUD, ClientRead
from app.models.auth.common.access_policy import AccessPolicy
from app.models.auth.tenant import TenantCRUD, TenantRead, TenantStatus, TenantUpdate
from app.schemas.auth.api_key import CreateApiKeyRequest, CreateApiKeyResponse
from app.schemas.auth.client import CreateClientRequest, CreateClientResponse
from app.schemas.auth.tenant import CreateTenantRequest, CreateTenantResponse
from app.services.auth.api_key_service import ApiKeyService
from app.services.auth.client_service import ClientService
from app.services.auth.tenant_service import TenantService


def prepare_accounts(
    tenant_service: TenantService,
    tenant_crud: TenantCRUD,
    tenant_name: str,
    tenant_description: str,
    tenant_policy: AccessPolicy,
    client_service: ClientService,
    client_crud: ClientCRUD,
    client_name: str,
    client_description: str,
    client_policy: AccessPolicy,
    api_key_service: ApiKeyService,
    api_key_crud: ApiKeyCRUD,
    api_key_name: str,
    api_key_description: str,
    api_key_policy: AccessPolicy,
) -> tuple[
    CreateTenantResponse,
    CreateClientResponse,
    CreateApiKeyResponse,
    TenantRead,
    ClientRead,
    ApiKeyRead,
]:
    # Create tenant
    tenant_resp = tenant_service.create_tenant(
        create_request=CreateTenantRequest(
            tenant_name=tenant_name,
            description=tenant_description,
            access_policy=tenant_policy,
        )
    )
    tenant_created = tenant_crud.get(obj_id=tenant_resp.tenant_id)

    # Activate tenant
    tenant_crud.update(
        obj_id=tenant_created.id,
        obj_update=TenantUpdate(status=TenantStatus.ACTIVE),
    )

    # Create client
    client_resp = client_service.create_client(
        create_request=CreateClientRequest(
            tenant_id=tenant_resp.tenant_id,
            client_name=client_name,
            description=client_description,
            access_policy=client_policy,
        )
    )
    client_created = client_crud.get(obj_id=client_resp.client_id)

    # Create api key
    api_key_resp = api_key_service.create_api_key(
        client_id=client_resp.client_id,
        create_request=CreateApiKeyRequest(
            key_name=api_key_name,
            description=api_key_description,
            access_policy=api_key_policy,
        ),
    )
    api_key_created = api_key_crud.get(obj_id=api_key_resp.key_id)

    return (
        tenant_resp,
        client_resp,
        api_key_resp,
        tenant_created,
        client_created,
        api_key_created,
    )
