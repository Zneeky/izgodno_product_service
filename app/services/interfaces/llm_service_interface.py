from abc import ABC, abstractmethod

class ILLMService(ABC):
    @abstractmethod
    async def extract_product_fields(self, title: str) -> dict:
        pass

    @abstractmethod
    def extract_json_from_response(response: str) -> dict:
        pass
