import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base

class ProductVariation(Base):
    __tablename__ = "product_variations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    sku = Column(String, index=True, nullable=True)
    specs = Column(JSONB, nullable=True)  # Includes both primary + secondary specs

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    product = relationship("Product", back_populates="variations")
    offers = relationship("ProductPrice", back_populates="variation", cascade="all, delete")
