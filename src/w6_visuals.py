"""W6 executive visuals — the siting product, and why covariates did not improve it.

Eleven arguments, fifteen figures, in the order a talk should make them.

**The premise, in two figures.** `plot_seasonality` opens the deck with the year
as the record shows it: most fires start in spring, most acres burn in summer.
Acres as a filled area, starts as a dashed line, on one calendar with neither
y-axis drawn — two scales in one frame would make the curve crossing look
meaningful when it falls wherever the scalings happen to intersect. National,
all 2.27M cleaned fires. `plot_cause_map` then supplies the spatial half: all
105 Level III ecoregions shaded by natural share of attributed acres, a West/East
split at roughly the 100th meridian. Its finding is that the distribution is
**bimodal** — 50 regions below 20% natural, 28 above 80%, 27 in between — so
regions commit to one cause, and the national average describes almost none of
them.

**Is that mix forecastable?** `plot_tier1_tiles` answers it as three stat tiles,
not a chart: a region's own history places **73%** of its next-season burned-acre
composition on the right cause, against **42%** for the national average mix and
**52%** for an even split. The national average losing to an uninformed guess is
the bimodality above resurfacing as forecast error. Tiles show `1 - TVD`, which
on a simplex *is* the overlap between predicted and actual composition, so the
label is literal and the number reads the intuitive way round.
`plot_volatility_map` is the honest counterweight, held for Q&A rather than the
deck: regions do move year to year (median SD 0.181), they simply move around
their own level rather than the national one. `plot_k_sweep` then asks how much
history that average needs, and finds the gain front-loaded: one prior season to
three is worth 5.3 points, and every window from three up sits within 1.4 points
of the best.

**One level deeper.** `plot_human_tiles` asks the same question of the Human
branch's 11 sub-causes and draws it with the same `_draw_score_tiles`, because
the beats are one question at two levels and a reader should not have to learn a
second encoding. Reported as top-1 rather than `1 - TVD`: on 11 classes an
overlap score stays comfortable without ever naming the right leader (the
national mix scores 0.643 TVD at 16% top-1). History reaches **54%** against a
9% chance floor. `plot_ablation_ladder` then answers the obvious challenge:
gradient boosting on region character reaches 36%, and the same model *handed
the trailing history as a feature* reaches 47.5% -- still 7 points short of
taking that feature's mean. The floor is drawn as a rule across the plot so a
bar that stops short of it reads as a failure without a legend.

**The third class.** `plot_unknown_triage` ranks region-seasons by *predicted
unattributed acres* -- the forecast missing fraction times the burn -- so the
Unknown branch outputs a work order rather than a data-quality complaint.
Ranking by rate alone would put small badly-reported regions on top; ranking by
acres puts Southwestern Tablelands MAM there at 1.17M acres. The branch's own
forecast holds up: acre-weighted MAE 0.167 against a global mean's 0.240.

**The product.** `plot_siting_glance` ranks hexes by the persistence baseline
and fills the ground that catches 30% of next season's starts: **12 of 198
hexes, 6.1% of the region, a 5.2x lift** over treating ground at random. Two
fills rather than graded tiers, because the W6 modeling settled that ignition
is a *gate, not a dial*. `plot_capture_curve` is its companion and the more
sobering half — the whole ranking rather than its top, showing the return decay
to 2.09x at 60% capture and 1.16x at 90%, which is near-uniform treatment. The
diminishing return is the recommendation.

**Why the covariates added nothing.** The reason is the hardest idea in the talk:
these covariates identify dry *places*, not dry *years*, and place is what
persistence already knows. Stated as a pair of correlations (NDVI +0.228 raw,
+0.098 within-hex) it is two numbers on a slide that no audience absorbs.
`plot_ndvi_map` shows what NDVI is on real ground; `plot_persistence_pair` shows
both layers persisting across a decade gap; `plot_ndvi_variance` draws the split
directly — between-place sd ~0.132 against within-hex ~0.048, so NDVI is ~2.8x
more about which hex than which year.

**Why the product ranks starts, not acres.** `plot_acres_concentration` shows
natural acres concentrating almost degenerately once a cell burns at all (top 1%
of burning cells hold 55%, top 10% hold 98%), which is what makes the tail the
only decile that matters. `plot_branch_deciles` then shows the baseline missing
exactly that decile — and missing it *differently* on the two branches (Natural
269.8x under, Human 12.3x), which is why Human can be ranked by expected acres
and Natural cannot. Both read from the cached acres panel via
`decile_error_table`, so a figure cannot drift from the notebook that reported
the number.

Design contract, shared with `w5_visuals`
-----------------------------------------
**No headline or caption is drawn into any image.** Every function returns the
numbers a caption would need, so the prose lives in notebook markdown and the PNG
stays composable for a slide — and so the figure and the text cannot disagree.

Encoding notes that cost several drafts to find
------------------------------------------------
* **Fill, not stroke, for categories.** A stroke is a boundary cue; the reader
  must inspect edges hex by hex. Fill is pre-attentive.
* **Ranking under a budget is not classification.** An outcome map colored by
  hit/false-positive/miss reads as failure by arithmetic — with a fifth of the
  ground treatable and most hexes igniting, misses are guaranteed. Tiers ask the
  question a planner actually has: what do I do first?
* **Tiers, not a smooth ramp.** The W6 modeling settled that ignition is a
  **gate, not a dial**, so priority order is real but graded intensity is not.
* **Cut tiers by capture, not by a ground budget.** An invented top-20% decided
  by itself whether the figure looked like success or failure.

Color
-----
Palette is imported from `w5_visuals` so the deck stays one system. Greenness
gets its own green ramp (NDVI *is* greenness; the flame ramp would imply the map
shows burning), ignitions get ember, and neutral ground is deliberately *off* the
ramp so "not treated" reads as a different state rather than "slightly treated."
"""
from __future__ import annotations

from pathlib import Path

import warnings

import numpy as np
import pandas as pd

# Reuse the project palette rather than defining a second one.
from w5_visuals import (POINT_ORANGE, PERIM_FILL, SURFACE, TEXT_MUTED,
                        TEXT_PRIMARY, TEXT_SECONDARY)


# Sequential green, light -> dark: vegetation density. A single hue ramped by
# lightness, for the same reasons the flame ramp is built that way in
# `w5_visuals` -- a yellow->green->blue rainbow would read as categories on a
# continuous quantity and lose its ordering in grayscale. Green is the honest
# hue here: NDVI *is* greenness, and borrowing the flame ramp would imply the
# map shows burning, which it does not.
# Week index of the first day of each calendar month (day-of-year / 7), for
# labeling a 52-week axis in months. Non-integer by construction: months do not
# start on week boundaries, and rounding them to the nearest week visibly drifts
# by December.
MONTH_START_WEEKS = np.array(
    [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]) / 7.0

# March through early June. `plot_seasonality` finds the spring starts peak
# inside this window rather than by taking the curve's global maximum, which
# falls in the July 4 week -- a one-week holiday spike, not a seasonal peak.
SPRING_WEEKS = slice(8, 23)

# Meteorological-season triads to plain names, for axis labels. The triads are
# the project's internal vocabulary and stay in every returned table; only the
# drawn axis is translated.
SEASON_NAMES = {"DJF": "Winter", "MAM": "Spring", "JJA": "Summer", "SON": "Fall"}


SEQ_GREEN = [
    "#e8f0dc", "#cfe0b8", "#aecd90", "#88b768", "#639f47",
    "#43862f", "#2c6c20", "#1a5216", "#0d380f",
]


def _green_cmap():
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list("proj_ndvi", SEQ_GREEN)


def hex_polygons(hex_ids):
    """(lon, lat) rings for H3 cells, for plotting without a geo dependency.

    `data/hex_grid_res5.parquet` stores IDs, not geometry, so boundaries come
    from `h3` directly -- the same source `hex_burn` uses to build the grid, so
    there is exactly one definition of where a cell is.
    """
    import h3

    rings = []
    for h in hex_ids:
        # h3 returns (lat, lon); matplotlib wants (x, y) = (lon, lat).
        rings.append([(lon, lat) for lat, lon in h3.cell_to_boundary(h)])
    return rings


def plot_ndvi_map(ndvi: pd.DataFrame, grid: pd.DataFrame, out_path: Path, *,
                  region_prefix: str = "Klamath",
                  years: tuple[int, int] | None = None,
                  value_col: str = "ndvi",
                  figsize: tuple[float, float] = (11.0, 5.6)) -> dict:
    """One region's hexes shaded by greenness — what NDVI *is*, before what it does.

    The variance figure asks an audience to reason about a quantity most of them
    have never seen. This is the primer: a real place, its cells colored by how
    much vegetation the satellite reads.

    Two panels, the same region in its greenest and brownest years on record, on a
    **shared color scale** so the comparison is honest. The point the pair makes
    is deliberately the talk's point: the map barely changes. Where a hex sits in
    the ordering is a property of the hex; the year moves it very little.

    Returns the caption numbers, including the two years chosen and the
    between/within spreads restricted to this region.
    """
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    ids = grid.loc[grid["region"].str.startswith(region_prefix), "hex_id"]
    sub = ndvi[ndvi["hex_id"].isin(set(ids))].copy()
    if sub.empty:
        raise ValueError(f"no NDVI rows for region prefix {region_prefix!r}")

    region_name = grid.loc[grid["hex_id"].isin(sub["hex_id"]), "region"].iloc[0]
    by_year = sub.groupby("season_year")[value_col].mean()
    lo_year, hi_year = (years if years is not None
                        else (int(by_year.idxmin()), int(by_year.idxmax())))

    # Shared scale across both panels: a per-panel scale would manufacture a
    # difference out of two nearly identical maps.
    vmin, vmax = float(sub[value_col].min()), float(sub[value_col].max())
    cmap = _green_cmap()

    fig, axes = plt.subplots(1, 2, figsize=figsize, facecolor=SURFACE,
                             gridspec_kw={"wspace": 0.04})

    for ax, yr in zip(axes, (hi_year, lo_year)):
        frame = sub[sub["season_year"] == yr]
        rings = hex_polygons(frame["hex_id"])
        coll = PolyCollection(rings, array=frame[value_col].to_numpy(),
                              cmap=cmap, edgecolors=SURFACE, linewidths=0.3)
        coll.set_clim(vmin, vmax)
        ax.add_collection(coll)
        ax.autoscale_view()
        ax.set_aspect("equal")
        ax.set_facecolor(SURFACE)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(f"{yr}   (regional average {by_year[yr]:.2f})",
                     fontsize=11, color=TEXT_SECONDARY, pad=8)

    cbar = fig.colorbar(coll, ax=axes, fraction=0.028, pad=0.02)
    cbar.set_label("NDVI — vegetation density", fontsize=9.5,
                   color=TEXT_SECONDARY)
    cbar.ax.tick_params(colors=TEXT_SECONDARY, labelsize=8.5)
    cbar.outline.set_visible(False)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.25)
    plt.close(fig)

    g = sub.groupby("hex_id")[value_col]
    return {
        "region": region_name,
        "n_hex": int(sub["hex_id"].nunique()),
        "greenest_year": hi_year,
        "brownest_year": lo_year,
        "greenest_mean": float(by_year[hi_year]),
        "brownest_mean": float(by_year[lo_year]),
        "year_range": float(by_year.max() - by_year.min()),
        "between_sd": float(g.mean().std()),
        "within_sd": float(g.std().mean()),
        "out_path": str(out_path),
    }


# Sequential ember, light -> dark: ignition counts. Warm, so it reads as fire
# against the green vegetation ramp in the same figure, but a distinct hue family
# from both -- the two rows must not look like two renderings of one quantity.
SEQ_EMBER = [
    "#fde3c8", "#fcc999", "#f9a86a", "#f3843f", "#e35f22",
    "#c2400f", "#951f07", "#5f0f04",
]


def plot_persistence_pair(panel: pd.DataFrame, ndvi: pd.DataFrame,
                          grid: pd.DataFrame, out_path: Path, *,
                          region_prefix: str = "Klamath",
                          early_end: int = 2006,
                          late_start: int = 2015,
                          figsize: tuple[float, float] = (11.5, 6.2)) -> dict:
    """Both halves of the argument in one frame: ignitions persist, and so does greenness.

    Four maps of the same region, two rows x two eras:

    * top row    — natural ignitions per season, early era then late era
    * bottom row — NDVI, early era then late era

    The eras are **disjoint by design** (default: through 2005, then 2015 onward),
    so left-to-right stability is not an artifact of overlapping windows.

    Read across the top: *fires happen where fires happened.* Read across the
    bottom: *green places stay green.* Read top-to-bottom: the two patterns are
    not the same map, which is why "fires happen where the fuel is" is the wrong
    compression -- in this region the correlation between them is in fact
    negative. Both layers are stable; only one of them is the target; and the
    stable part of the covariate is information the ignition history already
    carries.

    Returns the split-half stabilities and the cross-layer correlation.
    """
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import LinearSegmentedColormap
    from scipy.stats import spearmanr

    ids = set(grid.loc[grid["region"].str.startswith(region_prefix), "hex_id"])
    region_name = grid.loc[grid["hex_id"].isin(ids), "region"].iloc[0]

    fires = panel[(panel["hex_id"].isin(ids)) & (panel["season_ord"] == 2)]
    fires = fires[["hex_id", "season_year", "starts_natural"]]
    veg = ndvi[ndvi["hex_id"].isin(ids)][["hex_id", "season_year", "ndvi"]]

    def era(df, col, lo, hi, how):
        m = df[(df["season_year"] >= lo) & (df["season_year"] <= hi)]
        return m.groupby("hex_id")[col].agg(how)

    # Ignitions are averaged **per season**, not summed: the two eras span
    # different numbers of years, and a sum would make the shorter era uniformly
    # paler for arithmetic reasons rather than because its pattern differs. The
    # figure's claim is about *pattern*, so the rate is the honest quantity.
    layers = {
        ("fires", "early"): era(fires, "starts_natural", 0, early_end - 1, "mean"),
        ("fires", "late"): era(fires, "starts_natural", late_start, 9999, "mean"),
        ("ndvi", "early"): era(veg, "ndvi", 0, early_end + 3, "mean"),
        ("ndvi", "late"): era(veg, "ndvi", late_start, 9999, "mean"),
    }

    order = sorted(ids)
    ember = LinearSegmentedColormap.from_list("proj_ember", SEQ_EMBER)
    green = _green_cmap()

    fig, axes = plt.subplots(2, 2, figsize=figsize, facecolor=SURFACE,
                             gridspec_kw={"wspace": 0.02, "hspace": 0.08})

    for row, (layer, cmap, label) in enumerate((
        ("fires", ember, "natural ignitions"),
        ("ndvi", green, "NDVI"),
    )):
        vals = pd.concat([layers[(layer, "early")], layers[(layer, "late")]])
        vmin, vmax = float(vals.min()), float(vals.max())
        for col, eranm in enumerate(("early", "late")):
            ax = axes[row][col]
            s = layers[(layer, eranm)].reindex(order).fillna(0.0)
            coll = PolyCollection(hex_polygons(order), array=s.to_numpy(),
                                  cmap=cmap, edgecolors=SURFACE, linewidths=0.25)
            coll.set_clim(vmin, vmax)
            ax.add_collection(coll)
            ax.autoscale_view()
            ax.set_aspect("equal")
            ax.set_facecolor(SURFACE)
            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_visible(False)
            if row == 0:
                span = (f"through {early_end - 1}" if eranm == "early"
                        else f"{late_start} onward")
                ax.set_title(span, fontsize=11.5, color=TEXT_SECONDARY, pad=8)
            if col == 0:
                ax.set_ylabel(label, fontsize=11, color=TEXT_PRIMARY, labelpad=10)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.25)
    plt.close(fig)

    f_e = layers[("fires", "early")].reindex(order).fillna(0.0)
    f_l = layers[("fires", "late")].reindex(order).fillna(0.0)
    n_e = layers[("ndvi", "early")].reindex(order)
    n_l = layers[("ndvi", "late")].reindex(order)
    ok = n_e.notna() & n_l.notna()
    return {
        "region": region_name,
        "n_hex": len(order),
        "fires_split_half": float(spearmanr(f_e, f_l).statistic),
        "ndvi_split_half": float(spearmanr(n_e[ok], n_l[ok]).statistic),
        "cross_layer": float(spearmanr(f_l[ok], n_l[ok]).statistic),
        "early_era": f"through {early_end - 1}",
        "late_era": f"{late_start} onward",
        "out_path": str(out_path),
    }


def ndvi_variance_split(ndvi: pd.DataFrame, *, value_col: str = "ndvi") -> dict:
    """The two spreads the figure draws, as numbers.

    Separated from the plotting so a notebook can quote the statistic without
    rendering, and so the figure and the prose can never disagree.
    """
    g = ndvi.groupby("hex_id")[value_col]
    between = float(g.mean().std())
    within = float(g.std().mean())
    return {
        "between_sd": between,
        "within_sd": within,
        "ratio": between / within if within else float("nan"),
        "n_hex": int(ndvi["hex_id"].nunique()),
        "n_years": int(ndvi["season_year"].nunique()),
        "n_obs": int(len(ndvi)),
    }


