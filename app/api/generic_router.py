from typing import Annotated, Any, TypeVar

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from pymongo.database import Database

from app.api.dependency import get_db
from app.models.common.generic_crud import GenericCRUDBase
from app.models.common.object_id import PyObjectId
from app.schemas.errors import NotFoundException


class GenericRouter[
    CRUDClass: GenericCRUDBase,  # type: ignore  # noqa: PGH003
    DBSchema: BaseModel,
    ReadSchema: BaseModel,
    UpdateSchema: BaseModel,
]:
    @classmethod
    def create_crud_router(
        cls,
        name: str,
        crud: type[CRUDClass],
        db_schema: type[DBSchema],
        read_schema: type[ReadSchema],
        update_schema: type[UpdateSchema],
        filter_schema: TypeVar("FilterSchema") | None = None,  # type: ignore  # noqa: PGH003
    ) -> APIRouter:
        """
        Build a CRUD router for a given model/service.
        """
        router = APIRouter(tags=[f"CRUD: '{name}' Model"])

        # GET all
        @router.get(
            "/",
            description=f"""
This endpoint returns all **{db_schema.__name__}** instances.

### Authentication
- **SuperAdmin**

### Request Query Parameters
- `None`

### Request Body
- `None`

### Response
- `list[{read_schema.__name__}]`: The retrieved instances.""",
        )
        def get_all(
            db: Annotated[Database[dict[str, Any]], Depends(get_db)],
        ) -> list[read_schema]:  # type: ignore  # noqa: PGH003
            return crud(db=db).search()  # type: ignore  # noqa: PGH003

        # GET one
        @router.get(
            "/{obj_id}",
            description=f"""
This endpoint returns single **{db_schema.__name__}** instance.

### Authentication
- **SuperAdmin**

### Request Query Parameters
- **obj_id** (`str`): The ID of the `{db_schema.__name__}` to get.

### Request Body
- `None`

### Response
- `{read_schema.__name__}`: The retrieved instance.""",
            responses={
                **NotFoundException.get_response(),
            },
        )
        def get(
            db: Annotated[Database[dict[str, Any]], Depends(get_db)],
            obj_id: PyObjectId,
        ) -> read_schema:  # type: ignore  # noqa: PGH003
            return crud(db=db).get(obj_id=obj_id)  # type: ignore  # noqa: PGH003

        # CREATE
        @router.post(
            "/",
            description=f"""
This endpoint creates a new **{db_schema.__name__}** instance.

### Authentication
- **SuperAdmin**

### Request Query Parameters
- `None`

### Request Body
- `{db_schema.__name__}`: The new `{db_schema.__name__}` data to create.

### Response
- `{read_schema.__name__}`: The created instance.""",
        )
        def create(
            db: Annotated[Database[dict[str, Any]], Depends(get_db)],
            obj_create: db_schema,  # type: ignore  # noqa: PGH003
        ) -> read_schema:  # type: ignore  # noqa: PGH003
            return crud(db=db).create(obj_create=obj_create)  # type: ignore  # noqa: PGH003

        # UPDATE
        @router.put(
            "/{obj_id}",
            description=f"""
This endpoint updates single **{db_schema.__name__}** instance.

### Authentication
- **SuperAdmin**

### Request Query Parameters
- **obj_id** (`PyObjectId`): The ID of the `{db_schema.__name__}` instance to update.

### Request Body
- `{update_schema.__name__}`: The updated `{db_schema.__name__}` data.

### Response
- `{read_schema.__name__}`: The updated instance.""",
            responses={
                **NotFoundException.get_response(),
            },
        )
        def update(
            db: Annotated[Database[dict[str, Any]], Depends(get_db)],
            obj_update: update_schema,  # type: ignore  # noqa: PGH003
            obj_id: PyObjectId,
        ) -> read_schema:  # type: ignore  # noqa: PGH003
            return crud(db=db).update(  # type: ignore  # noqa: PGH003
                obj_update=obj_update,
                obj_id=obj_id,
            )

        # DELETE
        @router.delete(
            "/{obj_id}",
            description=f"""
This endpoint deletes single **{db_schema.__name__}** instance.

### Authentication
- **SuperAdmin**

### Request Query Parameters
- **obj_id** (`str`): The ID of the `{db_schema.__name__}` instance to delete.

### Request Body
- `None`

### Response
- `None`""",
            responses={
                **NotFoundException.get_response(),
            },
        )
        def delete(
            db: Annotated[Database[dict[str, Any]], Depends(get_db)],
            obj_id: PyObjectId,
        ) -> None:
            crud(db=db).delete(obj_id=obj_id)  # type: ignore  # noqa: PGH003

        # SEARCH if filter enabled
        if filter_schema:

            @router.post("/search")
            def search(
                db: Annotated[Database[dict[str, Any]], Depends(get_db)],
                obj_filter: filter_schema,  # type: ignore  # noqa: PGH003
            ) -> list[read_schema]:  # type: ignore  # noqa: PGH003
                return crud(db=db).search(query=obj_filter.query())  # type: ignore  # noqa: PGH003

        return router
