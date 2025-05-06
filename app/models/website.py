import uuid
from sqlalchemy import UUID, Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models import website_categories

class Website(Base):
    __tablename__ = "websites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, index=True)
    domain = Column(String, unique=True, index=True)
    
    categories = relationship("Category", secondary=website_categories, back_populates="websites")
    prices = relationship("ProductPrice", back_populates="website", cascade="all, delete")