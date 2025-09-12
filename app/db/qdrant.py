from qdrant_client import QdrantClient

from app.core.config.qdrant import config as cfg_qdrant

qdrant_client = QdrantClient(url=cfg_qdrant.QDRANT_URL)
