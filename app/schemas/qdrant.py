from typing import Annotated, Any

import numpy as np
from pydantic import BaseModel, Field, model_validator
from scipy.linalg import norm

from app.core.config.qdrant import config as cfg_qdrant


class QdrantPoint(BaseModel):
    vector: Annotated[
        list[float],
        Field(min_length=cfg_qdrant.VECTOR_SIZE, max_length=cfg_qdrant.VECTOR_SIZE),
    ]
    payload: dict[str, Any]

    @model_validator(mode="after")  # type: ignore  # noqa: PGH003
    @classmethod
    def normalize_vector(cls, model: "QdrantPoint") -> "QdrantPoint":
        """
        Normalize vector
        """
        vec = np.asarray(model.vector, dtype=np.float32)
        n = norm(vec)
        model.vector = [x / n for x in model.vector]
        return model


class QdrantPointRead(QdrantPoint):
    id: str


class QdrantPointUpdate(BaseModel):
    vector: list[float] | None = None
    payload: dict[str, Any] | None = None


class QdrantSearchQuery(BaseModel):
    vector: list[float]
    limit: int = 10
    score_threshold: float | None = None
    filter_conditions: dict[str, Any] | None = None
    with_payload: bool = True
    with_vector: bool = False


class QdrantSearchResult(BaseModel):
    id: str
    score: float
    payload: dict[str, Any]
    vector: list[float]
