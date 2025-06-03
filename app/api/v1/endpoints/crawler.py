from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from app.services.interfaces.crawling_service_interface import ICrawlingService
from app.dependencies import get_crawling_service  # ⬅️ this is your new provider

router = APIRouter()

@router.get("/crawl")
async def crawl_url(
    url: str,
    crawling_service: ICrawlingService = Depends(get_crawling_service)
):
    html = await crawling_service.fetch_google_search_html()

    return {"html": html}

@router.post("/crawl/search")
async def crawl_search_pages(
    category_id: UUID,
    query: str = Query(..., description="Search query used for relevance filtering"),
    crawling_service: ICrawlingService = Depends(get_crawling_service)
):
    results = await crawling_service.crawl_all_search_pages(category_id=category_id, query=query)
    return {"results": results}

@router.post("/crawl/generate/json-css-strategy")
async def generate_json_css_strategy(
    website_id: str,
    html: str,
    crawling_service: ICrawlingService = Depends(get_crawling_service)
):
    return await crawling_service.generate_json_css_strategy(website_id, html)

