# quotes-playwright (Proyecto4)

Scraper de [quotes.toscrape.com](https://quotes.toscrape.com) con **Playwright** (navegador real, contenido dinámico).
Pieza #3 del portafolio Fiverr: a mano (books-scraper) → framework (books-scrapy) → navegador real (este).

## El sitio y por qué Playwright

| URL | ¿Qué devuelve curl? | ¿Necesita navegador? |
|-----|---------------------|----------------------|
| `/` | 10 citas en HTML crudo | No (estática) |
| `/js/` | 0 citas en crudo, 10 en navegador | Sí (JS las renderiza) |
| `/scroll` | Scroll infinito | Sí |
| `/login` | Form de login | Sí |
| `/api/quotes?page=N` | JSON (la API oculta) | No (petición directa) |

En `/js/` los datos viajan **inline** en el HTML (`var data = [...]`), pero el DOM se arma con jQuery. curl ve el dato pero no el DOM renderizado. Ese es el caso de uso que justifica Playwright: leer lo que el navegador ejecuta.

## Modos de scraping

- `dom` — lee el HTML renderizado con `page.locator()` (CSS selectors).
- `inline` — lee la variable JS `data` incrustada en la página (más rápido, sin depender del DOM).
- `raw` — HTML crudo sin navegador, parsea `var data =` directamente.
- `scroll` — `/scroll` con `page.evaluate("window.scrollTo(...)")` e intercepta `/api/quotes` vía `page.on("response")`.
- `--authors` — además scrapea la página estática de cada autor (`/author/<slug>/`).

Ejemplo:

```
source .venv/bin/activate
python main.py --mode inline --pages 2 --format json csv --authors
```

## Tres enfoques comparados

| | books-scraper (a mano) | books-scrapy (framework) | quotes-playwright (navegador real) |
|---|---|---|---|
| Herramienta | `requests` + `BeautifulSoup` | `Scrapy` | `Playwright` (Chromium headless) |
| Contenido dinámico | No lo ve (HTML crudo) | No lo ve (sin JS) | Sí lo ejecuta y renderiza |
| Esperas | No necesita | No necesita | `wait_for_selector`, timeouts del navegador |
| Selectores | BeautifulSoup `.select()` | CSS de Scrapy / XPath | `page.locator()` + `get_attribute()` |
| Sesión / login | `requests.Session()` | middlewares de Scrapy | `browser.new_context()` (cookies aisladas) |
| API oculta | F12 Network → petición directa | F12 Network → petición directa | `page.on("response")` vs DOM inline |
| Scroll infinito | No aplica | No aplica | `mouse.wheel` / `window.scrollTo` + esperar nodos |
| Ideal para | Sitios estáticos | Sitios estáticos a gran escala | Sitios que requieren JS |

## Fases del proyecto

0. Setup: venv (uv), playwright + pytest, Chromium, smoke 10/10.
1. Primera página `/js/`: Quote(texto, autor, tags) desde el DOM.
2. Paginación: botón "Next" (URL directa, no `page.click`).
3. Autores: página `/author/<slug>/` — datos del autor, relación quote.autor.
4. Login: `/login` con `page.fill()` + `page.click()`.
5. Scroll infinito `/scroll`: wheel + esperar nodos nuevos.
6. Storage: JSON / CSV / SQLite (upsert por `(text, author)`).
7. API interceptada: `page.on("response")` contra `/api/quotes` — DOM vs API.
8. Tests sin red + README comparativo (este archivo) + publicar repo.

## Tests sin red

Los tests de `tests/` leen fixtures de HTML guardadas en `tests/fixtures/`. No hacen red ni lanzan el navegador.

```
pytest -v
```

## Requisitos

```
playwright==1.64.0
pytest==9.1.1
```

Chromium ya instalado con `playwright install chromium` (headless shell en `~/.cache/ms-playwright`).

## Repos hermanos del portafolio

- books-scraper — a mano (requests + BeautifulSoup)
- books-scrapy — framework Scrapy
- quotes-playwright — navegador real Playwright (este repo)
