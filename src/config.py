import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# sitio

BASE_URL = "https://quotes.toscrape.com/js"
LOGIN_URL = "https://quotes.toscrape.com/login"
SITE = "https://quotes.toscrape.com"
SCROLL_URL = f"{SITE}/scroll"
API_URL = f"{SITE}/api/quotes"


# selectors
SEL_QUOTE = "div.quote"
SEL_TEXT = "span.text"
SEL_AUTHOR = "small.author"
SEL_TAG = "a.tag"
SEL_NEXT = "li.next a"

# selectors_Login
SEL_USER = "#username"
SEL_PASS = "#password"
SEL_SUBMIT = "input[type='submit']"
SEL_LOGOUT = "a[href='/logout']"

# selectors_Authors
SEL_AUTHOR_LINK = "a[href^='/author']"
SEL_A_NAME = "h3.author-title"
SEL_A_BORN_DATE = "span.author-born-date"
SEL_A_BORN_LOC = "span.author-born-location"
SEL_A_DESC = "div.author-description"


# Navegador

HEADLESS = True
TIMEOUT_MS = 15_000
USER_AGENT = "quotes-playwright/1.0 (proyecto de aprendizaje de scraping)"

# Reintentos
MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_SCROLLS = 50

# Pausa entre paginas
DELAY_BETWEEN_PAGES_S = 0.5

USERNAME = os.getenv("QUOTES_USER", "")
PASSWORD = os.getenv("QUOTES_PASSWORD", "")
# Salida
OUTPUT_JSON = DATA_DIR / "quotes.json"
OUTPUT_CSV = DATA_DIR / "quotes.csv"
OUTPUT_DB = DATA_DIR / "quotes.db"
OUTPUT_AUTHORS_JSON = DATA_DIR / "authors.json"
