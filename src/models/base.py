"""Base Pydantic models for blog-AI."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TimestampedModel(BaseModel):
    """Base model with timestamp tracking."""

    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        arbitrary_types_allowed=False,
    )


class ContentModel(BaseModel):
    """Base model for content structures."""

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )
