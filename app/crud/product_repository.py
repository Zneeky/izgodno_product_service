# app/crud/product.py
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Product
from app.models.price import ProductPrice
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
    
    async def save_best_offers_to_db(
        self,
        flat_offers: list[dict],
        variation_id: UUID,
    ):
        for offer in flat_offers:
            domain = offer.get("domain")
            price = offer.get("item_current_price")
            url = offer.get("item_page_url")
            item_name = offer.get("item")
            currency = offer.get("price_currency", "BGN")  # Optional fallback

            if not (domain and price and url):
                print(f"[SKIP] Incomplete offer data: {offer}")
                continue

            # Get matching Website by domain
            website_result = await self.db.execute(
                select(Website).where(Website.domain == domain.lower())
            )
            website = website_result.scalars().first()

            if not website:
                print(f"[SKIP] No Website found for domain '{domain}'")
                continue

            product_price = ProductPrice(
                variation_id = variation_id,
                website_id = website.id,
                price = float(price),
                currency = currency,
                url = url,
                in_stock = "available",
                offer_metadata = {"item": item_name}
            )

            self.db.add(product_price)

        await self.db.commit()


    async def get_recent_prices_for_variation(
        self,
        variation_id: UUID,
        hours: int = 36
    ) -> List[ProductPrice]:
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)

        stmt = (
            select(ProductPrice)
            .options(
                joinedload(ProductPrice.website),
                joinedload(ProductPrice.variation)
            )
            .where(
                ProductPrice.variation_id == variation_id,
                ProductPrice.timestamp >= time_threshold
            )
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_website_by_domain(self, domain: str) -> Website | None:
        stmt = select(Website).where(Website.domain == domain.lower())
        result = await self.db.execute(stmt)
        return result.scalars().first()
