"""SQLite connection + versioned migrations (PRAGMA user_version)."""
from __future__ import annotations

import os
import sqlite3

_V1 = """
CREATE TABLE foods (
    id          INTEGER PRIMARY KEY,
    source      TEXT NOT NULL,            -- manual | off | usda | ai
    source_id   TEXT NOT NULL,
    name        TEXT NOT NULL,
    brand       TEXT,
    category    TEXT,
    kcal_100g   REAL NOT NULL,
    protein_100g REAL NOT NULL,
    carbs_100g  REAL NOT NULL,
    fat_100g    REAL NOT NULL,
    serving_g   REAL,                     -- weight of one serving/piece/slice, if known
    package_g   REAL,                     -- weight of the whole package/loaf, if known
    updated_at  TEXT NOT NULL,
    UNIQUE (source, source_id)
);
CREATE INDEX idx_foods_brand ON foods (brand COLLATE NOCASE);
CREATE INDEX idx_foods_category ON foods (category);

CREATE VIRTUAL TABLE foods_fts USING fts5(
    name, brand, category,
    content='foods', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER foods_ai AFTER INSERT ON foods BEGIN
    INSERT INTO foods_fts(rowid, name, brand, category) VALUES (new.id, new.name, new.brand, new.category);
END;
CREATE TRIGGER foods_ad AFTER DELETE ON foods BEGIN
    INSERT INTO foods_fts(foods_fts, rowid, name, brand, category) VALUES ('delete', old.id, old.name, old.brand, old.category);
END;
CREATE TRIGGER foods_au AFTER UPDATE ON foods BEGIN
    INSERT INTO foods_fts(foods_fts, rowid, name, brand, category) VALUES ('delete', old.id, old.name, old.brand, old.category);
    INSERT INTO foods_fts(rowid, name, brand, category) VALUES (new.id, new.name, new.brand, new.category);
END;

CREATE TABLE entries (
    id          INTEGER PRIMARY KEY,
    logged_at   TEXT NOT NULL,            -- UTC ISO-8601
    local_date  TEXT NOT NULL,            -- YYYY-MM-DD in the configured timezone at log time
    raw_text    TEXT NOT NULL
);
CREATE INDEX idx_entries_local_date ON entries (local_date);

CREATE TABLE entry_items (
    id          INTEGER PRIMARY KEY,
    entry_id    INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    food_id     INTEGER REFERENCES foods(id) ON DELETE SET NULL,
    name        TEXT NOT NULL,
    amount_text TEXT NOT NULL,
    grams       REAL,
    kcal        REAL, protein REAL, carbs REAL, fat REAL,   -- NULL while unresolved
    source      TEXT NOT NULL,            -- db | ai | manual | unresolved
    status      TEXT NOT NULL,            -- resolved | unresolved
    note        TEXT
);
CREATE INDEX idx_items_entry ON entry_items (entry_id);

CREATE TABLE ingest_runs (
    id          INTEGER PRIMARY KEY,
    source      TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    stored      INTEGER NOT NULL DEFAULT 0,
    skipped     INTEGER NOT NULL DEFAULT 0,
    error       TEXT
);
"""

MIGRATIONS = [_V1]


def connect(path: str) -> sqlite3.Connection:
    if path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    migrate(conn)
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for version, script in enumerate(MIGRATIONS, start=1):
        if version > current:
            conn.executescript(script)
            conn.execute(f"PRAGMA user_version = {version}")
            conn.commit()
