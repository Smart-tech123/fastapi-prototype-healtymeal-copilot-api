from app.api.generic_router import GenericRouter
from app.models.auth.client import (
    Client,
    ClientCRUD,
    ClientRead,
    ClientUpdate,
)

router = GenericRouter[
    ClientCRUD,
    Client,
    ClientRead,
    ClientUpdate,
].create_crud_router(
    name="Client",
    crud=ClientCRUD,
    db_schema=Client,
    read_schema=ClientRead,
    update_schema=ClientUpdate,
)
