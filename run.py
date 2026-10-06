"""National Parks SQL project: one entry point for the whole pipeline.

    python run.py download   # fetch raw data into data/raw/
    python run.py build      # load + clean into data/national_parks.db
    python run.py analyze    # run 14 SQL analyses -> results/, figures/, reports/
    python run.py all        # all of the above
"""
from __future__ import annotations

import argparse
import sys

from src import analyze, build, charts, download, report
from src.db import DB_PATH, FIGURES_DIR, REPORTS_DIR, RESULTS_DIR


def do_download() -> bool:
    print("\n[1/3] Download")
    return download.main()


def do_build() -> None:
    print("\n[2/3] Build database")
    build.build()
    print(f"  ✓ {DB_PATH.relative_to(DB_PATH.parent.parent.parent)}")


def do_analyze() -> None:
    print("\n[3/3] Analyze")
    if not DB_PATH.exists():
        sys.exit("  Database not found. Run `python run.py build` first.")
    results = analyze.run_all()
    figs = charts.make_all(results, FIGURES_DIR)
    md = report.write(results, REPORTS_DIR / "FINDINGS.md")
    print(f"  ✓ {len(results)} result tables in {RESULTS_DIR.name}/, "
          f"{len(figs)} figures in {FIGURES_DIR.name}/, report at reports/{md.name}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("step", choices=["download", "build", "analyze", "all"])
    step = p.parse_args().step
    if step in ("download", "all") and not do_download():
        sys.exit(1)
    if step in ("build", "all"):
        do_build()
    if step in ("analyze", "all"):
        do_analyze()


if __name__ == "__main__":
    main()
