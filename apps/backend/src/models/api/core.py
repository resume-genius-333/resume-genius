from typing import List, Optional, TypeVar, Generic

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class OptionalResponse(BaseModel, Generic[T]):
    result: Optional[T]
