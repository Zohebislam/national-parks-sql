"""Static figures for the README, built from the query results."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter, PercentFormatter  # noqa: E402

from .analyze import as_dicts  # noqa: E402

# Validated categorical palette (fixed order, never cycled) + neutral inks.
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK_2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "xtick.color": INK_2, "ytick.color": INK_2,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "legend.frameon": False, "legend.labelcolor": INK_2,
})

millions = FuncFormatter(lambda v, _: f"{v / 1e6:.0f}M")


def _short(name: str) -> str:
    return name.replace(" National Parks", "").replace(" National Park", "").replace(" and Preserve", "")


def _subtitle(ax, text: str) -> None:
    ax.text(0, 1.02, text, transform=ax.transAxes, color=MUTED, fontsize=9, va="bottom")


def _save(fig, out: Path, name: str) -> Path:
    fig.tight_layout()
    path = out / name
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def visitation_trend(r, out):
    rows = [d for d in as_dicts(r["q06_system_visitation_trend"]) if d["year"] >= 1950]
    years = [d["year"] for d in rows]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(years, [d["total_visitors"] for d in rows], color=MUTED, lw=1.2,
            label="Annual visits")
    ax.plot(years, [d["moving_avg_5y"] for d in rows], color=BLUE, lw=2.2,
            label="5-year moving average")
    ax.yaxis.set_major_formatter(millions)
    ax.grid(axis="x", visible=False)
    ax.set_title("National Park visitation over time", pad=22)
    _subtitle(ax, "Recreation visits across all parks in the dataset")
    ax.legend(loc="upper left")
    return _save(fig, out, "01_visitation_trend.png")


def richness_leaderboard(r, out, top=15):
    rows = as_dicts(r["q02_biodiversity_leaderboard"])[:top][::-1]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    names = [_short(d["park_name"]) for d in rows]
    ax.barh(names, [d["species_richness"] for d in rows], color=BLUE, height=0.7)
    for i, d in enumerate(rows):
        ax.text(d["species_richness"], i, f" {d['species_richness']:,}",
                va="center", color=INK_2, fontsize=8.5)
    ax.grid(axis="y", visible=False)
    ax.set_title(f"Top {top} parks by species richness", pad=22)
    _subtitle(ax, "Approved species records currently present in each park")
    return _save(fig, out, "02_richness_leaderboard.png")


def pressure_quartiles(r, out):
    rows = as_dicts(r["q09_pressure_vs_biodiversity"])
    labels = ["Q1\nmost\ncrowded", "Q2", "Q3", "Q4\nleast\ncrowded"][:len(rows)]
    panels = [("avg_pct_non_native", "% non-native species"),
              ("avg_at_risk_per_1k_species", "At-risk species per 1,000"),
              ("avg_species_richness", "Avg. species richness")]
    fig, axes = plt.subplots(1, 3, figsize=(11, 4))
    for ax, (key, title) in zip(axes, panels):
        vals = [d[key] or 0 for d in rows]
        colors = [ORANGE if i == 0 else BLUE for i in range(len(vals))]
        ax.bar(labels, vals, color=colors, width=0.62)
        for i, v in enumerate(vals):
            ax.text(i, v, f"{v:,.1f}" if v < 100 else f"{v:,.0f}", ha="center",
                    va="bottom", color=INK_2, fontsize=8.5)
        ax.set_title(title, fontsize=11)
        ax.grid(axis="x", visible=False)
    fig.suptitle("Do more crowded parks look more stressed?", x=0.01, ha="left",
                 fontsize=13, fontweight="bold", color=INK)
    fig.text(0.01, 0.9, "Parks split into quartiles by visitors per acre",
             color=MUTED, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    path = out / "03_pressure_vs_biodiversity.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def crowding_scatter(r, out, n_labels=6):
    rows = [d for d in as_dicts(r["park_scorecard"])
            if d["visitors_per_acre"] and d["non_native_share"] is not None]
    fig, ax = plt.subplots(figsize=(9, 5))
    xs = [d["visitors_per_acre"] for d in rows]
    ys = [d["non_native_share"] for d in rows]
    ax.scatter(xs, ys, s=46, color=BLUE, edgecolor=SURFACE, linewidth=1.5, zorder=3)
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    # least-squares trend on log10(x), drawn as a reference line
    import math
    lx = [math.log10(x) for x in xs]
    mx, my = sum(lx) / len(lx), sum(ys) / len(ys)
    slope = sum((a - mx) * (b - my) for a, b in zip(lx, ys)) / sum((a - mx) ** 2 for a in lx)
    ends = [min(lx), max(lx)]
    ax.plot([10 ** e for e in ends], [my + slope * (e - mx) for e in ends],
            color=ORANGE, lw=2, label="Linear trend (log x)", zorder=2)
    ax.legend(loc="upper left")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_xlabel("Visitors per acre (log scale)")
    ax.set_ylabel("Share of species that are non-native")
    picks = {d["park_code"]: d for key in ("non_native_share", "visitors_per_acre")
             for d in sorted(rows, key=lambda d: d[key], reverse=True)[:n_labels // 2]}
    for d in picks.values():
        ax.annotate(_short(d["park_name"]), (d["visitors_per_acre"], d["non_native_share"]),
                    xytext=(5, 3), textcoords="offset points", fontsize=8, color=INK_2)
    ax.set_title("Crowding vs. invasive species, by park", pad=22)
    _subtitle(ax, "Each dot is one national park")
    return _save(fig, out, "04_crowding_vs_invasion.png")


def risk_index(r, out, top=12):
    rows = as_dicts(r["q13_park_risk_index"])[:top][::-1]
    drivers = ["crowding", "visitor growth", "invasive species", "at-risk species"]
    palette = dict(zip(drivers, [BLUE, ORANGE, AQUA, YELLOW]))
    fig, ax = plt.subplots(figsize=(9, 5.4))
    ax.barh([_short(d["park_name"]) for d in rows], [d["pressure_index"] for d in rows],
            color=[palette[d["main_driver"]] for d in rows], height=0.7)
    for i, d in enumerate(rows):
        v = d["pressure_index"]
        ax.text(v, i, f" {v:.2f} " , va="center", ha="left" if v >= 0 else "right",
                color=INK_2, fontsize=8.5)
    ax.axvline(0, color=MUTED, lw=1)
    lo, hi = ax.get_xlim()
    ax.set_xlim(lo - 0.15 * (hi - lo) * (lo < 0), hi + 0.08 * (hi - lo))
    handles = [plt.Rectangle((0, 0), 1, 1, color=palette[k]) for k in drivers]
    ax.legend(handles, drivers, title="Main driver", loc="lower right",
              title_fontsize=9, fontsize=8.5)
    ax.grid(axis="y", visible=False)
    ax.set_title(f"Parks under the most pressure (top {top})", pad=22)
    _subtitle(ax, "Composite index: mean z-score of crowding, growth, invasion, at-risk species")
    return _save(fig, out, "05_pressure_index.png")


def category_invasion(r, out):
    rows = [d for d in as_dicts(r["q03_category_mix"]) if d["pct_non_native"] is not None]
    rows = sorted(rows, key=lambda d: d["pct_non_native"])
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh([d["category"] for d in rows], [d["pct_non_native"] for d in rows],
            color=BLUE, height=0.7)
    for i, d in enumerate(rows):
        ax.text(d["pct_non_native"], i, f" {d['pct_non_native']:.1f}%", va="center",
                color=INK_2, fontsize=8.5)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.grid(axis="y", visible=False)
    ax.set_title("Which kinds of life are most invaded?", pad=22)
    _subtitle(ax, "Non-native share of species records, by category")
    return _save(fig, out, "06_invasion_by_category.png")


def make_all(results: dict, out: Path) -> list[Path]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    return [fn(results, out) for fn in (visitation_trend, richness_leaderboard,
                                        pressure_quartiles, crowding_scatter,
                                        risk_index, category_invasion)]
