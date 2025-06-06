from abc import ABC, abstractmethod

class ILLMService(ABC):
    @abstractmethod
    async def extract_product_fields(self, title: str) -> dict:
        pass

    @abstractmethod
    def extract_json_from_response(response: str) -> dict:
        pass

    @abstractmethod
    def llm_match_products(self, new_product: dict, existing_products: list[dict]) -> dict:
        pass

    @abstractmethod
    async def choose_best_offer_per_domain(self, original_product: dict, offers: list[dict]) -> list[dict]:
        pass
    
    @abstractmethod
    async def get_variations_from_web(self, brand: str, model: str) -> list[dict]:
        pass