def plot_ndvi_variance(ndvi: pd.DataFrame, out_path: Path, *,
                       value_col: str = "ndvi",
                       n_show: int = 150,
                       seed: int = 0,
                       figsize: tuple[float, float] = (11.0, 6.4)) -> dict:
    """Two panels: NDVI as measured, then with each hex centered on its own mean.

    Left panel — one row per sampled hex, sorted by mean NDVI, each row showing
    that hex's yearly values. The vertical structure *is* the between-place
    variance: the spread down the page dwarfs the spread within any single row.

    Right panel — the identical values with each hex's own mean subtracted. The
    vertical structure collapses to a flat band. That band is everything a
    forecast has left once persistence has taken the place effect, and it is what
    the covariate rungs were fitting.

    Returns the caption numbers from `ndvi_variance_split`, plus `n_shown`.
    """
    import matplotlib.pyplot as plt

    stats = ndvi_variance_split(ndvi, value_col=value_col)

    # Sample hexes for legibility. All 2,663 rows would render as a solid block
    # and destroy the per-row cloud that carries the argument.
    rng = np.random.default_rng(seed)
    hexes = ndvi["hex_id"].unique()
    if len(hexes) > n_show:
        hexes = rng.choice(hexes, size=n_show, replace=False)
    sub = ndvi[ndvi["hex_id"].isin(hexes)].copy()

    means = sub.groupby("hex_id")[value_col].mean()
    order = means.sort_values().index
    row_of = {h: i for i, h in enumerate(order)}
    sub["row"] = sub["hex_id"].map(row_of)
    sub["centered"] = sub[value_col] - sub["hex_id"].map(means)

    fig, axes = plt.subplots(1, 2, figsize=figsize, facecolor=SURFACE,
                             sharey=True, gridspec_kw={"wspace": 0.12})

    for ax, col, title in (
        (axes[0], value_col, "as measured"),
        (axes[1], "centered", "each hex centered on its own average"),
    ):
        ax.scatter(sub[col], sub["row"], s=3.2, c=PERIM_FILL, alpha=0.32,
                   linewidths=0, rasterized=True)
        ax.set_facecolor(SURFACE)
        ax.set_yticks([])
        ax.set_title(title, fontsize=11, color=TEXT_SECONDARY, pad=10)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(TEXT_MUTED)
        ax.tick_params(axis="x", colors=TEXT_SECONDARY, labelsize=9)

    # Equal x-spans so the collapse is a fair visual comparison, not an artifact
    # of two different scales. Both panels get the width of the wider one.
    span = max(
        sub[value_col].max() - sub[value_col].min(),
        sub["centered"].max() - sub["centered"].min(),
    ) * 1.06
    for ax, col in ((axes[0], value_col), (axes[1], "centered")):
        mid = (sub[col].max() + sub[col].min()) / 2
        ax.set_xlim(mid - span / 2, mid + span / 2)

    axes[0].set_ylabel(f"{len(order)} hexes, sorted by average greenness",
                       fontsize=9.5, color=TEXT_MUTED)
    axes[0].set_xlabel("NDVI", fontsize=10, color=TEXT_SECONDARY)
    axes[1].set_xlabel("NDVI minus the hex's own average", fontsize=10,
                       color=TEXT_SECONDARY)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.25)
    plt.close(fig)

    stats["n_shown"] = len(order)
    stats["out_path"] = str(out_path)
    return stats


# The five covariate ablations on ignition targets, transcribed from the
# notebooks that ran them. Both branches share one population -- JJA, the six
# forest ecoregions NDVI was fetched for, held out 2010+, 29,293 cells -- so the
# two lines are directly comparable and the figure needs no scope caveat.
#
# Natural: notebook 12, cell 29 (the NDVI ladder).
# Human:   notebook 14, cell 15.
#
# Human's ladder did not run a "+ climate + NDVI (anomaly)" rung, so the shared
# rung set is the four both branches tried. Hardcoded rather than recomputed:
# these are published numbers, and a figure that silently re-fits could drift
# from the report. `IGNITION_LADDER_SOURCE` names where to re-verify them.
IGNITION_LADDER_SOURCE = (
    "notebook/12_hex_ignition_baselines.ipynb cell 29; "
    "notebook/14_hex_human_branch.ipynb cell 15"
)

IGNITION_LADDER = {
    "rungs": ["the region's own history",
              "+ drought",
              "+ fuel load",
              "+ both"],
    "natural": [0.4235, 0.4280, 0.4278, 0.4230],
    "human":   [0.4863, 0.4680, 0.4818, 0.4807],
    "n_test": 29293,
}


def plot_ignition_ladder(out_path: Path, *,
                         ladder: dict | None = None,
                         figsize: tuple[float, float] = (11.0, 4.6)) -> dict:
    """Beat 12 — the repair attempt, and its verdict, as two flat lines.

    Both branches' held-out ranking skill against the rungs that were added to
    improve it. The claim is the *flatness*: four covariate specifications, two
    branches, and neither line goes anywhere.

    **Why a line and not the bar ladder of beat 6.** That figure asks "did any
    bar clear the rule," which is a comparison against a threshold. This one
    asks "did the sequence go up," which is a comparison along a path -- and a
    path is what a line encodes. Bars here would also double the ink for two
    branches and invite reading the pairs against each other, when the finding
    is about each line's own slope.

    **The y-axis starts at zero.** Cropping to the data would magnify moves of
    0.004 into visible steps and manufacture exactly the signal the beat says is
    absent. A null has to be drawn on a scale where a real effect would have
    been visible; anything else argues the case by axis choice.

    **No values printed on the points.** The number that matters is the one that
    is *not* there -- no gain above +0.005 -- and a reader who starts comparing
    four decimal places has stopped seeing the shape. The notebook prints the
    table for anyone who wants it.
    """
    import matplotlib.pyplot as plt

    d = ladder or IGNITION_LADDER
    rungs = list(d["rungs"])
    x = np.arange(len(rungs))

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    series = [("human", d["human"], PERIM_FILL, "human fire"),
              ("natural", d["natural"], POINT_ORANGE, "lightning fire")]

    for _, vals, color, label in series:
        ax.plot(x, vals, color=color, lw=2.6, marker="o", ms=9,
                markerfacecolor=SURFACE, markeredgewidth=2.6,
                markeredgecolor=color, zorder=3, clip_on=False)
        # Labeled at the line's own left end rather than in a legend, so the
        # eye never leaves the plot to decode a color.
        ax.annotate(label, xy=(0, vals[0]), xytext=(-14, 0),
                    textcoords="offset points", ha="right", va="center",
                    fontsize=15.5, fontweight="bold", color=color)

    # Left headroom for the in-plot series labels, which replace a legend.
    ax.set_xlim(-1.30, len(rungs) - 0.88)
    ax.set_ylim(0, 0.60)
    ax.set_xticks(x)
    ax.set_xticklabels(rungs, fontsize=13.5, color=TEXT_SECONDARY)
    ax.set_yticks([0, 0.2, 0.4, 0.6])
    ax.set_yticklabels(["0", "0.2", "0.4", "0.6"], fontsize=11,
                       color=TEXT_MUTED)
    # No y-axis title: it collided with the series labels, and the two of them
    # were saying the same thing. The scale's meaning rides on the annotation
    # and the headline instead.

    # The one annotation, spanning the added rungs so it reads as a verdict on
    # the three additions rather than on the baseline.
    ax.annotate("nothing we added moved it",
                xy=(2.0, 0.545), ha="center", va="center",
                fontsize=17, fontweight="bold", color=TEXT_PRIMARY)

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_MUTED)
    ax.tick_params(axis="both", length=0)
    ax.grid(axis="y", color=TEXT_MUTED, alpha=0.16, lw=0.8)
    ax.set_axisbelow(True)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    spans = {k: max(v) - min(v) for k, v in
             (("natural", d["natural"]), ("human", d["human"]))}
    best = {k: max(v) - v[0] for k, v in
            (("natural", d["natural"]), ("human", d["human"]))}
    return {"n_test": d["n_test"],
            "natural_floor": d["natural"][0], "human_floor": d["human"][0],
            "natural_span": spans["natural"], "human_span": spans["human"],
            "natural_best_gain": best["natural"], "human_best_gain": best["human"],
            "source": IGNITION_LADDER_SOURCE,
            "out_path": str(out_path)}


# The acres ladder, from `13_hex_acres_baselines.ipynb` cell 15. Same rung
# vocabulary as IGNITION_LADDER above and the same six forest ecoregions, but a
# different target (burned area given a burn), a different baseline
# (burn-conditional persistence) and a much smaller test set -- 7,799 burning
# JJA cells rather than 29,293 hex-seasons. The populations are NOT
# interchangeable; the figures are comparable in *shape*, not cell for cell.
ACRES_LADDER_SOURCE = "notebook/13_hex_acres_baselines.ipynb cell 15"

ACRES_LADDER = {
    "rungs": ["the region's own history", "+ drought", "+ fuel load", "+ both"],
    # floor, + climate, + NDVI (raw), + NDVI + climate
    "natural": [0.2582, 0.2504, 0.2592, 0.3075],
    "n_test": 7799,
    "shuffled_sd": 26.6,     # real delta vs. the covariate-shuffled control
    "split_years": [0.012, 0.048, 0.062, 0.062, 0.066],   # 2008-2016
}


def plot_acres_ladder(out_path: Path, *,
                      ladder: dict | None = None,
                      figsize: tuple[float, float] = (11.0, 4.6)) -> dict:
    """Beat 13 — the same ladder as beat 12, on acres, and one rung lifts.

    Deliberately **the same figure as `plot_ignition_ladder`**: same rung
    labels, same axis, same left-hand series label, same zero-based scale. The
    beats are one experiment run against two targets, and the whole point is
    that the shape changes. A reader who has just learned to read beat 12's flat
    line should recognize this one instantly and see the last point lift.

    **Only the natural branch is drawn.** The acres ladder was run on natural
    magnitude; drawing a single line also stops the eye comparing two branches
    when the claim is about one line's own last step.

    **The step is annotated, the others are not.** Three rungs do nothing and
    the fourth does something -- and it is the *conjunction* that matters, since
    neither half works alone. The annotation says so, because a viewer reading
    left to right would otherwise credit the last thing added rather than the
    combination -- which the x-axis tick already names, so the callout carries
    the size of the step instead. Reported as the delta rather than the level,
    because the level (0.3075) invites comparison with beat 12's numbers across
    populations that are not comparable.
    """
    import matplotlib.pyplot as plt

    d = ladder or ACRES_LADDER
    rungs = list(d["rungs"])
    vals = list(d["natural"])
    x = np.arange(len(rungs))

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    ax.plot(x, vals, color=POINT_ORANGE, lw=2.6, marker="o", ms=9,
            markerfacecolor=SURFACE, markeredgewidth=2.6,
            markeredgecolor=POINT_ORANGE, zorder=3, clip_on=False)
    # Lifted clear of the floor rule, which runs the full width at this height
    # and would otherwise strike through the label.
    ax.annotate("lightning fire", xy=(0, vals[0]), xytext=(-14, 13),
                textcoords="offset points", ha="right", va="center",
                fontsize=15.5, fontweight="bold", color=POINT_ORANGE)

    # A reference rule at the floor, carried the full width. Without it the last
    # step is just a line that happens to end higher than it started; with it,
    # the three flat rungs visibly sit *on* the baseline and only the fourth
    # leaves it. This is also the honest way to show a small gain -- the
    # alternative, cropping the y-axis until +0.049 fills the frame, would
    # inflate a result that beat 14 then has to deflate.
    ax.axhline(vals[0], color=TEXT_MUTED, lw=1.3, ls=(0, (5, 4)), alpha=0.85,
               zorder=1)

    # The lift, bracketed at the point where it happens.
    ax.annotate("", xy=(3, vals[3]), xytext=(3, vals[0]),
                arrowprops=dict(arrowstyle="-|>", color=TEXT_PRIMARY, lw=2.2,
                                shrinkA=1, shrinkB=1), zorder=4)
    # The size of the step, not a restatement of the x-axis. The rung is already
    # labeled "+ both" underneath, so a callout saying the same thing in words
    # spends the deck's one annotation on information the reader has. The number
    # is the one thing the figure cannot otherwise show: the step is small in
    # absolute terms, and printing it keeps that visible rather than letting the
    # arrow imply more than +0.049 is worth. Beat 12 prints no numbers because
    # there its numbers are all ~0; here the number *is* the finding.
    ax.annotate(f"+{vals[3] - vals[0]:.3f}", xy=(3, vals[3]), xytext=(0, 16),
                textcoords="offset points", ha="center", va="bottom",
                fontsize=17, fontweight="bold", color=TEXT_PRIMARY)

    ax.set_xlim(-1.30, len(rungs) - 0.88)
    ax.set_ylim(0, 0.60)
    ax.set_xticks(x)
    ax.set_xticklabels(rungs, fontsize=13.5, color=TEXT_SECONDARY)
    ax.set_yticks([0, 0.2, 0.4, 0.6])
    ax.set_yticklabels(["0", "0.2", "0.4", "0.6"], fontsize=11,
                       color=TEXT_MUTED)

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_MUTED)
    ax.tick_params(axis="both", length=0)
    ax.grid(axis="y", color=TEXT_MUTED, alpha=0.16, lw=0.8)
    ax.set_axisbelow(True)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    return {"n_test": d["n_test"],
            "floor": vals[0],
            "best": max(vals),
            "gain": max(vals) - vals[0],
            "drought_alone": vals[1] - vals[0],
            "fuel_alone": vals[2] - vals[0],
            "shuffled_sd": d["shuffled_sd"],
            "source": ACRES_LADDER_SOURCE,
            "out_path": str(out_path)}


# Where the +0.049 lands, from `13_hex_acres_baselines.ipynb` cell 19 -- the
# same fitted model as ACRES_LADDER's winning rung, scored by burned-area decile
# on the held-out cells. `floor_x` and `model_x` are typical error as a
# multiplier (median absolute log error, read back). Transcribed for the same
# reason as the ladders: these are published numbers.
GAIN_DECILES_SOURCE = "notebook/13_hex_acres_baselines.ipynb cell 19"

GAIN_DECILES = {
    "decile":       [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "median_acres": [0.10, 0.10, 0.20, 0.35, 0.70, 1.50, 4.20, 20.30, 199.55, 5072.58],
    "floor_x":      [18.81, 13.08, 5.68, 3.42, 3.21, 3.51, 5.00, 9.01, 25.34, 854.85],
    "model_x":      [35.89, 23.15, 11.23, 6.63, 4.09, 2.67, 2.69, 4.16, 24.33, 867.80],
    "n_per_decile": 780,
}


def plot_gain_landing(out_path: Path, *,
                      data: dict | None = None,
                      figsize: tuple[float, float] = (10.6, 5.6)) -> dict:
    """Beat 14 — the gain is real, and it lands where nothing was at stake.

    **Beat 11's axis, reused exactly**: cells ordered by acres burned least to
    most, typical error on a log scale. The audience has already learned to read
    this frame twice (beat 11's two branches, beat 10's concentration curve
    sharing the ordering), so beat 14 spends none of its time teaching a new one
    and all of it on the comparison.

    Two lines, before and after, on one panel rather than side by side: the
    claim is about the *gap between them* closing in the middle and vanishing at
    the right, and a gap is only readable when both lines share an axis.

    **The right edge is the point.** The two lines meet there -- 855x to 868x --
    which is the same right edge beat 10 marked as holding 98% of the acres and
    beat 11 marked as where the forecast comes apart. Three beats now land the
    eye on the same place, which is the deck's argument for reframing rather
    than tuning.

    **The improvement is shaded, and so is the damage.** Deciles 6-9 improve;
    1-5 get materially *worse* (decile 1 nearly doubles, 18.8x to 35.9x). A
    figure showing only the win would misreport the trade -- the model buys
    middling cells by giving up small ones, and gains nothing where it counts.
    """
    import matplotlib.pyplot as plt

    d = data or GAIN_DECILES
    x = np.array(d["decile"], dtype=float)
    floor = np.array(d["floor_x"], dtype=float)
    model = np.array(d["model_x"], dtype=float)

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    better = model < floor
    # Shade the two verdicts separately. Same alpha for both so neither reads as
    # more important than the other; color carries the direction.
    ax.fill_between(x, floor, model, where=better, interpolate=True,
                    color=PERIM_FILL, alpha=0.20, linewidth=0, zorder=1)
    ax.fill_between(x, floor, model, where=~better, interpolate=True,
                    color=POINT_ORANGE, alpha=0.20, linewidth=0, zorder=1)

    ax.plot(x, floor, color=TEXT_MUTED, lw=2.4, marker="o", ms=6.5,
            mfc=SURFACE, mew=1.8, mec=TEXT_MUTED, zorder=3)
    ax.plot(x, model, color=PERIM_FILL, lw=2.8, marker="o", ms=6.5,
            mfc=SURFACE, mew=1.9, mec=PERIM_FILL, zorder=4)

    # The one shaded region that carries the headline: name the win, in the
    # blue lens, so a viewer is not left with two unexplained colors. The pink
    # lens needs no label -- it sits above "history alone", and "worse" is
    # legible from position alone once the win is named.
    mid = int(np.argmax(np.where(better, floor / model, 0)))
    ax.annotate("the gain\nlands here",
                xy=(x[mid], float(np.sqrt(floor[mid] * model[mid]))),
                xytext=(-40, 128), textcoords="offset points",
                ha="center", va="center", fontsize=13, fontweight="bold",
                color=PERIM_FILL, linespacing=1.25, zorder=5,
                arrowprops=dict(arrowstyle="-", color=PERIM_FILL, lw=1.3,
                                alpha=0.75, shrinkA=4, shrinkB=6,
                                connectionstyle="arc3,rad=0.16"))

    # Series labels go on the left, where the two lines are furthest apart and
    # the plot is empty. Anchoring them mid-curve put both on top of the lines.
    ax.annotate("history alone", xy=(x[0], floor[0]), xytext=(10, -22),
                textcoords="offset points", ha="left", va="top",
                fontsize=13.5, fontweight="bold", color=TEXT_SECONDARY)
    ax.annotate("+ drought and fuel", xy=(x[0], model[0]), xytext=(10, 16),
                textcoords="offset points", ha="left", va="bottom",
                fontsize=13.5, fontweight="bold", color=PERIM_FILL)

    # The verdict sits in the upper-middle dead space and points at the
    # convergence, rather than lying across the rising curve.
    ax.annotate("no better where the acres are",
                xy=(x[-1] - 0.12, model[-1] * 0.80), xytext=(-28, 96),
                textcoords="offset points", ha="right", va="center",
                fontsize=15, fontweight="bold", color=TEXT_PRIMARY,
                arrowprops=dict(arrowstyle="-|>", color=TEXT_PRIMARY, lw=1.8,
                                connectionstyle="arc3,rad=-0.18",
                                shrinkA=6, shrinkB=6))

    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(v)*10}%" for v in x])
    ax.set_xlim(0.6, 10.6)
    ax.set_xlabel("cells ordered by acres burned, least to most",
                  fontsize=11, color=TEXT_SECONDARY)
    ax.set_ylabel("how far off the forecast was", fontsize=11,
                  color=TEXT_SECONDARY)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}x" if v >= 1 else "")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_MUTED)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=10)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    return {"improved_deciles": [int(v) for v, b in zip(x, better) if b],
            "worsened_deciles": [int(v) for v, b in zip(x, better) if not b],
            "top_floor_x": float(floor[-1]),
            "top_model_x": float(model[-1]),
            "top_median_acres": float(d["median_acres"][-1]),
            "worst_damage_x": float((model / floor).max()),
            "n_per_decile": d["n_per_decile"],
            "source": GAIN_DECILES_SOURCE,
            "out_path": str(out_path)}


