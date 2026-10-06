"""Fetch the three public source files into data/raw/.

Sources
-------
1. parks.csv, species.csv  - NPS "Biodiversity in National Parks" (Kaggle,
   nationalparkservice/park-biodiversity). Species lists from NPSpecies.
2. national_parks.csv      - NPS annual recreation visits per unit, 1904-2016
   (TidyTuesday 2019-09-17, compiled from data.world / NPS IRMA stats).
"""
from __future__ import annotations

import shutil
import subprocess
import urllib.request
import zipfile

from .db import DATA_RAW

VISITS_URL = (
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/"
    "data/2019/2019-09-17/national_parks.csv"
)
KAGGLE_SLUG = "nationalparkservice/park-biodiversity"
KAGGLE_PAGE = "https://www.kaggle.com/datasets/" + KAGGLE_SLUG

REQUIRED = ["parks.csv", "species.csv", "national_parks.csv"]


def _download_visits() -> None:
    target = DATA_RAW / "national_parks.csv"
    if target.exists():
        print(f"  ✓ {target.name} already present")
        return
    print(f"  ↓ downloading visitation data ...")
    urllib.request.urlretrieve(VISITS_URL, target)
    print(f"  ✓ saved {target.name} ({target.stat().st_size / 1e6:.1f} MB)")


def _download_kaggle() -> None:
    if (DATA_RAW / "parks.csv").exists() and (DATA_RAW / "species.csv").exists():
        print("  ✓ parks.csv and species.csv already present")
        return
    zip_in_raw = DATA_RAW / "archive.zip"
    if zip_in_raw.exists():
        _unzip(zip_in_raw)
        return
    if shutil.which("kaggle"):
        print("  ↓ downloading biodiversity data with the Kaggle CLI ...")
        subprocess.run(
            ["kaggle", "datasets", "download", "-d", KAGGLE_SLUG,
             "-p", str(DATA_RAW), "--unzip"],
            check=True,
        )
        print("  ✓ parks.csv and species.csv saved")
        return
    print(
        "\n  ! parks.csv / species.csv not found. Get them one of two ways:\n"
        f"    a) Browser: open {KAGGLE_PAGE}, click Download, and put\n"
        f"       archive.zip (or the two CSVs) in {DATA_RAW}\n"
        "    b) CLI: pip install kaggle, add your API token\n"
        "       (kaggle.com > Settings > Create New Token), then re-run.\n"
    )


def _unzip(path) -> None:
    with zipfile.ZipFile(path) as z:
        for name in ("parks.csv", "species.csv"):
            z.extract(name, DATA_RAW)
    print("  ✓ extracted parks.csv and species.csv from archive.zip")


def main() -> bool:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    _download_visits()
    _download_kaggle()
    missing = [f for f in REQUIRED if not (DATA_RAW / f).exists()]
    if missing:
        print(f"  Missing: {', '.join(missing)}")
        return False
    return True
