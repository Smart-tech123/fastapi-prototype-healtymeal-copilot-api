from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config.mongo import config as cfg_mongo

pymongo_client: MongoClient[dict[str, Any]] = MongoClient(
    str(cfg_mongo.MONGO_URL),
    document_class=dict[str, Any],
)

pymongo_db: Database[dict[str, Any]] = pymongo_client.get_database(cfg_mongo.DB_NAME)