# The gate test, from `13_hex_acres_baselines.ipynb` cell 22. JJA natural,
# held-out years, "big" = a hex-season producing >= 1,000 acres.
GATE_SOURCE = "notebook/13_hex_acres_baselines.ipynb cell 22"

GATE = {
    "p_none": 0.00294,   # P(>=1000 ac | no ignition recorded)
    "p_some": 0.06694,   # P(>=1000 ac | >= 1 ignition)
    "big_acres": 1000,
}


def plot_ignition_gate(out_path: Path, *,
                       gate: dict | None = None,
                       figsize: tuple[float, float] = (10.0, 5.0)) -> dict:
    """Beat 16 — ignition is the gate the tail failure leaves open.

    Two bars, one comparison, no axis. The claim is a *ratio between two
    probabilities*, and the deck has no other slide that makes one -- so this
    uses the plainest encoding available rather than reusing an axis the
    audience already knows.

    **Drawn as proportion of a common frame.** Each bar sits in a light track
    representing all hex-seasons of its kind, so the eye compares filled
    fractions rather than two floating lengths. At 0.29% against 6.7% the small
    bar is nearly invisible at true scale -- which is the point, and is why the
    percentages are printed rather than left to be read off a scale.

    **No y-axis and no gridlines.** A 22.8x ratio between two numbers under 7%
    would need a log axis to draw "fairly," and a log axis on two bars invites
    the audience to decode a scale instead of seeing a contrast.
    """
    import matplotlib.pyplot as plt

    g = gate or GATE
    p_none, p_some = float(g["p_none"]), float(g["p_some"])
    ratio = p_some / p_none

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    rows = [(1.0, p_some, "at least one ignition", POINT_ORANGE),
            (0.0, p_none, "no ignition recorded", TEXT_MUTED)]
    track = max(p_some, p_none) * 1.18

    for y, p, label, color in rows:
        ax.barh(y, track, height=0.30, color="#efedea", edgecolor="none",
                zorder=1)
        ax.barh(y, p, height=0.30, color=color, edgecolor="none", zorder=2)
        ax.annotate(label, xy=(0, y + 0.235), xytext=(0, 0),
                    textcoords="offset points", ha="left", va="bottom",
                    fontsize=14.5, fontweight="bold", color=color)
        ax.annotate(f"{p:.1%}", xy=(p, y), xytext=(12, 0),
                    textcoords="offset points", ha="left", va="center",
                    fontsize=17, fontweight="bold", color=color)

    # One decimal, not zero: the report, CLAUDE.md and the storyboard all quote
    # 22.8x, and a slide reading "23x" is a discrepancy someone will catch.
    ax.annotate(f"{ratio:.1f}x", xy=(track * 0.70, 0.5),
                ha="center", va="center", fontsize=42, fontweight="bold",
                color=TEXT_PRIMARY)
    ax.annotate("more likely", xy=(track * 0.70, 0.5), xytext=(0, -36),
                textcoords="offset points", ha="center", va="center",
                fontsize=14.5, color=TEXT_SECONDARY)

    ax.set_xlim(0, track * 1.02)
    ax.set_ylim(-0.42, 1.52)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlabel(
        f"share of hex-seasons that went on to burn "
        f"{g['big_acres']:,}+ acres",
        fontsize=11.5, color=TEXT_SECONDARY, loc="left")
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    return {"p_none": p_none, "p_some": p_some, "ratio": ratio,
            "big_acres": g["big_acres"], "source": GATE_SOURCE,
            "out_path": str(out_path)}


# The dial test, from `13_hex_acres_baselines.ipynb` cells 24-25. JJA natural,
# held-out years, igniting cells only. `share_of_big` is where the >=1,000-acre
# hex-seasons actually came from -- the decisive column, and the one a figure
# built only from `p_big` would hide.
DIAL_SOURCE = "notebook/13_hex_acres_baselines.ipynb cells 24-25"

DIAL = {
    "labels":   ["1", "2", "3", "4-5", "6-10", "11-20"],
    "n_cells":  [24808, 7935, 3410, 2778, 1501, 246],
    "p_big":    [0.0542, 0.0725, 0.0924, 0.1001, 0.1086, 0.1911],
    "per_ign":  [0.0542, 0.0362, 0.0308, 0.0229, 0.0151, 0.0143],
    "share_one": 0.493,     # of all >=1,000-acre cells, those with exactly 1 start
    "share_two": 0.704,     # ... with 2 or fewer
    "n_big": 2724,
}


def plot_one_is_enough(out_path: Path, *,
                       dial: dict | None = None,
                       figsize: tuple[float, float] = (10.6, 4.2)) -> dict:
    """Beat 17 — where the large fires actually came from.

    One stacked bar over the 2,724 held-out large-fire cells, split by how many
    ignitions their hex had that season. Half the bar is a single ignition.

    **An earlier version put the rate curves beside this and failed the glance
    test.** Those curves argue a rate-versus-total subtlety -- risk rises with
    count, risk *per ignition* falls -- which is the supporting argument, not the
    claim, and it was given the larger panel while the proof sat second and
    smaller. The curves are now Q&A material: they answer "but doesn't more
    ignitions mean more risk?", which is a question, not the headline.

    **Segments are cumulative published figures, differenced.** Notebook 13
    reports 49.3% at exactly one ignition and 70.4% at two or fewer; the three
    segments follow by subtraction, so nothing here is a number the notebook did
    not print.

    **Only the first segment carries color.** It is the one the planner would
    deprioritise by ranking on ignition count, and the figure's whole job is to
    make that ground impossible to overlook.
    """
    import matplotlib.pyplot as plt

    d = dial or DIAL
    one = float(d["share_one"])
    two = float(d["share_two"]) - one          # exactly two
    more = 1.0 - float(d["share_two"])         # three or more

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    segs = [(one, POINT_ORANGE, "ONE ignition", SURFACE),
            (two, "#c9c6c1", "two", TEXT_PRIMARY),
            (more, "#e6e3df", "three or more", TEXT_PRIMARY)]

    left = 0.0
    for width, color, label, text_colour in segs:
        ax.barh(0, width, left=left, height=0.52, color=color,
                edgecolor=SURFACE, lw=2.5, zorder=2)
        cx = left + width / 2
        ax.annotate(f"{width:.0%}", xy=(cx, 0.055), ha="center", va="center",
                    fontsize=34 if color == POINT_ORANGE else 21,
                    fontweight="bold", color=text_colour, zorder=3)
        ax.annotate(label, xy=(cx, -0.13), ha="center", va="center",
                    fontsize=15 if color == POINT_ORANGE else 12.5,
                    fontweight="bold", color=text_colour, zorder=3)
        left += width

    ax.annotate("half of every large fire started with a single ignition",
                xy=(0, 0.40), ha="left", va="bottom", fontsize=16.5,
                fontweight="bold", color=TEXT_PRIMARY)
    ax.annotate(f"all {d['n_big']:,} large fires in the held-out years, "
                f"by how many times their cell ignited that season",
                xy=(0, -0.40), ha="left", va="top", fontsize=12,
                color=TEXT_SECONDARY)

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.62, 0.62)
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    return {"share_one": one, "share_exactly_two": two,
            "share_three_plus": more, "share_two_or_fewer": float(d["share_two"]),
            "n_big": d["n_big"], "source": DIAL_SOURCE,
            "out_path": str(out_path)}


def plot_recommendation(out_path: Path, *,
                        figsize: tuple[float, float] = (11.0, 5.6)) -> dict:
    """Beat 19 — the three products, closing the Tier-1 structure the deck opened.

    **Not a chart, and deliberately so.** Beat 19's headline is three
    instructions, each pointing at a different product at a different grain, so
    any single figure has to pick one and demote the other two. Worse, every
    candidate has already been shown -- the siting map is beat 7, the triage list
    beat 18, the Tier-1 tiles beat 3 -- and re-showing one in the final position
    asks the audience to re-read rather than to receive the conclusion.

    What has *not* been shown is all three side by side. Drawing them that way
    makes the closing point structural rather than rhetorical: the recommendation
    is three products because the model has three classes, and the deck opened on
    exactly that split. Beat 3 stated the allocator; this returns to it with each
    class now carrying a deliverable.

    **Shares are the full-record Tier 1 split** (`CLAUDE.md`): Natural 58.9%,
    Human 22.7%, Unknown 18.5%. Printed because they say why the three legs are
    not equal in weight, and because the Human figure is a floor -- Unknown
    concentrates in human-dominated regions.

    **Rows are ordered by share, not by the headline's clause order.** The
    headline leads with cause because that is the project's research question;
    the slide leads with Natural because that is where the acres are, and a
    viewer scanning a table reads the top row as the biggest.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    rows = [
        ("NATURAL", 0.589, "Site the work by ignition",
         "rank ground, treat what ignites at all", "hex-season", POINT_ORANGE),
        ("HUMAN", 0.227, "Target causes by region",
         "rank causes by the acres they drive", "ecoregion-season", PERIM_FILL),
        ("UNKNOWN", 0.185, "Fix the record underneath",
         "rank regions by unattributed acres", "ecoregion-season", TEXT_SECONDARY),
    ]

    # Rows fill the frame: the closing line that used to sit beneath them moved to
    # its own slide in W7, so there is no longer a band to reserve at the bottom.
    y0, dy = 0.845, 0.30
    for i, (cls, share, action, how, grain, color) in enumerate(rows):
        y = y0 - i * dy

        # class + share, left rail
        ax.text(0.018, y + 0.030, cls, fontsize=13, fontweight="bold",
                color=color, va="center")
        ax.text(0.018, y - 0.048, f"{share:.1%} of acres", fontsize=11.5,
                color=TEXT_MUTED, va="center")

        # the instruction, carrying the row
        ax.add_patch(FancyBboxPatch(
            (0.205, y - 0.092), 0.545, 0.184,
            boxstyle="round,pad=0.006,rounding_size=0.02",
            facecolor="#f4f2ef", edgecolor=color, lw=1.6, zorder=1))
        ax.text(0.232, y + 0.032, action, fontsize=17.5, fontweight="bold",
                color=color, va="center", zorder=2)
        ax.text(0.232, y - 0.044, how, fontsize=12.5, color=TEXT_SECONDARY,
                style="italic", va="center", zorder=2)

        ax.text(0.775, y, grain, fontsize=12.5, color=TEXT_MUTED,
                va="center", ha="left")

    # The slide has to *land* the talk, not summarize it. An earlier version
    # closed on "three products, because the model has three classes" -- true,
    # and a specification rather than a conclusion. The recommendation is the
    # No closing line on this figure. It carried "Rank the ground, not the fire"
    # and the finding beneath it until W7, when both moved to a text-only slide of
    # their own -- a closer competing with three product rows for the same glance
    # lands as neither. This figure now does one job: show the three products.

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    return {"classes": [r[0] for r in rows],
            "shares": [r[1] for r in rows],
            "grains": [r[4] for r in rows],
            "out_path": str(out_path)}


def plot_grain_parallel(out_path: Path, *,
                        figsize: tuple[float, float] = (10.8, 5.2)) -> dict:
    """Beat 15 — the concession, as a grain problem the deck has already solved once.

    The only figure in the deck that plots no data, and the only one whose
    subject is the *method* rather than the fire. Both are deliberate. Every
    number beat 15 could show has been shown already -- the tail is beat 11, the
    concentration beat 10, the nulls 12-14 -- and re-plotting any of them invites
    the audience to re-audit numbers at the moment the talk needs them accepting
    a conclusion.

    **What it draws instead is the parallel.** Beat 7 fixed a forecast by
    dropping grain in *space*: the region was too coarse to site anything, so
    the map broke into hexes. The tail failure is the same defect on the *time*
    axis -- a season is too coarse to say how big a fire gets -- and the deck
    cannot fix it, because same-day data is a different acquisition project.

    Drawing them as two parallel rows makes the second drop arrive as
    recognition rather than as a new claim: the audience has already lived
    through the first one and watched it work.

    **The solved row is closed and ticked; the open row is dashed.** The
    asymmetry is the honesty -- one drop is a result, the other is a hypothesis.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def node(cx, cy, text, color, filled, w=0.20, h=0.145):
        ax.add_patch(FancyBboxPatch(
            (cx - w / 2, cy - h / 2), w, h,
            boxstyle="round,pad=0.008,rounding_size=0.03",
            facecolor="#efedea" if filled else "none",
            edgecolor=color, lw=1.8,
            linestyle="solid" if filled else (0, (5, 3.5)), zorder=2))
        ax.text(cx, cy, text, ha="center", va="center", fontsize=17,
                fontweight="bold", color=color, zorder=3)

    rows = [
        # y, axis label, coarse, fine, color, solved
        (0.700, "WHERE IT BURNS", "the region", "the hex", TEXT_SECONDARY, True),
        (0.290, "HOW BIG IT GETS", "the season", "the day", POINT_ORANGE, False),
    ]

    for y, axis_label, coarse, fine, color, solved in rows:
        ax.text(0.035, y, " ".join(axis_label), ha="left", va="center",
                fontsize=10.5, fontweight="bold", color=color)
        node(0.455, y, coarse, color, solved)
        node(0.775, y, fine, color, solved)
        ax.annotate("", xy=(0.664, y), xytext=(0.566, y),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=2.2,
                                    shrinkA=0, shrinkB=0))
        ax.text(0.930, y, "solved" if solved else "untested",
                ha="left", va="center", fontsize=12.5,
                fontweight="bold" if not solved else "normal",
                color=TEXT_MUTED if solved else POINT_ORANGE,
                style="normal" if solved else "italic")

    ax.text(0.5, 0.045,
            "one drop is a result. the other is a hypothesis.",
            ha="center", va="center", fontsize=13, style="italic",
            color=TEXT_SECONDARY)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    return {"solved": ("the region", "the hex"),
            "untested": ("the season", "the day"),
            "out_path": str(out_path)}


def siting_ranking(panel: pd.DataFrame, grid: pd.DataFrame, *,
                   region_prefix: str = "Klamath",
                   target_year: int = 2020,
                   season_ord: int = 2) -> tuple[pd.DataFrame, str]:
    """Hexes of one region-season, ranked by predicted ignitions.

    The prediction is the persistence baseline -- the hex's own natural + human
    ignition history from seasons strictly before `target_year` -- so the
    ranking is a forecast, not a retrospective sort. Shared by the map and the
    capture curve so the two cannot disagree about the order.
    """
    ids = set(grid.loc[grid["region"].str.startswith(region_prefix), "hex_id"])
    region_name = grid.loc[grid["hex_id"].isin(ids), "region"].iloc[0]

    d = panel[(panel["hex_id"].isin(ids))
              & (panel["season_ord"] == season_ord)
              & (panel["season_year"] == target_year)].copy()
    d = d.dropna(subset=["pers_natural", "pers_human"])
    d["pred"] = d["pers_natural"] + d["pers_human"]
    d["actual"] = d["starts_natural"] + d["starts_human"]
    return d.sort_values("pred", ascending=False).reset_index(drop=True), region_name


