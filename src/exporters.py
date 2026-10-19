import csv
import json
import sqlite3
from dataclasses import fields
from pathlib import Path

from src import config
from src.models import Quote


def _prepare(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _to_json(quotes: list[Quote], path: Path = config.OUTPUT_JSON) -> Path:
    _prepare(path)
    data = [q.to_dict() for q in quotes]
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def _to_csv(quotes: list[Quote], path: Path = config.OUTPUT_CSV) -> Path:
    _prepare(path)
    fieldnames = [f.name for f in fields(Quote)]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for q in quotes:
            row = q.to_dict()
            row["tags"] = "|".join(q.tags)
            writer.writerow(row)
    return path


def _to_sqlite(quotes: list[Quote], path: Path = config.OUTPUT_DB) -> Path:
    _prepare(path)
    conn = sqlite3.connect(path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                author TEXT NOT NULL,
                tags TEXT,
                UNIQUE (text, author)
                )
                """
            )
            conn.executemany(
                """
                INSERT INTO quotes (text, author, tags)
                VALUES (:text, :author, :tags)
                ON CONFLICT (text, author) DO UPDATE SET tags = excluded.tags
                """,
                [
                    {"text": q.text, "author": q.author, "tags": "|".join(q.tags)}
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
