from fastapi import APIRouter, Depends
from app.crud.product_repository import ProductRepository
from app.dependencies import get_parser_service
from app.schemas.product import ParsedProductWithVariationResponse, ProductNameRequest, ParsedProductResponse
from app.services.interfaces.parser_service_interface import IParserService

router = APIRouter()

@router.post("/parse-product/", response_model=ParsedProductWithVariationResponse)
async def parse_product(request: ProductNameRequest, parser_service: IParserService = Depends(get_parser_service)):
    return await parser_service.handle_product_parsing(request.name)
