from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
)

from app.core.config.qdrant import config as cfg_qdrant
from app.schemas.errors import ErrorCode404, NotFoundException
from app.schemas.qdrant import (
    QdrantPoint,
    QdrantPointRead,
    QdrantPointUpdate,
    QdrantSearchQuery,
    QdrantSearchResult,
)
from app.utils.uuid import UuidUtil


class QdrantService:
    def __init__(self, qdrant_client: QdrantClient, collection_name: str) -> None:
        self.client = qdrant_client
        self.collection_name = collection_name

        # Create collection if it doesn't exist
        existing_collections = self.client.get_collections().collections
        if self.collection_name not in [col.name for col in existing_collections]:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=cfg_qdrant.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )

    # Point Operations
    def create_point(self, point_data: QdrantPoint) -> QdrantPointRead:
        """Create a new point"""
        point_id = str(UuidUtil.make_uuid())
        point = PointStruct(
            id=point_id,
            vector=point_data.vector,
            payload=point_data.payload,
        )

        self.client.upsert(collection_name=self.collection_name, points=[point])

        return QdrantPointRead(
            id=point_id,
            vector=point_data.vector,
            payload=point_data.payload,
        )

    def get_all_points(self) -> list[QdrantPointRead]:
        """Get all points"""
        points, next_page_offset = self.client.scroll(
            collection_name=self.collection_name,
            limit=100,  # Number of points per batch
            with_payload=True,
            with_vectors=True,
        )

        all_points = points

        # Continue scrolling if there are more points
        while next_page_offset is not None:
            points, next_page_offset = self.client.scroll(
                collection_name=self.collection_name,
                offset=next_page_offset,
                limit=100,
                with_payload=True,
                with_vectors=True,
            )
            all_points.extend(points)

        return [
            QdrantPointRead(
                id=point.id,
                vector=point.vector,
                payload=point.payload,
            )
            for point in all_points
        ]

    def get_point(self, point_id: str) -> QdrantPointRead:
        """Get a point by ID"""
        points = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[point_id],
            with_payload=True,
            with_vectors=True,
        )

        if not points:
            raise NotFoundException(
                error_code=ErrorCode404.NOT_FOUND,
                message=f"Point '{point_id}' not found",
            )

        point = points[0]
        return QdrantPointRead(
            id=point.id,
            vector=point.vector,
            payload=point.payload,
        )

    def update_point(self, point_id: str, point_data: QdrantPointUpdate) -> QdrantPointRead:
        """Update a point"""
        # Get existing point first
        existing_point = self.get_point(point_id)

        # Update vector if provided
        vector = point_data.vector if point_data.vector else existing_point.vector

        # Update payload if provided
        payload = existing_point.payload or {}
        if point_data.payload:
            payload.update(point_data.payload)

        # Upsert the updated point
        updated_point = PointStruct(
            id=point_id,
            vector=vector,
            payload=payload,
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[updated_point],
        )

        return QdrantPointRead(
            id=point_id,
            vector=vector,
            payload=payload,
        )

    def delete_point(self, point_id: str) -> None:
        """Delete a point"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[point_id],
        )

    # Search Operations
    def search_points(self, search_query: QdrantSearchQuery) -> list[QdrantSearchResult]:
        """Search for similar points"""
        # Build filter if provided
        query_filter = None
        if search_query.filter_conditions:
            conditions = []
            for field, value in search_query.filter_conditions.items():
                conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
            query_filter = Filter(must=conditions)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=search_query.vector,
            limit=search_query.limit,
            score_threshold=search_query.score_threshold,
            query_filter=query_filter,
            with_payload=search_query.with_payload,
            with_vectors=search_query.with_vector,
        )

        search_results = []
        for result in results:
            search_result = QdrantSearchResult(
                id=result.id,
                score=result.score,
                payload=result.payload if search_query.with_payload else None,
                vector=result.vector if search_query.with_vector else None,
            )
            search_results.append(search_result)

        return search_results

    # Utility Operations
    def count_points(self) -> int:
        """Count points in collection"""
        info = self.client.get_collection(self.collection_name)
        return info.points_count or 0

    def clear(self) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(filter=Filter()),
        )
