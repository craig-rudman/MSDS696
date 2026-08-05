"""Burned acres per hex-season: the target for "how much burns", not "where it starts".

The second of the two questions the fuel-density probe has to answer. The
ignition work (`src/hex_ignitions.py`) asks *where do fires start*; this asks
*where do the acres land*. They are different targets with different physics, and
the W6 results give a specific reason to expect the covariates to behave
differently here:

    fuel load probably does not decide WHETHER a fire starts -- ignition sources
    (lightning, roads, people) decide that. It very plausibly decides HOW FAR
    one runs once started.

So this is the target where a vegetation index has a mechanism to work through,
and it is also the target where the baseline is known to be weak. W4
(`07_natural_location.ipynb`) measured persistence under-predicting *every one*
of the six largest held-out Natural cells by 1-1.7 orders of magnitude. That is a
measured gap for a covariate to fill, unlike ignition counts where persistence is
strong and nothing has beaten it.

Why this needs perimeters, and the ignition target does not
------------------------------------------------------------
The mirror image of the note in `src/hex_ignitions.py`. FPA-FOD stores a
*pinpoint* ignition location but `FIRE_SIZE` describes an *area*, so:

    starts -> the point is exactly right; perimeters would smear one ignition
              across ~26 hexes and count it 26 times
    acres  -> the point is exactly wrong; a fire larger than a hex (62,494 ac)
              provably cannot fit in the cell its ignition falls in

Acres therefore come from `data/hex_acres_res5.parquet`, built by
`src/hex_burn.py`, where MTBS perimeters distribute each fire's acreage across
the hexes it actually covered with weights summing to 1.0. Point-only fires keep
full weight on their containing hex, which is accurate at a mean of 14 acres
against a 62,494-acre cell.

The distribution is the whole problem
--------------------------------------
Measured on Natural acres, res-5, full record:

    nonzero cells        167,822 of 4,166,910   (4.03%)
    median when nonzero  1.0 acre
    99th percentile      17,109 acres
    maximum              606,945 acres
    top 1% of burning cells hold  55.3% of all natural acres
    top 10%                        98.2%

Five orders of magnitude, and the mass sits in a handful of cells. Two
consequences drive every design choice below:

1. **Model log10(acres), not acres.** On the raw scale a single megafire cell
   dominates any squared-error fit, and the model learns that cell rather than
   the phenomenon.
2. **Separate the two questions the target actually contains** -- *will this hex
   burn at all* (4% of cells) and *how much given that it burns*. A single model
   asked both answers the first and ignores the second, because 96% of the rows
   are zeros. `hurdle_frames()` returns them separately.

Scoring: rank, and the shuffled null
-------------------------------------
Same reasoning as `src/hex_panel.py`. Spearman is invariant to monotone
transforms so it does not depend on getting a likelihood right for a
5-orders-of-magnitude target, and it matches the siting decision, which consumes
an ordering. The shuffled-persistence control -- same predicted values, wrong
hexes -- has never been run on acres, so "is burned area predictable above
chance at all" is an open question this module makes answerable.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from config import MISSING, ProjectConfig
from hex_panel import HEX_GROUP_KEYS, HEX_SORT_KEYS, rank_score
from trailing import TrailingMean

# Trailing window for the acres baseline. Named for its target, per the
# convention in config.py — the ignition target sweeps its own k independently
# and there is deliberately no shared default.
ACRES_K = 7

# log10 floor for zero-acre cells. Acres below 1 exist in the record (a 0.2-acre
# fire), so the floor sits below the smallest real value rather than at 0.
LOG_FLOOR = -4.0

CAUSE_SURFACES: dict[str, str] = {
    "Natural": "natural",
    "Human": "human",
    MISSING: "unknown",
}


def build_panel(
    data_dir: Path,
    *,
    cfg: ProjectConfig | None = None,
    partial_winters: Sequence[int] = (0, 116),
) -> pd.DataFrame:
    """Dense hex x season_idx burned-acre panel, one column per cause surface.

    Densified against the full grid for the same reason as the ignition panel:
    "nothing burned here this season" is an observation, not a missing value.
    Building only from cells that burned would condition the model on already-
    burning hexes and make the 4% nonzero rate invisible.
    """
    cfg = ProjectConfig() if cfg is None else cfg

    hex_acres = pd.read_parquet(data_dir / "hex_acres_res5.parquet")
    hexgrid = pd.read_parquet(data_dir / "hex_grid_res5.parquet")
    fires = pd.read_parquet(
        data_dir / "fires_clean.parquet",
        columns=["FOD_ID", "season_idx", "NWCG_CAUSE_CLASSIFICATION"],
    )

    d = hex_acres.merge(fires, left_on="fire_key", right_on="FOD_ID", how="inner")
    d["surface"] = d["NWCG_CAUSE_CLASSIFICATION"].map(CAUSE_SURFACES)

    wide = (
        d.pivot_table(index=["hex_id", "season_idx"], columns="surface",
                      values="hex_acres", aggfunc="sum", fill_value=0.0,
                      observed=True)
        .reset_index()
    )
    for col in CAUSE_SURFACES.values():
        if col not in wide.columns:
            wide[col] = 0.0
    wide = wide.rename(columns={c: f"acres_{c}" for c in CAUSE_SURFACES.values()})

    seasons = [s for s in range(0, 117) if s not in set(partial_winters)]
    spine = pd.MultiIndex.from_product(
        [hexgrid["hex_id"].unique(), seasons], names=["hex_id", "season_idx"]
    )
    acre_cols = [f"acres_{c}" for c in CAUSE_SURFACES.values()]
    panel = (
        wide.set_index(["hex_id", "season_idx"])[acre_cols]
        .reindex(spine, fill_value=0.0)
        .reset_index()
    )

    panel = panel.merge(
        hexgrid[["hex_id", "region", "land_area_acres", "landmass"]],
        on="hex_id", how="left",
    )
    panel["acres_total"] = panel[acre_cols].sum(axis=1)
    panel["season_year"] = cfg.base_year + (panel["season_idx"] // 4)
    panel["season_ord"] = panel["season_idx"] % 4

    # log10 targets. The floor keeps zero cells on the same scale as the rest
    # rather than dropping them, so the hurdle's two stages share a frame.
    for c in list(CAUSE_SURFACES.values()) + ["total"]:
        a = panel[f"acres_{c}"].to_numpy()
        panel[f"log_{c}"] = np.where(a > 0, np.log10(np.maximum(a, 1e-4)), LOG_FLOOR)
        panel[f"burned_{c}"] = (a > 0).astype(int)

    return panel.sort_values(list(HEX_SORT_KEYS)).reset_index(drop=True)


def add_persistence(
    panel: pd.DataFrame,
    targets: Sequence[str] = ("log_natural", "log_human"),
    *,
    k: int = ACRES_K,
) -> pd.DataFrame:
    """Trailing-mean baseline on the log target, via `trailing.TrailingMean`.

    Persistence is computed on the **log** scale deliberately. On raw acres the
    trailing mean of a hex that had one 600,000-acre season is dominated by that
    season forever; in log space it is a typical-magnitude estimate, which is
    what "this hex burns about this much" should mean.
    """
    out = panel.copy()
    pred = TrailingMean(k=k).predict(out, list(targets), group_keys=HEX_GROUP_KEYS)
    for t in targets:
        out[f"pers_{t}"] = pred[t]
    return out


def add_burn_persistence(
    panel: pd.DataFrame,
    surfaces: Sequence[str] = ("natural", "human"),
    *,
    k: int = ACRES_K,
) -> pd.DataFrame:
    """Trailing baseline computed over BURNING seasons only.

    Separate from `add_persistence` because the two answer different questions,
    and conflating them is what made the first magnitude scoring meaningless.

    `pers_log_*` averages every prior season including the zeros, so a hex that
    has never burned carries `LOG_FLOOR` — a placeholder meaning "no history",
    not a prediction of 0.0001 acres. Scoring a real 600,000-acre burn against
    it produced a 1e10x "error" that measured the placeholder, not the model.
    18% of burning cells were in that state.

    This version masks the zeros before the trailing mean, so `persburn_log_*`
    reads "when this hex has burned, about how much" and is NaN where the hex
    has no prior burn at all. NaN is the honest answer there, and it drops the
    cell from magnitude scoring rather than poisoning it.
    """
    out = panel.copy()
    for s in surfaces:
        masked = f"_burnlog_{s}"
        out[masked] = np.where(out[f"acres_{s}"] > 0, out[f"log_{s}"], np.nan)
    cols = [f"_burnlog_{s}" for s in surfaces]
    pred = TrailingMean(k=k).predict(out, cols, group_keys=HEX_GROUP_KEYS)
    for s in surfaces:
        out[f"persburn_log_{s}"] = pred[f"_burnlog_{s}"]
    return out.drop(columns=cols)


def hurdle_frames(
    panel: pd.DataFrame,
    surface: str = "natural",
    *,
    cfg: ProjectConfig | None = None,
    season_ord: int | None = 2,
    require_history: bool = True,
):
    """Split the target into its two questions: does it burn, and how much.

    Returns `(occurrence, magnitude)` frames. `occurrence` is every scorable
    cell with a 0/1 `burned_*` target; `magnitude` is the burning subset only,
    with the log-acres target. Asking one model both questions lets the 96%
    zeros answer for the 4%.

    `require_history` drops magnitude cells whose burn-conditional baseline is
    undefined (the hex has never burned before). Those cells are unscoreable
    against a persistence floor by construction — see `add_burn_persistence`.
    """
    cfg = ProjectConfig() if cfg is None else cfg
    frame = panel
    if season_ord is not None:
        frame = frame[frame["season_ord"] == season_ord]
    occurrence = frame
    magnitude = frame[frame[f"acres_{surface}"] > 0]
    col = f"persburn_log_{surface}"
    if require_history and col in magnitude.columns:
        magnitude = magnitude[magnitude[col].notna()]
    return occurrence, magnitude


def shuffled_null(
    y: np.ndarray, pred: np.ndarray, *, rng: np.random.Generator | None = None
) -> float:
    """Rank score of the same predictions attached to the wrong cells.

    The honest null: it preserves the exact distribution of predicted values and
    destroys only the cell-to-cell mapping, so it isolates spatial skill from the
    ability to emit plausible-looking magnitudes.
    """
    rng = np.random.default_rng(0) if rng is None else rng
    return rank_score(y, rng.permutation(pred))


def _self_check() -> None:
    """Assert densification, the log floor, and that persistence is trailing."""
    panel = pd.DataFrame({
        "hex_id": ["a"] * 3,
        "season_idx": [2, 6, 10],
        "log_natural": [1.0, 3.0, 5.0],
        "season_ord": [2, 2, 2],
        "season_year": [1992, 1993, 1994],
    }).sort_values(list(HEX_SORT_KEYS)).reset_index(drop=True)

    out = add_persistence(panel, targets=("log_natural",))
    p = out["pers_log_natural"].to_numpy()
    assert np.isnan(p[0]), "first occurrence must have no history"
    assert p[1] == 1.0, f"expected mean of [1.0], got {p[1]}"
    assert p[2] == 2.0, f"expected mean of [1,3], got {p[2]}"

    # The log floor must sit below any real acreage, so a zero cell never reads
    # as a small fire.
    assert LOG_FLOOR < np.log10(0.01), "log floor collides with real small fires"

    # Burn-conditional persistence must ignore the zero seasons entirely, and
    # must be NaN — never LOG_FLOOR — where a hex has no prior burn. This is the
    # bug that made the first magnitude scoring meaningless.
    frame = pd.DataFrame({
        "hex_id": ["a"] * 4,
        "season_idx": [2, 6, 10, 14],
        "acres_natural": [0.0, 100.0, 0.0, 1000.0],
        "log_natural": [LOG_FLOOR, 2.0, LOG_FLOOR, 3.0],
        "season_ord": [2, 2, 2, 2],
        "season_year": [1992, 1993, 1994, 1995],
    }).sort_values(list(HEX_SORT_KEYS)).reset_index(drop=True)
    b = add_burn_persistence(frame, surfaces=("natural",))["persburn_log_natural"]
    assert np.isnan(b.iloc[0]) and np.isnan(b.iloc[1]), "no prior burn must be NaN"
    assert b.iloc[2] == 2.0, f"should average burning seasons only, got {b.iloc[2]}"
    assert b.iloc[3] == 2.0, f"zero season must not dilute, got {b.iloc[3]}"

    # The shuffled null must destroy a perfect predictor.
    y = np.arange(1000.0)
    assert rank_score(y, y) > 0.99, "rank_score broken on a perfect predictor"
    assert abs(shuffled_null(y, y.copy())) < 0.1, "shuffled null retained skill"

    print("hex_acres._self_check passed")


if __name__ == "__main__":
    _self_check()


# --- caching -------------------------------------------------------------
# Same contract as hex_panel.build_cached: the panel is a pure function of the
# source artifacts, so it is built once and read thereafter. This also keeps the
# two persistence baselines defined in exactly one place — the failure that
# produced the unstable ablation numbers logged in W6 was the baseline being
# re-derived at each call site.

PANEL_CACHE = "hex_acres_panel.parquet"


def build_cached(
    data_dir: Path,
    *,
    cfg: ProjectConfig | None = None,
    rebuild: bool = False,
    verbose: bool = True,
) -> pd.DataFrame:
    """Load the acres panel from cache, building it once if absent.

    Returns the panel with both baselines attached: `pers_log_*` (all seasons,
    including zeros) and `persburn_log_*` (burning seasons only). They answer
    different questions and are not interchangeable — see `add_burn_persistence`.
    """
    cache = data_dir / PANEL_CACHE
    if cache.exists() and not rebuild:
        if verbose:
            print(f"acres panel: loaded from {cache.name}")
        return pd.read_parquet(cache)

    panel = build_panel(data_dir, cfg=cfg)
    panel = add_persistence(panel)
    panel = add_burn_persistence(panel)
    panel.to_parquet(cache, index=False)
    if verbose:
        print(f"acres panel: built and cached to {cache.name}  {panel.shape}")
    return panel
