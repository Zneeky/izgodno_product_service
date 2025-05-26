from abc import ABC, abstractmethod

class ICrawlingService(ABC):
    @abstractmethod
    async def get_raw_html(self, url: str) -> str:
        pass

    @abstractmethod
    async def fetch_raw_html(url: str) -> str:
        pass