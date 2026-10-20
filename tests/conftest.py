"""Fixtures compartidas para los tests de quotes-playwright."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def html_page1():
    """HTML renderizado de /js/ pagina 1 (fixture sin red)."""
    return (FIXTURES / "page1.html").read_text(encoding="utf-8")


@pytest.fixture
def html_page10():
    """HTML renderizado de /js/ pagina 10 (ultima, sin boton Next)."""
    return (FIXTURES / "page10.html").read_text(encoding="utf-8")
