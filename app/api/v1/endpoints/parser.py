from typing import List
from fastapi import APIRouter, Depends
from app.crud.product_repository import ProductRepository
from app.dependencies import get_parser_service
from app.schemas.product import DomainData, ParsedProductWithVariationResponse, ProductNameRequest, ParsedProductResponse, ProductPriceOut
from app.services.interfaces.parser_service_interface import IParserService

router = APIRouter()

@router.post("/parse-product/", response_model=List[ProductPriceOut])
async def parse_product(request: ProductNameRequest, parser_service: IParserService = Depends(get_parser_service)):
    matched_porduct_with_variation = await parser_service.handle_product_parsing(request.name)
    offers = await parser_service.parse_product_and_find_best_offer(matched_porduct_with_variation)
    return offers