def plot_siting_glance(panel: pd.DataFrame, grid: pd.DataFrame, out_path: Path, *,
                       region_prefix: str = "Klamath",
                       target_year: int = 2020,
                       captures: tuple[float, float] = (0.30, 0.60),
                       label: bool = True,
                       locator: bool = True,
                       cfg=None,
                       figsize: tuple[float, float] = (7.6, 7.6)) -> dict:
    """Beat 7 — the ground the ranking names, in two bands.

    Hexes ranked by the persistence baseline, then filled in two bands cut where
    cumulative captured ignitions cross each of `captures`. In the default
    region:

    * **deep** -- 12 of 198 hexes, 6.1% of the ground, catching **31.7%** of
      next season's starts (5.23x lift)
    * **light** -- the next 45 hexes, taking the total to 28.8% of the ground
      for **60.1%** of starts (2.09x)
    * **pale** -- the remaining 141 hexes, where the ranking has stopped paying

    **Two bands and a wide lightness gap, not a graded ramp.** An earlier
    three-tier version shaded 12 / 45 / 97 hexes in adjacent saturations of one
    hue and read as continuous, which asserts the gradation the W6 modeling
    denies -- ignition is a **gate, not a dial**. Two bands separated by a large
    lightness step read as two decisions, which is what they are: treat first,
    treat next, stop.

    **The bands are the map's version of the capture curve's first two marks**,
    so the pair can be shown together and read as one argument: the curve gives
    the rate of decay, the map gives the ground it corresponds to. Both read the
    same `siting_ranking`.

    Labels name what each band buys rather than what it is, because "6.1% of the
    ground catches a third of the starts" is the sentence a planner acts on.
    `label=False` renders the bare map for a slide that carries its own caption.
    """
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from scipy.stats import spearmanr

    d, region_name = siting_ranking(panel, grid, region_prefix=region_prefix,
                                    target_year=target_year)
    cum = (d["actual"].cumsum() / d["actual"].sum()).to_numpy()
    n = len(d)
    cuts = [int((cum < c).sum()) + 1 for c in captures]

    # One hue, two steps, with a deliberately large lightness gap between them
    # and again before the untreated ground -- so the eye sorts three states
    # rather than reading a ramp.
    DEEP, LIGHT, REST = "#8c180c", "#f0a884", "#eeece8"
    faces = [DEEP if r < cuts[0] else
             LIGHT if r < cuts[1] else REST for r in range(n)]

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.add_collection(PolyCollection(hex_polygons(d["hex_id"].tolist()),
                                     facecolors=faces, edgecolors=SURFACE,
                                     linewidths=0.5))
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)

    bands = []
    for i, cut in enumerate(cuts):
        bands.append({"capture_target": captures[i],
                      "n_hex": cut,
                      "ground": cut / n,
                      "caught": float(cum[cut - 1]),
                      "lift": float(cum[cut - 1]) / (cut / n)})

    rings = hex_polygons(d["hex_id"].tolist())

    if label:
        # Leader lines onto the bands themselves rather than a legend: a reader
        # should not have to match a swatch to a color. Each label is the
        # shortest sentence saying what that ground buys -- no hex count, no
        # lift multiple, both of which the return value carries for a caption.
        # Sized and weighted to survive projection from the back of a room.
        centers = np.array([np.array(r).mean(axis=0) for r in rings])
        span = centers[:, 0].max() - centers[:, 0].min()

        def anchor(lo, hi, side):
            """The band member closest to that band's own center of mass.

            Two rejected alternatives. The raw centroid lands on ground that is
            not in the band -- the light band wraps around the deep one -- so
            the leader appears to point at untreated hexes. Taking the extreme
            member on the label's side instead lands on whichever outlier is
            furthest out, pointing away from the mass the label describes.
            Nearest-to-centroid keeps the leader on a real hex in the thick of
            the band.
            """
            block = centers[lo:hi]
            c = block.mean(axis=0)
            return block[np.linalg.norm(block - c, axis=1).argmin()]

        # Text steps darker than the fill: a hue picked to read as an area wash
        # goes thin and washed-out as bold type at this size.
        DEEP_INK, LIGHT_INK = DEEP, "#c2632f"

        for lo, hi, color, ink, text, dx in (
            (0, cuts[0], DEEP, DEEP_INK,
             f"{bands[0]['ground']:.0%} of the region\n"
             f"{bands[0]['caught']:.0%} of the starts", -1.0),
            (cuts[0], cuts[1], LIGHT, LIGHT_INK,
             f"{bands[1]['ground']:.0%} of the region\n"
             f"{bands[1]['caught']:.0%} of the starts", 1.0),
        ):
            xy = anchor(lo, hi, dx)
            ax.annotate(text, xy=(xy[0], xy[1]),
                        xytext=(xy[0] + dx * span * 0.70, xy[1]),
                        ha="right" if dx < 0 else "left", va="center",
                        fontsize=17, fontweight="bold", color=ink,
                        linespacing=1.35,
                        arrowprops=dict(arrowstyle="-", color=ink, lw=1.2,
                                        alpha=0.55, shrinkA=8, shrinkB=8))

    if locator:
        # A small CONUS outline with this ecoregion filled, bottom-left where
        # the hex geography and the leader labels leave the canvas empty. An
        # audience that cannot place "Klamath Mountains" reads the hex map as
        # an abstract shape; this costs one corner and removes that.
        import geopandas as gpd

        cfg_ = cfg or _cfg()
        eco = gpd.read_file(cfg_.conus_ecoregions)[["US_L3NAME", "geometry"]]

        # Bottom-align the locator with the hexes themselves, not with the axes
        # box: `set_aspect("equal")` leaves slack above and below the geography,
        # so a hardcoded y would drift with the region's shape. Convert the
        # lowest hex vertex into axes coordinates and sit the inset on it.
        ymin_data = min(v[1] for ring in rings for v in ring)
        y0 = ax.transAxes.inverted().transform(
            ax.transData.transform((0.0, ymin_data)))[1]

        # Height follows CONUS's own aspect. A square inset box leaves a wide
        # band of empty axes under a shape that is roughly 3:2, which floats the
        # visible outline well above the alignment line.
        conus = eco.dissolve()
        x0b, y0b, x1b, y1b = conus.total_bounds
        inset_w = 0.62
        inset_h = inset_w * (y1b - y0b) / (x1b - x0b)
        inset = ax.inset_axes([-0.73, y0, inset_w, inset_h])
        inset.set_facecolor(SURFACE)
        conus.plot(ax=inset, facecolor="#e6e3df", edgecolor=SURFACE,
                   linewidth=0.6)
        here = eco[eco["US_L3NAME"] == region_name]
        if not here.empty:
            here.dissolve().plot(ax=inset, facecolor=DEEP, edgecolor=DEEP,
                                 linewidth=0.4)
        inset.set_aspect("equal")
        inset.set_zorder(5)
        inset.patch.set_alpha(1.0)
        # A light rule around the locator, not `set_axis_off`: without it the
        # small outline floats in the same white space as the hex map and reads
        # as part of the geography rather than as a separate reference frame.
        inset.set_xticks([])
        inset.set_yticks([])
        for sp in inset.spines.values():
            sp.set_visible(True)
            sp.set_color(TEXT_MUTED)
            sp.set_linewidth(0.8)
            sp.set_alpha(0.45)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.25)
    plt.close(fig)

    return {
        "region": region_name,
        "n_hex": int(n),
        "target_year": target_year,
        "bands": bands,
        "n_untreated": int(n - cuts[-1]),
        "actual_starts": int(d["actual"].sum()),
        "rho": float(spearmanr(d["pred"], d["actual"]).statistic),
        "out_path": str(out_path),
    }


def plot_capture_curve(panel: pd.DataFrame, grid: pd.DataFrame, out_path: Path, *,
                       region_prefix: str = "Klamath",
                       target_year: int = 2020,
                       marks: tuple[float, ...] = (0.30, 0.60, 0.90),
                       figsize: tuple[float, float] = (9.0, 5.6)) -> dict:
    """What the ranking is worth: ground spent against starts caught.

    The companion to `plot_siting_glance`, and deliberately the less flattering
    of the pair. The map shows the top of the ranking, where the skill is real.
    This shows the *whole* ranking, most of which is weak: the curve rises
    steeply over the first few percent of ground and then bends toward the
    random diagonal. Reaching 90% capture takes 77.8% of the region at a 1.16x
    lift -- near-uniform treatment.

    The diagonal is the counterfactual a planner needs, so it is drawn rather
    than described: treating ground at random catches starts in proportion to
    the ground treated. The filled band between curve and diagonal is the value
    the ranking adds, and its narrowing is the diminishing return.

    Both figures read the same `siting_ranking`, so the marked points here are
    the same cut the map draws.
    """
    import matplotlib.pyplot as plt

    d, region_name = siting_ranking(panel, grid, region_prefix=region_prefix,
                                    target_year=target_year)
    n = len(d)
    x = np.arange(1, n + 1) / n
    y = (d["actual"].cumsum() / d["actual"].sum()).to_numpy()

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.plot([0, 1], [0, 1], color=TEXT_MUTED, lw=0.9, ls=(0, (4, 3)), zorder=2)
    ax.fill_between(x, x, y, color=POINT_ORANGE, alpha=0.13, linewidth=0, zorder=1)
    ax.plot(x, y, color=POINT_ORANGE, lw=2.8, zorder=3)

    points = []
    for t in marks:
        i = int((y < t).sum())
        gx, gy = float(x[i]), float(y[i])
        points.append({"target": t, "ground": gx, "caught": gy, "lift": gy / gx})
        ax.plot([gx, gx], [0, gy], color=TEXT_MUTED, lw=0.8, ls=":", zorder=2)
        ax.plot([0, gx], [gy, gy], color=TEXT_MUTED, lw=0.8, ls=":", zorder=2)
        ax.plot([gx], [gy], "o", ms=7, color=POINT_ORANGE, mec=SURFACE, mew=1.6,
                zorder=4)
        ax.annotate(f"{gy:.0%} of starts\nunder {gx:.0%} of ground",
                    xy=(gx, gy), xytext=(12, -6), textcoords="offset points",
                    ha="left", va="top", fontsize=10.5, color=TEXT_PRIMARY,
                    linespacing=1.35)

    ax.annotate("treating ground at random", xy=(0.66, 0.66), xytext=(0.70, 0.55),
                fontsize=9.5, color=TEXT_MUTED)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("share of the region treated", fontsize=11, color=TEXT_SECONDARY)
    ax.set_ylabel("share of next season's starts caught", fontsize=11,
                  color=TEXT_SECONDARY)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_MUTED)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9.5)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    return {"region": region_name, "n_hex": n, "target_year": target_year,
            "points": points, "out_path": str(out_path)}



def _cfg():
    from config import ProjectConfig

    return ProjectConfig()

def decile_error_table(panel: pd.DataFrame, surface: str, *,
                       cfg=None, season_ord: int | None = None,
                       min_acres: float = 1.0) -> pd.DataFrame:
    """Typical error by burned-area decile, for one branch.

    Reproduces the tables in notebooks 13 and 14 rather than restating them, so
    a figure cannot drift from the notebook that reported the number. The
    statistic is the median *absolute* log error read back as a multiplier; the
    sign of the median log error carries the direction.

    **`min_acres=1.0` excludes the reporting floor, and that is a data-quality
    decision rather than a tidying one.** 25.3% of all FPA-FOD rows are recorded
    at exactly 0.1 acres -- 44.5% of natural fires against 19.0% of human ones --
    which is a default someone enters for a fire too small to measure, not a
    measurement. Below ~1 acre the "error" is partly the record being wrong
    rather than the model: dropping that floor cuts the smallest decile's error
    from 10.0x to 4.3x. The excluded cells carry a negligible share of acres.

    `season_ord=2` restricts to JJA (the natural branch's population);
    `season_ord=None` keeps all four seasons (the human branch's). **The two
    populations are not interchangeable.**
    """
    import hex_acres as ha

    cfg = cfg or _cfg()
    _, mag = ha.hurdle_frames(panel, surface, cfg=cfg, season_ord=season_ord)
    mag = mag[mag["season_year"] >= cfg.test_start].copy()

    acres, logcol = f"acres_{surface}", f"log_{surface}"
    mag = mag[mag[acres] >= min_acres]
    mag["log_err"] = mag[logcol] - mag[f"persburn_{logcol}"]
    mag["decile"] = pd.qcut(mag[acres].rank(method="first"), 10,
                            labels=range(1, 11))

    out = mag.groupby("decile", observed=True).agg(
        median_acres=(acres, "median"),
        median_log_err=("log_err", "median"),
        n=("log_err", "size"),
    )
    out["x_off"] = 10 ** out["median_log_err"].abs()
    out["under"] = out["median_log_err"] > 0
    return out


def plot_branch_deciles(panel: pd.DataFrame, out_path: Path, *,
                        cfg=None, min_acres: float = 1.0,
                        figsize: tuple[float, float] = (10.0, 5.6)) -> dict:
    """Beat 11 — up to a point both causes are predictable; past it, natural is harder.

    Two curves on one log axis: typical error against the burned-area decile of
    the cell. They track each other closely through the small and middle
    deciles and separate in the upper half, where natural runs 2-3x worse *at
    the same cell size* and then an order of magnitude worse at the top.

    **Follows `plot_acres_concentration` (beat 10), not the reverse.** That
    figure marks the right edge as the cells holding 98% of the acres; this one
    shows the forecast coming apart on the same edge. Same axis, same direction,
    so the separation lands where the audience was just told the stakes are.

    **Minimal annotation, deliberately.** The headline carries the claim; the
    figure only has to show two curves together, then apart. Earlier drafts
    labeled both tails with their multiples and their median acreage, which
    invited a reader to audit four numbers instead of seeing one shape.

    **Cells below `min_acres` are excluded** -- see `decile_error_table` for why
    the 0.1-acre reporting floor makes the smallest deciles partly a picture of
    reporting convention rather than of forecast error.
    """
    import matplotlib.pyplot as plt

    cfg = cfg or _cfg()
    nat = decile_error_table(panel, "natural", cfg=cfg, season_ord=2,
                             min_acres=min_acres)
    hum = decile_error_table(panel, "human", cfg=cfg, season_ord=None,
                             min_acres=min_acres)

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    x = np.arange(1, 11)

    for tbl, color, label in ((hum, PERIM_FILL, "human"),
                               (nat, POINT_ORANGE, "natural")):
        y = tbl["x_off"].to_numpy()
        ax.plot(x, y, color=color, lw=2.8, marker="o", ms=7, mfc=SURFACE,
                mew=1.9, zorder=3)
        ax.annotate(label, xy=(x[-1], y[-1]), xytext=(14, 0),
                    textcoords="offset points", ha="left", va="center",
                    fontsize=13, fontweight="bold", color=color)

    ax.set_yscale("log")
    # Each point is a decile, so the axis is already a percentage of cells --
    # label it as one rather than making a viewer decode "decile 7".
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d*10}%" for d in x])
    ax.set_xlim(0.6, 10.9)
    ax.set_xlabel("cells ordered by acres burned, least to most",
                  fontsize=11, color=TEXT_SECONDARY)
    ax.set_ylabel("how far off the forecast was", fontsize=11,
                  color=TEXT_SECONDARY)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}x" if v >= 1 else "")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_MUTED)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=10)

    return_ = {
        "min_acres": min_acres,
        "natural_top_x": float(nat["x_off"].iloc[-1]),
        "natural_top_median_acres": float(nat["median_acres"].iloc[-1]),
        "human_top_x": float(hum["x_off"].iloc[-1]),
        "human_top_median_acres": float(hum["median_acres"].iloc[-1]),
        "natural_n": int(nat["n"].sum()),
        "human_n": int(hum["n"].sum()),
        "out_path": str(out_path),
    }
    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)
    return return_


def plot_acres_concentration(panel: pd.DataFrame, out_path: Path, *,
                             surface: str = "natural",
                             min_acres: float = 0.0,
                             figsize: tuple[float, float] = (8.6, 5.8)) -> dict:
    """Beat 10 — almost all the acres sit in almost none of the cells.

    A Lorenz-style cumulative curve over burning cells, **ordered smallest to
    largest so the axis runs the same direction as `plot_branch_deciles`.** The
    two beats are a pair and this one leads: 10 names which cells hold the acres,
    11 then shows the forecast failing on exactly those cells. Ordering the
    stakes first means beat 11 lands as a consequence rather than as one more
    disappointment. Drawn with opposite orientations, a viewer who learned one
    would read the other backwards, so both run least-to-most.

    Zero-acre cells are excluded deliberately: 96% of hex-seasons never burn,
    and including them would make the curve a statement about how rare fire is
    rather than about how unevenly it concentrates *once it happens*.

    **"Largest cells" is the wrong phrase and the figure avoids it.** Every
    res-5 hex is the same ~62,494 acres, so a reader who sees "largest" reads
    geography when the ordering is by *acres burned*. The annotations say
    worst-burning; the axis says least to most.

    **Sub-acre cells stay in, unlike beat 11.** That figure drops them because
    their *error* is a reporting artifact -- 25.3% of FPA-FOD rows sit at
    exactly 0.1 acres. Here the quantity being counted is acres, and those acres
    are real however coarsely they were recorded. The cells matter enormously to
    this figure and not at all to the total: they are **46.9% of burning cells
    and 0.018% of the acres**, which is precisely the concentration the curve
    exists to show. Excluding them would move the headline from 98% to 93% by
    shrinking the count of cells rather than by removing any burn.

    The diagonal is the counterfactual: what the curve would look like if acres
    were spread evenly across burning cells. The gap between curve and diagonal
    is the finding, drawn as a filled band so it reads without either axis.
    """
    import matplotlib.pyplot as plt

    col = f"acres_{surface}"
    # Burning cells only, then any explicit floor on top. `>= min_acres` alone
    # would admit the 96% of hex-seasons that never burn when the floor is 0.
    keep = (panel[col] > 0) & (panel[col] >= min_acres)
    s = panel.loc[keep, col].sort_values().to_numpy()
    cum = np.cumsum(s) / s.sum()
    frac = np.arange(1, len(s) + 1) / len(s)

    def top_share(p):
        """Share of acres held by the largest `p` of cells."""
        k = max(1, int(round(len(s) * p)))
        return float(s[-k:].sum() / s.sum())

    top1, top10 = top_share(0.01), top_share(0.10)

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    ax.plot([0, 1], [0, 1], color=TEXT_MUTED, lw=0.9, ls=(0, (4, 3)), zorder=2)
    ax.fill_between(frac, cum, frac, color=POINT_ORANGE, alpha=0.13,
                    linewidth=0, zorder=1)
    ax.plot(frac, cum, color=POINT_ORANGE, lw=2.4, zorder=3)

    # Mark the two cuts from the right-hand (largest) end, which is where the
    # acres are and where beat 11's failure lives.
    for p, share in ((0.10, top10), (0.01, top1)):
        x = 1.0 - p
        y = 1.0 - share
        ax.plot([x, x], [0, y], color=TEXT_MUTED, lw=0.8, ls=":", zorder=2)
        ax.plot([x, 1.0], [y, y], color=TEXT_MUTED, lw=0.8, ls=":", zorder=2)
        ax.plot([x], [y], "o", ms=6, color=POINT_ORANGE, mec=SURFACE, mew=1.5,
                zorder=4)
        ax.annotate(f"the worst-burning {p:.0%} of cells\nhold {share:.0%} of the acres",
                    xy=(x, y), xytext=(-14, 16), textcoords="offset points",
                    ha="right", va="bottom", fontsize=10.5, color=TEXT_PRIMARY,
                    linespacing=1.35, zorder=5)

    ax.annotate("if acres were spread evenly", xy=(0.40, 0.40),
                xytext=(0.05, 0.60), fontsize=9.5, color=TEXT_MUTED)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("cells ordered by acres burned, least to most",
                  fontsize=11, color=TEXT_SECONDARY)
    ax.set_ylabel(f"cumulative share of {surface} acres", fontsize=11,
                  color=TEXT_SECONDARY)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_MUTED)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9.5)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.25)
    plt.close(fig)

    return {
        "surface": surface,
        "min_acres": min_acres,
        "n_burning": int(len(s)),
        "n_cells": int(len(panel)),
        "top1_share": top1,
        "top10_share": top10,
        "out_path": str(out_path),
    }


