"""TerraClimate pre-season covariates at H3 hex grain.

The hex-grain counterpart to `src/terraclimate.py`. Same source, same leakage
rule, same covariates — the only thing that changes is the spatial unit the grid
is reduced onto, from EPA Level III polygon to res-5 hex.

Why re-fetch rather than re-aggregate
-------------------------------------
`data/terraclimate_cache/` cannot be reused. Those checkpoints hold values
**already reduced to region means**; the underlying grid is gone, and a region
mean cannot be disaggregated back to the hexes inside it. The network cost is
therefore paid again in full.

Why hex grain is expected to behave differently from the W4 null
----------------------------------------------------------------
`07_natural_location.ipynb` found that these four covariates, aggregated to
Level III and pooled across 105 regions, added nothing on top of a region's own
trailing fire history. The stratification cell immediately after it showed why:
per-region Spearman |rho| ranged from 0.086 to 0.529 and *inverted* in two
regions, so pooling averaged a real signal to zero. The notebook's own reading is
that "the covariates are real but the grain of the model is wrong."

The resolution arithmetic supports going finer here. TerraClimate is 1/24 degree
(~4 km); a res-5 hex is ~9.9 km edge, ~62,494 acres. So each hex contains roughly
4-6 native grid cells — enough that the mean is not just one pixel resampled, and
genuinely finer than the ecoregion average that produced the null.

Checkpoint granularity — the resumability contract
--------------------------------------------------
The unit of work is one **(variable, landmass, year)**: 4 vars x 2 landmasses x
30 years = 240 checkpoints, each ~20-40s of network. An interrupt, a dropped
connection or a THREDDS error costs at most one unit, never the run. Re-running
`build()` skips every unit already on disk.

Two things make the resume trustworthy rather than merely intended:

1. **Atomic writes.** Each checkpoint is written to a `.tmp` name and renamed
   only on success, so a crash mid-write cannot leave a truncated parquet that a
   later run would load as complete. (Inherited from `terraclimate.fetch_monthly`,
   which had the same hazard.)
2. **The mask is cached separately.** Point-in-polygon for 36,234 hexes against
   the TerraClimate grid is the expensive one-time computation — far more than a
   single year's download. It is built once per landmass, persisted, and reused
   by every variable-year, so an interrupted run never rebuilds it.

Failures are caught per unit and reported, not raised: one bad year leaves a hole
that the next run fills, rather than losing the 200 units that already succeeded.

Leakage discipline
------------------
Unchanged from `terraclimate.py`, and deliberately delegated to it rather than
reimplemented — `preseason_months` and `season_start` are imported, so the DJF
off-by-one-year trap has exactly one definition in the project. A covariate for
target season S aggregates the `lag_months` months ending the month before S
opens; nothing inside S is ever read.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

# The leakage rule, the season spine and the covariate list all come from the
# region-grain module. Re-declaring any of them here would create the second copy
# that src/config.py exists to prevent.
from terraclimate import (
    BBOX_AK,
    BBOX_CONUS,
    COVARIATES,
    preseason_months,
    season_index,
    _open,
)

# One checkpoint per (var, landmass, year). Small enough that an interrupt is
# cheap; large enough that the per-unit overhead stays negligible.
CACHE_NAME = "hex_climate_cache"
MASK_NAME = "hex_masks"


def hex_centroids(hexgrid: pd.DataFrame) -> pd.DataFrame:
    """Lat/lon center of every hex, from the H3 id itself.

    No geometry needed: `h3.cell_to_latlng` inverts the id. Cheap enough that it
    is not cached.
    """
    import h3

    ll = [h3.cell_to_latlng(h) for h in hexgrid["hex_id"]]
    return pd.DataFrame(
        {
            "hex_id": hexgrid["hex_id"].to_numpy(),
            "lat": [a for a, _ in ll],
            "lon": [b for _, b in ll],
            "landmass": hexgrid["landmass"].to_numpy(),
        }
    )


def build_hex_index(
    hexgrid: pd.DataFrame,
    lats: np.ndarray,
    lons: np.ndarray,
    *,
    landmass: str,
) -> pd.DataFrame:
    """Map every TerraClimate grid cell to the hex that contains its center.

    The inverse of `terraclimate._region_masks`, and cheaper: rather than
    point-in-polygon against 36,234 hex geometries, each grid-cell center is
    converted directly to its containing H3 cell with `latlng_to_cell`. That is
    an O(1) arithmetic operation per grid cell, so the whole grid resolves in one
    vectorised pass.

    Returns `(row, col, hex_id)` for grid cells whose containing hex is part of
    the analysis grid — cells over ocean or outside the ecoregion coverage simply
    do not match and are dropped.

    Note the aggregation this implies: a hex's value is the mean of the grid
    cells whose *centers* land inside it. At ~4 km grid against a ~9.9 km-edge
    hex that is 4-6 cells per hex. No cos(latitude) weighting is applied, unlike
    the region-grain module: a single res-5 hex spans too little latitude for the
    convergence of meridians to matter within it, and H3 cells are already
    near-equal-area by construction.
    """
    import h3

    lon_g, lat_g = np.meshgrid(lons, lats)
    rows = np.repeat(np.arange(len(lats)), len(lons))
    cols = np.tile(np.arange(len(lons)), len(lats))

    flat_lat = lat_g.ravel()
    flat_lon = lon_g.ravel()
    cell = [h3.latlng_to_cell(a, b, 5) for a, b in zip(flat_lat, flat_lon)]

    idx = pd.DataFrame({"row": rows, "col": cols, "hex_id": cell})
    keep = set(hexgrid.loc[hexgrid["landmass"] == landmass, "hex_id"])
    return idx[idx["hex_id"].isin(keep)].reset_index(drop=True)


def _mask_path(cache_dir: Path, landmass: str) -> Path:
    return cache_dir / f"{MASK_NAME}_{landmass}.parquet"


def load_or_build_index(
    hexgrid: pd.DataFrame,
    var: str,
    year: int,
    bbox: dict,
    landmass: str,
    cache_dir: Path,
    *,
    verbose: bool = True,
) -> pd.DataFrame:
    """The grid->hex index, built once per landmass and persisted.

    This is the expensive part of the whole build — more than any single year's
    download — so it is cached separately from the variable-year checkpoints. An
    interrupted run reloads it instead of recomputing it.
    """
    path = _mask_path(cache_dir, landmass)
    if path.exists():
        return pd.read_parquet(path)

    if verbose:
        print(f"  building grid->hex index for {landmass} (one time)...", flush=True)
    da = _open(var, year, bbox)
    idx = build_hex_index(hexgrid, da["lat"].values, da["lon"].values, landmass=landmass)
    tmp = path.with_suffix(".parquet.tmp")
    idx.to_parquet(tmp, index=False)
    tmp.replace(path)
    if verbose:
        print(f"  index: {len(idx):,} grid cells -> {idx['hex_id'].nunique():,} hexes",
              flush=True)
    return idx


def fetch_year(
    var: str,
    year: int,
    bbox: dict,
    idx: pd.DataFrame,
    *,
    landmass: str,
    cache_dir: Path,
    verbose: bool = True,
) -> pd.DataFrame | None:
    """One checkpoint unit: monthly hex means for a single variable-year.

    Returns tidy `(hex_id, month, value)`, or None if the fetch failed — the
    caller records the gap and carries on rather than aborting the run.
    """
    ckpt = cache_dir / f"{var}_{landmass}_{year}.parquet"
    if ckpt.exists():
        if verbose:
            print(f"    {var} {landmass} {year} cached", flush=True)
        return pd.read_parquet(ckpt)

    try:
        da = _open(var, year, bbox)
        arr = da.values                                  # (time, lat, lon)
        times = pd.to_datetime(da["time"].values)
    except Exception as e:                               # network / THREDDS fault
        print(f"    {var} {landmass} {year} FAILED: {type(e).__name__}: {e}",
              flush=True)
        return None

    r = idx["row"].to_numpy()
    c = idx["col"].to_numpy()
    # (time, n_selected_gridcells) -- one column per grid cell inside some hex.
    vals = arr[:, r, c]

    long = pd.DataFrame(vals, index=times, columns=idx["hex_id"].to_numpy())
    long = (
        long.T.groupby(level=0).mean().T          # mean over grid cells in each hex
        .stack()
        .rename("value")
        .reset_index()
        .rename(columns={"level_0": "month", "level_1": "hex_id"})
    )

    tmp = ckpt.with_suffix(".parquet.tmp")
    long.to_parquet(tmp, index=False)
    tmp.replace(ckpt)
    if verbose:
        print(f"    {var} {landmass} {year} done ({len(long):,} rows)", flush=True)
    return long


def to_hex_season(
    monthly: pd.DataFrame,
    col: str,
    *,
    lag_months: int = 3,
    years: Sequence[int],
) -> pd.DataFrame:
    """Collapse monthly hex values onto the hex-season cell, pre-season only.

    Vectorised rather than the row-at-a-time loop in
    `terraclimate.to_region_season`: at 36,234 hexes that loop would be ~4.2M
    iterations of dictionary lookup. Here each (season, season_year) window is
    one groupby over the months in it.

    Cells whose full pre-season window is not covered are NaN, never a partial
    mean — same rule as the region-grain module.
    """
    monthly = monthly.copy()
    monthly["month"] = pd.to_datetime(monthly["month"])

    out: list[pd.DataFrame] = []
    for season_year in years:
        for season in ("DJF", "MAM", "JJA", "SON"):
            window = preseason_months(season, season_year, lag_months)
            sub = monthly[monthly["month"].isin(window)]
            if sub.empty:
                continue
            g = sub.groupby("hex_id")["value"].agg(["mean", "count"])
            # Partial windows are dropped rather than averaged: a hex with 1 of 3
            # months present must not report a value that looks complete.
            g = g[g["count"] == len(window)]
            out.append(
                pd.DataFrame({
                    "hex_id": g.index,
                    "season": season,
                    "season_year": season_year,
                    "season_idx": season_index(season, season_year),
                    col: g["mean"].to_numpy(),
                })
            )
    if not out:
        return pd.DataFrame(columns=["hex_id", "season", "season_year", "season_idx", col])
    return pd.concat(out, ignore_index=True)


def build(
    data_dir: Path,
    *,
    years: Sequence[int] = range(1991, 2021),
    lag_months: int = 3,
    out_name: str = "hex_season_climate.parquet",
    cache_dir: Path | None = None,
    covariates: dict | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """Fetch every covariate at hex grain and write the hex-season table.

    Resumable at (variable, landmass, year) granularity — 240 units for the full
    default run. Re-run after any interrupt and it continues from the last
    completed unit. Delete `cache_dir` to force a clean refetch.

    `years` starts at 1991 for the same reason as the region build: the DJF 1992
    pre-season window reaches back into December 1991.
    """
    covariates = COVARIATES if covariates is None else covariates
    cache_dir = data_dir / CACHE_NAME if cache_dir is None else cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    hexgrid = pd.read_parquet(data_dir / "hex_grid_res5.parquet")
    years = list(years)

    if verbose:
        n_units = len(covariates) * 2 * len(years)
        done = len(list(cache_dir.glob("*.parquet"))) - len(
            list(cache_dir.glob(f"{MASK_NAME}_*.parquet"))
        )
        print(f"hex grid: {len(hexgrid):,} hexes "
              f"({(hexgrid.landmass == 'CONUS').sum():,} CONUS / "
              f"{(hexgrid.landmass == 'AK').sum():,} AK)")
        print(f"checkpoints: {cache_dir}")
        print(f"units: {n_units} (var x landmass x year) | already cached: {max(done, 0)}",
              flush=True)

    boxes = (("CONUS", BBOX_CONUS), ("AK", BBOX_AK))
    failures: list[tuple[str, str, int]] = []
    frames: list[pd.DataFrame] = []

    for var, (col, _why) in covariates.items():
        if verbose:
            print(f"\n{var} -> {col}", flush=True)
        parts: list[pd.DataFrame] = []
        for landmass, bbox in boxes:
            idx = load_or_build_index(
                hexgrid, var, years[0], bbox, landmass, cache_dir, verbose=verbose
            )
            for year in years:
                got = fetch_year(var, year, bbox, idx, landmass=landmass,
                                 cache_dir=cache_dir, verbose=verbose)
                if got is None:
                    failures.append((var, landmass, year))
                else:
                    parts.append(got)
        if not parts:
            continue
        monthly = pd.concat(parts, ignore_index=True)
        # A hex cannot straddle both boxes (landmass is exclusive), but averaging
        # duplicates is harmless insurance against an overlapping bbox edit.
        monthly = monthly.groupby(["hex_id", "month"], as_index=False)["value"].mean()
        frames.append(to_hex_season(monthly, col, lag_months=lag_months, years=years))

    if not frames:
        raise RuntimeError("no covariate completed; nothing to write")

    keys = ["hex_id", "season", "season_year", "season_idx"]
    merged = frames[0]
    for f in frames[1:]:
        merged = merged.merge(f, on=keys, how="outer")

    # Same spine trim as the region build: fire record years, no partial winters.
    merged = merged[(merged["season_year"] >= 1992) & (merged["season_year"] <= 2020)]
    merged = merged[~merged["season_idx"].isin([0, 116])]
    merged = merged.sort_values(["hex_id", "season_idx"]).reset_index(drop=True)

    out_path = data_dir / out_name
    merged.to_parquet(out_path, index=False)
    if verbose:
        print(f"\nwrote {out_path}  {merged.shape}")
        if failures:
            print(f"INCOMPLETE — {len(failures)} unit(s) failed; re-run build() "
                  f"to fill: {failures[:8]}{'...' if len(failures) > 8 else ''}")
    return merged


def _self_check() -> None:
    """Assert the pieces this module adds; the leakage rule is checked upstream."""
    import terraclimate as tc

    tc._self_check()          # the DJF trap, asserted where it is defined

    # to_hex_season must drop a partial window rather than average it.
    monthly = pd.DataFrame({
        "hex_id": ["a", "a", "b"],
        "month": pd.to_datetime(["2015-03-01", "2015-04-01", "2015-03-01"]),
        "value": [1.0, 3.0, 9.0],
    })
    out = to_hex_season(monthly, "v", lag_months=3, years=[2015])
    jja = out[out["season"] == "JJA"]
    # JJA 2015 window is Mar/Apr/May. Hex "a" has 2 of 3 months, "b" has 1 of 3 —
    # neither is complete, so the frame must be empty rather than partially mean'd.
    assert jja.empty, f"partial pre-season window leaked a value:\n{jja}"

    monthly3 = pd.DataFrame({
        "hex_id": ["a"] * 3,
        "month": pd.to_datetime(["2015-03-01", "2015-04-01", "2015-05-01"]),
        "value": [1.0, 2.0, 3.0],
    })
    out3 = to_hex_season(monthly3, "v", lag_months=3, years=[2015])
    jja3 = out3[out3["season"] == "JJA"]
    assert len(jja3) == 1 and abs(jja3["v"].iloc[0] - 2.0) < 1e-9, "complete window mismean"

    print("hex_climate._self_check passed")


if __name__ == "__main__":
    _self_check()
