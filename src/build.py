"""Build the SQLite database: load raw CSVs into staging, then run the SQL
pipeline (schema -> transform -> views) and the data-quality report."""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from .db import DATA_RAW, DB_PATH, RESULTS_DIR, SQL_DIR, connect, query, run_script

# Source header -> staging column. Matching by header name (not position)
# makes the loader robust to column re-ordering and extra unnamed columns.
PARKS_MAP = {
    "Park Code": "park_code", "Park Name": "park_name", "State": "state",
    "Acres": "acres", "Latitude": "latitude", "Longitude": "longitude",
}
SPECIES_MAP = {
    "Species ID": "species_id", "Park Name": "park_name", "Category": "category",
    "Order": "taxon_order", "Family": "family", "Scientific Name": "scientific_name",
    "Common Names": "common_names", "Record Status": "record_status",
    "Occurrence": "occurrence", "Nativeness": "nativeness", "Abundance": "abundance",
    "Seasonality": "seasonality", "Conservation Status": "conservation_status",
}
VISITS_MAP = {
    "year_raw": "year_raw", "unit_code": "unit_code", "unit_name": "unit_name",
    "unit_type": "unit_type", "region": "region", "state": "state",
    "visitors": "visitors",
}


RECORD_STATUSES = {"Approved", "In Review"}


def repair_shifted_species_row(row: dict) -> dict:
    """A comma inside 'Common Names' shifts every later field one column right
    in ~60 source rows (the overflow lands in the unnamed 14th column). Detect
    it by 'Record Status' holding a non-status value while 'Occurrence' holds a
    real one, then glue the name back together and shift fields left."""
    if (row.get("Record Status") not in RECORD_STATUSES
            and row.get("Occurrence") in RECORD_STATUSES):
        row = dict(row)
        row["Common Names"] = f"{row['Common Names']},{row['Record Status']}"
        order = ["Record Status", "Occurrence", "Nativeness", "Abundance",
                 "Seasonality", "Conservation Status", ""]
        for here, nxt in zip(order, order[1:]):
            row[here] = row.get(nxt)
        row[""] = None
    return row


def _load_csv(con: sqlite3.Connection, path: Path, table: str,
              colmap: dict[str, str], row_filter=None, row_fixer=None) -> int:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        # Some copies of the visitation file call the raw year column "year".
        colmap = {("year" if src == "year_raw" and src not in fields else src): dst
                  for src, dst in colmap.items()}
        missing = set(colmap) - fields
        if missing:
            raise ValueError(f"{path.name} is missing expected columns: {sorted(missing)}")
        targets = list(colmap.values())
        sql = (f"INSERT INTO {table} ({', '.join(targets)}) "
               f"VALUES ({', '.join('?' * len(targets))})")
        rows = (
            tuple(r.get(src) for src in colmap)
            for r in map(row_fixer or (lambda x: x), reader)
            if row_filter is None or row_filter(r)
        )
        con.executemany(sql, rows)
    return con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def build(raw_dir: Path = DATA_RAW, db_path: Path = DB_PATH,
          results_dir: Path = RESULTS_DIR, verbose: bool = True) -> dict:
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    con = connect(db_path)
    log = print if verbose else (lambda *a, **k: None)

    log("  • creating schema")
    run_script(con, SQL_DIR / "01_schema.sql")

    log("  • loading staging tables")
    n_parks = _load_csv(con, raw_dir / "parks.csv", "stg_parks", PARKS_MAP)
    n_species = _load_csv(con, raw_dir / "species.csv", "stg_species", SPECIES_MAP,
                          row_fixer=repair_shifted_species_row)
    # Only National Parks (not monuments, seashores, ...) and real year rows.
    n_visits = _load_csv(
        con, raw_dir / "national_parks.csv", "stg_visits", VISITS_MAP,
        row_filter=lambda r: (r.get("unit_type") or "").strip() == "National Park",
    )
    log(f"    stg_parks={n_parks:,}  stg_species={n_species:,}  stg_visits={n_visits:,}")

    log("  • transforming into model tables")
    run_script(con, SQL_DIR / "02_transform.sql")
    log("  • creating analytical views")
    run_script(con, SQL_DIR / "03_views.sql")
    con.commit()

    counts = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ("parks", "taxa", "park_species", "annual_visits")}
    log("    " + "  ".join(f"{k}={v:,}" for k, v in counts.items()))

    log("  • running data-quality checks")
    cols, rows = query(con, (SQL_DIR / "04_data_quality.sql").read_text())
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    with (results_dir / "00_data_quality.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    for name, observed, expectation, status in rows:
        log(f"    [{status:4}] {name}: {observed:,} (expected {expectation})")
    con.close()

    if any(r[3] == "FAIL" for r in rows):
        raise RuntimeError("Data-quality check FAILED; see results/00_data_quality.csv")
    return counts