def season_curves(fires: pd.DataFrame, *, years: int | None = None) -> dict:
    """Weekly starts and acres per year, split Human / Natural.

    Separated from the plotting so the notebook can quote peak weeks without
    rendering. Counts are divided by the number of years in the record so the
    axis reads as "a typical year" rather than a 29-year total, which no
    audience holds in their head.
    """
    d = fires.dropna(subset=["DISCOVERY_DOY"]).copy()
    n_years = years or int(d["FIRE_YEAR"].nunique())
    d["cls"] = np.where(d["NWCG_CAUSE_CLASSIFICATION"] == "Natural", "Natural",
                        np.where(d["NWCG_CAUSE_CLASSIFICATION"]
                                 .str.startswith("Missing"), "Unknown", "Human"))
    # 52 weeks; the ragged 53rd is folded into the last so the curve closes.
    d["week"] = (((d["DISCOVERY_DOY"] - 1) // 7).clip(0, 51)).astype(int)

    starts = (d.pivot_table(index="week", columns="cls", values="FIRE_SIZE",
                            aggfunc="size", fill_value=0)
              .reindex(range(52), fill_value=0) / n_years)
    acres = (d.pivot_table(index="week", columns="cls", values="FIRE_SIZE",
                           aggfunc="sum", fill_value=0)
             .reindex(range(52), fill_value=0) / n_years)

    def peak(frame, col):
        return int(frame[col].idxmax())

    return {
        "starts": starts, "acres": acres, "n_years": n_years,
        "human_starts_peak": peak(starts, "Human"),
        "natural_starts_peak": peak(starts, "Natural"),
        "human_acres_peak": peak(acres, "Human"),
        "natural_acres_peak": peak(acres, "Natural"),
        "offset_weeks": peak(starts, "Natural") - peak(starts, "Human"),
    }


def plot_seasonality(fires: pd.DataFrame, out_path: Path, *,
                     years: int | None = None,
                     figsize: tuple[float, float] = (11.0, 5.8)) -> dict:
    """Beat 1 — the count-vs-consequence gap, on one calendar.

    Acres as a filled area, starts as a dashed line, both against the week of
    the year. The two peaks sit weeks apart: most fires start in spring, most
    acres burn in summer. That gap is the premise the whole project rests on —
    counting ignitions and counting consequences give different answers about
    when the year is dangerous.

    **Neither y-axis is drawn, and no magnitude appears anywhere.** Two series
    on two scales in one frame invites the reader to read the point where the
    dashed line crosses the filled area as meaningful. It is not: it falls
    wherever the two arbitrary scalings happen to intersect. Removing the axes
    removes that false affordance, leaving only what is genuinely comparable —
    the *shape* of each curve along a shared calendar, i.e. when each one peaks.

    **Why the acres magnitude is not quoted either.** Each plotted point is a
    mean across the 29 years for that week-of-year slot, and weekly acres are
    heavy-tailed enough that the mean is not a typical value: in the peak week
    the mean is 526k against a median of 237k, a 2.2x gap driven by 2015 alone
    (4.38M acres in that one week). Labeling 526k as "typical" would assert
    exactly what the project's own tail analysis disproves. Starts do not have
    this problem — mean 2,458 against median 2,342 — but a magnitude on one
    curve and not the other would invite the comparison the missing axes are
    there to prevent. The figure claims *when*, and only when.

    Callers wanting the numbers get them in the return value, where they can be
    reported with the mean/median caveat attached.

    **Weekly, not monthly, and the reason is a correctness one.** Monthly bars
    are smoother and drop the July 4 spike, but aggregation merges that spike
    into July and lifts July (10,141 starts) above March (9,726) — which inverts
    the claim, making July rather than spring the starts maximum. At weekly grain
    the spring hump is the genuine seasonal peak (2,458 in a typical week) and
    the July 4 week (2,817) is a separable one-week event.

    **The spring peak is located within spring, not by `idxmax`.** The global
    maximum of the starts curve is that July 4 week, so anchoring the callout to
    the global max points the leader at a holiday spike while the caption reads
    "spring."

    All causes combined. The Human/Natural split is a later beat; a four-curve
    version of this figure loses the one comparison it exists to make.
    """
    import matplotlib.pyplot as plt

    s = season_curves(fires, years=years)
    starts = s["starts"].sum(axis=1)
    acres = s["acres"].sum(axis=1)
    weeks = np.arange(52)

    # Spring window: March through early June. Deliberately excludes the July 4
    # week, which is the curve's global maximum but not a seasonal one.
    spring_peak = int(starts.iloc[SPRING_WEEKS].idxmax())
    acres_peak = int(acres.idxmax())

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.fill_between(weeks, acres, color=POINT_ORANGE, alpha=0.28,
                    linewidth=0, zorder=2)
    ax.plot(weeks, acres, color=POINT_ORANGE, lw=2.8, zorder=3)
    ax.set_facecolor(SURFACE)
    ax.set_ylim(0, float(acres.max()) * 1.52)

    ax2 = ax.twinx()
    ax2.plot(weeks, starts, color=TEXT_SECONDARY, lw=2.0, ls=(0, (5, 2.5)),
             zorder=4)
    ax2.set_ylim(0, float(starts.max()) * 1.52)

    for a in (ax, ax2):
        for sp in a.spines.values():
            sp.set_visible(False)
        a.set_yticks([])
        a.set_xticks([])

    # A faint baseline for the calendar to sit on, and month letters centered
    # between true month starts -- "week 29" means nothing to an audience.
    ax.axhline(0, color=TEXT_MUTED, lw=0.8, alpha=0.55, zorder=1)
    edges = np.append(MONTH_START_WEEKS, 52.0)
    for x, m in zip((edges[:-1] + edges[1:]) / 2, "JFMAMJJASOND"):
        ax.annotate(m, xy=(x, 0), xycoords=("data", "axes fraction"),
                    xytext=(0, -14), textcoords="offset points", ha="center",
                    va="top", fontsize=11, color=TEXT_SECONDARY,
                    annotation_clip=False)

    # The two callouts are the only text on the canvas. Each is colored to its
    # own curve, which is what binds them -- no legend, no series labels.
    ax2.annotate(
        "most fires start in spring",
        xy=(spring_peak, float(starts.iloc[spring_peak])),
        xytext=(spring_peak - 3.0, float(starts.max()) * 1.30),
        ha="center", va="bottom", fontsize=12.5, color=TEXT_SECONDARY,
        arrowprops=dict(arrowstyle="-", color=TEXT_MUTED, lw=0.9, alpha=0.6,
                        shrinkA=4, shrinkB=4))
    ax.annotate(
        "most acres burn in summer",
        xy=(acres_peak, float(acres.max())),
        xytext=(acres_peak + 9.5, float(acres.max()) * 1.28),
        ha="center", va="bottom", fontsize=12.5, color=POINT_ORANGE,
        arrowprops=dict(arrowstyle="-", color=POINT_ORANGE, lw=0.9, alpha=0.6,
                        shrinkA=4, shrinkB=4))

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    # Per-year values in the two peak week-slots, so a caption can report the
    # mean-vs-median gap rather than restating the mean as though it were typical.
    d = fires.dropna(subset=["DISCOVERY_DOY"]).copy()
    d["week"] = (((d["DISCOVERY_DOY"] - 1) // 7).clip(0, 51)).astype(int)
    acres_by_year = (d.loc[d["week"] == acres_peak]
                     .groupby("FIRE_YEAR")["FIRE_SIZE"].sum())
    starts_by_year = (d.loc[d["week"] == spring_peak]
                      .groupby("FIRE_YEAR").size())

    return {
        "n_years": s["n_years"],
        "spring_starts_peak_week": spring_peak,
        "spring_starts_mean": float(starts.iloc[spring_peak]),
        "spring_starts_median": float(starts_by_year.median()),
        "july4_week": int(starts.idxmax()),
        "july4_starts_mean": float(starts.max()),
        "acres_peak_week": acres_peak,
        "acres_peak_mean": float(acres.max()),
        "acres_peak_median": float(acres_by_year.median()),
        "acres_peak_max": float(acres_by_year.max()),
        "acres_peak_max_year": int(acres_by_year.idxmax()),
        "out_path": str(out_path),
    }


# Diverging ember <-> blue, through a desaturated middle. Blue and orange are
# already the project's Human and Natural hues (`plot_branch_deciles`, the
# seasonality figure), so the map inherits the deck's existing binding rather
# than teaching a third color language. The midpoint is deliberately pale and
# slightly warm-gray: a region that genuinely splits its acres between causes
# should recede, not compete with the committed ones.
DIV_CAUSE = [
    "#2c5f9e", "#4f86c6", "#8fb3d9", "#ccd6db", "#e8dcd2",
    "#f3b183", "#ea8c4d", "#d2661f", "#a83e08",
]


def _cause_cmap():
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list("proj_cause", DIV_CAUSE)


def region_cause_dominance(panel, *, min_acres: float = 0.0) -> pd.DataFrame:
    """Natural share of *attributed* acres, per Level III region.

    The denominator is Human + Natural, deliberately excluding the Unknown mass.
    On a total-acres denominator a region with poor cause reporting drifts toward
    the middle of the scale for a records reason rather than a fire reason, which
    would make the map partly a picture of attribution quality -- the subject of
    a different branch and a later beat. `unknown_share` is returned alongside so
    that caveat stays quotable.
    """
    t = panel.tier1_composition()
    g = t.groupby("region")[["human_ac", "natural_ac", "unknown_ac", "total_ac"]].sum()
    resolved = g["human_ac"] + g["natural_ac"]
    out = pd.DataFrame({
        "human_ac": g["human_ac"],
        "natural_ac": g["natural_ac"],
        "total_ac": g["total_ac"],
        "resolved_ac": resolved,
        "natural_share": g["natural_ac"] / resolved.where(resolved > 0),
        "unknown_share": g["unknown_ac"] / g["total_ac"].where(g["total_ac"] > 0),
    })
    return out[out["total_ac"] >= min_acres] if min_acres else out


def plot_cause_map(panel, out_path: Path, *, cfg=None,
                   figsize: tuple[float, float] = (12.0, 7.0)) -> dict:
    """Beat 2 — cause is regional: one map, 105 ecoregions, two colors.

    Every Level III ecoregion filled by its natural share of attributed acres.
    Deep blue is human-dominated, deep ember natural-dominated.

    **The finding the map carries is that the distribution is bimodal, not
    graded.** 50 of 105 regions sit below 20% natural and 28 above 80%; only 27
    fall in between. Regions largely commit to one cause or the other, which is
    what licenses a per-region prevention/mitigation split rather than a single
    national posture. A continuous ramp would let a viewer read a smooth
    gradient that is not there, so the color scale is stepped at the deciles
    that matter and the two committed ends carry most of the range.

    Alaska is drawn inset rather than dropped. It is 20 of the 105 regions and
    the most natural-dominated ground in the record; omitting it would remove
    one whole end of the very contrast the slide is making.
    """
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm

    cfg = cfg or _cfg()
    dom = region_cause_dominance(panel)

    conus = gpd.read_file(cfg.conus_ecoregions)[["US_L3NAME", "geometry"]]
    conus = conus.dissolve(by="US_L3NAME").join(dom, how="left")
    ak = gpd.read_file(cfg.ak_ecoregions)[["US_L3NAME", "geometry"]]
    ak = ak.dissolve(by="US_L3NAME").join(dom, how="left")

    cmap = _cause_cmap()
    bounds = [0, .05, .20, .40, .60, .80, .95, 1.0]
    norm = BoundaryNorm(bounds, cmap.N)
    style = dict(cmap=cmap, norm=norm, edgecolor=SURFACE, linewidth=0.25,
                 missing_kwds={"color": "#eeece8", "edgecolor": SURFACE,
                               "linewidth": 0.25})

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    conus.plot(column="natural_share", ax=ax, **style)
    ax.set_aspect("equal"); ax.set_axis_off()

    # Alaska inset, its own equal-area CRS preserved -- reprojecting it into the
    # CONUS Albers would distort it badly at that latitude. Placed clear of the
    # southern border so it does not read as continuous with Texas.
    inset = ax.inset_axes([-0.04, -0.02, 0.30, 0.34])
    inset.set_facecolor(SURFACE)
    ak.plot(column="natural_share", ax=inset, **style)
    inset.set_aspect("equal"); inset.set_axis_off()
    inset.annotate("Alaska", xy=(0.52, 0.02), xycoords="axes fraction",
                   ha="center", va="bottom", fontsize=9.5, color=TEXT_MUTED)

    # Horizontal bar under the map. Ticks are placed at the *bin edges* the
    # BoundaryNorm actually uses -- passing round numbers like 0.5 against uneven
    # bins puts the label somewhere other than the color it names.
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(sm, ax=ax, fraction=0.030, pad=0.02, shrink=0.52,
                        orientation="horizontal", ticks=bounds, spacing="uniform")
    cbar.ax.set_xticklabels([f"{b:.0%}" for b in bounds], fontsize=9,
                            color=TEXT_SECONDARY)
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(length=0)

    # The two ends carry the meaning, so they are labeled where the color is
    # rather than restated in a sentence underneath. Each sits outside its own
    # end of the bar, in its own hue, so the binding needs no reading order.
    for x, ha, txt, color in ((-0.03, "right", "human-dominated", PERIM_FILL),
                               (1.03, "left", "natural-dominated", POINT_ORANGE)):
        cbar.ax.annotate(txt, xy=(x, 0.5), xycoords="axes fraction",
                         ha=ha, va="center", fontsize=11, color=color)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.2)
    plt.close(fig)

    q = dom["natural_share"].dropna()
    return {
        "n_regions": int(len(q)),
        "human_dominated": int((q < 0.20).sum()),
        "natural_dominated": int((q > 0.80).sum()),
        "mixed": int(((q >= 0.20) & (q <= 0.80)).sum()),
        "median_natural_share": float(q.median()),
        "out_path": str(out_path),
    }


# Sequential purple, pale -> deep: year-to-year volatility of the cause mix.
# Deliberately off both the ember and blue ramps -- volatility is not "more
# natural" or "more human", it is a third quantity about a region's *behavior*,
# and reusing either cause hue would imply it takes a side.
SEQ_VOLATILE = [
    "#f4f1f6", "#e2dcea", "#c9bedb", "#ac9bc7", "#8b76b0",
    "#6d5596", "#513a79", "#37245b",
]


def region_year_volatility(panel, *, min_years: int = 20) -> pd.DataFrame:
    """Year-to-year SD of a region's natural share, seasons pooled.

    Seasons are pooled *within* a region-year before the share is taken, so the
    figure answers "does this region's cause mix hold still from year to year"
    without re-stating the seasonal signal the opening figure already carries.

    Denominator is attributed acres (Human + Natural), matching
    `region_cause_dominance` so the volatility map and the dominance map
    partition the same quantity.
    """
    t = panel.tier1_composition()
    y = (t.groupby(["region", "season_year"])[["human_ac", "natural_ac", "total_ac"]]
         .sum().reset_index())
    resolved = y["human_ac"] + y["natural_ac"]
    y["nat"] = y["natural_ac"] / resolved.where(resolved > 0)
    y = y.dropna(subset=["nat"])

    g = y.groupby("region")
    out = pd.DataFrame({
        "n_years": g.size(),
        "total_ac": g["total_ac"].sum(),
        "nat_mean": g["nat"].mean(),
        "nat_sd": g["nat"].std(),
    })
    out["commitment"] = (out["nat_mean"] - 0.5).abs()
    return out[out["n_years"] >= min_years]


def plot_volatility_map(panel, out_path: Path, *, cfg=None,
                        min_years: int = 20,
                        figsize: tuple[float, float] = (12.0, 7.0)) -> dict:
    """Beat 3 — which regions' cause mix holds still, and which flip.

    Companion to `plot_cause_map`, on the same geometry and the same
    attributed-acres denominator. That map says *which* cause a region runs on;
    this one says *whether that answer stays put* from year to year, which is
    the property a next-season forecast actually depends on.

    **The two maps are not independent.** Volatility tracks how close a region's
    long-run mix sits to an even split: Spearman -0.880 between |mean - 0.5| and
    the year-to-year SD. Regions dominated by one cause hold that mix; regions
    near 50/50 swing across the whole range. Part of that is mechanical -- a
    share pinned near 0 or 1 has less room to move, the same floor/ceiling effect
    that makes binomial variance peak at p=0.5 -- so the honest reading is that
    commitment and stability *coincide*, not that one causes the other. The
    planner-relevant consequence is unchanged either way.

    **Small regions dominate the volatile end** (Bristol Bay-Nushagak at 0.458
    on 0.1M acres, Cook Inlet at 0.435 on 0.6M) because one fire can flip a
    small region's mix. `total_ac` is returned so a caption can say so, and the
    notebook quotes the volatile *large* regions separately.
    """
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap

    cfg = cfg or _cfg()
    vol = region_year_volatility(panel, min_years=min_years)

    conus = gpd.read_file(cfg.conus_ecoregions)[["US_L3NAME", "geometry"]]
    conus = conus.dissolve(by="US_L3NAME").join(vol, how="left")
    ak = gpd.read_file(cfg.ak_ecoregions)[["US_L3NAME", "geometry"]]
    ak = ak.dissolve(by="US_L3NAME").join(vol, how="left")

    cmap = LinearSegmentedColormap.from_list("proj_vol", SEQ_VOLATILE)
    bounds = [0, .05, .10, .15, .20, .25, .30, .35, .50]
    norm = BoundaryNorm(bounds, cmap.N)
    style = dict(cmap=cmap, norm=norm, edgecolor=SURFACE, linewidth=0.25,
                 missing_kwds={"color": "#eeece8", "edgecolor": SURFACE,
                               "linewidth": 0.25})

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    conus.plot(column="nat_sd", ax=ax, **style)
    ax.set_aspect("equal"); ax.set_axis_off()

    inset = ax.inset_axes([-0.04, -0.02, 0.30, 0.34])
    inset.set_facecolor(SURFACE)
    ak.plot(column="nat_sd", ax=inset, **style)
    inset.set_aspect("equal"); inset.set_axis_off()
    inset.annotate("Alaska", xy=(0.52, 0.02), xycoords="axes fraction",
                   ha="center", va="bottom", fontsize=9.5, color=TEXT_MUTED)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(sm, ax=ax, fraction=0.030, pad=0.02, shrink=0.52,
                        orientation="horizontal", ticks=bounds, spacing="uniform")
    cbar.ax.set_xticklabels([f"{b:.2f}" for b in bounds], fontsize=9,
                            color=TEXT_SECONDARY)
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(length=0)
    for x, ha, txt in ((-0.03, "right", "holds its mix"),
                       (1.03, "left", "flips year to year")):
        cbar.ax.annotate(txt, xy=(x, 0.5), xycoords="axes fraction",
                         ha=ha, va="center", fontsize=11, color=TEXT_SECONDARY)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.2)
    plt.close(fig)

    from scipy.stats import spearmanr
    v = vol.dropna(subset=["nat_sd"])
    rho = spearmanr(v["commitment"], v["nat_sd"])
    big = v[v["total_ac"] >= 1_000_000]
    return {
        "n_regions": int(len(v)),
        "median_sd": float(v["nat_sd"].median()),
        "stable_under_10": int((v["nat_sd"] < 0.10).sum()),
        "volatile_over_30": int((v["nat_sd"] > 0.30).sum()),
        "rho_commitment_volatility": float(rho.statistic),
        "n_big_regions": int(len(big)),
        "median_sd_big": float(big["nat_sd"].median()),
        "out_path": str(out_path),
    }


def _draw_score_tiles(labels, values, out_path: Path, *,
                      figsize: tuple[float, float] = (11.0, 3.6),
                      ranges=None, notes=None) -> None:
    """Render one row of stat tiles. Shared by the Tier-1 and Human beats.

    One implementation, two slides: the beats are the same question one level
    apart in the hierarchy, so they should look identical and the reader should
    not have to learn a second encoding to read the second one.

    Tiles are ordered worst -> best left to right. A reader scans that way, so
    the sequence builds to the winning number instead of opening on it, and the
    uninformed baselines end up adjacent -- which is where the sharpest
    comparison lives. The winner takes the ember accent; the rest sit in a
    recessive neutral, because the point is which one wins.

    `notes`, when given, is one string per tile (empty for tiles that carry
    none), drawn in the span's slot. It exists for beats whose metric admits no
    per-cell interval -- a top-1 hit rate is 0/1 per cell, so its quartiles are 0
    and 1 -- where the honest equivalent is a stated split rather than a span.

    `ranges`, when given, is one `(low, high)` per tile in the same order as
    `values`, drawn as a span beneath the bar with the headline mean marked on
    it. **It is a spread across region-seasons, not a confidence interval** --
    the tile's number is an average over thousands of cells and a planner
    receives one of them, so the span answers "how much does this vary from
    place to place", which is a different question from "how sure are we of the
    average". The label drawn says "typical range" for that reason: no
    inferential claim is being made.

    No title and no caption is drawn: the slide's headline supplies the framing,
    and the numbers a caption would need are returned by the caller.
    """
    import matplotlib.pyplot as plt

    order = np.argsort(np.asarray(values, dtype=float))
    labels = list(np.asarray(labels, dtype=object)[order])
    values = list(np.asarray(values, dtype=float)[order])
    if ranges is not None:
        ranges = [tuple(r) for r in np.asarray(ranges, dtype=float)[order]]
    if notes is not None:
        notes = list(np.asarray(notes, dtype=object)[order])
    best = len(values) - 1

    fig, axes = plt.subplots(1, len(values), figsize=figsize, facecolor=SURFACE,
                             gridspec_kw={"wspace": 0.14})
    for i, (ax, label, value) in enumerate(zip(np.atleast_1d(axes), labels, values)):
        ax.set_facecolor(SURFACE)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)

        win = i == best
        accent = POINT_ORANGE if win else "#b9b6b0"
        ink = TEXT_PRIMARY if win else TEXT_SECONDARY

        ax.text(0, 0.86, label, fontsize=12.5, color=TEXT_SECONDARY,
                ha="left", va="top")
        # Proportional figures at display size, per the stat-tile contract.
        ax.text(0, 0.50, f"{value:.0%}", fontsize=52, color=ink,
                ha="left", va="center", fontweight="bold")

        # A shared 0-100% track, so the bars are comparable across tiles.
        bar_y = 0.17 if (ranges is None and notes is None) else 0.30
        ax.add_patch(plt.Rectangle((0, bar_y), 1.0, 0.05, facecolor="#eeece8",
                                   edgecolor="none"))
        ax.add_patch(plt.Rectangle((0, bar_y), value, 0.05, facecolor=accent,
                                   edgecolor="none"))

        if ranges is not None:
            low, high = ranges[i]
            span_y = 0.15
            # The span sits on the SAME 0-100% track as the bar above it, so the
            # eye reads width against the bar without a second scale to learn.
            ax.plot([low, high], [span_y, span_y], color=accent, lw=2.4,
                    solid_capstyle="butt", zorder=2)
            for x in (low, high):
                ax.plot([x, x], [span_y - 0.035, span_y + 0.035], color=accent,
                        lw=1.4, zorder=3)
            ax.text(0, 0.02, f"typical range {low:.0%}–{high:.0%}", fontsize=9.5,
                    color=TEXT_SECONDARY, ha="left", va="bottom")

        if notes is not None and notes[i]:
            # A single annotation line, used where the metric admits no interval
            # (top-1 is 0/1 per cell). Same slot as the span's caption so the two
            # beats still line up vertically at the same height.
            ax.text(0, 0.02, notes[i], fontsize=9.5, color=ink if win else TEXT_SECONDARY,
                    ha="left", va="bottom")

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)


