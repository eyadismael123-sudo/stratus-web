"""Common response schemas — matches web/types/index.ts envelope."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    pages: int


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: str | None = None
    error_message: str | None = None
    meta: PaginationMeta | dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    error: str
    error_message: str
    meta: dict[str, Any] | None = None
