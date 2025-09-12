from typing import Any, override

from pydantic import BaseModel
from pymongo import IndexModel
from pymongo.database import Database

from app.models.common.base_models import TimeStampedModel
from app.models.common.object_id import PyObjectId
from app.schemas.errors import ErrorCode404, NotFoundException
from app.utils.datetime import DatetimeUtil


class GenericCRUDBase[DBSchema: BaseModel, ReadSchema: BaseModel, UpdateSchema: BaseModel]:
    """
    Base class for CRUD operations.

    Operations:
        get: Get an object by ID.
        search: Search for objects that match the query.
        count: Count the number of objects that match the query.
        create: Create a new object.
        update: Update an object by ID.
        delete: Delete an object by ID.
        delete_many: Delete all objects that match the query.
        clear: Clear all objects in the collection.
    """

    def __init__(
        self,
        db: Database[dict[str, Any]],
        collection_name: str,
        read_schema: type[ReadSchema],
        indexes: list[list[str]] | None = None,
    ) -> None:
        """
        Initialize the CRUDBase class.

        Args:
            db (Database[dict[str, Any]]): The database to use.
            collection_name (str): The name of the collection to use.
            read_schema (type[ReadSchema]): The schema to use for reading objects.
        """
        self.db = db
        self.coll = db.get_collection(collection_name)
        self.read_schema = read_schema
        self.indexes = indexes

    def create_indexes(self) -> None:
        if self.indexes:
            self.coll.create_indexes(
                [
                    IndexModel(
                        index,
                        unique=True,
                    )
                    for index in self.indexes
                ]
            )

    def get(self, obj_id: PyObjectId | str) -> ReadSchema:
        """
        Get an object by ID.

        Args:
            obj_id (PyObjectId | str): The ID of the object to get.

        Returns:
            ReadSchema: The object.

        Exceptions:
            HTTPException: If the object is not found.
        """
        doc = self.coll.find_one({"_id": PyObjectId(obj_id)})
        if doc is None:
            raise NotFoundException(
                error_code=ErrorCode404.NOT_FOUND,
                message="Item not found",
            )
        return self.read_schema.model_validate(doc)

    def search(self, query: dict[str, Any] | None = None) -> list[ReadSchema]:
        """
        Search for objects that match the query.

        Args:
            query (dict[str, Any]): The query to match objects.

        Returns:
            list[ReadSchema]: A list of objects that match the query.
        """
        cursor = self.coll.find(query or {})
        return [self.read_schema.model_validate(doc) for doc in cursor]

    def count(self, query: dict[str, Any] | None = None) -> int:
        """
        Count the number of objects that match the query.

        Args:
            query (dict[str, Any]): The query to match objects.

        Returns:
            int: The number of objects that match the query.
        """
        return self.coll.count_documents(query or {})

    def create(self, obj_create: DBSchema) -> ReadSchema:
        """
        Create a new object.

        Args:
            obj_create (DBSchema): The object to create.

        Returns:
            ReadSchema: The created object.
        """
        obj_dict = obj_create.model_dump()
        res = self.coll.insert_one(obj_dict)
        obj_dict["_id"] = res.inserted_id
        return self.read_schema.model_validate(obj_dict)

    def update(self, obj_id: PyObjectId | str, obj_update: UpdateSchema) -> ReadSchema:
        """
        Update an object by ID.

        Args:
            obj_update (UpdateSchema): The updated object.
            obj_id (PyObjectId): The ID of the object to update.

        Returns:
            ReadSchema: The updated object.

        Exceptions:
            HTTPException: If the object is not found.
        """
        obj_dict = obj_update.model_dump(exclude_unset=True)
        res = self.coll.update_one({"_id": PyObjectId(obj_id)}, {"$set": obj_dict})

        if res.matched_count == 0:
            raise NotFoundException(
                error_code=ErrorCode404.NOT_FOUND,
                message="Item not found",
            )

        doc = self.coll.find_one({"_id": PyObjectId(obj_id)})
        return self.read_schema.model_validate(doc)

    def delete(self, obj_id: PyObjectId | str) -> None:
        """
        Delete an object by ID.

        Args:
            obj_id (PyObjectId | str): The ID of the object to delete.

        Exceptions:
            HTTPException: If the object is not found.
        """
        res = self.coll.delete_one({"_id": PyObjectId(obj_id)})
        if res.deleted_count == 0:
            raise NotFoundException(
                error_code=ErrorCode404.NOT_FOUND,
                message="Item not found",
            )

    def delete_many(self, query: dict[str, Any]) -> int:
        """
        Delete all objects that match the query.

        Args:
            query (dict[str, Any]): The query to match objects.

        Returns:
            int: The number of deleted objects.
        """
        res = self.coll.delete_many(query)
        return res.deleted_count

    def clear(self) -> None:
        """
        Clear all objects in the collection.
        """
        self.coll.delete_many({})


class TimeStampedCRUDBase[
    DBSchema: TimeStampedModel,
    ReadSchema: BaseModel,
    UpdateSchema: BaseModel,
](
    GenericCRUDBase[
        DBSchema,
        ReadSchema,
        UpdateSchema,
    ]
):
    def __init__(
        self,
        db: Database[dict[str, Any]],
        collection_name: str,
        read_schema: type[ReadSchema],
        indexes: list[list[str]] | None = None,
    ) -> None:
        super().__init__(db, collection_name, read_schema, indexes)

    @override
    def create(self, obj_create: DBSchema) -> ReadSchema:
        """
        Create a new object.

        Args:
            obj_create (CreateSchema): The object to create.

        Returns:
            ReadSchema: The created object.
        """
        obj_dict = obj_create.model_dump()

        # Set created_at and updated_at
        obj_dict[TimeStampedModel.Field.created_at] = DatetimeUtil.get_current_timestamp()

        # Insert
        res = self.coll.insert_one(obj_dict)
        obj_dict["_id"] = res.inserted_id
        return self.read_schema.model_validate(obj_dict)

    @override
    def update(self, obj_id: PyObjectId | str, obj_update: UpdateSchema) -> ReadSchema:
        obj_dict = obj_update.model_dump(exclude_unset=True)

        # Set updated_at
        obj_dict[TimeStampedModel.Field.updated_at] = DatetimeUtil.get_current_timestamp()

        # Update
        res = self.coll.update_one({"_id": PyObjectId(obj_id)}, {"$set": obj_dict})
        if res.matched_count == 0:
            raise NotFoundException(
                error_code=ErrorCode404.NOT_FOUND,
                message="Item not found",
            )

        return self.get(obj_id=obj_id)
