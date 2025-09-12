import pytest
from fastapi import HTTPException, status

from app.models.auth.api_key import ApiKey, ApiKeyCRUD, ApiKeyUpdate
from app.models.auth.client import ClientCRUD
from app.schemas.auth.api_key import CreateApiKeyRequest, UpdateApiKeyRequest
from app.services.auth.api_key_service import ApiKeyService
from app.services.auth.auth_service import AuthService
from app.utils.rand import RandUtil


@pytest.mark.usefixtures("client_creates")
def test_create_api_key(
    api_key_crud: ApiKeyCRUD,
    api_key_service: ApiKeyService,
    api_key_creates: list[ApiKey],
    client_crud: ClientCRUD,
) -> None:
    client_list = client_crud.search()
    api_key_crud.clear()
    for obj_create in api_key_creates:
        client_id = client_list[RandUtil.get_int(up=len(client_list))].id
        resp = api_key_service.create_api_key(
            client_id=client_id,
            create_request=CreateApiKeyRequest(
                key_name=obj_create.key_name,
                description=obj_create.description,
                access_policy=obj_create.access_policy,
            ),
        )

        assert resp.client_id == client_id
        assert resp.key_name == obj_create.key_name
        assert resp.description == obj_create.description

        api_key_created = api_key_crud.get(obj_id=resp.key_id)

        assert resp.key_name == api_key_created.key_name
        assert resp.description == api_key_created.description
        assert resp.access_policy == api_key_created.access_policy

        key_id = resp.key_plain.split(".")[0]
        assert str(resp.key_id) == key_id

        key_secret_plain = resp.key_plain.split(".")[1]
        assert key_secret_plain.startswith(api_key_created.key_secret_front)
        assert AuthService.verify_api_key(key_secret_plain, api_key_created.key_secret_hash)

    assert api_key_crud.count() == len(api_key_creates)


@pytest.mark.usefixtures("api_key_creates")
def test_update_api_key(
    api_key_crud: ApiKeyCRUD,
    api_key_service: ApiKeyService,
) -> None:
    obj_list = api_key_crud.search()
    for obj in obj_list:
        new_description = RandUtil.get_str()
        resp = api_key_service.update_api_key(
            api_key_id=obj.id,
            update_request=UpdateApiKeyRequest(
                description=new_description,
            ),
        )
        assert resp.description == new_description

        obj_updated = api_key_crud.get(obj_id=obj.id)
        assert obj_updated.description == new_description


@pytest.mark.usefixtures("api_key_creates")
def test_get_api_key(
    api_key_crud: ApiKeyCRUD,
    api_key_service: ApiKeyService,
) -> None:
    obj_list = api_key_crud.search()
    for obj in obj_list:
        resp = api_key_service.get_api_key(api_key_id=obj.id)

        assert resp.client_id == obj.client_id
        assert resp.key_name == obj.key_name
        assert resp.description == obj.description


@pytest.mark.usefixtures("api_key_creates")
def test_delete_api_key(api_key_crud: ApiKeyCRUD, api_key_service: ApiKeyService) -> None:
    obj_list = api_key_crud.search()
    api_key_id = obj_list[RandUtil.get_int(up=len(obj_list))].id

    api_key_service.delete_api_key(api_key_id)
    assert len(obj_list) - 1 == api_key_crud.count()

    try:
        api_key_crud.get(api_key_id)
        msg = "ApiKey not deleted"
        raise AssertionError(msg)
    except HTTPException as ex:
        assert ex.status_code == status.HTTP_404_NOT_FOUND  # noqa: PT017


@pytest.mark.usefixtures("api_key_creates")
def test_delete_client_api_keys(
    api_key_crud: ApiKeyCRUD,
    api_key_service: ApiKeyService,
) -> None:
    api_keys = api_key_crud.search()
    api_key_count = len(api_keys)

    client_keys_count = RandUtil.get_int(lo=1, up=api_key_count - 1)
    assert client_keys_count > 0

    client_1_id = RandUtil.get_mongo_id()

    for i in range(api_key_count):
        if i >= client_keys_count:
            api_key_crud.update(
                obj_update=ApiKeyUpdate(
                    client_id=client_1_id,
                ),
                obj_id=api_keys[i].id,
            )

    api_key_service.delete_client_api_keys(client_id=client_1_id)

    assert client_keys_count == api_key_crud.count()
