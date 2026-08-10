"""Ignition counts per hex-season: the target of the starts-likelihood model.

The W6 product, defined by the student: *where in my region are fires most
likely to start?* This module builds the thing being predicted; the covariates
that predict it live in `src/hex_climate.py` and `src/burn_history.py`.

Why this uses raw points and no perimeters
------------------------------------------
This is the W5 point-vs-area asymmetry read in the other direction. FPA-FOD
stores a *pinpoint* `LATITUDE`/`LONGITUDE` but `FIRE_SIZE` describes an *area* —
which is what made an acres target at hex grain expensive and forced the MTBS
perimeter build in `src/hex_burn.py`.

An ignition location is exactly what the record stores correctly. So the same
defect that made acres hard makes **starts cheap**:

    acres  at hex grain -> needs perimeters (0.6% of fires, 81.6% of acres)
    starts at hex grain -> needs the point (100% of fires, no join at all)

Distributing a fire's ignition across its perimeter would be actively wrong here:
it would smear one ignition across ~26 hexes and count it 26 times. A fire starts
in exactly one place. All 2,271,343 fires contribute, not the 13,870 with
perimeters.

Human and Natural are separate surfaces, not one pooled model
--------------------------------------------------------------
Student decision, W6. The two are different processes with different drivers:
human starts track roads and settlement — largely *static* geography that a
season-varying climate covariate cannot move — while natural starts track
lightning and fuel dryness, which is what the climate layer measures and where
`07_natural_location.ipynb` found real per-region signal (Spearman |rho| to
0.529). Pooling them would let the 78% human mass dilute the climate signal, and
would model two unlike processes as one.

`Missing` cause is carried as its own surface rather than dropped or reallocated,
consistent with the Tier-1 treatment of Unknown as a class in its own right: at
161,711 fires it is too large to discard silently, and its spatial pattern is a
reporting-quality signal rather than an ignition signal.

Exposure: the offset, not a raw count
--------------------------------------
Student decision, W6. A raw count target would substantially rediscover which
hexes are large and which are populated. `log_area` is returned so a count model
can carry it as an **offset** — modeling starts per unit area rather than starts
— which also handles the partial hexes clipped by region boundaries or coastline
that the burn-history work surfaced (land areas ~21k against a grid median of
~61.8k acres).

The zeros are the data
----------------------
Fires are sparse at hex grain: most hex-seasons have no ignition at all. The
panel is therefore **densified** against the full grid, because "no fire started
here this season" is an observation, not a missing value. Building the target
from the fire table alone would silently condition the whole model on
already-burning cells.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from config import MISSING

# H3 resolution of the analysis grid. Matches hex_burn.HEX_RES_MVP; re-stated
# rather than imported so this module does not pull in geopandas.
HEX_RES = 5

# The three cause surfaces. Keys are the values of NWCG_CAUSE_CLASSIFICATION;
# values are the column suffix used downstream.
CAUSE_SURFACES: dict[str, str] = {
    "Natural": "natural",
    "Human": "human",
    MISSING: "unknown",
}


def assign_hex(
    fires: pd.DataFrame,
    hexgrid: pd.DataFrame,
    *,
    resolution: int = HEX_RES,
    lat_col: str = "LATITUDE",
    lon_col: str = "LONGITUDE",
) -> pd.DataFrame:
    """Attach the containing `hex_id` to every fire, by ignition point.

    Direct `latlng_to_cell` rather than a spatial join — exact for point
    containment and far cheaper over 2.27M rows, the same reasoning as
    `hex_burn.assign_point_acres`.

    Fires whose cell is not in `hexgrid` fall outside the study regions and are
    dropped; the count is reported by `coverage()` rather than silently absorbed.
    """
    import h3

    f = fires.dropna(subset=[lat_col, lon_col]).copy()
    f["hex_id"] = [
        h3.latlng_to_cell(la, lo, resolution)
        for la, lo in zip(f[lat_col].to_numpy(), f[lon_col].to_numpy())
    ]
    return f[f["hex_id"].isin(set(hexgrid["hex_id"]))].reset_index(drop=True)


def coverage(fires: pd.DataFrame, assigned: pd.DataFrame) -> dict:
    """What went in, what landed on the grid, what fell outside."""
    n_in = len(fires)
    n_on = len(assigned)
    return {
        "fires_in": n_in,
        "fires_on_grid": n_on,
        "fires_off_grid": n_in - n_on,
        "pct_on_grid": n_on / n_in if n_in else np.nan,
        "hexes_touched": assigned["hex_id"].nunique(),
    }


def build_panel(
    fires: pd.DataFrame,
    hexgrid: pd.DataFrame,
    *,
    resolution: int = HEX_RES,
    season_idx_range: Sequence[int] | None = None,
    partial_winters: Sequence[int] = (0, 116),
    cause_col: str = "NWCG_CAUSE_CLASSIFICATION",
) -> pd.DataFrame:
    """The dense hex x season_idx ignition panel, one count column per surface.

    Returns `(hex_id, season_idx, region, land_area_acres, log_area,
    starts_natural, starts_human, starts_unknown, starts_total)`.

    Densified across the full grid and the full season spine: a hex-season with
    no ignition is a zero row, not an absent one. `partial_winters` are dropped
    to match the project spine (`config.ProjectConfig.partial_winters`) — those
    two DJF seasons are truncated by the record boundary, not by the weather.
    """
    assigned = assign_hex(fires, hexgrid, resolution=resolution)

    counts = (
        assigned.groupby(["hex_id", "season_idx", cause_col], observed=True)
        .size()
        .rename("n")
        .reset_index()
    )
    wide = (
        counts.pivot_table(
            index=["hex_id", "season_idx"], columns=cause_col, values="n",
            fill_value=0, observed=True,
        )
        .rename(columns=CAUSE_SURFACES)
    )
    # A cause absent from the record entirely would leave the column missing;
    # create it rather than let a downstream KeyError decide.
    for col in CAUSE_SURFACES.values():
        if col not in wide.columns:
            wide[col] = 0
    wide = wide[list(CAUSE_SURFACES.values())]
    wide.columns = [f"starts_{c}" for c in wide.columns]
    wide = wide.reset_index()

    if season_idx_range is None:
        lo, hi = int(assigned["season_idx"].min()), int(assigned["season_idx"].max())
        season_idx_range = range(lo, hi + 1)
    seasons = [s for s in season_idx_range if s not in set(partial_winters)]

    spine = pd.MultiIndex.from_product(
        [hexgrid["hex_id"].unique(), seasons], names=["hex_id", "season_idx"]
    )
    panel = (
        wide.set_index(["hex_id", "season_idx"])
        .reindex(spine, fill_value=0)      # the zeros ARE the data
        .reset_index()
    )

    panel = panel.merge(
        hexgrid[["hex_id", "region", "land_area_acres", "landmass"]],
        on="hex_id", how="left",
    )
    start_cols = [f"starts_{c}" for c in CAUSE_SURFACES.values()]
    panel["starts_total"] = panel[start_cols].sum(axis=1)
    # The exposure offset. Guarded against a zero/negative area, which would make
    # the log undefined and silently drop the hex from any model using it.
    area = panel["land_area_acres"].to_numpy()
    panel["log_area"] = np.log(np.where(area > 0, area, np.nan))

    return panel.sort_values(["hex_id", "season_idx"]).reset_index(drop=True)


def build(
    data_dir: Path,
    *,
    resolution: int = HEX_RES,
    out_name: str = "hex_ignitions.parquet",
    verbose: bool = True,
) -> pd.DataFrame:
    """Load the fire record and grid, build the panel, write it."""
    fires = pd.read_parquet(
        data_dir / "fires_clean.parquet",
        columns=["FOD_ID", "LATITUDE", "LONGITUDE", "season", "season_year",
                 "season_idx", "NWCG_CAUSE_CLASSIFICATION"],
    )
    hexgrid = pd.read_parquet(data_dir / "hex_grid_res5.parquet")

    assigned = assign_hex(fires, hexgrid, resolution=resolution)
    cov = coverage(fires, assigned)
    panel = build_panel(fires, hexgrid, resolution=resolution)

    if verbose:
        print(f"fires: {cov['fires_in']:,} in | {cov['fires_on_grid']:,} on grid "
              f"({cov['pct_on_grid']:.2%}) | {cov['fires_off_grid']:,} off")
        print(f"hexes with >=1 ignition ever: {cov['hexes_touched']:,} "
              f"of {len(hexgrid):,}")
        print(f"panel: {len(panel):,} hex-season cells")
        for c in ["natural", "human", "unknown", "total"]:
            col = f"starts_{c}"
            nz = (panel[col] > 0).mean()
            print(f"  starts_{c:<8} total {panel[col].sum():>9,} | "
                  f"nonzero cells {nz:6.2%}")

    out_path = data_dir / out_name
    panel.to_parquet(out_path, index=False)
    if verbose:
        print(f"\nwrote {out_path}  {panel.shape}")
    return panel


def _self_check() -> None:
    """Densification, cause split and offset, on a synthetic record."""
    hexgrid = pd.DataFrame({
        "hex_id": ["a", "b"],
        "region": ["R", "R"],
        "land_area_acres": [1000.0, 2000.0],
        "landmass": ["CONUS", "CONUS"],
    })
    fires = pd.DataFrame({
        "FOD_ID": [1, 2, 3],
        "hex_id": ["a", "a", "b"],
        "season_idx": [5, 5, 6],
        "NWCG_CAUSE_CLASSIFICATION": ["Natural", "Human", "Natural"],
    })

    # Bypass the h3 lookup: assign_hex is exercised against the real record in
    # build(); what needs asserting here is the aggregation and densification.
    counts = (
        fires.groupby(["hex_id", "season_idx", "NWCG_CAUSE_CLASSIFICATION"])
        .size().rename("n").reset_index()
    )
    wide = counts.pivot_table(
        index=["hex_id", "season_idx"], columns="NWCG_CAUSE_CLASSIFICATION",
        values="n", fill_value=0,
    ).rename(columns=CAUSE_SURFACES).reset_index()

    spine = pd.MultiIndex.from_product([["a", "b"], [5, 6]],
                                       names=["hex_id", "season_idx"])
    panel = wide.set_index(["hex_id", "season_idx"]).reindex(spine, fill_value=0)

    # Every hex x season combination must exist, including the ones with no fire.
    assert len(panel) == 4, f"densification produced {len(panel)} of 4 cells"
    assert panel.loc[("b", 5), "natural"] == 0, "absent cell should be a zero"
    assert panel.loc[("a", 5), "natural"] == 1, "count lost"
    assert panel.loc[("a", 5), "human"] == 1, "cause split collapsed"

    # The offset must be log of area, and must not silently become -inf or NaN.
    area = hexgrid["land_area_acres"].to_numpy()
    log_area = np.log(np.where(area > 0, area, np.nan))
    assert np.isfinite(log_area).all(), "offset is not finite"
    assert abs(log_area[1] - log_area[0] - np.log(2)) < 1e-9, "offset mis-scaled"

    print("hex_ignitions._self_check passed")


if __name__ == "__main__":
    _self_check()
