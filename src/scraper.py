import time
from urllib.parse import urljoin

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

from src import config
from src.models import Author, Quote
from src.parser import (
    has_next_raw,
    parse_author,
    parse_inline,
    parse_page,
    parse_raw,
    quote_from_item,
)

MODES = ("dom", "inline", "raw", "scroll")
_MAS_CITAS = "([sel, n]) => document.querySelectorAll(sel).length > n"


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


def _get_html(context, url: str) -> str:
    for intento in range(1, config.MAX_RETRIES + 1):
        try:
            resp = context.request.get(url, timeout=config.TIMEOUT_MS)
            if not resp.ok:
                raise RuntimeError(f"HTTP {resp.status}")
            return resp.text()
        except (PlaywrightError, RuntimeError) as e:
            print(f"Intento {intento}/{config.MAX_RETRIES} falló en {url}: {e}")
            if intento == config.MAX_RETRIES:
                raise
            time.sleep(config.RETRY_DELAY)


def _next_url(page: Page) -> str | None:
    """Devuelve la URL de la página siguiente, o None si es la última"""
    link = page.locator(config.SEL_NEXT)
    if link.count() == 0:
        return None
    return urljoin(page.url, link.first.get_attribute("href"))


def login(page: Page, user: str, password: str) -> None:
    page.goto(config.LOGIN_URL, wait_until="domcontentloaded")
    page.fill(config.SEL_USER, user)
    page.fill(config.SEL_PASS, password)
    page.click(config.SEL_SUBMIT)
    try:
        page.wait_for_selector(config.SEL_LOGOUT)
    except PlaywrightError:
        raise RuntimeError("Login fallido: revisa el usuario y contrasena")


def scrape_paginated(page: Page, max_pages=None, parser=parse_page) -> list[Quote]:
    quotes: list[Quote] = []
    url = config.BASE_URL
    numero = 0

    while url:
        numero += 1
        _load(page, url)
        encontradas = parser(page)
        quotes.extend(encontradas)
        print(f"Pagina {numero}: {len(encontradas)} citas")

        if max_pages and numero >= max_pages:
            break
        url = _next_url(page)

        if url:
            time.sleep(config.DELAY_BETWEEN_PAGES_S)
    return quotes


def scrape_raw(context, max_pages=None) -> list[Quote]:
    quotes: list[Quote] = []
    n = 1
    while True:
        url = config.BASE_URL if n == 1 else f"{config.BASE_URL}/page/{n}"
        html = _get_html(context, url)
        encontradas = parse_raw(html)
        quotes.extend(encontradas)
        print(f"Pagina {n}: {len(encontradas)} citas")

        if not has_next_raw(html) or (max_pages and n >= max_pages):
            break
        n += 1
        time.sleep(config.DELAY_BETWEEN_PAGES_S)
    return quotes


def scrape_scroll(
    page: Page,
    max_pages=None,
) -> list[Quote]:
    paginas: dict[int, dict] = {}

    def capturar(resp):
        if "/api/quotes" in resp.url and resp.ok:
            try:
                data = resp.json()
                paginas[data["page"]] = data
            except Exception:
                pass

    page.on("response", capturar)
    page.goto(config.SCROLL_URL, wait_until="networkidle")

    limite = max_pages or config.MAX_SCROLLS
    while len(paginas) < limite:
        if paginas and not paginas[max(paginas)]["has_next"]:
            break

        antes = page.locator(config.SEL_QUOTE).count()
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        try:
            page.wait_for_function(
                _MAS_CITAS,
                arg=[config.SEL_QUOTE, antes],
                timeout=config.TIMEOUT_MS,
            )
        except PlaywrightError:
            break
        page.wait_for_timeout(200)

    page.remove_listener("response", capturar)
    if not paginas:
        return parse_page(page)

    claves = sorted(paginas)[:limite]
    quotes = [quote_from_item(i) for n in claves for i in paginas[n]["quotes"]]
    print(f"Scroll: {len(claves)} paginas de la API, {len(quotes)} citas")
    return quotes


def scrape_author(page: Page, urls: list[str]) -> list[Author]:
    authors = []
    for url in urls:
        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_selector(config.SEL_A_NAME)
            authors.append(parse_author(page))
        except PlaywrightError as e:
            print(f"Author omitido {url}: {e}")
            time.sleep(config.DELAY_BETWEEN_PAGES_S)
    return authors


def scrape(
    mode: str = "dom",
    max_pages: int | None = None,
    headless: bool = config.HEADLESS,
    credentials: tuple[str, str] | None = None,
    with_authors: bool = False,
) -> tuple[list[Quote], list[Author]]:
    if mode not in MODES:
        raise ValueError(f"Modo no valido: {mode}. Usa uno de {MODES}")

    quotes: list[Quote] = []
    authors: list[Author] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=config.USER_AGENT)
        page = context.new_page()
        page.set_default_timeout(config.TIMEOUT_MS)

        try:
            if credentials:
                login(page, *credentials)
            if mode == "raw":
                quotes = scrape_raw(context, max_pages)
            elif mode == "inline":
                quotes = scrape_paginated(page, max_pages, parser=parse_inline)
            elif mode == "scroll":
                quotes = scrape_scroll(page, max_pages)
            else:
                quotes = scrape_paginated(page, max_pages)

            if with_authors:
                urls = sorted({q.author_url for q in quotes if q.author_url})
                authors = scrape_author(page, urls)

        finally:
            browser.close()

    return quotes, authors
