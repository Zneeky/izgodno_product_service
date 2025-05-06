from pydantic import BaseModel
from typing import Optional

class ProductNameRequest(BaseModel):
    name: str

class ParsedProductResponse(BaseModel):
    brand: Optional[str]
    model: Optional[str]
    storage: Optional[str]
    color: Optional[str]
    serial_number: Optional[str]
