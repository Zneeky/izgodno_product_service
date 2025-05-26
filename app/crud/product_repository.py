# app/crud/product.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Product
from app.models.category import Category
from app.models.product_variation import ProductVariation
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


    async def create(self, parsed: ProductBaseModel, category_id: UUID ,category_name: str) -> ParsedProductResponse:
        product = Product(
            name = f"{parsed.brand} {parsed.model}",
            brand = parsed.brand,
            model = parsed.model,
            category_id = category_id,
            sku = parsed.sku,
            attributes = parsed.attributes,
        )
        self.db.add(product)
        await self.db.commit()
        return ParsedProductResponse(
                id = product.id,
                brand = product.brand,
                model = product.model,
                sku = product.sku,
                attributes = product.attributes,
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

    async def create_variation(self, product_id: UUID, specs: dict, sku: str) -> ProductVariation:
        variation = ProductVariation(
            product_id=product_id,
            specs=specs,
            sku=sku
        )
        self.db.add(variation)
        await self.db.commit()
        await self.db.refresh(variation)
        return variation
