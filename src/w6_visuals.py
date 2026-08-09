"""W6 executive visuals — the siting product, and why covariates did not improve it.

Two arguments, five figures, in the order a talk should make them.

**The product.** `plot_siting_glance` ranks hexes by the persistence baseline and
cuts them into triage tiers defined by *what they buy* — 30/60/90% of a season's
ignitions caught. In the default region the first 30% of starts sits under 6.1%
of the ground (a 4.95x lift over picking ground at random) while reaching 90%
takes 77.8% (1.16x, barely better than treating everywhere). The diminishing
return is the recommendation. `plot_siting_vs_burn` scores the same ranking
against the held-out season.

**Why the covariates added nothing.** The reason is the hardest idea in the talk:
these covariates identify dry *places*, not dry *years*, and place is what
persistence already knows. Stated as a pair of correlations (NDVI +0.228 raw,
+0.098 within-hex) it is two numbers on a slide that no audience absorbs.
`plot_ndvi_map` shows what NDVI is on real ground; `plot_persistence_pair` shows
both layers persisting across a decade gap; `plot_ndvi_variance` draws the split
directly — between-place sd ~0.132 against within-hex ~0.048, so NDVI is ~2.8x
more about which hex than which year.

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
* **Tiers, not a smooth ramp.** The W6 modelling settled that ignition is a
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

import numpy as np
import pandas as pd

# Reuse the project palette rather than defining a second one.
from w5_visuals import PERIM_FILL, SURFACE, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY


# Sequential green, light -> dark: vegetation density. A single hue ramped by
# lightness, for the same reasons the flame ramp is built that way in
# `w5_visuals` -- a yellow->green->blue rainbow would read as categories on a
# continuous quantity and lose its ordering in grayscale. Green is the honest
# hue here: NDVI *is* greenness, and borrowing the flame ramp would imply the
# map shows burning, which it does not.
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


def plot_siting_glance(panel: pd.DataFrame, grid: pd.DataFrame, out_path: Path, *,
                       region_prefix: str = "Klamath",
                       target_year: int = 2020,
                       capture_tiers: tuple[float, float, float] = (0.30, 0.60, 0.90),
                       figsize: tuple[float, float] = (7.4, 7.6)) -> dict:
    """Triage tiers defined by what they BUY, not by how much ground they cost.

    Hexes are ranked by the persistence baseline (their own ignition history,
    natural and human, from seasons strictly before `target_year`), then cut at
    the ranks where cumulative captured ignitions cross each of `capture_tiers`.
    So the tiers answer "how far down the list do I go to catch 30% of the
    starts, then 60%, then 90%?"

    Defining tiers by capture rather than by a ground budget removes an arbitrary
    parameter -- an earlier draft used a flat top-20%, and that choice alone
    decided whether the figure looked like success or failure. It also makes the
    figure carry the finding that matters: **the returns diminish hard.** In the
    default region the first 30% of starts sits under ~6% of the ground (a ~5x
    lift), while reaching 90% takes ~78% of it (~1.2x, barely better than
    treating everywhere).

    That is why tier 3 is deliberately very pale. It is not a recommendation to
    treat; it is the visible cost of chasing full coverage, and its sheer area is
    the argument for stopping earlier.

    Why saturation of one hue and not categorical outcome colors: this is a
    **ranking under a budget**, not a classification. And why discrete tiers and
    not a smooth ramp: the W6 modelling settled that ignition is a **gate, not a
    dial**, so priority order is real but graded intensity is not.
    """
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from scipy.stats import spearmanr

    ids = set(grid.loc[grid["region"].str.startswith(region_prefix), "hex_id"])
    region_name = grid.loc[grid["hex_id"].isin(ids), "region"].iloc[0]

    d = panel[(panel["hex_id"].isin(ids))
              & (panel["season_ord"] == 2)
              & (panel["season_year"] == target_year)].copy()
    d = d.dropna(subset=["pers_natural", "pers_human"])
    d["pred"] = d["pers_natural"] + d["pers_human"]
    d["actual"] = d["starts_natural"] + d["starts_human"]
    d = d.sort_values("pred", ascending=False).reset_index(drop=True)

    cum = d["actual"].cumsum() / d["actual"].sum()
    cuts = [int((cum < t).sum()) + 1 for t in capture_tiers]

    # One hue, three steps, with a wide lightness gap before tier 3 so it reads
    # as "eventually" rather than as a third recommendation.
    T1, T2, T3, REST = "#8c180c", "#ef8b5e", "#fbdcc8", "#f2f0ed"
    rank = np.arange(len(d))
    faces = [T1 if r < cuts[0] else
             T2 if r < cuts[1] else
             T3 if r < cuts[2] else REST for r in rank]

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

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.2)
    plt.close(fig)

    n = len(d)
    return {
        "region": region_name,
        "n_hex": n,
        "target_year": target_year,
        "capture_tiers": capture_tiers,
        "hexes_per_tier": cuts,
        "ground_frac": [c / n for c in cuts],
        "lift": [t / (c / n) for t, c in zip(capture_tiers, cuts)],
        "actual_starts": int(d["actual"].sum()),
        "rho": float(spearmanr(d["pred"], d["actual"]).statistic),
        "out_path": str(out_path),
    }


def plot_siting_vs_burn(panel: pd.DataFrame, grid: pd.DataFrame,
                        out_path: Path, *,
                        region_prefix: str = "Klamath",
                        target_year: int = 2020,
                        top_frac: float = 0.20,
                        min_starts: float = 1.0,
                        figsize: tuple[float, float] = (7.4, 7.6)) -> dict:
    """Hits and misses, as four flat fills — no stroke, no size, no ramp.

    Every hex is exactly one of four outcomes, and each gets its own fill:

    * **hit**            — sited, and fire started there
    * **false positive** — sited, and nothing started
    * **miss**           — not sited, but fire started there
    * **correct pass**   — not sited, and nothing started

    Encoding the hit with an outline (an earlier draft) fails at a glance,
    because a stroke is a boundary cue and the reader has to inspect edges hex by
    hex to find it. Fill is pre-attentive: the eye sorts four colors in one pass
    without visiting each shape.

    Color logic. The two **errors** are the colors that must separate fastest, so
    they take opposite ends of the warm/cool axis: false positives blue (effort
    spent where nothing happened) and misses ember (fire the plan did not reach).
    Hits are the dark neutral -- correct, and deliberately not competing for
    attention -- and correct passes are the pale ground. The result is that a
    reader's eye lands on the *errors* first, which is the honest thing for a
    verification figure to do.

    **Ignitions, not acres, define the outcome, and that choice is the finding.**
    Scored against burned *acres* this same ranking captures only ~5% of the
    burn -- because burned area in the tail is unpredictable (top decile
    under-predicted 270x) while ignition *location* is not. The figure shows what
    the model claims to do.
    """
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from scipy.stats import spearmanr

    ids = set(grid.loc[grid["region"].str.startswith(region_prefix), "hex_id"])
    region_name = grid.loc[grid["hex_id"].isin(ids), "region"].iloc[0]

    d = panel[(panel["hex_id"].isin(ids))
              & (panel["season_ord"] == 2)
              & (panel["season_year"] == target_year)].copy()
    d = d.dropna(subset=["pers_natural", "pers_human"])
    d["pred"] = d["pers_natural"] + d["pers_human"]
    d["actual"] = d["starts_natural"] + d["starts_human"]

    d = d.sort_values("pred", ascending=False).reset_index(drop=True)
    n_top = max(1, int(round(len(d) * top_frac)))
    d["sited"] = np.arange(len(d)) < n_top
    d["ignited"] = d["actual"] >= min_starts

    HIT = "#4a4a48"       # correct and treated: dark neutral, not attention-seeking
    FALSE_POS = "#4f86c6" # effort spent, nothing happened
    MISS = "#c2400f"      # fire the plan did not reach
    PASS_ = "#eeece8"     # correctly left alone

    faces = []
    for sited, ig in zip(d["sited"], d["ignited"]):
        faces.append(HIT if (sited and ig) else
                     FALSE_POS if sited else
                     MISS if ig else PASS_)

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

    fig.savefig(out_path, dpi=200, facecolor=SURFACE, bbox_inches="tight",
                pad_inches=0.2)
    plt.close(fig)

    hit = int((d["sited"] & d["ignited"]).sum())
    fp = int((d["sited"] & ~d["ignited"]).sum())
    miss = int((~d["sited"] & d["ignited"]).sum())
    return {
        "region": region_name,
        "n_hex": int(len(d)),
        "target_year": target_year,
        "n_sited": n_top,
        "hits": hit,
        "false_positives": fp,
        "misses": miss,
        "correct_passes": int(len(d) - hit - fp - miss),
        "precision": hit / n_top,
        "starts_capture": float(d.loc[d["sited"], "actual"].sum() / d["actual"].sum()),
        "lift": float(d.loc[d["sited"], "actual"].sum() / d["actual"].sum()) / top_frac,
        "rho": float(spearmanr(d["pred"], d["actual"]).statistic),
        "colors": {"hit": HIT, "false_positive": FALSE_POS, "miss": MISS,
                   "correct_pass": PASS_},
        "out_path": str(out_path),
    }
