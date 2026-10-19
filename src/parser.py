import json
from urllib.parse import urljoin

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page

from src import config
from src.models import Author, Quote


def parse_quote(
    card: Locator,
) -> Quote:
    """Convierte un div.quote en un objeto Quote"""
    text = card.locator(config.SEL_TEXT).inner_text().strip()
    text = text.strip("\u201c\u201d")  # quita las comillas tipográficas

    author = card.locator(config.SEL_AUTHOR).inner_text().strip()
    tags = [t.strip() for t in card.locator(config.SEL_TAG).all_inner_texts()]

    href = card.locator(config.SEL_AUTHOR_LINK).first.get_attribute("href")
    author_url = urljoin(config.BASE_URL, href) if href else None

    return Quote(text=text, author=author, tags=tags, author_url=author_url)


def parse_page(page: Page) -> list[Quote]:
    """Extrae todas las citas visibles en la página actual"""
    quotes = []
    for card in page.locator(config.SEL_QUOTE).all():
        try:
            quotes.append(parse_quote(card))
        except (PlaywrightError, ValueError) as e:
            # PlaywrightError: la tarjeta no tiene el dato (timeout del locator).
            # ValueError: el modelo rechazó el dato (Quote vacío). Se omite y se
            # anuncia; cualquier OTRO error (nuestro) revienta.
            print(f"Cita omitida por error: {e}")

    return quotes


def _text(page: Page, selector: str) -> str | None:
    loc = page.locator(selector)
    return loc.first.inner_text().strip() if loc.count() else None


def parse_author(page: Page) -> Author:
    loc = _text(page, config.SEL_A_BORN_LOC)
    if loc and loc.startswith("in "):
        loc = loc[3:]
    return Author(
        name=_text(page, config.SEL_A_NAME) or "",
        url=page.url,
        born_date=_text(page, config.SEL_A_BORN_DATE),
        born_location=loc,
        description=_text(page, config.SEL_A_DESC),
    )


def quote_from_item(item: dict) -> Quote:
    autor = item.get("author", {})
    slug = autor.get("slug")
    return Quote(
        text=item["text"].strip('\u201c\u201d"'),
        author=autor.get("name", ""),
        tags=item.get("tags", []),
        author_url=f"{config.SITE}/author/{slug}" if slug else None,
    )


def parse_inline(page: Page) -> list[Quote]:
    """Lee la variable JS `data` que esta cargando en la pagina."""
    items = page.evaluate("() => data")
    return [quote_from_item(i) for i in items]


def parse_raw(html: str) -> list[Quote]:
    """Extrae `data` del html crudo, sin renderizar nada."""
    marca = "var data = "
    inicio = html.index(marca) + len(marca)
    items, _ = json.JSONDecoder().raw_decode(html[inicio:])
    return [quote_from_item(i) for i in items]
