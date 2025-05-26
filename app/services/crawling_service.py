from app.services.interfaces.crawling_service_interface import ICrawlingService
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlResult,  CrawlerRunConfig
from patchright.async_api import async_playwright

BLOCKED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".woff", ".woff2", ".ttf", ".eot", ".otf", ".mp4", ".webm", ".css", ".js")
BLOCKED_DOMAINS = ["googletagmanager.com", "google-analytics.com", "doubleclick.net", "facebook.net", "adservice.google.com"]
# Will persist Chrome profile between runs
class CrawlingService(ICrawlingService):
      
    # Function to fetch raw HTML with minimized network traffic
    async def fetch_raw_html( url: str) -> str:
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
                         if request.resource_type in ['image', 'stylesheet', 'font', 'script', 'media', 'other'] 
                         or request.url.lower().endswith(BLOCKED_EXTENSIONS) 
                         or any(domain in request.url for domain in BLOCKED_DOMAINS)
                         else route.continue_())

            # Go to the desired page
            await page.goto("https://www.google.com/search?q=iphone+14+pro+256gb+цена")

            await page.wait_for_timeout(100)  # Wait for 5 seconds to ensure the page is fully loaded
            # Get the raw HTML content of the page
            raw_html = await page.content()

            # Close the browser
            await context.close()

            return raw_html

    async def get_raw_html(self, url: str) -> str:
        print("🌐 Crawling URL:", url)
            
        # run_config = CrawlerRunConfig(
        #         url=url,
        #         capture_network_requests=True,
        #         exclude_all_images=True,
        #         verbose=True
        # )

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
        
