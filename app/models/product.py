import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)  # e.g. "Redmi Note 14"
    brand = Column(String, index=True)
    model = Column(String, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    category = relationship("Category", back_populates="products")
    variations = relationship("ProductVariation", back_populates="product", cascade="all, delete")

    __table_args__ = (
        UniqueConstraint("name", "category_id", "brand", name="uq_product_name_category_brand"),
    )
    