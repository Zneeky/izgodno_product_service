import uuid
from sqlalchemy import UUID, Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.website_categories import website_category

class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category")
    websites = relationship("Website", secondary=website_category, back_populates="categories")