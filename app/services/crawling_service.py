import asyncio
from datetime import datetime
import json
import random
from uuid import UUID
from app.crud.product_repository import ProductRepository
from app.models.website import Website
from app.services.interfaces.crawling_service_interface import ICrawlingService
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlResult,  CrawlerRunConfig, DefaultMarkdownGenerator, JsonCssExtractionStrategy, JsonXPathExtractionStrategy, LLMConfig, LLMContentFilter
from patchright.async_api import async_playwright
from urllib.parse import quote
from typing import Optional
from app.core.config import settings

HER_PATH = "page.har"
CLOUDFLARE_SITES = ['plesio']
BLOCKED_RESOURCE_TYPES = ["image", "media", "font", "stylesheet"]
BLOCKED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".woff", ".woff2", ".ttf", ".eot", ".otf", ".mp4", ".webm", ".css", ".js")
BLOCKED_DOMAINS = ["googletagmanager.com", "google-analytics.com", "doubleclick.net", "facebook.net", "adservice.google.com"]
class CrawlingService(ICrawlingService):
    def __init__(self, repo: ProductRepository, proxy: Optional[str] = None):
        self.repo = repo
        self.proxy = proxy
        self.groq_api_key = settings.GROQ_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.groq_model = "groq/llama3-8b-8192"
        self.openai_model = settings.OPENAI_MODEL

    
    async def start_browser(self):
        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir="",
                    channel="chrome",
                    headless=False, 
                    no_viewport=True,
                    record_har_path=HER_PATH,)

    async def stop_browser(self):
        await self.context.close()
        await self.playwright.stop()

    async def fetch_raw_html_search_page(self, url: str) -> str:
        cloudflare_route_detected = False  # reset per page

        async def route_handler(route):
            nonlocal cloudflare_route_detected
            url = route.request.url
            if '/challenges.cloudflare.com/' in url or '/cdn-cgi/' in url or 'https://stantek.com/static/assets/no-image.svg' in url:
                cloudflare_route_detected = True
                await route.continue_()
            elif route.request.resource_type in BLOCKED_RESOURCE_TYPES:
                await route.abort()
            else:
                await route.continue_()

        page = await self.context.new_page()
        await page.route("**/*", route_handler)

        try:
            print(f"🌐 Fetching with JS: {url}")
            await page.goto(url)  # Increase timeout if needed

            wait_time = 10000 if cloudflare_route_detected else 2000
            print(f"⏳ Waiting for {wait_time / 1000} seconds...")
            await page.wait_for_timeout(wait_time)

            html = await page.content()
        except Exception as e:
            print(f"[ERROR] Failed to fetch {url}: {e}")
            html = ""
        finally:
            await page.close()

        return html
    
    async def crawl_all_search_pages(self, category_id: UUID, query: str) -> list[dict]:
        await self.start_browser()

        all_websites = await self.repo.get_websites_by_category_id(category_id)
        websites = [site for site in all_websites if site.schema and site.search_url]
        #websites = [site for site in all_websites if site.name == "Stantek"]
        print(f"[crawl4ai] Found {len(websites)} websites with schema for category {category_id}")

        async with AsyncWebCrawler() as crawler:

            # Concurrently fetch HTML pages using the same browser context
            async def fetch_html(site):
                url = f"{site.search_url}{query}"
                html = await self.fetch_raw_html_search_page(url)
                return (site, html)

            fetch_tasks = [fetch_html(site) for site in websites]
            fetched_results = await asyncio.gather(*fetch_tasks)

            valid_results = [(site, html) for site, html in fetched_results if html.strip()]

            # Crawl concurrently as before
            async def crawl(site, html):
                run_config = CrawlerRunConfig(
                    extraction_strategy=JsonCssExtractionStrategy(site.schema, verbose=True),
                )
                try:
                    raw_url = f"raw:{html}"
                    result = await crawler.arun(url=raw_url, config=run_config)
                    if result.success:
                        return {
                            "domain": site.domain,
                            "extracted_data": json.loads(result.extracted_content)
                        }
                    else:
                        print(f"[crawl4ai] Failed for {site.domain}: {result.error_message}")
                        return None
                except Exception as e:
                    print(f"[Exception] Failed to crawl {site.domain}: {str(e)}")
                    return None

            crawl_tasks = [crawl(site, html) for site, html in valid_results]
            crawl_results = await asyncio.gather(*crawl_tasks)

        await self.stop_browser()

        return [res for res in crawl_results if res is not None]

      
    # Function to fetch raw HTML with minimized network traffic
    async def fetch_google_search_html(self, url: str) -> str:
        async with async_playwright() as p:
            # Launch the browser in headless mode
            har_path="page.har"

            context = await p.chromium.launch_persistent_context(
                user_data_dir="",
                channel="chrome",
                headless=False, 
                no_viewport=True,
                record_har_path=har_path,
            )

            page = await context.new_page()


            # Intercept requests and block unwanted resources like images, styles, and fonts
            await page.route("**/*", lambda route, request: route.abort() 
                         if request.resource_type in ['image', 'stylesheet', 'font', 'script', 'media', 'other', 'png', 'jpeg', 'web','image/png', 'image/jpeg', 'image/gif'] 
                         or request.url.lower().endswith(BLOCKED_EXTENSIONS) 
                         or any(domain in request.url for domain in BLOCKED_DOMAINS)
                         else route.continue_())

            # Go to the desired page
            await page.goto("https://www.google.com/search?q=iphone+14+pro+256gb+цена")

            # Get the raw HTML content of the page
            raw_html = await page.content()

            # Close the browser
            await context.close()

            return raw_html

    async def get_raw_html(self, url: str) -> str:
        print("🌐 Crawling URL:", url)

        browser_config = BrowserConfig(
            headless=True,
            verbose=True,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            run_config = CrawlerRunConfig(
                url=url,
                capture_network_requests=True,
                exclude_all_images=True,
                verbose=True
            )

            result: CrawlResult = await crawler.arun(url="https://www.technopolis.bg/bg/Smartfoni-i-mobilni-telefoni/Smartfon-GSM--MOTOROLA-G75-CHARCOAL-GREY-PB3Y0006PL/p/505710", config=run_config)

            print("📡 Total requests made:", result.network_requests.__sizeof__())

    
    async def generate_json_css_strategy(self, website_id: UUID, html: str) -> None:
        # Get website from DB
        site: Website = await self.repo.get_website_by_id(website_id)
        print(f"🌐 Generating schema for website: {site.domain}")

        if not site:
            raise ValueError(f"Website with ID {website_id} not found.")

        # Generate schema using LLM
        css_schema = JsonCssExtractionStrategy.generate_schema(
            html,
            llm_config=self.create_llm_config("groq/meta-llama/llama-4-scout-17b-16e-instruct", self.groq_api_key),
            query=(
                "Analyze this eCommerce HTML page and generate a JSON schema for extracting products. "
                "Each object should represent a single product and should contain the following fields: "
                "`item`, `item_current_price`, `item_page_url`, `item_image_url`, `price_currency`, and `item_available`."
                "Include item_available if there is an idicator for availability, look for text like 'налично', 'в наличност', 'изчерпано', 'available', 'out of stock' etc. Don't include if not clear idicator is present. "
                "Create selectors that are as universal as possible, so they can be used for any item on the page. Make sure you are specific enough so that the correct data is extracted."
                "Ensure that `item_current_price` gets the newest and most relevant price for the item, the type should be text"
                "Make it as universal as possible, so it can be used for any item on the page."
                "Ensure you get the price currency where it is BGN or ЛВ (Bulgarian Lev) "
            ),
        )

        # Update and save
        site.schema = css_schema
        site.schema_timestamp = datetime.now()

        self.repo.db.add(site)
        await self.repo.db.commit()

            

    def create_llm_config(self, provider: str, token_env: str) -> LLMConfig:
        return LLMConfig(
            provider=provider,
            api_token=token_env
        )

    def create_llm_filter(
        self,
        llm_config: LLMConfig,
        instruction: str,
        chunk_token_threshold: int = 2000,
        verbose: bool = True
    ) -> LLMContentFilter:
        return LLMContentFilter(
            llm_config=llm_config,
            instruction=instruction,
            chunk_token_threshold=chunk_token_threshold,
            verbose=verbose
        )

    def create_markdown_generator(
        self,
        content_filter: LLMContentFilter,
        ignore_links: bool = False,
        content_source: str = "cleaned_html",
    ) -> DefaultMarkdownGenerator:
        return DefaultMarkdownGenerator(
            content_source=content_source,
            #content_filter=content_filter,
            options={"ignore_links": ignore_links}
        )

    def create_extraction_strategy(self, schema: dict) -> JsonCssExtractionStrategy:
        return JsonCssExtractionStrategy(schema)

    def create_crawler_config(
        self,
        markdown_generator: DefaultMarkdownGenerator,
        extraction_strategy: JsonXPathExtractionStrategy = None,
        use_cache: bool = False
    ) -> CrawlerRunConfig:
        return CrawlerRunConfig(
            markdown_generator=markdown_generator,
            extraction_strategy=extraction_strategy,
            cache_mode=CacheMode.CACHE if use_cache else CacheMode.BYPASS
        )
        
