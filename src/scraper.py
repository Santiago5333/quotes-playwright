import time
from urllib.parse import urljoin

from playwright.sync_api import Error as PlaywrightError, Page, sync_playwright

from src import config
from src.models import Quote
from src.parser import parse_page


def _load(page: Page, url: str) -> None:
    """Cargar una url y esperar las citas, con reintentos"""
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_selector(config.SEL_QUOTE)
            return
        except PlaywrightError as e:
            print(f"Intento {attempt}/{config.MAX_RETRIES} falló en {url}: {e}")
            if attempt == config.MAX_RETRIES:
                raise
            time.sleep(config.RETRY_DELAY)


def _next_url(page: Page) -> str | None:
    """Devuelve la URL de la página siguiente, o None si es la última"""
    link = page.locator(config.SEL_NEXT)
    if link.count() == 0:
        return None
    return urljoin(page.url, link.first.get_attribute("href"))


def scrape(
    max_pages: int | None = None, headless: bool = config.HEADLESS
) -> list[Quote]:
    quotes: list[Quote] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=config.USER_AGENT)
        page = context.new_page()
        page.set_default_timeout(config.TIMEOUT_MS)

        try:
            url = config.BASE_URL
            page_num = 0
            while url:
                page_num += 1
                _load(page, url)
                parsed = parse_page(page)
                quotes.extend(parsed)
                print(f"Página {page_num}: {len(parsed)} citas")

                if max_pages and page_num >= max_pages:
                    break
                url = _next_url(page)
                if url:
                    time.sleep(config.DELAY_BETWEEN_PAGES_S)
        finally:
            browser.close()
    return quotes
