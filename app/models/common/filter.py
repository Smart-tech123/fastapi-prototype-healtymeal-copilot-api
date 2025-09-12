from enum import StrEnum
from typing import Any, TypeVar

from pydantic import BaseModel

ObjectType = TypeVar("ObjectType")


class ObjectFilterCondition(StrEnum):
    EQ = "eq"
    NE = "ne"


class ObjectFilterField[ObjectType](BaseModel):
    value: ObjectType
    condition: ObjectFilterCondition = ObjectFilterCondition.EQ

    def query(self) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        if self.condition is ObjectFilterCondition.EQ:
            ret = {"$eq": self.value}
        elif self.condition is ObjectFilterCondition.NE:
            ret = {"$ne": self.value}
        return ret


class ListFilterCondition(StrEnum):
    ALL = "all"
    ANY = "any"
    N_ALL = "not_all"
    N_ANY = "not_any"


class ListFilterField[ObjectType](BaseModel):
    values: list[ObjectType]
    condition: ListFilterCondition = ListFilterCondition.ALL

    def query(self) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        if self.condition is ListFilterCondition.ALL:
            ret = {"$all": self.values}
        elif self.condition is ListFilterCondition.ANY:
            ret = {"$in": self.values}
        elif self.condition is ListFilterCondition.N_ALL:
            ret = {"$not": {"$all": self.values}}
        elif self.condition is ListFilterCondition.N_ANY:
            ret = {"$nin": self.values}
        return ret


class StringFilterCondition(StrEnum):
    EQ = "eq"
    NE = "ne"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    CONTAINS = "contains"


class StringFilterField(BaseModel):
    value: str
    condition: StringFilterCondition = StringFilterCondition.CONTAINS
    case_sensitive: bool = False

    def query(self) -> dict[str, Any]:
        ret = {}
        if self.condition is StringFilterCondition.EQ:
            ret = (
                {
                    "$eq": self.value,
                }
                if self.case_sensitive
                else {
                    "$regex": f"^{self.value}$",
                    "$options": "i",
                }
            )
        elif self.condition is StringFilterCondition.NE:
            ret = {
                "$ne": self.value,
            }
        elif self.condition is StringFilterCondition.STARTS_WITH:
            ret = (
                {
                    "$regex": f"^{self.value}",
                }
                if self.case_sensitive
                else {
                    "$regex": f"^{self.value}",
                    "$options": "i",
                }
            )
        elif self.condition is StringFilterCondition.ENDS_WITH:
            ret = (
                {
                    "$regex": f"{self.value}$",
                }
                if self.case_sensitive
                else {
                    "$regex": f"{self.value}$",
                    "$options": "i",
                }
            )
        elif self.condition is StringFilterCondition.CONTAINS:
            ret = (
                {
                    "$regex": self.value,
                }
                if self.case_sensitive
                else {
                    "$regex": self.value,
                    "$options": "i",
                }
            )
        return ret


class ComparableFilterCondition(StrEnum):
    EQ = "eq"  # ==
    NE = "ne"  # !=
    GT = "gt"  # (min, +inf)
    LT = "lt"  # (-inf, max)
    GTE = "gte"  # [min, +inf)
    LTE = "lte"  # (-inf, max]
    GT_LT = "gt_lt"  # (min, max)
    GT_LTE = "gt_lte"  # (min, max]
    GTE_LT = "gte_le"  # [min, max)
    GTE_LTE = "gte_lte"  # [min, max]


ComparableValueType = TypeVar("ComparableValueType")


class ComparableFilterField[ComparableValueType](BaseModel):
    value: ComparableValueType | tuple[ComparableValueType, ComparableValueType]
    condition: ComparableFilterCondition

    def query(self) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        if isinstance(self.value, tuple):
            if self.condition is ComparableFilterCondition.GT_LT:
                ret = {
                    "$gt": self.value[0],
                    "$lt": self.value[1],
                }
            elif self.condition is ComparableFilterCondition.GT_LTE:
                ret = {
                    "$gt": self.value[0],
                    "$lte": self.value[1],
                }
            elif self.condition is ComparableFilterCondition.GTE_LT:
                ret = {
                    "$gte": self.value[0],
                    "$lt": self.value[1],
                }
            elif self.condition is ComparableFilterCondition.GTE_LTE:
                ret = {
                    "$gte": self.value[0],
                    "$lte": self.value[1],
                }
            else:
                msg = f"invalid condition for value pair: {self.condition.value}"
                raise TypeError(msg)
        else:
            if self.condition is ComparableFilterCondition.EQ:
                ret = {
                    "$eq": self.value,
                }
            elif self.condition is ComparableFilterCondition.NE:
                ret = {
                    "$ne": self.value,
                }
            elif self.condition is ComparableFilterCondition.GT:
                ret = {
                    "$gt": self.value,
                }
            elif self.condition is ComparableFilterCondition.LT:
                ret = {
                    "$lt": self.value,
                }
            elif self.condition is ComparableFilterCondition.GTE:
                ret = {
                    "$gte": self.value,
                }
            elif self.condition is ComparableFilterCondition.LTE:
                ret = {
                    "$lte": self.value,
                }
            else:
                msg = f"invalid confition for single value: {self.condition.value}"
                raise TypeError(msg)
        return ret


class FilterBase(BaseModel):
    def query(self) -> dict[str, Any]:
        raise NotImplementedError
