"""Database connection helpers.

SQLite ships with Python, so the project needs no database server. Some SQLite
builds (e.g. older macOS system Python) are compiled without the math
functions the queries use (sqrt, log10, power); we register Python fallbacks
only when they are missing, so the SQL stays standard and portable.
"""
from __future__ import annotations

import math
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
ANALYSIS_DIR = SQL_DIR / "analysis"
DATA_RAW = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "national_parks.db"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
REPORTS_DIR = ROOT / "reports"


def _safe(fn):
    def wrapped(*args):
        if any(a is None for a in args):
            return None
        try:
            return fn(*args)
        except (ValueError, ZeroDivisionError, OverflowError):
            return None
    return wrapped


def _has_function(con: sqlite3.Connection, expr: str) -> bool:
    try:
        con.execute(f"SELECT {expr}").fetchone()
        return True
    except sqlite3.OperationalError:
        return False


def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    if sqlite3.sqlite_version_info < (3, 25, 0):
        raise RuntimeError(
            f"SQLite {sqlite3.sqlite_version} is too old (window functions need 3.25+)."
        )
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    fallbacks = {
        "sqrt": (1, "sqrt(4)", math.sqrt),
        "log10": (1, "log10(10)", math.log10),
        "power": (2, "power(2, 2)", math.pow),
    }
    for name, (nargs, probe, fn) in fallbacks.items():
        if not _has_function(con, probe):
            con.create_function(name, nargs, _safe(fn), deterministic=True)
    return con


def run_script(con: sqlite3.Connection, path: Path) -> None:
    con.executescript(path.read_text(encoding="utf-8"))


def query(con: sqlite3.Connection, sql: str) -> tuple[list[str], list[tuple]]:
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return cols, [tuple(r) for r in cur.fetchall()]
