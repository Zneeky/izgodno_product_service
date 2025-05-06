from fastapi import APIRouter
from app.schemas.product import ProductNameRequest, ParsedProductResponse
from app.services.parser_service import parse_product_name

router = APIRouter()

@router.post("/", response_model=ParsedProductResponse)
def parse_product(request: ProductNameRequest):
    return parse_product_name(request.name)