def _weighted_quantile(values, weights, q: float) -> float:
    """Quantile of `values` under `weights`, by the cumulative-weight definition.

    numpy has no weighted percentile. Sort by value, walk the cumulative weight,
    and read off where it crosses `q` of the total -- with the cumulative taken
    at interval midpoints so the result is symmetric between q and 1-q rather
    than biased half a step toward the low end.

    Exists so the tiles' spread carries the SAME acre weighting as the headline
    mean above it. Mixing an acre-weighted mean with unweighted percentiles put a
    42% headline over a 50-79% range on the national tile, which reads as a
    mistake even though both numbers were correct.
    """
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    order = np.argsort(values)
    v, wt = values[order], weights[order]
    cum = np.cumsum(wt) - 0.5 * wt
    cum /= wt.sum()
    return float(np.interp(q, cum, v))


def tier1_baseline_scores(panel, *, k: int = 7, cfg=None) -> pd.DataFrame:
    """Acre-weighted TVD for three predictors of a region-season's cause mix.

    * **history** -- the cell's own k-season trailing mean, forward-chaining
    * **national** -- the record's overall composition, applied to every cell
    * **naive** -- an uninformed 1/3 on each class

    **"History" groups by `(region, season)`, so each season is its own series.**
    Klamath summer sees only prior Klamath summers; k=7 is therefore seven prior
    *same-season* occurrences -- about seven years back, not seven consecutive
    seasons. The tile label says "seasonal history" rather than "history" for
    that reason. Pooling the four seasons would average a region's
    human-dominated winter against its lightning-dominated summer and predict
    neither, which is beat 1's seasonality reappearing as a modelling error.

    `correct` is `1 - TVD`, which for two compositions on a simplex is exactly
    their overlap (the sum of elementwise minima). "Share of the composition
    placed on the right cause" is therefore a literal reading of the number, not
    a gloss -- verified by construction in the notebook.
    """
    cfg = cfg or _cfg()
    classes = ["human", "natural", "unknown"]
    t = panel.tier1_composition().sort_values(["region", "season", "season_year"])

    trail = pd.DataFrame({
        c: t.groupby(["region", "season"])[c]
            .transform(lambda s: s.shift(1).rolling(k, min_periods=1).mean())
        for c in classes})
    d = t[trail.notna().all(axis=1) & (t["season_year"] >= cfg.test_start)]
    act = d[classes].to_numpy()
    w = d["total_ac"].to_numpy()

    hist = trail.loc[d.index].to_numpy()
    hist = hist / hist.sum(axis=1, keepdims=True)
    national = np.tile(t[classes].mean().to_numpy(), (len(d), 1))
    national = national / national.sum(axis=1, keepdims=True)
    naive = np.full_like(act, 1 / 3)

    def per_cell(pred):
        """Per-cell TVD, kept rather than reduced -- the spread is the point."""
        return 0.5 * np.abs(pred - act).sum(axis=1)

    def score(pred):
        return float(np.average(per_cell(pred), weights=w))

    rows = [("the region's own seasonal history", "history", score(hist)),
            ("the national average mix", "national", score(national)),
            ("an even split across causes", "naive", score(naive))]
    out = pd.DataFrame(rows, columns=["label", "key", "tvd"]).set_index("key")
    out["correct"] = 1 - out["tvd"]

    # Middle half of the per-cell distribution, on the same 1 - TVD scale as the
    # headline. The tiles report a mean over thousands of held-out region-seasons
    # and a planner receives exactly one of them, so the spread is what says how
    # much a single number can be relied on.
    #
    # ACRE-WEIGHTED quantiles, matching the headline's weighting. Unweighted ones
    # were tried first and produced a figure that reads as an error: the national
    # tile came out at a 42% headline against a 50-79% range, because that
    # predictor fails hardest on the big-burn cells the acre weighting is
    # dominated by and does adequately on the many small ones. Both numbers were
    # right and the pair was unreadable. One denominator throughout is the same
    # discipline the spoken script applies to every share it quotes.
    for key, pred in (("history", hist), ("national", national), ("naive", naive)):
        acc = 1 - per_cell(pred)
        for q in (25, 50, 75):
            out.loc[key, f"p{q}"] = _weighted_quantile(acc, w, q / 100)

    out.attrs["n_cells"] = int(len(d))
    out.attrs["test_start"] = int(cfg.test_start)
    return out


def plot_tier1_tiles(panel, out_path: Path, *, k: int = 7, cfg=None,
                     figsize: tuple[float, float] = (11.0, 3.6)) -> dict:
    """Beat 3 — three tiles: does a region's own history forecast its cause mix?

    Not a chart. Three numbers compared once, with no time axis -- the form is a
    stat tile, and forcing it into a bar chart adds an axis the reader does not
    need.

    **Each tile carries the middle half of its own per-cell distribution**
    (p25-p75 of `1 - TVD`), added W7. The headline is an acre-weighted mean over
    thousands of held-out region-seasons and a planner receives exactly one of
    them, so a bare mean overstates what a single forecast is worth. The span is
    variation across region-seasons, **not** a confidence interval on the mean --
    the drawn label says "typical range" to keep that distinction in the figure
    rather than only in the notes.

    **The value shown is `1 - TVD`, not TVD.** TVD is a distance, so lower is
    better, and a tile whose biggest number is the worst result reads backwards
    in the two seconds a slide gets. The inverse is not a cosmetic flip: on a
    simplex `1 - TVD` equals the overlap between the predicted and actual
    composition, so "share of the composition placed on the right cause" is
    literal. The TVD is printed underneath in muted ink so the figure still ties
    to the notebooks.

    Each tile carries a short bar on a shared 0-100% track -- one measure, one
    scale, so the bars are comparable and the winner is visible without reading
    the digits. The winning tile takes the project's ember accent; the others sit
    in a recessive neutral, because the point is which one wins, not three
    parallel results.
    """
    scores = tier1_baseline_scores(panel, k=k, cfg=cfg)
    _draw_score_tiles(scores["label"], scores["correct"], out_path,
                      figsize=figsize,
                      ranges=scores[["p25", "p75"]].to_numpy())

    return {
        "n_cells": scores.attrs["n_cells"],
        "test_start": scores.attrs["test_start"],
        "k": k,
        **{f"{key}_correct": float(r["correct"]) for key, r in scores.iterrows()},
        **{f"{key}_tvd": float(r["tvd"]) for key, r in scores.iterrows()},
        **{f"{key}_p{q}": float(r[f"p{q}"])
           for key, r in scores.iterrows() for q in (25, 50, 75)},
        "best": str(scores["correct"].idxmax()),
        "out_path": str(out_path),
    }


def tier1_k_sweep(panel, *, ks=range(1, 9), cfg=None) -> pd.DataFrame:
    """Acre-weighted TVD across trailing-window lengths, reproducing notebook 06.

    Calls `trailing.TrailingMean` rather than reimplementing the window, so this
    figure and `06_analysis.ipynb` cannot drift apart.
    """
    from trailing import TrailingMean

    cfg = cfg or _cfg()
    classes = ["human", "natural", "unknown"]
    t = panel.tier1_composition()
    actual = t[classes].to_numpy()
    in_test = (t["season_year"] >= cfg.test_start).to_numpy()
    w = t["total_ac"].to_numpy()

    rows = []
    for k in ks:
        pred = TrailingMean(k).predict(t, classes).to_numpy()
        tvd = 0.5 * np.abs(pred - actual).sum(axis=1)
        m = in_test & ~np.isnan(tvd)
        rows.append({"k": k, "n": int(m.sum()),
                     "tvd": float(np.average(tvd[m], weights=w[m])),
                     "tvd_unweighted": float(tvd[m].mean())})
    out = pd.DataFrame(rows).set_index("k")
    out["correct"] = 1 - out["tvd"]
    return out


def plot_k_sweep(panel, out_path: Path, *, ks=range(1, 9), cfg=None,
                 tol: float = 0.015,
                 figsize: tuple[float, float] = (10.0, 5.2)) -> dict:
    """Beat 4 — how many past seasons a forecast should average.

    One curve: acre-weighted TVD -- the error in the predicted cause mix --
    against the number of prior same-season occurrences averaged. Falling is
    better, and the values are exactly the ones `06_analysis.ipynb` reports, so
    nothing on the axis is a derived quantity needing its own explanation.

    (The beat-3 tiles invert the same measure to `1 - TVD`, because a stat tile
    whose largest number is its worst result reads backwards. A curve has no
    such problem: a falling line reads as improvement on its own.)

    **The gain is front-loaded and then flattens.** Going from one prior season
    to three buys most of what is available; k=7 is the acre-weighted optimum but
    sits only ~0.012 above k=3. The honest reading is not "more history is always
    better" but "one year is not enough, and beyond about three the curve is
    nearly flat" -- which is why the k=7 choice is cheap rather than critical.

    **The acre-weighted curve is not monotonic**, and the figure does not pretend
    otherwise: it ticks up at k=4 (+0.0019 TVD) and again at k=8 (+0.0014). Only
    the unweighted sweep falls monotonically. Drawing a smoothed or forced-
    monotone line would be asserting a cleaner result than the data gives.

    Nothing else is drawn -- no marked winner, no shaded plateau, no annotation.
    An earlier draft shaded k>=3 and labeled it, which restated the slide's own
    headline inside the figure; the flattening is legible in the curve's shape
    without help. `plateau_from` is still returned for the caption.
    """
    import matplotlib.pyplot as plt

    sweep = tier1_k_sweep(panel, ks=ks, cfg=cfg)
    best_k = int(sweep["correct"].idxmax())
    # First window whose score is within `tol` of the best, and which every
    # longer window also stays within -- i.e. where the curve has flattened
    # rather than merely touched the band once.
    within = (sweep["correct"].max() - sweep["correct"]) <= tol
    plateau_from = int(next(k for k in sweep.index if within.loc[k:].all()))

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    x = list(sweep.index)
    y = sweep["tvd"].to_numpy()
    ax.plot(x, y, color=POINT_ORANGE, lw=2.6, marker="o", ms=7,
            mfc=SURFACE, mew=2.0, zorder=3)

    ax.set_xticks(x)
    ax.set_xlabel("prior seasons averaged", fontsize=11, color=TEXT_SECONDARY)
    ax.set_ylabel("error in the predicted cause mix", fontsize=11,
                  color=TEXT_SECONDARY)
    span = float(y.max() - y.min())
    ax.set_ylim(y.min() - span * 0.25, y.max() + span * 0.20)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_MUTED)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=10)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    return {
        "best_k": best_k,
        "best_correct": float(sweep.loc[best_k, "correct"]),
        "best_tvd": float(sweep.loc[best_k, "tvd"]),
        "k1_correct": float(sweep["correct"].iloc[0]),
        "gain_k1_to_best": float(sweep.loc[best_k, "correct"] - sweep["correct"].iloc[0]),
        "gain_k3_to_best": float(sweep.loc[best_k, "correct"] - sweep.loc[3, "correct"]),
        "plateau_from": plateau_from,
        "plateau_spread": float(sweep.loc[plateau_from:, "correct"].max()
                                - sweep.loc[plateau_from:, "correct"].min()),
        "monotonic_acre_wtd": bool((sweep["tvd"].diff().dropna() <= 0).all()),
        "n_cells": int(sweep["n"].iloc[0]),
        "out_path": str(out_path),
    }


