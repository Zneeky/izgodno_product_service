from sqlalchemy import Table, Column, ForeignKey
from app.db.session import Base
from sqlalchemy.dialects.postgresql import UUID

website_category = Table(
    "website_categories",
    Base.metadata,
    Column("website_id", UUID(as_uuid=True), ForeignKey("websites.id")),
    Column("category_id", UUID(as_uuid=True), ForeignKey("categories.id"))
)