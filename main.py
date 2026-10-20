import argparse
import sys

from src import config
from src.exporters import EXPORTERS, export, export_authors
from src.scraper import MODES, scrape


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scraper de quotes.toscrape.com/js con Playwright"
    )
    parser.add_argument(
        "--mode",
        choices=MODES,
        default="dom",
        help="dom: lee el html renderizado | inline: lee la variable JS `data`|"
        "raw: html crudo sin Navegador | scroll: scroll infinito + api",
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=None,
        help="Maximo de paginas a recorrer (por defecto, todas)",
    )
    parser.add_argument(
        "--format",
        nargs="+",
        choices=list(EXPORTERS),
        default=["json"],
        dest="formats",
        help="Formato de salida: json csv sqlite",
    )
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=config.HEADLESS,
        help="Navegador sin ventana (--no-headless para verlo)",
    )
    parser.add_argument(
        "--authors",
        action="store_true",
        help="Scrapea tambien la pagina de cada author",
    )
    parser.add_argument("--user", default=config.USERNAME, help="Usuario del login")
    parser.add_argument(
        "--password", default=config.PASSWORD, help="Contrasena del login"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.pages is not None and args.pages < 1:
        print("--pages debe ser 1 o mayor.")
        return 2
    creds = (args.user, args.password) if args.user and args.password else None

    try:
        quotes, authors = scrape(
            mode=args.mode,
            max_pages=args.pages,
            headless=args.headless,
            credentials=creds,
            with_authors=args.authors,
        )
    except Exception as e:
        print(f"Error durante el scraping: {e}")
        return 1

    if not quotes:
        print("No se encontraron citas, no se exporta nada.")
        return 1

    rutas = export(quotes, args.formats)
    if authors:
        rutas.extend(export_authors(authors))
    print(f"\n{len(quotes)} citas guardadas:")
    for ruta in dict.fromkeys(rutas):
        print(f" - {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
