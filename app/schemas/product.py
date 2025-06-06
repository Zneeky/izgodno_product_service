from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, List, Optional

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
    category_id: UUID


class ProductData(BaseModel):
    item: str
    item_current_price: str
    item_image_url: str
    item_page_url: str
    price_currency: str

class DomainData(BaseModel):
    domain: str
    extracted_data: List[ProductData]


class ProductPriceOut(BaseModel):
    id: UUID
    variation_id: UUID
    website_id: UUID
    price: float
    currency: str
    url: str
    in_stock: Optional[str]
    shipping_cost: Optional[float]
    offer_metadata: Optional[Dict[str, Any]]
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
