import csv
import json
import sqlite3
from contextlib import closing
from dataclasses import fields
from pathlib import Path

from src import config
from src.models import Author, Quote
from src.scraper import MODES, scrape


def _prepare(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _ensure_colum(conn: sqlite3.Connection, table: str, colum: str, tipo: str) -> None:
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    if cols and colum not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {colum} {tipo}")


def _to_json(quotes: list[Quote], path: Path = config.OUTPUT_JSON) -> Path:
    _prepare(path)
    data = [q.to_dict() for q in quotes]
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def _to_csv(quotes: list[Quote], path: Path = config.OUTPUT_CSV) -> Path:
    _prepare(path)
    compos = ["text", "author", "tags", "author_url"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=compos)
        writer.writeheader()
        for q in quotes:
            row = q.to_dict()
            row["tags"] = "|".join(q.tags)
            writer.writerow(row)
    return path


def _to_sqlite(quotes: list[Quote], path: Path = config.OUTPUT_DB) -> Path:
    _prepare(path)
    try:
        with closing(sqlite3.connect(path)) as conn, conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                author TEXT NOT NULL,
                tags TEXT,
                author_url TEXT,
                UNIQUE (text, author)
                )
                """)
            _ensure_colum(conn, "quotes", "author_url", "TEXT")
            conn.executemany(
                """
                INSERT INTO quotes (text, author, tags, author_url)
                VALUES (:text, :author, :tags, :author_url)
                ON CONFLICT (text, author) DO UPDATE SET
                    tags = excluded.tags,
                    author_url = excluded.author_url
                """,
                [
                    {
                        "text": q.text,
                        "author": q.author,
                        "tags": "|".join(q.tags),
                        "author_url": q.author_url,
                    }
                    for q in quotes
                ],
            )
    finally:
        conn.close()
    return path


EXPORTERS = {"json": _to_json, "csv": _to_csv, "sqlite": _to_sqlite}


def export(quotes: list[Quote], formats: list[str]) -> list[Path]:
    paths = []
    for fmt in formats:
        if fmt not in EXPORTERS:
            valid_formats = ", ".join(sorted(EXPORTERS))
            raise ValueError(f"Formato no soportado: {fmt}. Válidos: {valid_formats}")
        paths.append(EXPORTERS[fmt](quotes))
    return paths


def export_authors(authors: list[Author]) -> list[Path]:
    """Guarda autores en authors.json y en la tabla authors de quotes.db."""
    if not authors:
        return []

    _prepare(config.OUTPUT_AUTHORS_JSON)
    with config.OUTPUT_AUTHORS_JSON.open("w", encoding="utf-8") as f:
        json.dump([a.to_dict() for a in authors], f, ensure_ascii=False, indent=2)

    with closing(sqlite3.connect(config.OUTPUT_DB)) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS authors (
                url TEXT PRIMARY KEY,
                name TEXT,
                born_date TEXT,
                born_location TEXT,
                description TEXT
            )
        """)
        conn.executemany(
            """
            INSERT INTO authors (url, name, born_date, born_location, description)
            VALUES (:url, :name, :born_date, :born_location, :description)
            ON CONFLICT (url) DO UPDATE SET
                name = excluded.name,
                born_date = excluded.born_date,
                born_location = excluded.born_location,
                description = excluded.description
            """,
            [a.to_dict() for a in authors],
        )
    return [config.OUTPUT_AUTHORS_JSON, config.OUTPUT_DB]
