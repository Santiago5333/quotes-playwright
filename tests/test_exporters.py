"""Tests de los exporters: JSON, CSV, SQLite y el dispatch de export().

Todos los tests escriben en directorios temporales (pytest tmp_path).
No hacen peticiones de red ni lanzan el navegador.
"""

import csv
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import Quote  # noqa: E402
from src.exporters import _to_json, _to_csv, _to_sqlite, export, EXPORTERS  # noqa: E402

QUOTES = [
    Quote(
        text="texto 1",
        author="Autor 1",
        tags=["a", "b"],
        author_url="https://ejemplo.com/1",
    ),
    Quote(
        text="texto 2",
        author="Autor 2",
        tags=[],
        author_url=None,
    ),
]


def test_to_json_crea_archivo_valido(tmp_path):
    destino = tmp_path / "quotes.json"
    ruta = _to_json(QUOTES, destino)
    assert ruta == destino
    data = json.loads(destino.read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[0]["author"] == "Autor 1"
    assert data[0]["author_url"] == "https://ejemplo.com/1"
    assert data[1]["author_url"] is None


def test_to_csv_4_columnas(tmp_path):
    destino = tmp_path / "quotes.csv"
    _to_csv(QUOTES, destino)
    with destino.open(encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        assert lector.fieldnames == ["text", "author", "tags", "author_url"]
        filas = list(lector)
    assert len(filas) == 2
    assert filas[0]["tags"] == "a|b"
    assert filas[0]["author_url"] == "https://ejemplo.com/1"
    assert filas[1]["tags"] == ""
    assert filas[1]["author_url"] == ""


def test_to_sqlite_upsert_no_duplica_al_reexportar(tmp_path):
    destino = tmp_path / "quotes.db"
    _to_sqlite(QUOTES, destino)
    _to_sqlite(QUOTES, destino)  # misma data otra vez: upsert, no duplicar
    conn = sqlite3.connect(destino)
    try:
        count = conn.execute("SELECT count(*) FROM quotes").fetchone()[0]
    finally:
        conn.close()
    assert count == 2


def test_export_dispatch_todos_los_formatos_validos(tmp_path):
    rutas = export(QUOTES, ["json", "csv", "sqlite"])
    assert len(rutas) == 3
    assert all(r.exists() for r in rutas)


def test_export_formato_invalido_levanta_valuerror():
    try:
        export(QUOTES, ["xml"])
        raise AssertionError("deberia haber levantado ValueError")
    except ValueError as e:
        assert "json" in str(e)
        assert "csv" in str(e)
        assert "sqlite" in str(e)


def test_exporters_registro_tiene_tres_formatos():
    assert set(EXPORTERS) == {"json", "csv", "sqlite"}
