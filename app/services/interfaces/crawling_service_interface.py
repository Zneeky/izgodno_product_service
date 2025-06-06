from abc import ABC, abstractmethod
from uuid import UUID

class ICrawlingService(ABC):
    @abstractmethod
    async def fetch_raw_html_search_page(self, url: str) -> str:
        pass

    @abstractmethod
    async def crawl_all_search_pages(self, category_id: UUID, query: str) -> list[dict]:
        pass

    @abstractmethod
    async def get_raw_html(self, url: str) -> str:
        pass

    @abstractmethod
    async def fetch_google_search_html(url: str) -> str:
        pass

    @abstractmethod
    async def generate_json_css_strategy(self, website_id: UUID, html: str) -> dict:
        pass

    @abstractmethod
    async def generate_json_xpath_strategy(self, website_id: UUID, html: str) -> None:
        pass