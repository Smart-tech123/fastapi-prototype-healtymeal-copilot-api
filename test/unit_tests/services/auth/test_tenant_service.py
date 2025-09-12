import pytest
from fastapi import HTTPException, status

from app.models.auth.tenant import Tenant, TenantCRUD
from app.schemas.auth.tenant import CreateTenantRequest, UpdateTenantRequest
from app.services.auth.tenant_service import TenantService
from app.utils.rand import RandUtil


def test_create_tenant(
    tenant_crud: TenantCRUD,
    tenant_service: TenantService,
    tenant_creates: list[Tenant],
) -> None:
    tenant_crud.clear()
    for obj_create in tenant_creates:
        resp = tenant_service.create_tenant(
            create_request=CreateTenantRequest(
                tenant_name=obj_create.tenant_name,
                description=obj_create.description,
                access_policy=obj_create.access_policy,
            ),
        )

        assert resp.tenant_name == obj_create.tenant_name
        assert resp.description == obj_create.description
        assert resp.access_policy == obj_create.access_policy

    assert tenant_crud.count() == len(tenant_creates)


@pytest.mark.usefixtures("tenant_creates")
def test_update_tenant(
    tenant_crud: TenantCRUD,
    tenant_service: TenantService,
) -> None:
    obj_list = tenant_crud.search()
    for obj in obj_list:
        new_description = RandUtil.get_str()
        resp = tenant_service.update_tenant(
            tenant_id=obj.id,
            update_request=UpdateTenantRequest(
                description=new_description,
            ),
        )
        assert resp.description == new_description

        obj_updated = tenant_crud.get(obj_id=obj.id)
        assert obj_updated.description == new_description


@pytest.mark.usefixtures("tenant_creates")
def test_get_tenant(
    tenant_crud: TenantCRUD,
    tenant_service: TenantService,
) -> None:
    obj_list = tenant_crud.search()
    for obj in obj_list:
        resp = tenant_service.get_tenant(tenant_id=obj.id)

        assert resp.tenant_id == obj.id
        assert resp.tenant_name == obj.tenant_name
        assert resp.description == obj.description


@pytest.mark.usefixtures("tenant_creates")
def test_delete_tenant(tenant_crud: TenantCRUD, tenant_service: TenantService) -> None:
    obj_list = tenant_crud.search()
    tenant_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    tenant_service.delete_tenant(tenant_id)
    assert len(obj_list) - 1 == tenant_crud.count()

    try:
        tenant_crud.get(tenant_id)
        msg = "Tenant not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017


@pytest.mark.usefixtures("tenant_creates")
def test_rotate_key(tenant_crud: TenantCRUD, tenant_service: TenantService) -> None:
    obj_list = tenant_crud.search()
    tenant = obj_list[RandUtil.get_int(up=len(obj_list))]
    key_count_before = len(tenant.keys)

    tenant_service.rotate(tenant.id)
    tenant_rotated = tenant_crud.get(tenant.id)

    key_count_after = len(tenant_rotated.keys)

    assert key_count_before + 1 == key_count_after
