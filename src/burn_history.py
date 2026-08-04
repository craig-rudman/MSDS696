"""Prior-burn state per hex-season: the fuel-consumption covariate.

The hypothesis this module exists to test, stated by the student in W6: a hex
that burned recently has had its fuel consumed, so it should be *less* likely to
carry a subsequent ignition-driven run. Unlike drought, prior burn is a **state,
not a forecast** — it is known with certainty before the target season opens,
which makes it the one covariate here with no forecasting requirement of its own.

Why this needs perimeters, and cannot use ignition points
---------------------------------------------------------
This is the W5 finding pointed at a new target. To know "this hex burned last
year" you need the burned *footprint*, not the ignition point. A point says where
a fire started and nothing about which hexes it consumed. Two thirds of
MTBS-mapped fires cross more than one res-5 hex, so a burn-history feature built
from points would mark one hex burned and leave the other 25 that actually burned
marked unburned — with the error concentrated in exactly the large fires that
remove the most fuel.

So the source split is not a data-quality filter, it is a semantic one:

    perimeter rows -> real fuel consumption, usable as burn history
    point rows     -> ~14 acres against a ~62,494-acre hex (0.02% of the cell)

Point-only fires are **excluded** here. Measured on the W6 coverage pass, 37.4%
of hex-years carry *some* burn but only 2.01% carry a perimeter burn; the gap is
almost entirely small point fires that remove no meaningful fuel. Including them
would make the feature encode *where people report small fires*, which is very
close to the ignition target itself — leaking the target into its own predictor.

The 1.0 fence
-------------
`burned_frac` is clamped to 1.0. Measured before clamping, 166 of 21,866
perimeter hex-years (0.759%, holding 7.04% of perimeter acres) exceed 1.0, with a
maximum of 2.13 — a hex reporting 213% of its own land area burned.

The cause is a numerator/denominator footprint mismatch, not bad acreage: 114 of
the 166 are *single-fire* cells, so multi-fire overlap and complex
double-counting are ruled out. `distribute_perimeter_acres` intersects perimeters
against the **full H3 cell**, while `land_area_acres` measures only the part
inside the ecoregion polygon. Every offending hex is a partial one clipped by a
region boundary or coastline (land areas ~21k against a grid median of ~61.8k),
so a fire covering a full hex that is 35% inside the region reports ~2.9x.

The acres themselves are sound — W5 verified conservation at 99.61% on-grid — so
only the *ratio* is affected. The considered fix was to divide by full H3 cell
area and carry a `hex_completeness` column; the student chose the simpler clamp,
which is defensible at 0.759% of cells. The consequence to remember when reading
results: genuine full-burn cells and partial-hex artifacts both land on exactly
1.0 and are not distinguishable afterward.

Leakage discipline
------------------
Same rule as `src/terraclimate.py`, same trap. History for target `season_idx` t
aggregates seasons strictly earlier than t — never t itself, which would read the
burn scar the target is trying to predict. The DJF year boundary carries the same
off-by-one hazard documented in `terraclimate.season_start`, and is handled here
by working purely on the `season_idx` spine (already boundary-correct out of
`04_cleaning.ipynb`) rather than on calendar dates.

`hex_acres_res5.parquet` has no season column — it keys on `fire_key` — so the
season attach happens here, through `FOD_ID`.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Point-source rows are dropped rather than downweighted. See the module
# docstring: the exclusion is semantic, not a quality filter.
PERIMETER = "perimeter"

# The clamp. See "The 1.0 fence" above — a value of exactly 1.0 in the output may
# be either a true full burn or a clipped partial hex.
FRAC_CEILING = 1.0


def hex_season_burn(
    hex_acres: pd.DataFrame,
    fires: pd.DataFrame,
    hexgrid: pd.DataFrame,
    *,
    perimeter_only: bool = True,
    ceiling: float = FRAC_CEILING,
) -> pd.DataFrame:
    """Observed burn per (hex_id, season_idx) — the raw state, no lagging yet.

    Returns `(hex_id, season_idx, season, season_year, burned_acres, burned_frac,
    n_fires)`. `burned_frac` is `burned_acres / land_area_acres`, clamped to
    `ceiling`.

    This is deliberately the *contemporaneous* state: it is not safe to use as a
    feature for its own season. `trailing_burn` applies the lag.
    """
    ha = hex_acres
    if perimeter_only:
        ha = ha[ha["source"] == PERIMETER]

    keys = ["FOD_ID", "season", "season_year", "season_idx"]
    d = ha.merge(fires[keys], left_on="fire_key", right_on="FOD_ID", how="inner")

    cell = (
        d.groupby(["hex_id", "season_idx"], observed=True)
        .agg(
            burned_acres=("hex_acres", "sum"),
            n_fires=("fire_key", "nunique"),
            season=("season", "first"),
            season_year=("season_year", "first"),
        )
        .reset_index()
    )

    cell = cell.merge(hexgrid[["hex_id", "land_area_acres"]], on="hex_id", how="left")
    frac = cell["burned_acres"] / cell["land_area_acres"]
    cell["burned_frac"] = frac.clip(upper=ceiling)

    return cell[
        ["hex_id", "season_idx", "season", "season_year",
         "burned_acres", "burned_frac", "n_fires"]
    ]


def trailing_burn(
    cell: pd.DataFrame,
    grid_hexes: pd.Series | pd.Index,
    *,
    season_idx_max: int,
    windows: tuple[int, ...] = (4, 12, 20),
) -> pd.DataFrame:
    """Lagged burn history on the dense hex x season_idx panel.

    `cell` is sparse — it holds only hex-seasons that actually burned (~2% of
    cells). A burn-history feature needs the **zeros**: "this hex did not burn"
    is the informative majority case. So the panel is densified against
    `grid_hexes` first, then lagged.

    Windows are in `season_idx` units (4 = one year, 12 = three years, 20 = five
    years). Every returned column is a function of seasons strictly earlier than
    the row's own `season_idx`.

    Columns returned per window `w`: `burned_frac_lag{w}` (summed burned fraction
    over the trailing w seasons) and `any_burn_lag{w}` (did it burn at all).
    Also `seasons_since_burn`, censored at `season_idx_max` when never burned.
    """
    hexes = pd.Index(pd.unique(pd.Series(grid_hexes)), name="hex_id")
    spine = pd.MultiIndex.from_product(
        [hexes, range(season_idx_max + 1)], names=["hex_id", "season_idx"]
    )

    dense = (
        cell.set_index(["hex_id", "season_idx"])[["burned_frac", "burned_acres"]]
        .reindex(spine)
        .fillna(0.0)
        .reset_index()
    )
    # Sort is load-bearing for the shift/rolling idiom, exactly as in
    # src/trailing.py: unsorted input silently attaches one hex's history to
    # another hex's rows with no NaN and no exception to catch it.
    dense = dense.sort_values(["hex_id", "season_idx"]).reset_index(drop=True)

    g = dense.groupby("hex_id", observed=True)["burned_frac"]
    # shift(1) BEFORE rolling: the target season's own burn must never enter its
    # own feature. This single call is the leakage rule for this module.
    prior = g.shift(1)

    out = dense[["hex_id", "season_idx"]].copy()
    for w in windows:
        rolled = prior.groupby(dense["hex_id"], observed=True).rolling(
            w, min_periods=1
        ).sum()
        vals = rolled.reset_index(level=0, drop=True).sort_index()
        # season_idx 0 has no prior season, so shift(1) leaves NaN there. The
        # correct value is 0.0 -- "no prior burn on record" -- not missing: a NaN
        # here would drop the first season of every hex from any model that
        # masks incomplete rows, which is 36,234 cells for no reason.
        out[f"burned_frac_lag{w}"] = np.nan_to_num(vals.to_numpy(), nan=0.0)
        out[f"any_burn_lag{w}"] = (out[f"burned_frac_lag{w}"] > 0).astype(int)

    # Seasons since the hex last burned, censored when it never has. Computed
    # from `prior` so a hex burning in its own target season does not read as 0.
    #
    # `prior` is already shifted, so a True at row t means the burn happened at
    # t-1. Recording `idx - 1` rather than `idx` is what makes the distance count
    # from the burn itself; using `idx` here reports every gap one season short.
    burned = prior.to_numpy() > 0
    idx = dense["season_idx"].to_numpy()
    last = np.where(burned, idx - 1, -1)
    last_seen = (
        pd.Series(last, index=dense.index)
        .groupby(dense["hex_id"], observed=True)
        .cummax()
        .to_numpy()
    )
    since = np.where(last_seen < 0, season_idx_max, idx - last_seen)
    out["seasons_since_burn"] = since

    return out


def build(
    data_dir: Path,
    *,
    windows: tuple[int, ...] = (4, 12, 20),
    perimeter_only: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    """Load the W5 hex artifacts and return the lagged burn-history panel."""
    hex_acres = pd.read_parquet(data_dir / "hex_acres_res5.parquet")
    hexgrid = pd.read_parquet(data_dir / "hex_grid_res5.parquet")
    fires = pd.read_parquet(
        data_dir / "fires_clean.parquet",
        columns=["FOD_ID", "season", "season_year", "season_idx"],
    )

    cell = hex_season_burn(
        hex_acres, fires, hexgrid, perimeter_only=perimeter_only
    )
    season_idx_max = int(fires["season_idx"].max())
    lagged = trailing_burn(
        cell, hexgrid["hex_id"], season_idx_max=season_idx_max, windows=windows
    )

    if verbose:
        n_cells = len(lagged)
        print(f"burn-history panel: {n_cells:,} hex-season cells "
              f"({hexgrid['hex_id'].nunique():,} hexes x {season_idx_max + 1} seasons)")
        print(f"observed burn cells (perimeter only): {len(cell):,} "
              f"({len(cell) / n_cells:.2%})")
        for w in windows:
            share = lagged[f"any_burn_lag{w}"].mean()
            print(f"  any_burn_lag{w:<2}: {share:.2%} of cells have prior burn")

    return lagged


def _self_check() -> None:
    """Leakage and densification checks on a synthetic panel.

    Mirrors `terraclimate._self_check`: the failure this guards against is silent
    and produces plausible-looking numbers, so it is asserted rather than trusted.
    """
    # One hex burning at season_idx 2 only.
    cell = pd.DataFrame({
        "hex_id": ["a"],
        "season_idx": [2],
        "burned_frac": [0.5],
        "burned_acres": [100.0],
    })
    out = trailing_burn(cell, pd.Series(["a", "b"]), season_idx_max=5, windows=(4,))
    a = out[out.hex_id == "a"].set_index("season_idx")

    # The burn is at t=2, so t=2 itself must NOT see it (that is the leak), and
    # t=3 must.
    assert a.loc[2, "burned_frac_lag4"] == 0.0, "leak: season saw its own burn"
    assert a.loc[3, "burned_frac_lag4"] == 0.5, "lag failed to carry prior burn"
    assert a.loc[2, "seasons_since_burn"] == 5, "since-burn leaked its own season"
    assert a.loc[3, "seasons_since_burn"] == 1, "since-burn miscounted"

    # A hex that never burned must still appear, densified with zeros.
    b = out[out.hex_id == "b"]
    assert len(b) == 6, "densification dropped a never-burned hex"
    assert (b["burned_frac_lag4"] == 0).all(), "never-burned hex has burn history"

    print("burn_history._self_check passed")


if __name__ == "__main__":
    _self_check()
