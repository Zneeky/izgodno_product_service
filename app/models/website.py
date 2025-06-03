from datetime import datetime, timezone
import uuid
from sqlalchemy import UUID, Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.website_categories import website_category

class Website(Base):
    __tablename__ = "websites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, index=True)
    domain = Column(String, unique=True, index=True)
    logo_url = Column(String, nullable=True)
    search_url = Column(String, nullable=True)
    affiliate_link = Column(String, nullable=True)
    affiliate_id = Column(String, nullable=True)
    schema = Column(JSONB, nullable=True)
    schema_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    categories = relationship("Category", secondary=website_category, back_populates="websites")
    prices = relationship("ProductPrice", back_populates="website", cascade="all, delete")