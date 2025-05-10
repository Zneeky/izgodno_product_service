# app/crud/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")

class AbstractRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_sku(self, sku: str) -> T | None: ...

    @abstractmethod
    async def create(self, obj: T, category_name: str) -> T: ...

    @abstractmethod
    async def get_all_categories(self, session) -> list[T]: ...

    @abstractmethod
    async def get_category_by_name(self, name: str, parent_id: str | None = None) -> T | None: ...

    @abstractmethod
    async def get_category_by_id(self, category_id: str) -> T | None: ...

    @abstractmethod
    async def create_category(self, name: str, parent_id: str | None = None) -> T: ...
