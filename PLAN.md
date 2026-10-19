# quotes-playwright — plan de fases

Objetivo: mismo oficio, tercera herramienta. Scrapear quotes.toscrape.com
(sitio con contenido dinámico) con Playwright y cerrar el portafolio de
tres repos: a mano (books-scraper) → framework (books-scrapy) → navegador
real (este).

## Mapa mental: lo que ya sabés → lo nuevo

    requests / Scrapy                    Playwright
    ---------------------------------------------------------------
    requests.get(url)                    page.goto(url) — un NAVEGADOR ejecuta HTML+JS
    BeautifulSoup .select(".clase")      page.locator(".clase") — mismo CSS, más potente
    soup.find_all("div.quote")           page.locator("div.quote").all()
    [el.get_text() for el in lista]      locator.inner_text() / all_text_contents()
    a::attr(href) (scrapy)               locator.get_attribute("href")
    "esperar que cargue" (no existía)    page.wait_for_selector() — o nada: los locators
                                         auto-esperan al materializarse
    reintentos/timeout del config       timeouts del navegador (goto, wait_for)
    ThreadPoolExecutor para imágenes     browser.new_context() × N (contexts aislados)
    login con Session de requests       page.fill() + page.click(); la sesión (cookies)
                                         vive en el context
    la API oculta que ves en F12 Network page.on("response", ...) para interceptarla

## El sitio, verificado con curl (15-oct)

    /                    10 quotes en el HTML crudo  (NO necesita navegador: el "antes")
    /js/                  0 en crudo, 10 en navegador (el JS las renderiza: el "por qué")
    /scroll               scroll infinito
    /login                form de login
    /api/quotes?page=N    JSON que alimenta a /js/ (la API oculta)

## Fases

    0. [x] Setup: venv uv, playwright + pytest, chromium, smoke 10/10 (15-oct)
    1. Primera página /js/: Quote(texto, autor, tags) desde el DOM renderizado
    2. Paginación: el botón "Next" (page.click) — ¿click real o URL directa?
    3. Autores: página /author/<slug>/ — datos del autor, relación quote.autor
    4. Login: /login con page.fill — qué cambia con sesión iniciada
    5. Scroll infinito (/scroll): wheel/End + esperar nodos nuevos
    6. Storage: JSON/CSV/SQLite (patrones de Proyecto2: reusar o reescribir)
    7. La API interceptada: page.on("response") contra /api/quotes — DOM vs API
       (la comparativa va al README)
    8. Tests sin red + README comparativo (tres enfoques) + publicar repo 3

## Fase 1 — hints (arrancá acá)

1. La API sync (la simple, la de los ejemplos):
   `from playwright.sync_api import sync_playwright`. Todo corre dentro de
   `with sync_playwright() as p: ...`.
2. Estructura de siempre:
   `p.chromium.launch(headless=True)` → `browser.new_page()` → `page.goto(url)`
   → `browser.close()` al final. (Si después querés sesiones aisladas por
   datos distintos: `new_context().new_page()`.)
3. Después del goto el JS sigue corriendo: lo que curl ve vacío se llena solo.
   `page.wait_for_selector(".quote")` es tu "el dato ya está". O dejá que el
   locator espere solo cuando lo materializás.
4. Un locator es promesa + acción en un paso: `page.locator(".quote")` no
   busca nada todavía; `.count()`, `.all()`, `.inner_text()` lo materializan.
5. Modelo sugerido (dataclass, como models.py del Proyecto2):
   `Quote(texto: str, autor: str, tags: list[str])`. Los tags de cada quote
   están en `.tags .tag` dentro del nodo.
6. Ejercicio 1: extraer la página 1 de /js/ e imprimir
   (texto, autor, [tags]) — sin archivos ni storage. Meta: 10 filas.
7. Cuando funcione: quitá `wait_for_selector` y volvé a correr unas
   cuantas veces. ¿Se rompe siempre? ¿A veces? Esa carrera es el aprendizaje
   central de hoy — anotala para el README.

## Convenciones

- Código tuyo: hints y revisiones, no soluciones.
- Verificar el PRODUCTO (hoy el conteo en pantalla; el disco cuando haya
  storage), nunca "no explotó".
- Git ya inicializado (rama main, sin commits). Completar .gitignore
  (data/ cuando exista) antes del primer push.
