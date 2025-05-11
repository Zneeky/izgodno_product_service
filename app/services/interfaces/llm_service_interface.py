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
