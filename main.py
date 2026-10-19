import argparse
import sys

from src import config
from src.exporters import EXPORTERS, export
from src.scraper import scrape


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scraper de quotes.toscrape.com/js con Playwright"
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.pages is not None and args.pages < 1:
        print("--pages debe ser 1 o mayor ")
        return 2
    try:
        quotes = scrape(max_pages=args.pages, headless=args.headless)
    except Exception as e:
        print(f"Error durante el scraping: {e}")
        return 1

    if not quotes:
        print("No se encontraron citas, no se exporta nada.")
        return 1

    rutas = export(quotes, args.formats)
    print(f"\n{len(quotes)} citas guardadas:")
    for ruta in rutas:
        print(f" - {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
