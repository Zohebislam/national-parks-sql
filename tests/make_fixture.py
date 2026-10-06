"""Generate a small SYNTHETIC dataset with the exact column layout of the real
sources, used only to test that the pipeline and every query run correctly.
The values are random; nothing here is a real finding.

It deliberately includes the messiness the real files have: duplicate
(park, species) rows, 'Total' year rows, non-National-Park units, blank
fields, comma-formatted acres, and a status value missing from the lookup.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

CATEGORIES = [
    ("Vascular Plant", 0.55), ("Bird", 0.12), ("Insect", 0.08), ("Mammal", 0.05),
    ("Fish", 0.04), ("Fungi", 0.04), ("Nonvascular Plant", 0.04),
    ("Reptile", 0.02), ("Amphibian", 0.02), ("Invertebrate", 0.02),
    ("Slug/Snail", 0.01), ("Algae", 0.01),
]
STATUSES = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
            "Species of Concern", "Endangered", "Threatened", "In Recovery",
            "Under Review"]
GREEK = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
         "Iota", "Kappa", "Lambda", "Mu"]


def make(out_dir: Path, seed: int = 7) -> Path:
    rng = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    parks = []
    for i, g in enumerate(GREEK):
        parks.append({
            "Park Code": "T" + g[:3].upper().ljust(3, "X"),
            "Park Name": f"Testpark {g} National Park",
            "State": rng.choice(["CA", "UT", "WY", "AK", "FL", "TN"]),
            "Acres": f"{rng.randint(5_000, 3_000_000):,}",
            "Latitude": round(rng.uniform(25, 65), 2),
            "Longitude": round(rng.uniform(-150, -80), 2),
        })
    with (out_dir / "parks.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(parks[0]))
        w.writeheader()
        w.writerows(parks)

    pool = []
    cats, weights = zip(*CATEGORIES)
    for j in range(900):
        cat = rng.choices(cats, weights)[0]
        pool.append((f"Genus{j // 7} species{j}", cat, f"Order{j % 30}", f"Family{j % 80}"))

    header = ["Species ID", "Park Name", "Category", "Order", "Family",
              "Scientific Name", "Common Names", "Record Status", "Occurrence",
              "Nativeness", "Abundance", "Seasonality", "Conservation Status", ""]
    sid = 0
    with (out_dir / "species.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for p in parks:
            k = rng.randint(150, 600)
            non_native_p = rng.uniform(0.05, 0.3)
            for name, cat, order, fam in rng.sample(pool, k):
                sid += 1
                row = [f"{p['Park Code']}-{sid:04d}", p["Park Name"], cat, order, fam,
                       name, f"Common {name.split()[-1]}",
                       rng.choices(["Approved", "In Review"], [0.97, 0.03])[0],
                       rng.choices(["Present", "Probably Present", "Not Confirmed",
                                    "Not Present (Historical Report)"], [0.85, 0.05, 0.05, 0.05])[0],
                       "Not Native" if rng.random() < non_native_p
                       else rng.choices(["Native", "Unknown", ""], [0.92, 0.05, 0.03])[0],
                       rng.choice(["Common", "Uncommon", "Rare", "Abundant", ""]),
                       rng.choice(["Resident", "Breeder", "Migratory", ""]),
                       rng.choice(STATUSES), ""]
                w.writerow(row)
                if rng.random() < 0.01:                     # duplicate row
                    w.writerow(row)
        # a status value that is not in the lookup table
        w.writerow(["X-1", parks[0]["Park Name"], "Bird", "O", "F", "Genus0 species0",
                    "c", "Approved", "Present", "Native", "Rare", "", "Breeder", ""])

    vcols = ["year_raw", "gnis_id", "geometry", "metadata", "number_of_records",
             "parkname", "region", "state", "unit_code", "unit_name", "unit_type",
             "visitors", "year"]
    with (out_dir / "national_parks.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=vcols)
        w.writeheader()
        for p in parks:
            base = rng.uniform(5e4, 3e6)
            growth = rng.uniform(-0.01, 0.07)
            total = 0
            for y in range(1980, 2017):
                v = int(base * (1 + growth) ** (y - 1980) * rng.uniform(0.9, 1.1))
                total += v
                w.writerow({"year_raw": str(y), "unit_code": p["Park Code"],
                            "unit_name": p["Park Name"], "unit_type": "National Park",
                            "region": rng.choice(["PW", "IM", "SE"]), "state": p["State"],
                            "visitors": v, "year": y, "number_of_records": 1})
            w.writerow({"year_raw": "Total", "unit_code": p["Park Code"],
                        "unit_name": p["Park Name"], "unit_type": "National Park",
                        "visitors": total, "number_of_records": 1})
        w.writerow({"year_raw": "2016", "unit_code": "TMON", "unit_name": "Test Monument",
                    "unit_type": "National Monument", "visitors": 999, "year": 2016})
    return out_dir


if __name__ == "__main__":
    print(make(Path(__file__).parent / "fixture_data"))
