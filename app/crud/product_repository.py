# app/crud/product.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Product
from app.models.website_categories import website_category
from app.models.category import Category
from app.models.product_variation import ProductVariation
from app.models.website import Website
from app.schemas.product import ParsedProductResponse, ProductBaseModel
from app.crud.base import AbstractRepository
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify
from sqlalchemy.orm import joinedload

class ProductRepository(AbstractRepository[Product]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_sku(self, sku: str) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.sku == sku))
        return result.scalars().first()
    
    async def get_by_brand_and_model(self, brand: str, model: str) -> list[Product]:
        stmt = select(Product).options(joinedload(Product.category)).where(
            Product.brand == brand,
            Product.model == model
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


    async def create_product(self, brand: str, model:str, category_id: UUID ,category_name: str) -> ParsedProductResponse:
        product = Product(
            name = f"{brand} {model}",
            brand = brand,
            model = model,
            category_id = category_id,
        )
        self.db.add(product)
        await self.db.commit()
        return ParsedProductResponse(
                id = product.id,
                brand = product.brand,
                model = product.model,
                category_name = category_name
            )
    
    async def get_all_categories(self) -> list[Category]:
        stmt = select(Category)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_category_by_name(self, name: str, parent_id: UUID | None = None) -> Category | None:
        stmt = select(Category).where(Category.name == name)
        if parent_id:
            stmt = stmt.where(Category.parent_id == parent_id)
        else:
            stmt = stmt.where(Category.parent_id == None)

        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_category_by_id(self, category_id: UUID) -> Category | None:
        stmt = select(Category).where(Category.id == category_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_category(self, name: str, parent_id: UUID | None = None) -> Category:
        new_cat = Category(name=name, slug=slugify(name), parent_id=parent_id)
        self.db.add(new_cat)
        await self.db.commit()
        await self.db.refresh(new_cat)
        return new_cat
    
    async def get_variations_by_product_id(self, product_id: UUID) -> list[ProductVariation]:
        stmt = select(ProductVariation).where(ProductVariation.product_id == product_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_variation(self, product_id: UUID, variation_name: str, variation_key: str, sku: str) -> ProductVariation:
        variation = ProductVariation(
            product_id=product_id,
            variation_name=variation_name,
            variation_key=variation_key,
            sku=sku
        )
        self.db.add(variation)
        await self.db.commit()
        await self.db.refresh(variation)
        return variation
    
    async def get_website_by_id(self, website_id: UUID) -> Website | None:
        stmt = select(Website).where(Website.id == website_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_websites_by_category_id(self, category_id: UUID) -> list[Website]:
        stmt = (
            select(Website)
            .join(website_category, Website.id == website_category.c.website_id)
            .where(website_category.c.category_id == category_id)
            .options(joinedload(Website.categories))
        )
        result = await self.db.execute(stmt)
        return result.unique().scalars().all()
