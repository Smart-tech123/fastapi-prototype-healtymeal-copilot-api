import pytest
from fastapi import HTTPException, status

from app.models.auth.client import Client, ClientCRUD, ClientUpdate
from app.models.auth.tenant import TenantCRUD
from app.schemas.auth.client import CreateClientRequest, UpdateClientRequest
from app.services.auth.auth_service import AuthService
from app.services.auth.client_service import ClientService
from app.utils.rand import RandUtil


@pytest.mark.usefixtures("tenant_creates")
def test_create_client(
    client_crud: ClientCRUD,
    client_service: ClientService,
    client_creates: list[Client],
    tenant_crud: TenantCRUD,
) -> None:
    tenant_list = tenant_crud.search()
    client_crud.clear()
    for obj_create in client_creates:
        tenant_id = tenant_list[RandUtil.get_int(up=len(tenant_list))].id
        resp = client_service.create_client(
            create_request=CreateClientRequest(
                tenant_id=tenant_id,
                client_name=obj_create.client_name,
                description=obj_create.description,
                access_policy=obj_create.access_policy,
            ),
        )

        assert resp.tenant_id == tenant_id
        assert resp.client_name == obj_create.client_name
        assert resp.description == obj_create.description
        assert resp.access_policy == obj_create.access_policy

        client_created = client_crud.get(obj_id=resp.client_id)

        assert resp.client_name == client_created.client_name
        assert resp.description == client_created.description
        assert resp.access_policy == client_created.access_policy
        assert AuthService.verify_password(
            resp.client_secret_plain,
            client_created.client_secret_hash,
        )

    assert client_crud.count() == len(client_creates)


@pytest.mark.usefixtures("client_creates")
def test_update_client(
    client_crud: ClientCRUD,
    client_service: ClientService,
) -> None:
    obj_list = client_crud.search()
    for obj in obj_list:
        new_description = RandUtil.get_str()
        resp = client_service.update_client(
            client_id=obj.id,
            update_request=UpdateClientRequest(
                description=new_description,
            ),
        )
        assert resp.description == new_description

        obj_updated = client_crud.get(obj_id=obj.id)
        assert obj_updated.description == new_description


@pytest.mark.usefixtures("client_creates")
def test_get_client(
    client_crud: ClientCRUD,
    client_service: ClientService,
) -> None:
    obj_list = client_crud.search()
    for obj in obj_list:
        resp = client_service.get_client(client_id=obj.id)

        assert resp.tenant_id == obj.tenant_id
        assert resp.client_name == obj.client_name
        assert resp.description == obj.description


@pytest.mark.usefixtures("client_creates")
def test_get_by_client_name(
    client_crud: ClientCRUD,
    client_service: ClientService,
) -> None:
    obj_list = client_crud.search()
    for obj in obj_list:
        client = client_service.get_by_client_name(client_name=obj.client_name)

        assert client is not None
        assert client.tenant_id == obj.tenant_id
        assert client.client_name == obj.client_name
        assert client.description == obj.description


@pytest.mark.usefixtures("client_creates")
def test_delete_client(client_crud: ClientCRUD, client_service: ClientService) -> None:
    obj_list = client_crud.search()
    client_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    client_service.delete_client(client_id)
    assert len(obj_list) - 1 == client_crud.count()

    try:
        client_crud.get(client_id)
        msg = "Client not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017


@pytest.mark.usefixtures("client_creates")
def test_delete_tenant_clients(
    client_crud: ClientCRUD,
    client_service: ClientService,
) -> None:
    clients = client_crud.search()
    client_count = len(clients)

    tenant_client_count = RandUtil.get_int(lo=1, up=client_count - 1)
    assert tenant_client_count > 0

    tenant_id = RandUtil.get_mongo_id()

    for i in range(client_count):
        if i >= tenant_client_count:
            client_crud.update(
                obj_update=ClientUpdate(
                    tenant_id=tenant_id,
                ),
                obj_id=clients[i].id,
            )

    client_service.delete_tenant_clients(tenant_id=tenant_id)

    assert tenant_client_count == client_crud.count()


@pytest.mark.usefixtures("client_creates")
def test_rotate(
    client_crud: ClientCRUD,
    client_service: ClientService,
) -> None:
    obj_list = client_crud.search()
    client_id = obj_list[RandUtil.get_int(up=len(obj_list))].id
    new_secret = client_service.rotate(client_id=client_id)

    obj = client_crud.get(obj_id=client_id)
    assert obj is not None
    assert new_secret != obj.client_secret_hash
    assert AuthService.verify_password(new_secret, obj.client_secret_hash)
