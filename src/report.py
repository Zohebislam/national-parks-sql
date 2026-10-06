"""Write reports/FINDINGS.md: every number is pulled from the query results,
so the write-up regenerates itself whenever the data changes."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from .analyze import as_dicts


def _table(rows: list[dict], cols: list[tuple[str, str]], n: int = 5) -> str:
    head = "| " + " | ".join(label for _, label in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    body = []
    for d in rows[:n]:
        cells = []
        for key, _ in cols:
            v = d[key]
            if isinstance(v, float):
                v = f"{v:,.2f}"
            elif isinstance(v, int):
                v = f"{v:,}"
            cells.append(str(v).replace(" National Parks", "").replace(" National Park", "") if v is not None else "–")
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([head, sep, *body])


def _direction(r: float) -> str:
    if r is None:
        return "no measurable"
    s = "strong" if abs(r) >= 0.5 else "moderate" if abs(r) >= 0.3 else "weak"
    return f"{s} {'positive' if r > 0 else 'negative'}"


def write(results: dict, path: Path) -> Path:
    ov = as_dicts(results["q01_dataset_overview"])[0]
    rich = as_dicts(results["q02_biodiversity_leaderboard"])
    cat = as_dicts(results["q03_category_mix"])
    risk = as_dicts(results["q04_threatened_hotspots"])
    inv = as_dicts(results["q05_invasive_pressure"])
    trend = as_dicts(results["q06_system_visitation_trend"])
    growth = as_dicts(results["q07_fastest_growing_parks"])
    crowd = as_dicts(results["q08_crowding_index"])
    quart = as_dicts(results["q09_pressure_vs_biodiversity"])
    corr = {(d["x_metric"], d["y_metric"]): d for d in as_dicts(results["q10_correlation_matrix"])}
    twins = as_dicts(results["q11_park_similarity"])
    unique = as_dicts(results["q12_unique_species"])
    index = as_dicts(results["q13_park_risk_index"])
    gems = as_dicts(results["q14_hidden_gems"])
    robust = {d["test"]: d["pearson_r"] for d in as_dicts(results["q15_robustness_checks"])}
    r_nohi = robust.get("Excluding Hawaii (island outliers)")
    r_partial = robust.get("Controlling for park size (partial r)")

    peak = max(trend, key=lambda d: d["total_visitors"])
    first_decade = next((d for d in trend if d["year"] == ov["last_visit_year"] - 10), None)
    decade_growth = (
        100 * (trend[-1]["total_visitors"] / first_decade["total_visitors"] - 1)
        if first_decade else None
    )
    invaded_cat = max((d for d in cat if d["pct_non_native"] is not None and d["park_records"] >= 100),
                      key=lambda d: d["pct_non_native"], default=None)
    q_hi, q_lo = quart[0], quart[-1]
    r_inv = corr.get(("log crowding", "non-native share"), {}).get("pearson_r")
    r_risk = corr.get(("log crowding", "at-risk per 1k"), {}).get("pearson_r")
    r_size = corr.get(("log park size", "non-native share"), {}).get("pearson_r")

    md = f"""# Findings: Visitor Pressure and Biodiversity in U.S. National Parks

*Auto-generated from `sql/analysis/` on {date.today():%B %d, %Y}. Every number below
comes from a query result in `results/`; re-run `python run.py all` to refresh.*

## Scope
{ov['parks']} national parks across {ov['states']} states covering
{ov['total_acres']:,} acres, {ov['distinct_species']:,} distinct species
({ov['park_species_records']:,} park-level records), and visitation from
{ov['first_visit_year']} to {ov['last_visit_year']}
({ov['visitors_last_year']:,} visits in {ov['last_visit_year']}).

## Key findings

1. **{'Visitation is at a record high.' if peak['year'] == ov['last_visit_year'] else 'Visitation has peaked.'}** Total visits peaked in {peak['year']} at
   {peak['total_visitors']:,}{f", up {decade_growth:.1f}% over the final decade of data" if decade_growth is not None else ""}.
