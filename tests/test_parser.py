"""Tests del parser: parse_raw, has_next_raw y quote_from_item.

Todos los tests leen fixtures de HTML guardadas en tests/fixtures/.
No hacen peticiones de red ni lanzan el navegador.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parser import parse_raw, has_next_raw, quote_from_item  # noqa: E402


def test_parse_raw_devuelve_10_citas_en_pagina_1(html_page1):
    quotes = parse_raw(html_page1)
    assert len(quotes) == 10


def test_parse_raw_campos_no_vacios(html_page1):
    q = parse_raw(html_page1)[0]
    assert q.text.strip()
    assert q.author.strip()
    assert isinstance(q.tags, list)
    assert q.author_url is not None
    assert q.author_url.startswith("https://quotes.toscrape.com/author/")


def test_parse_raw_autor_y_slug(html_page1):
    urls = [q.author_url for q in parse_raw(html_page1)]
    assert all(u is not None for u in urls)
    assert len({u for u in urls if u}) >= 2  # al menos dos autores distintos


def test_has_next_raw_pagina_1_tiene_siguiente(html_page1):
    assert has_next_raw(html_page1) is True


def test_has_next_raw_pagina_10_no_tiene_siguiente(html_page10):
    assert has_next_raw(html_page10) is False


def test_quote_from_item_con_slug():
    item = {
        "text": "Probando",
        "author": {"name": "Autor Prueba", "slug": "autor-prueba"},
        "tags": ["tag1", "tag2"],
    }
    q = quote_from_item(item)
    assert q.text == "Probando"
    assert q.author == "Autor Prueba"
    assert q.tags == ["tag1", "tag2"]
    assert q.author_url == "https://quotes.toscrape.com/author/autor-prueba"


def test_quote_from_item_sin_slug():
    item = {
        "text": "Sin autor",
        "author": {},
        "tags": [],
    }
    try:
        quote_from_item(item)
    except ValueError as e:
        assert "autor" in str(e).lower() or "author" in str(e).lower()
        return
    raise AssertionError("deberia haber levantado ValueError por autor vacio")
