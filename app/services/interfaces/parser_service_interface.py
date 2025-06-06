# interfaces/parser_service_interface.py
from abc import ABC, abstractmethod
from app.schemas.product import ParsedProductWithVariationResponse

class IParserService(ABC):
    @abstractmethod
    async def handle_product_parsing(self, name: str) -> ParsedProductWithVariationResponse:
        pass

    @abstractmethod
    async def parse_product_and_find_best_offer(self, product_data: ParsedProductWithVariationResponse):
        pass

    