2. **Crowding varies by orders of magnitude.** {crowd[0]['park_name']} sees
   {crowd[0]['visitors_per_acre']:,.2f} visitors per acre, versus
   {crowd[-1]['visitors_per_acre']:,.4f} at {crowd[-1]['park_name']}.
3. **Most crowded vs. least crowded parks.** The top crowding quartile averages
   {q_hi['avg_pct_non_native']}% non-native species and {q_hi['avg_at_risk_per_1k_species']}
   at-risk species per 1,000, compared with {q_lo['avg_pct_non_native']}% and
   {q_lo['avg_at_risk_per_1k_species']} in the least crowded quartile.
4. **Correlation check.** Across parks, crowding has a {_direction(r_inv)} relationship
   with non-native share (r = {r_inv}) and a {_direction(r_risk)} relationship with
   at-risk species density (r = {r_risk}). Park size has a {_direction(r_size)}
   relationship with non-native share (r = {r_size}), so size is a confounder to keep in mind.
5. **Robustness (Q15).** The crowding–invasion link holds when Hawaii's island parks are
   removed (r = {r_nohi}) but weakens to r = {r_partial} after controlling for park size:
   part of the pattern is simply that small parks are both more crowded and easier to invade.
6. **{invaded_cat['category'] if invaded_cat else 'n/a'}** is the most invaded category
   ({invaded_cat['pct_non_native'] if invaded_cat else '–'}% of records non-native).
7. **{index[0]['park_name']}** tops the composite Pressure Index
   ({index[0]['pressure_index']}), driven mainly by {index[0]['main_driver']}.
8. **Irreplaceable parks.** {unique[0]['park_name'] if unique else 'n/a'} holds the most
   species found in no other national park ({unique[0]['species_found_only_here'] if unique else 0:,}).

## Supporting tables

**Most biodiverse parks (Q02)**
{_table(rich, [("richness_rank", "#"), ("park_name", "Park"), ("species_richness", "Species"), ("species_per_1k_acres", "Per 1k acres")])}

**Most at-risk species (Q04)**
{_table(risk, [("risk_rank", "#"), ("park_name", "Park"), ("esa_listed", "ESA-listed"), ("at_risk_total", "At-risk"), ("most_at_risk_category", "Top category")])}

**Most invaded parks (Q05)**
{_table(inv, [("park_name", "Park"), ("pct_non_native", "% non-native"), ("pts_vs_system_avg", "pts vs avg")])}

**Fastest-growing parks, 10-yr CAGR (Q07)**
{_table(growth, [("growth_rank", "#"), ("park_name", "Park"), ("visitors_latest", "Latest visitors"), ("cagr_10y_pct", "CAGR %")])}

**Crowding quartiles (Q09)**
{_table(quart, [("label", "Quartile"), ("avg_visitors_per_acre", "Visitors/acre"), ("avg_pct_non_native", "% non-native"), ("avg_at_risk_per_1k_species", "At-risk/1k"), ("avg_species_richness", "Richness")], n=4)}

**Pressure Index (Q13)**
{_table(index, [("risk_rank", "#"), ("park_name", "Park"), ("pressure_index", "Index"), ("main_driver", "Main driver")])}

**Ecological twins (Q11)**
{_table(twins, [("park_a", "Park A"), ("park_b", "Park B"), ("jaccard", "Jaccard")])}

**Hidden gems: above-median biodiversity, below-median crowds (Q14)**
{_table(gems, [("gem_rank", "#"), ("park_name", "Park"), ("species_richness", "Species"), ("visitors_latest", "Visitors")])}

## Caveats
Correlation is not causation. Species lists reflect survey effort as well as true
diversity, and the species snapshot and visitation series do not line up perfectly in
time. See the README's *Limitations* section.
"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md, encoding="utf-8")
    return path
