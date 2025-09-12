from collections.abc import Generator
from typing import Any

from pymongo.database import Database

from app.db.mongo import pymongo_db


def get_database() -> Generator[Database[dict[str, Any]], None, None]:
    """
    Get database connection

    Returns:
        Database connection
    """
    yield pymongo_db
