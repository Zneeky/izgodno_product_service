from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.crawling_service import CrawlingService
from app.services.interfaces.crawling_service_interface import ICrawlingService
from app.services.interfaces.llm_service_interface import ILLMService
from app.services.interfaces.parser_service_interface import IParserService
from app.crud.base import AbstractRepository
from app.services.llm_service import LLMService
from app.services.parser_service import ParserService
from app.crud.product_repository import ProductRepository

def get_product_repository(db: AsyncSession = Depends(get_db)) -> AbstractRepository:
    return ProductRepository(db)

async def get_parser_service(db: AsyncSession = Depends(get_db)) -> IParserService:
    repo = ProductRepository(db)
    llm_service = LLMService()
    return ParserService(repo=repo, llm_service=llm_service)

def get_crawling_service() -> ICrawlingService:
    return CrawlingService()