def human_subcause_scores(panel, *, k: int | None = None, cfg=None) -> pd.DataFrame:
    """Top-1 hit rate for three predictors of a region-season's human sub-cause mix.

    The Tier-1 question one level down: given that a region-season's human acres
    are what they are, which of the **11** human sub-causes leads them?

    * **history** -- the cell's own k-season trailing mean, forward-chaining
    * **national** -- the training-years acre-weighted mix, applied everywhere
    * **chance** -- 1/11, an even split across the sub-causes

    Reported as top-1 rather than `1 - TVD`. On an 11-way simplex most of the
    mass sits in a few classes, so overlap scores stay high for reasons that have
    nothing to do with naming the right leader -- and "which cause do I target"
    is a top-1 question. Weights are `human_total_ac`, matching
    `08_human_cause.ipynb`.
    """
    from trailing import TrailingMean

    cfg = cfg or _cfg()
    k = cfg.shares_k if k is None else k
    hc, cols = panel.human_subcause_shares()
    act = hc[cols].to_numpy()
    w = hc["human_total_ac"].to_numpy()
    test = (hc["season_year"] >= cfg.test_start).to_numpy()
    train = (hc["season_year"] < cfg.test_start).to_numpy()

    pred = TrailingMean(k).predict(hc, cols).to_numpy()
    m = test & ~np.isnan(pred).any(axis=1)

    prior = np.average(act[train], weights=w[train], axis=0)
    prior = prior / prior.sum()

    def hit(P):
        return float(np.average(P[m].argmax(axis=1) == act[m].argmax(axis=1),
                                weights=w[m]))

    def tvd(P):
        return float(np.average(0.5 * np.abs(P - act).sum(axis=1)[m], weights=w[m]))

    national = np.tile(prior, (len(hc), 1))
    rows = [
        ("the region's own seasonal history", "history", hit(pred), tvd(pred)),
        ("the national human mix", "national", hit(national), tvd(national)),
        ("an even split across 11 causes", "chance", 1 / len(cols), np.nan),
    ]
    out = pd.DataFrame(rows, columns=["label", "key", "top1", "tvd"]).set_index("key")

    # Split the history rung by the cell's own PRE-SEASON dispersion -- the
    # confidence signal from 06_analysis.ipynb. Beat 3 shows its range as a
    # p25-p75 span, which this metric cannot carry: top-1 is a 0/1 outcome per
    # cell, so its quartiles are 0 and 1 and an interval would say nothing. The
    # honest equivalent is to report the hit rate at each end of the signal that
    # predicts it. Dispersion reuses the SAME window, shift and grouping as the
    # prediction, so it stays strictly pre-season information.
    disp_all = TrailingMean(k, how="std", min_periods=2).predict(hc, cols).to_numpy()
    # All-NaN rows are cells with fewer than two prior same-season observations;
    # nanmean warns on them and yields NaN, which is the wanted behaviour (they
    # are masked out below), so the warning is suppressed rather than the rows
    # imputed -- a zero here would read as "perfectly steady" on no evidence.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        dispersion = np.nanmean(disp_all, axis=1)
    ok = m & ~np.isnan(dispersion)
    hits = (pred[ok].argmax(axis=1) == act[ok].argmax(axis=1))
    d, wd = dispersion[ok], w[ok]
    lo, hi = np.percentile(d, [25, 75])
    out.attrs["steadiest_top1"] = float(np.average(hits[d <= lo], weights=wd[d <= lo]))
    out.attrs["volatile_top1"] = float(np.average(hits[d >= hi], weights=wd[d >= hi]))
    out.attrs["split_n"] = int(ok.sum())
    out.attrs["n_cells"] = int(m.sum())
    out.attrs["n_classes"] = len(cols)
    out.attrs["test_start"] = int(cfg.test_start)
    out.attrs["k"] = k
    out.attrs["leading_cause"] = cols[int(prior.argmax())].replace("sh_", "")
    return out


def plot_human_tiles(panel, out_path: Path, *, k: int | None = None, cfg=None,
                     figsize: tuple[float, float] = (11.0, 3.6)) -> dict:
    """Beat 5 — can history name the leading human sub-cause?

    Deliberately the same three-tile form as `plot_tier1_tiles`, drawn by the
    same `_draw_score_tiles`. The two beats ask one question at two levels of the
    hierarchy, so a reader who learned the encoding two slides ago should not
    have to learn a second one. The rhyme *is* the argument: same method, harder
    problem, still works.

    **Top-1, not `1 - TVD`, and the swap is deliberate.** Across 11 sub-causes
    the mass concentrates in a few classes, so an overlap score stays
    comfortable without the model ever naming the right leader -- the national
    mix scores 0.643 TVD while getting the leader right only 16% of the time.
    A planner asking "which cause do I target" is asking a top-1 question, so
    that is what the tiles report.

    The chance tile is 1/11 by construction rather than measured; it is the
    reference that makes 54% legible as a result rather than a bare number.
    """
    scores = human_subcause_scores(panel, k=k, cfg=cfg)
    steady = scores.attrs["steadiest_top1"]
    volatile = scores.attrs["volatile_top1"]
    notes = [f"{steady:.0%} steadiest · {volatile:.0%} most volatile"
             if key == "history" else "" for key in scores.index]
    _draw_score_tiles(scores["label"], scores["top1"], out_path, figsize=figsize,
                      notes=notes)
    return {
        "steadiest_top1": steady,
        "volatile_top1": volatile,
        "split_n": scores.attrs["split_n"],
        "n_cells": scores.attrs["n_cells"],
        "n_classes": scores.attrs["n_classes"],
        "k": scores.attrs["k"],
        "leading_cause": scores.attrs["leading_cause"],
        **{f"{key}_top1": float(r["top1"]) for key, r in scores.iterrows()},
        "history_tvd": float(scores.loc["history", "tvd"]),
        "national_tvd": float(scores.loc["national", "tvd"]),
        "best": str(scores["top1"].idxmax()),
        "out_path": str(out_path),
    }


def plot_ablation_ladder(labels, values, out_path: Path, *,
                         floor_index: int = 0,
                         value_fmt: str = "{:.0%}",
                         xlabel: str = "",
                         sort: bool = False,
                         figsize: tuple[float, float] = (10.0, 4.2)) -> dict:
    """A rung ladder: the baseline, then what each added model achieved.

    Horizontal bars with the labels given room to be sentences rather than
    abbreviations.

    **Ordering.** `sort=True` puts the bars in descending value, which is the
    right default for an audience: a bar chart whose lengths do not decrease
    reads as unordered, and the eye spends its first moment working out whether
    the sequence means anything. Ladder order (the rungs as they were *tried*)
    is chronology, and chronology is a fact about the project rather than about
    the result. Kept as the default only so existing callers do not shift under
    them; new callers should pass `sort=True`.

    **The floor is drawn as a rule across the whole plot, not just as a bar.**
    That is the encoding decision that makes the figure legible in two seconds:
    the rule is the line to beat, and every bar that stops short of it has
    visibly failed. Bars are colored by whether they clear it -- ember for the
    winner, recessive neutral for the rest -- so no legend is needed. Sorting
    does not weaken this: the floor keeps its rule wherever it lands, and when
    the floor wins it lands on top, which is itself the finding.

    Values are "higher is better" by contract; pass an inverted metric already
    flipped. `floor_index` marks which entry is the baseline **in the order
    passed in**, and is resolved before any sorting.
    """
    import matplotlib.pyplot as plt

    labels = list(labels)
    values = [float(v) for v in values]
    floor = values[floor_index]
    if sort:
        order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
        labels = [labels[i] for i in order]
        values = [values[i] for i in order]
    y = np.arange(len(values))[::-1]        # first label at the top

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    for yi, label, v in zip(y, labels, values):
        beats = v >= floor
        ax.barh(yi, v, height=0.52,
                color=POINT_ORANGE if beats else "#b9b6b0", edgecolor="none",
                zorder=2)
        # The floor bar's own label would sit on top of the floor rule, so it
        # goes inside the bar; the shorter bars keep their labels outside.
        inside = abs(v - floor) < 1e-9
        ax.annotate(value_fmt.format(v), xy=(v, yi),
                    xytext=(-10 if inside else 8, 0),
                    textcoords="offset points",
                    ha="right" if inside else "left", va="center",
                    fontsize=13,
                    color=SURFACE if inside else TEXT_SECONDARY,
                    fontweight="bold")

    # The line to beat, drawn the full height so a short bar reads as a failure.
    ax.axvline(floor, color=POINT_ORANGE, lw=1.4, ls=(0, (4, 3)), alpha=0.75,
               zorder=3)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=12, color=TEXT_SECONDARY)
    ax.set_xlim(0, max(values) * 1.22)
    ax.set_xticks([])
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10.5, color=TEXT_SECONDARY, loc="left")
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(TEXT_MUTED)
    ax.tick_params(axis="y", length=0)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    # Labels come back in drawn order so a caller printing `beats_floor`
    # alongside them cannot pair a verdict with the wrong rung after sorting.
    return {"floor": floor,
            "labels": labels,
            "values": values,
            "beats_floor": [bool(v >= floor) for v in values],
            "out_path": str(out_path)}


def human_rung_scores(panel, *, k: int | None = None, cfg=None,
                      include_ridge: bool = True) -> pd.DataFrame:
    """The Human branch's rungs, scored on one held-out set.

    Reproduces `08_human_cause.ipynb`'s ladder by calling the same
    `models.SimplexRegressor` and `trailing.TrailingMean`, so the figure cannot
    drift from the notebook that reported it.

    * **floor** -- the cell's own k-season trailing human mix
    * **coarse** -- gradient boosting on the region-season fingerprint features
      (`f_*`) plus season, with no view of the cell's human past
    * **history-aware** -- the same model, additionally handed the 11 trailing
      human-mix columns as features: the very quantity the floor averages
    * **ridge_history** -- a *different model family* on that same history-aware
      feature set (W7; `include_ridge`)

    **Why the ridge rung is here.** With only the three gradient-boosting rungs,
    the figure invites "you picked a learner that overfits" -- and every bar on
    it being the same family made "a learned model made it worse" read as a
    claim about learned models generally. Ridge answers it *on the figure*: it
    beats the booster (the booster was paying a variance cost on a small wide
    panel -- ~5,300 training cells, 23 features, 11 correlated targets) and
    still stops short of the floor. Two families converging just below a
    trailing mean is the evidence for an information ceiling.

    The **coarse** ridge rung is deliberately not returned: it scores 0.3567
    against gradient boosting's 0.3566, and two bars of identical length
    reading "36%" twice is noise. The five-rung table lives in
    `08_human_cause.ipynb`, which is the complete record.

    Fits 22 gradient-boosted regressors (plus 11 near-instant ridges), so it
    takes a couple of minutes.
    """
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    from models import SimplexRegressor
    from trailing import TrailingMean

    cfg = cfg or _cfg()
    k = cfg.shares_k if k is None else k
    hc, cols = panel.human_subcause_shares()
    feat = pd.read_parquet(cfg.data / "region_season_features.parquet")
    fcols = [c for c in feat.columns if c.startswith("f_")]
    key = ["region", "season", "season_year"]

    floor = TrailingMean(k).predict(hc, cols)
    hc = hc.assign(**{f"floor_{c}": floor[c].to_numpy() for c in cols})
    d = hc.merge(feat[key + fcols], on=key, how="left")
    d = d.join(pd.get_dummies(d["season"], prefix="s"))
    scols = [c for c in d.columns if c.startswith("s_")]

    act = d[cols].to_numpy()
    w = d["human_total_ac"].to_numpy()
    F = d[[f"floor_{c}" for c in cols]].to_numpy()
    ok = ~np.isnan(F).any(axis=1) & d[fcols].notna().all(axis=1).to_numpy()
    tr = (d["season_year"] < cfg.test_start).to_numpy() & ok
    te = (d["season_year"] >= cfg.test_start).to_numpy() & ok

    def score(P):
        t = 0.5 * np.abs(P - act).sum(axis=1)
        return (float(np.average(t[te], weights=w[te])),
                float(np.average(P[te].argmax(axis=1) == act[te].argmax(axis=1),
                                 weights=w[te])))

    base = d[fcols + scols].to_numpy().astype(float)
    X_hist = np.column_stack([base, F])

    # "seasonal" is load-bearing, not decoration: the grouping is (region, season),
    # so a cell sees only its own prior same-season occurrences. The tiles figure
    # says "seasonal history" too -- one baseline must not carry two names across
    # two consecutive slides.
    rows = [("the region's own seasonal history", "floor") + score(F)]
    for label, key_, X in (
        ("gradient boosting on region character", "coarse", base),
        ("gradient boosting, given that history", "history_aware", X_hist),
    ):
        # Acre weights in the fit, matching `08_human_cause.ipynb`. Without them
        # the learned rungs score differently -- the model spends its capacity on
        # cells that carry almost no acres.
        model = SimplexRegressor().fit(X[tr], act[tr], sample_weight=w[tr])
        rows.append((label, key_) + score(model.predict(X)))

    if include_ridge:
        # Same clip-and-renormalize projection SimplexRegressor applies, so the
        # only thing differing from the rung above is the learner. Scaled first:
        # the fingerprints put acres beside shares, and ridge penalizes raw
        # coefficients, so unscaled the penalty would land almost entirely on
        # whichever feature happens to be small-valued.
        #
        # Predicted on the test rows only, then scattered back. The gradient-boosting
        # rungs above predict the whole frame because HistGradientBoosting accepts NaN
        # natively; ridge does not, and rows outside `ok` carry NaN fingerprints. Only
        # `te` rows are ever scored, so restricting the predict is a fix rather than a
        # compromise -- but it means this block cannot be collapsed into the loop above.
        P = np.full_like(act, np.nan, dtype=float)
        P[te] = np.column_stack([
            make_pipeline(StandardScaler(), Ridge(alpha=1.0))
            .fit(X_hist[tr], act[tr, j], ridge__sample_weight=w[tr])
            .predict(X_hist[te])
            for j in range(act.shape[1])
        ])
        P[te] = np.clip(P[te], 0, None)         # ridge is unbounded; negatives are not shares
        P[te] /= P[te].sum(axis=1, keepdims=True)
        rows.append(("ridge, given that history", "ridge_history") + score(P))

    out = pd.DataFrame(rows, columns=["label", "key", "tvd", "top1"]).set_index("key")
    out.attrs["n_test"] = int(te.sum())
    out.attrs["n_train"] = int(tr.sum())
    out.attrs["k"] = k
    return out


def unknown_triage(panel, *, k: int | None = None, cfg=None, top: int = 8):
    """Where better cause reporting would recover the most acres.

    Two quantities per region-season, both needed: a high *missing fraction* on
    ground that barely burns is a records curiosity, and a low fraction on huge
    acreage still hides a lot. Ranking by predicted unattributed **acres** --
    the fraction times the burn -- is what makes the list operational.

    The fraction is predicted by the same k-season trailing mean used
    everywhere else, forward-chaining, so the ranking is a forecast rather than
    a retrospective tally. Returns `(table, scores)`: the top region-seasons,
    and the branch's persistence-vs-global-mean MAE.
    """
    from trailing import TrailingMean

    cfg = cfg or _cfg()
    k = cfg.shares_k if k is None else k
    aq = panel.attribution_quality().sort_values(["region", "season", "season_year"])

    pred = TrailingMean(k).predict(aq, ["missing_acre_frac"])["missing_acre_frac"].to_numpy()
    act = aq["missing_acre_frac"].to_numpy()
    w = aq["total_ac"].to_numpy()
    train = (aq["season_year"] < cfg.test_start).to_numpy()
    te = ((aq["season_year"] >= cfg.test_start).to_numpy()
          & ~np.isnan(pred) & ~np.isnan(act))

    global_mean = float(np.nanmean(act[train]))
    scores = {
        "n_cells": int(te.sum()),
        "persistence_mae": float(np.average(np.abs(act[te] - pred[te]), weights=w[te])),
        "global_mean_mae": float(np.average(np.abs(act[te] - global_mean), weights=w[te])),
        "persistence_mae_unwtd": float(np.abs(act[te] - pred[te]).mean()),
        "global_mean_mae_unwtd": float(np.abs(act[te] - global_mean).mean()),
    }

    o = aq[te].copy()
    o["pred_missing_ac"] = pred[te] * o["total_ac"]
    table = (o.groupby(["region", "season"])
             .agg(missing_frac=("missing_acre_frac", "mean"),
                  total_ac=("total_ac", "sum"),
                  pred_missing_ac=("pred_missing_ac", "sum"))
             .sort_values("pred_missing_ac", ascending=False)
             .head(top).reset_index())
    return table, scores


