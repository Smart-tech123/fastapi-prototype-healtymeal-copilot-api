from app.models.auth.client import Client, ClientRead
from app.models.auth.common.access_policy import AccessPolicy
from app.models.auth.tenant import Tenant, TenantRead, TenantStatus
from app.utils.rand import RandUtil


def mocked_is_super_admin() -> None:
    pass


def mocked_get_current_tenant() -> TenantRead:
    return TenantRead.model_validate(
        {
            "_id": RandUtil.get_mongo_id(),
            Tenant.Field.tenant_name: RandUtil.get_str(),
            Tenant.Field.description: RandUtil.get_str(),
            Tenant.Field.status: TenantStatus.ACTIVE,
            Tenant.Field.access_policy: AccessPolicy(
                allowed_ips=[],
                endpoints=[],
                scopes=[],
                rate_limit_per_min=0,
            ),
        }
    )


def mocked_get_current_client() -> ClientRead:
    return ClientRead.model_validate(
        {
            "_id": RandUtil.get_mongo_id(),
            Client.Field.tenant_id: RandUtil.get_mongo_id(),
            Client.Field.client_secret_hash: RandUtil.get_str(),
            Client.Field.client_name: RandUtil.get_str(),
            Client.Field.description: RandUtil.get_str(),
            Client.Field.access_policy: AccessPolicy(
                allowed_ips=[],
                endpoints=[],
                scopes=[],
                rate_limit_per_min=0,
            ),
        }
    )


def mocked_rate_limited() -> str:
    return "inf/minute"
