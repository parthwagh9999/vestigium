"""Common shared schema types used across the application.

Provides base classes for pagination, sorting, filtering, and
standard API response envelopes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseSchema):
    """Schema mixin for timestamp fields."""

    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginationParams(BaseSchema):
    """Pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=500, description="Items per page")
    sort_by: str | None = Field(default=None, description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")

    @property
    def offset(self) -> int:
        """Calculate the SQL OFFSET from page and page_size."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated API response envelope."""

    items: list[T]
    total: int = Field(description="Total number of matching items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int) -> PaginatedResponse[T]:
        """Create a paginated response from query results.

        Args:
            items: The items for this page.
            total: Total count of matching items.
            page: Current page number.
            page_size: Number of items per page.

        Returns:
            PaginatedResponse instance.
        """
        total_pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class SuccessResponse(BaseSchema):
    """Standard success response."""

    success: bool = True
    message: str = "Operation completed successfully"


class ErrorResponse(BaseSchema):
    """Standard error response."""

    error: str
    message: str
    status_code: int
    details: dict[str, Any] | None = None


class IDResponse(BaseSchema):
    """Response containing just an ID (for create operations)."""

    id: str
    message: str = "Created successfully"


class BulkOperationResponse(BaseSchema):
    """Response for bulk operations."""

    success_count: int = 0
    error_count: int = 0
    errors: list[dict[str, str]] = Field(default_factory=list)
    created_ids: list[str] = Field(default_factory=list)
