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

class ProductBaseModel(BaseModel):
    name: str
    brand: str
    model: str
    category_id: UUID 

class ParsedProductWithVariationResponse(BaseModel):
    product_id: UUID
    variation_id: UUID
    brand: str
    model: str
    variation: str
    category_name: Optional[str] = None