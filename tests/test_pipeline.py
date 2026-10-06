"""End-to-end tests on a synthetic fixture (no network, no real data needed).

    python -m unittest discover tests -v
"""
from __future__ import annotations

import statistics
import tempfile
import unittest
from pathlib import Path

from src import analyze, build, charts, report
from src.db import connect, query
from tests.make_fixture import make


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.db = root / "test.db"
        cls.results_dir = root / "results"
        build.build(make(root / "raw"), cls.db, cls.results_dir, verbose=False)
        cls.results = analyze.run_all(cls.db, cls.results_dir, verbose=False)
        cls.con = connect(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        cls.tmp.cleanup()

    def scalar(self, sql):
        return self.con.execute(sql).fetchone()[0]

    # ---- model integrity -------------------------------------------------
    def test_no_orphans(self):
        self.assertEqual(self.con.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_one_row_per_park_species(self):
        self.assertEqual(
            self.scalar("SELECT count(*) FROM park_species"),
            self.scalar("SELECT count(*) FROM (SELECT DISTINCT park_code, taxon_id FROM park_species)"),
        )

    def test_duplicates_were_removed(self):
        self.assertGreater(self.scalar("SELECT count(*) FROM stg_species"),
                           self.scalar("SELECT count(*) FROM park_species"))

    def test_total_rows_and_other_unit_types_excluded(self):
        self.assertEqual(self.scalar("SELECT count(*) FROM annual_visits WHERE park_code = 'TMON'"), 0)
        self.assertEqual(self.scalar("SELECT count(DISTINCT year) FROM annual_visits"), 2016 - 1980 + 1)

    def test_comma_acres_parsed(self):
        self.assertGreater(self.scalar("SELECT min(acres) FROM parks"), 1000)

    def test_unknown_status_nulled(self):
        self.assertEqual(self.scalar(
            "SELECT count(*) FROM park_species WHERE conservation_status = 'Breeder'"), 0)

    # ---- analyses --------------------------------------------------------
    def test_every_query_returns_rows(self):
        for name, (_, rows) in self.results.items():
            with self.subTest(query=name):
                self.assertGreater(len(rows), 0)

    def test_shares_are_valid(self):
        for d in analyze.as_dicts(self.results["q05_invasive_pressure"]):
            self.assertTrue(0 <= d["pct_non_native"] <= 100)

    def test_quartiles_partition_parks(self):
        q = analyze.as_dicts(self.results["q09_pressure_vs_biodiversity"])
        self.assertEqual(sum(d["parks"] for d in q), self.scalar("SELECT count(*) FROM parks"))

    def test_sql_pearson_matches_python(self):
        _, rows = query(self.con, """
            SELECT log10(visitors_per_acre), non_native_share FROM v_park_scorecard
            WHERE visitors_per_acre > 0 AND species_richness > 0 AND cagr_10y IS NOT NULL""")
        expected = statistics.correlation([r[0] for r in rows], [r[1] for r in rows])
        got = next(d["pearson_r"] for d in analyze.as_dicts(self.results["q10_correlation_matrix"])
                   if d["x_metric"] == "log crowding" and d["y_metric"] == "non-native share")
        self.assertAlmostEqual(got, expected, places=3)

    def test_jaccard_bounds(self):
        for d in analyze.as_dicts(self.results["q11_park_similarity"]):
            self.assertTrue(0 < d["jaccard"] <= 1)

    def test_pressure_index_zscores_center_on_zero(self):
        rows = analyze.as_dicts(self.results["q13_park_risk_index"])
        self.assertAlmostEqual(sum(d["pressure_index"] for d in rows) / len(rows), 0, places=1)

    def test_hidden_gems_respect_filters(self):
        for d in analyze.as_dicts(self.results["q14_hidden_gems"]):
            self.assertGreaterEqual(d["richness_percentile"], 50)
            self.assertLess(d["visitors_percentile"], 50)

    def test_partial_correlation_matches_python(self):
        import math
        _, rows = query(self.con, """SELECT log10(visitors_per_acre), non_native_share, log10(acres)
                                     FROM v_park_scorecard
                                     WHERE visitors_per_acre > 0 AND non_native_share IS NOT NULL""")
        x, y, z = ([r[i] for r in rows] for i in range(3))

        def resid(v):
            mz, mv = statistics.mean(z), statistics.mean(v)
            b = sum((a - mz) * (c - mv) for a, c in zip(z, v)) / sum((a - mz) ** 2 for a in z)
            return [c - mv - b * (a - mz) for a, c in zip(z, v)]
        expected = statistics.correlation(resid(x), resid(y))
        got = next(d["pearson_r"] for d in analyze.as_dicts(self.results["q15_robustness_checks"])
                   if d["test"].startswith("Controlling"))
        self.assertAlmostEqual(got, expected, places=3)

    # ---- loader repair -----------------------------------------------------
    def test_shifted_species_row_is_repaired(self):
        raw = {"Common Names": "Manatee", "Record Status": " Manati", "Occurrence": "Approved",
               "Nativeness": "Present", "Abundance": "Unknown", "Seasonality": "Unknown",
               "Conservation Status": "", "": "Endangered"}
        fixed = build.repair_shifted_species_row(raw)
        self.assertEqual(fixed["Common Names"], "Manatee, Manati")
        self.assertEqual(fixed["Record Status"], "Approved")
        self.assertEqual(fixed["Occurrence"], "Present")
        self.assertEqual(fixed["Conservation Status"], "Endangered")
        ok = {"Record Status": "Approved", "Occurrence": "Present"}
        self.assertEqual(build.repair_shifted_species_row(ok), ok)

    # ---- outputs ---------------------------------------------------------
    def test_figures_and_report_render(self):
        out = Path(self.tmp.name)
        figs = charts.make_all(self.results, out / "figures")
        self.assertEqual(len(figs), 6)
        self.assertTrue(all(f.stat().st_size > 10_000 for f in figs))
        md = report.write(self.results, out / "FINDINGS.md").read_text()
        self.assertIn("Key findings", md)
        self.assertNotIn("None%", md)


if __name__ == "__main__":
    unittest.main()