def plot_unknown_triage(panel, out_path: Path, *, k: int | None = None,
                        cfg=None, top: int = 8,
                        figsize: tuple[float, float] = (10.5, 5.4)) -> dict:
    """Beat 18 — the ranked list of where cause reporting is worth fixing.

    Horizontal bars, longest first: predicted unattributed acres per
    region-season on the held-out years. Horizontal because the labels are
    place names that will not abbreviate, and ranked because the slide's job is
    to name a first target rather than to characterise a distribution.

    **Ranked by acres, not by missing fraction, and that is the whole design.**
    The regions with the worst attribution rates are mostly small: Central Great
    Plains misses 66% of its cause attributions but burns a fifth of what the
    Southwestern Tablelands does. Multiplying the predicted fraction by the burn
    turns a data-quality complaint into a budget: fix reporting *here* and this
    many acres stop being invisible.

    The missing fraction is annotated on each bar rather than given its own
    axis, because it is context for the ranking, not the ranking itself.
    """
    import matplotlib.pyplot as plt

    table, scores = unknown_triage(panel, k=k, cfg=cfg, top=top)
    y = np.arange(len(table))[::-1]

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    vals = table["pred_missing_ac"].to_numpy() / 1000.0
    for yi, (_, row), v in zip(y, table.iterrows(), vals):
        lead = yi == y[0]
        ax.barh(yi, v, height=0.62,
                color=POINT_ORANGE if lead else "#c9b9ad", edgecolor="none",
                zorder=2)
        ax.annotate(f"{v:,.0f}k acres", xy=(v, yi), xytext=(8, 0),
                    textcoords="offset points", ha="left", va="center",
                    fontsize=11.5, color=TEXT_PRIMARY if lead else TEXT_SECONDARY,
                    fontweight="bold")
        # The rate, inside the bar: context for the ranking, not the ranking.
        ax.annotate(f"{row['missing_frac']:.0%} of its acres unattributed",
                    xy=(0, yi), xytext=(10, 0), textcoords="offset points",
                    ha="left", va="center", fontsize=9.5, color=SURFACE)

    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.region}  {r.season}" for r in table.itertuples()],
                       fontsize=11, color=TEXT_SECONDARY)
    ax.set_xlim(0, float(vals.max()) * 1.26)
    ax.set_xticks([])
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(TEXT_MUTED)
    ax.tick_params(axis="y", length=0)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    return {**scores,
            "top_region": f"{table.iloc[0]['region']} {table.iloc[0]['season']}",
            "top_acres": float(table.iloc[0]["pred_missing_ac"]),
            "out_path": str(out_path)}


def shuffled_control(panel, *, branch: str = "human", bins: int = 20,
                     seed: int = 0, cfg=None) -> dict:
    """Binned calibration for the real ranking and for a shuffled copy of it.

    The control permutes the persistence predictions across hexes. The value
    *distribution* is untouched -- same numbers, same spread, same everything a
    summary statistic sees -- and only the pairing with the ground is destroyed.
    Anything the real ranking scores above this is spatial information rather
    than a property of the numbers.

    Cells are grouped into `bins` equal-count strata by predicted value, and each
    stratum reports its mean prediction and its mean outcome. Binning is not
    cosmetic here: 84% of human hex-seasons and 96% of natural ones record zero
    starts, so a raw scatter is a solid blob on the origin and shows nothing.
    """
    from scipy.stats import spearmanr

    import hex_panel as hp

    cfg = cfg or _cfg()
    train, test = hp.split(panel, cfg=cfg)
    rng = np.random.default_rng(seed)

    y_all = panel[f"starts_{branch}"].to_numpy(float)
    pred_all = panel[f"pers_{branch}"].to_numpy()
    ok = test & np.isfinite(pred_all)
    y, pred = y_all[ok], pred_all[ok]
    shuffled = rng.permutation(pred)

    out = {"branch": branch, "n_test": int(ok.sum()), "bins": bins,
           "zero_share": float((y == 0).mean())}
    for label, p in (("real", pred), ("shuffled", shuffled)):
        strata = pd.qcut(pd.Series(p).rank(method="first"), bins, labels=False)
        frame = (pd.DataFrame({"stratum": strata, "y": y, "p": p})
                 .groupby("stratum")
                 .agg(pred=("p", "mean"), actual=("y", "mean"), n=("y", "size")))
        out[label] = frame
        out[f"{label}_rho"] = float(spearmanr(y, p).statistic)
        out[f"{label}_mae"] = float(np.mean(np.abs(y - p)))
    return out


def plot_shuffled_control(panel, out_path: Path, *, branch: str = "human",
                          bins: int = 20, seed: int = 0, cfg=None,
                          figsize: tuple[float, float] = (9.4, 5.8)) -> dict:
    """Beat 8 — the ranking against a shuffled copy of itself, in one panel.

    Each point is a stratum of hex-seasons: mean predicted starts on x, mean
    observed starts on y. The diagonal is perfect calibration.

    **The real ranking climbs the diagonal; the same predictions permuted across
    hexes go flat.** An identical set of numbers, re-paired with the wrong
    ground, and the stratum predicted to start almost five fires observes the
    same as the stratum predicted to start none.

    **One panel, not two.** Side by side, a reader has to hold the left shape in
    memory to judge the right one, and the flat line only reads as flat *against*
    the climb. Superimposed, the divergence is the mark itself -- the two series
    share an origin and separate, which is the finding drawn rather than
    asserted.

    Binned rather than raw because 84% of human hex-seasons record zero starts:
    1.59M points would be a solid blob on the origin.

    **"Shuffled" rather than "random", deliberately.** The control does not
    invent new numbers; it keeps every predicted value and only changes which
    hex each one lands on. The region's total forecast is untouched -- what is
    destroyed is the *siting* of it. That is what makes this the stronger
    control: a random predictor changes two things at once (the values and the
    pairing), so its failure is ambiguous, while this one isolates placement.
    `12_hex_ignition_baselines.ipynb` runs the random-noise control separately
    and the two land in the same place (rho -0.001 vs +0.0006), which is itself
    the finding: once the pairing is broken the predictions carry no more
    information than noise.

    The label also does useful work on a skeptic. "Random" invites "of course
    noise does not predict fires"; "shuffled" invites "those are the real
    numbers in the wrong places" -- which is the realisation the figure exists
    to produce.
    """
    import matplotlib.pyplot as plt

    res = shuffled_control(panel, branch=branch, bins=bins, seed=seed, cfg=cfg)
    real, shuf = res["real"], res["shuffled"]
    lim = max(real["pred"].max(), real["actual"].max(),
              shuf["actual"].max()) * 1.14

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.plot([0, lim], [0, lim], color=TEXT_MUTED, lw=0.9, ls=(0, (4, 3)),
            zorder=1)
    # The diagonal's *screen* angle is not 45 degrees unless the axes happen to
    # be square, and it changes with figsize, so it is measured off the display
    # transform rather than hardcoded. Needs a draw first so the transform is
    # populated.
    fig.canvas.draw()
    (px0, py0), (px1, py1) = ax.transData.transform([(0, 0), (lim, lim)])
    diag_deg = float(np.degrees(np.arctan2(py1 - py0, px1 - px0)))
    ax.annotate("perfect calibration", xy=(lim * 0.80, lim * 0.80),
                xytext=(0, 8), textcoords="offset points", ha="right",
                va="bottom", fontsize=9.5, color=TEXT_MUTED,
                rotation=diag_deg, rotation_mode="anchor")

    for frame, color, text, dx, dy, ha, va in (
        (shuf, "#b9b6b0", "shuffled", -14, 26, "right", "bottom"),
        # Directly above its own last point, centered. Trailing the line to the
        # right pushed the label past the final x tick and out of the plot
        # frame; sitting it on the line's left flank put text on the path. The
        # gap between the curve (3.7) and the diagonal (5.4) at this x leaves
        # room to go straight up.
        (real, POINT_ORANGE, "forecast", 0, 16, "center", "bottom"),
    ):
        ax.plot(frame["pred"], frame["actual"], color=color, lw=2.4,
                marker="o", ms=6, mfc=SURFACE, mew=1.6, zorder=3)
        x_end = float(frame["pred"].iloc[-1])
        y_end = float(frame["actual"].iloc[-1])
        ax.annotate(text, xy=(x_end, y_end), xytext=(dx, dy),
                    textcoords="offset points", ha=ha, va=va,
                    fontsize=12.5, fontweight="bold", color=color,
                    linespacing=1.35, annotation_clip=False)

    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("predicted starts", fontsize=11, color=TEXT_SECONDARY)
    ax.set_ylabel("observed starts", fontsize=11, color=TEXT_SECONDARY)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_MUTED)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=10)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    return {k: v for k, v in res.items() if k not in ("real", "shuffled")} | {
        "out_path": str(out_path)}


def season_predictability(panel, *, cfg=None, seed: int = 0,
                          by_year: bool = True) -> pd.DataFrame:
    """Held-out rank correlation per season, both branches, scored per year.

    **Scored one held-out year at a time (11 of them) rather than pooled.** A
    single pooled number cannot say whether a difference is stable or whether
    one good year is carrying the average, and nothing else in this deck shows
    a distribution. Eleven independent scores per season-branch give the
    spread for free -- no resampling, no assumed error model.

    Also scores a shuffled control per stratum, so the figure can state that the
    seasonal floors are not seasonal artifacts.
    """
    import hex_panel as hp

    cfg = cfg or _cfg()
    _, test = hp.split(panel, cfg=cfg)
    rng = np.random.default_rng(seed)
    seasons = {0: "DJF", 1: "MAM", 2: "JJA", 3: "SON"}
    years = sorted(panel.loc[test, "season_year"].unique()) if by_year else [None]

    rows = []
    for branch in ("human", "natural"):
        y = panel[f"starts_{branch}"].to_numpy(float)
        pred = panel[f"pers_{branch}"].to_numpy()
        for ord_, name in seasons.items():
            base = (test & np.isfinite(pred)
                    & (panel["season_ord"] == ord_).to_numpy())
            for yr in years:
                m = base if yr is None else (
                    base & (panel["season_year"] == yr).to_numpy())
                if m.sum() < 1000:
                    continue
                rows.append({
                    "branch": branch, "season": name,
                    "year": None if yr is None else int(yr),
                    "n_test": int(m.sum()),
                    "rho": hp.rank_score(y[m], pred[m]),
                    "shuffled": hp.rank_score(y[m], rng.permutation(pred[m])),
                })
    return pd.DataFrame(rows)


def plot_season_predictability(panel, out_path: Path, *, cfg=None, seed: int = 0,
                               figsize: tuple[float, float] = (9.8, 5.6)) -> dict:
    """Beat 9 — human ignition is predictable in every season; natural is not.

    Each branch scored separately in each of the **11 held-out years**, so every
    season carries eleven independent points rather than one pooled number. The
    band spans each season's min-to-max across those years; the line joins the
    medians.

    **This is the first figure in the deck that shows a distribution.** Every
    other beat reports a point estimate, which cannot answer "is that difference
    real or is one good year carrying it?" Here the answer is visible and does
    not depend on an assumed error model: **human beats natural in all 44
    season-years, without exception.** The nearest approach is JJA, where
    human's worst year (0.449) still edges natural's best (0.456) apart in every
    individual year.

    **The reading.** Human runs high and flat -- where people are does not change
    with the season, so a hex's own ignition history describes it all year.
    Natural is a summer surface: +0.41 in JJA, +0.10 in winter, because outside
    summer there is barely a lightning signal to persist.

    The shuffled controls are computed but not drawn; they sit between -0.003 and
    +0.001 in every stratum and would render as a third flat line on zero,
    repeating beat 8.
    """
    import matplotlib.pyplot as plt

    scores = season_predictability(panel, cfg=cfg, seed=seed, by_year=True)
    order = ["DJF", "MAM", "JJA", "SON"]
    x = np.arange(len(order))

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    summary = {}
    for branch, color, label in (("human", PERIM_FILL, "human"),
                                  ("natural", POINT_ORANGE, "natural")):
        sub = scores[scores["branch"] == branch]
        g = sub.groupby("season")["rho"]
        med = g.median().reindex(order).to_numpy()
        lo = g.min().reindex(order).to_numpy()
        hi = g.max().reindex(order).to_numpy()
        summary[branch] = {"median": med, "min": lo, "max": hi}

        # The band is the observed range across held-out years, not a modeled
        # interval -- no distributional assumption is being made.
        ax.fill_between(x, lo, hi, color=color, alpha=0.16, linewidth=0,
                        zorder=2)
        ax.plot(x, med, color=color, lw=2.8, marker="o", ms=8, mfc=SURFACE,
                mew=2.0, zorder=3)
        ax.annotate(label, xy=(x[-1], med[-1]), xytext=(14, 0),
                    textcoords="offset points", ha="left", va="center",
                    fontsize=13, fontweight="bold", color=color)

    ax.set_xticks(x)
    # Plain season names on the axis: DJF/MAM/JJA/SON is meteorological
    # shorthand a planner audience should not have to decode mid-slide. The
    # triads stay in the returned frame, which is what the notebook tabulates.
    ax.set_xticklabels([SEASON_NAMES[s] for s in order], fontsize=12,
                       color=TEXT_SECONDARY)
    ax.set_xlim(-0.35, len(order) - 0.30)
    ax.set_ylim(0, float(scores["rho"].max()) * 1.16)
    ax.set_ylabel("how well next season's starts can be ranked",
                  fontsize=11, color=TEXT_SECONDARY)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_MUTED)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=10)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    wide = scores.pivot_table(index=["season", "year"], columns="branch",
                              values="rho")
    return {
        "n_years": int(scores["year"].nunique()),
        "n_season_years": int(len(wide)),
        "natural_beats_human": int((wide["natural"] >= wide["human"]).sum()),
        "human_range": (float(summary["human"]["min"].min()),
                        float(summary["human"]["max"].max())),
        "natural_range": (float(summary["natural"]["min"].min()),
                          float(summary["natural"]["max"].max())),
        "shuffled_range": (float(scores["shuffled"].min()),
                           float(scores["shuffled"].max())),
        "out_path": str(out_path),
    }


def plot_data_sources(out_path: Path, *,
                      figsize: tuple[float, float] = (11.6, 6.2)) -> dict:
    """The closing reference slide — one record, four layers joined onto it.

    **Structure carries the argument, so the layout is a stack rather than a
    list.** The talk's whole method is that FPA-FOD is the spine and everything
    else is joined onto it; a flat bibliography would present five equal
    datasets and lose that. The base record sits in its own emphasized band,
    the four joined layers below it, each labelled with what it contributed and
    at which grain.

    **Attribution, not provenance-in-full.** Every row carries author, year and
    a resolvable identifier (DOI where one exists, else the canonical URL),
    which is what an audience needs to find the data. Access dates, file names
    and API endpoints belong in the repository, not on a slide read from ten
    feet away.

    Deliberately no figure numbers, no citation keys and no bracketed
    superscripts: nothing else in this deck cross-references a bibliography, so
    numbering would imply a machinery that does not exist.
    """
    import matplotlib.pyplot as plt

    base = ("FPA-FOD, 6th edition",
            "Short (2022) · Forest Service Research Data Archive",
            "doi.org/10.2737/RDS-2013-0009.6",
            "2.27M fires, 1992–2020 — the spine:\ndate, location, size, cause")

    layers = [
        ("EPA Level III ecoregions",
         "U.S. EPA (2025) · Omernik & Griffith (2014)",
         "epa.gov/eco-research/ecoregions",
         "the regional unit — 105 regions, drawn\nfrom terrain, vegetation and climate"),
        ("MTBS burned-area perimeters",
         "Eidenshink et al. (2007) · USGS",
         "doi.org/10.5066/P9IED7RZ",
         "fire as an area, not a point —\n81.6% of acres, spread across cells"),
        ("TerraClimate",
         "Abatzoglou et al. (2018) · Climatology Lab",
         "climatologylab.org/terraclimate",
         "drought before the season —\nPDSI, soil moisture, deficit, VPD"),
        ("MODIS MOD13A1 v6.1",
         "Didan (2021) · NASA LP DAAC",
         "doi.org/10.5067/MODIS/MOD13A1.061",
         "fuel load — 500 m vegetation index,\nvia Microsoft Planetary Computer"),
    ]

    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def row(y, name, cite, ident, contrib, *, accent):
        colour = POINT_ORANGE if accent else TEXT_PRIMARY
        ax.text(0.022, y + 0.038, name, fontsize=15 if accent else 13.5,
                fontweight="bold", color=colour, va="center")
        ax.text(0.022, y - 0.006, cite, fontsize=10.5,
                color=TEXT_SECONDARY, va="center")
        ax.text(0.022, y - 0.045, ident, fontsize=9.5,
                color=TEXT_MUTED, va="center", family="monospace")
        # The contribution gets its own column rather than sharing the citation
        # line: the longest citations (MTBS, MODIS) otherwise run under it and
        # the two texts overlap. Left-aligned at a fixed x so the eye can read
        # straight down and answer "what did each of these buy?"
        ax.text(0.585, y + 0.030, contrib, fontsize=10.5, style="italic",
                color=TEXT_SECONDARY, va="top", linespacing=1.5)

    row(0.88, *base, accent=True)
    ax.plot([0.022, 0.985], [0.775, 0.775], color=POINT_ORANGE,
            linewidth=1.2, alpha=0.55)
    ax.text(0.022, 0.735, "joined onto it", fontsize=10.5,
            color=TEXT_MUTED, style="italic", va="center")

    for k, spec in enumerate(layers):
        row(0.60 - k * 0.165, *spec, accent=False)

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)
    return {"base": base[0], "layers": [s[0] for s in layers],
            "out_path": str(out_path)}
