import uuid
from sqlalchemy import UUID, Column, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base
from sqlalchemy.dialects.postgresql import JSONB

class ProductPrice(Base):
    __tablename__ = "product_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    variation_id = Column(UUID(as_uuid=True), ForeignKey("product_variations.id"), nullable=False)
    website_id = Column(UUID(as_uuid=True), ForeignKey("websites.id"), nullable=False)

    price = Column(Float, nullable=False)
    currency = Column(String, default="BGN")
    url = Column(String, nullable=False)
    in_stock = Column(String, default="unknown")  # e.g. "yes", "no", "unknown"
    shipping_cost = Column(Float, nullable=True)
    offer_metadata = Column(JSONB, nullable=True)  # e.g. {"delivery": "2-3 days"}

    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    variation = relationship("ProductVariation", back_populates="offers")
    website = relationship("Website", back_populates="prices")