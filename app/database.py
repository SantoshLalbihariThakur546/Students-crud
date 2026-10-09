"""SQLite connection handling and schema creation."""
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterator

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("STUDENTS_DB", BASE_DIR / "students.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    date_of_birth   TEXT NOT NULL,            -- ISO format: YYYY-MM-DD
    email           TEXT UNIQUE,              -- stored lower-case, NULL allowed
    phone           TEXT,
    course          TEXT,
    address         TEXT,
    enrollment_date TEXT,                     -- ISO format: YYYY-MM-DD
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_students_name ON students(name);
CREATE INDEX IF NOT EXISTS idx_students_dob  ON students(date_of_birth);
"""


def get_connection() -> sqlite3.Connection:
    # check_same_thread=False: FastAPI runs sync endpoints in a thread pool.
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db() -> None:
    """Create the table if it does not exist (runs at app start-up)."""
    with closing(get_connection()) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request, always closed."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
