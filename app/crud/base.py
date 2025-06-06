# app/crud/base.py
from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar
from uuid import UUID

T = TypeVar("T")

class AbstractRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_sku(self, sku: str) -> T | None: ...

    @abstractmethod
    async def get_by_brand_and_model(self, brand: str, model: str) -> list[T]: ...

    @abstractmethod
    async def create_product(self, brand: str, model: str, category_id: UUID, category_name: str) -> T: ...

    @abstractmethod
    async def get_all_categories(self, session) -> list[T]: ...

    @abstractmethod
    async def get_category_by_name(self, name: str, parent_id: str | None = None) -> T | None: ...

    @abstractmethod
    async def get_category_by_id(self, category_id: str) -> T | None: ...

    @abstractmethod
    async def create_category(self, name: str, parent_id: str | None = None) -> T: ...

    @abstractmethod
    async def get_variations_by_product_id(self, product_id: UUID) -> list[T]: ...

    @abstractmethod
    async def create_variation(self, product_id: UUID, specs: dict, sku: str) -> T: ...

    @abstractmethod
    async def get_website_by_id(self, website_id: UUID) -> T | None: ...

    @abstractmethod
    async def get_websites_by_category_id(self, category_id: UUID) -> list[T]: ...

    @abstractmethod
    async def save_best_offers_to_db(self, flat_offers: list[dict], variation_id: UUID) -> List[T]: ...
    