from fastapi import APIRouter, Depends
from app.services.interfaces.crawling_service_interface import ICrawlingService
from app.dependencies import get_crawling_service  # ⬅️ this is your new provider

router = APIRouter()

@router.get("/crawl")
async def crawl_url(
    url: str,
    crawling_service: ICrawlingService = Depends(get_crawling_service)
):
    html = await crawling_service.fetch_raw_html()
    #html = await crawling_service.get_raw_html(url)

    return {"html": html}
