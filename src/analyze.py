"""Run every query in sql/analysis/ and save each result as a CSV."""
from __future__ import annotations

import csv
from pathlib import Path

from .db import ANALYSIS_DIR, DB_PATH, RESULTS_DIR, connect, query

Result = tuple[list[str], list[tuple]]


def question_of(sql_path: Path) -> str:
    """First comment line, e.g. '-- Q02 · Which parks ...' -> 'Which parks ...'."""
    first = sql_path.read_text(encoding="utf-8").splitlines()[0]
    return first.lstrip("- ").split("·", 1)[-1].strip()


def run_all(db_path: Path = DB_PATH, results_dir: Path = RESULTS_DIR,
            verbose: bool = True) -> dict[str, Result]:
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    con = connect(db_path)
    out: dict[str, Result] = {}
    for path in sorted(ANALYSIS_DIR.glob("q*.sql")):
        cols, rows = query(con, path.read_text(encoding="utf-8"))
        out[path.stem] = (cols, rows)
        with (results_dir / f"{path.stem}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        if verbose:
            print(f"    {path.stem:<34} {len(rows):>5} rows  · {question_of(path)}")
    # Also export the per-park wide table for anyone who wants to explore it.
    cols, rows = query(con, "SELECT * FROM v_park_scorecard ORDER BY park_name")
    out["park_scorecard"] = (cols, rows)
    with (results_dir / "park_scorecard.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    con.close()
    return out


def as_dicts(result: Result) -> list[dict]:
    cols, rows = result
    return [dict(zip(cols, r)) for r in rows]
