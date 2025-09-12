import re
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


class ChangeType(StrEnum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class Version(BaseModel):
    major: Annotated[
        int,
        Field(
            ge=0,
            description="Major version number",
            examples=[
                1,
            ],
        ),
    ]
    minor: Annotated[
        int,
        Field(
            ge=0,
            description="Minor version number",
            examples=[
                0,
            ],
        ),
    ]
    patch: Annotated[
        int,
        Field(
            ge=0,
            description="Patch version number",
            examples=[
                0,
            ],
        ),
    ]

    @classmethod
    def initial_version(cls) -> "Version":
        return cls(major=0, minor=0, patch=0)

    @classmethod
    def parse_str(cls, version: str) -> "Version":
        match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", version)
        if not match:
            msg = f"Invalid version string: {version}"
            raise ValueError(msg)

        major = int(match.group(1))
        minor = int(match.group(2)) if match.group(2) is not None else 0
        patch = int(match.group(3)) if match.group(3) is not None else 0

        return cls(major=major, minor=minor, patch=patch)

    def to_str(self) -> str:
        """
        Returns string representation of the version (e.g. "v1.2.3")
        """
        return f"v{self.major}.{self.minor}.{self.patch}"
