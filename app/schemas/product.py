from uuid import UUID
from pydantic import BaseModel
from typing import Any, Dict, Optional

class ProductNameRequest(BaseModel):
    name: str


class ParsedProductResponse(BaseModel):
    id: UUID
    brand: str
    model: str
    category_name: Optional[str]
    attributes: Optional[Dict[str, Any]]
    sku: str

class ProductBaseModel(BaseModel):
    name: str
    brand: str
    model: str
    sku: str
    attributes: Optional[Dict[str, Any]] = None
    category_id: UUID 