"""External climate covariates: TerraClimate monthly grids -> region-season cells.

The first activation of the climate/fuels layer deferred since W2. It exists
because of a specific W4 finding in `07_natural_location.ipynb`: on the six
largest held-out Natural cells, persistence under-predicts every megafire year
by 1-1.7 orders of magnitude, so a region's own calm-year history is actively
misleading on exactly the years that carry the acres. A big lightning-fire year
is a *weather and fuel-dryness* event, and nothing in the fire record itself can
see it coming. These covariates are the test of whether external pre-season
signal buys the lift history cannot.

Why TerraClimate and not the obvious alternatives
-------------------------------------------------
The analysis grain covers EPA Level III ecoregions in CONUS *and* Alaska (20 AK
regions). That single fact eliminated the two standard drought sources:
gridMET PDSI and nClimGrid SPEI/PDSI are both CONUS-only, so either would have
silently dropped every Alaska cell. TerraClimate is global terrestrial at
1/24 degree (~4 km), monthly, 1958-present, and carries PDSI plus the water-
balance terms - full panel coverage for 1992-2020 on both landmasses.

Fuels are represented by *condition*, not *load*. LANDFIRE was the candidate for
fuel load and was rejected for this panel: its base map is circa 2001 with
discrete vintages (2001/2008/2010/2012/2014/2016/2020) and usable Alaska
coverage only from the 2016 Remap. Against a 1992-2020 season-year panel it
would contribute almost no *interannual* variance - which is precisely the
variance the megafire-year problem needs explained. So the fuel signal here is
`def` (climatic water deficit), `soil` (soil moisture) and `vpd` (vapor pressure
deficit): how dry the fuel *is* going into the season, which is the driver of a
big lightning year far more than how much fuel exists. Fuel load remains a slow
cross-region story that ecoregion identity already partly encodes.

Leakage discipline - the part that matters most
-----------------------------------------------
Every value returned is observable strictly BEFORE its target season begins.
The rule is implemented in `preseason_months()` and is not optional: a covariate
for target season S is aggregated over the `lag_months` calendar months ending
the month before S starts. Nothing from within the target season is ever read.

The season_idx spine follows the project convention established in
`04_cleaning.ipynb`:

    season_idx = (season_year - 1992) * 4 + {DJF:0, MAM:1, JJA:2, SON:3}

with the meteorological-season subtlety that DJF of season_year Y spans
*December of Y-1* plus January-February of Y. The pre-season window for a DJF
target therefore ends in November of Y-1, not November of Y. That off-by-one-
year trap is handled in `season_start()` and is the single easiest way to leak
here, so it is unit-checked in `_self_check()`.

Spatial aggregation
-------------------
Each cell value is an **area-weighted** mean of the grid cells whose centers
fall inside the ecoregion polygon, weighted by cos(latitude) so that the
convergence of meridians does not over-weight northern grid cells - a real
concern at Alaska's latitudes, where a naive mean would bias high-latitude
regions. Regions are dissolved to one geometry per Level III name to match the
`region` key in `region_season_cause.parquet` (the shapefile ships polygons
split by state).

Cells are fetched from the THREDDS OPeNDAP endpoint with a server-side bounding
box, so we transfer roughly the CONUS+AK window rather than the ~15 GB the full
global archive would cost.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

THREDDS = (
    "http://thredds.northwestknowledge.net:8080/thredds/dodsC/"
    "TERRACLIMATE_ALL/data/TerraClimate_{var}_{year}.nc"
)

# The four covariates chosen for the Natural branch. Keys are the TerraClimate
# variable names (also the netCDF variable names); values are the column names
# used downstream and a one-line rationale kept next to the data it describes.
COVARIATES: dict[str, tuple[str, str]] = {
    "PDSI": ("pdsi", "Palmer Drought Severity Index - the direct drought ask"),
    "soil": ("soil_moisture", "column soil moisture (mm) - antecedent wetness"),
    "def": ("water_deficit", "climatic water deficit (mm) - dryness with an energy term"),
    "vpd": ("vpd", "vapor pressure deficit (kPa) - atmospheric dryness driver"),
}

# The season ordinal and spine origin are project-wide constants, not properties of
# the climate layer. They are sourced from `config` so the December rule has exactly
# one definition: an off-by-one-year here leaks 12 months of future climate into
# every winter cell, so a second copy of it is the last thing this module should own.
# The module-level aliases are kept so existing callers keep working unchanged.
from config import SEASON_ORDER as SEASON_OFFSET, ProjectConfig

BASE_YEAR = ProjectConfig().base_year

# Bounding boxes for the server-side subset. TerraClimate latitude descends from
# +90, so lat slices are given high -> low. AK is split out rather than using one
# giant box because a single CONUS+AK box would also drag in most of the Pacific.
BBOX_CONUS = dict(lat=(50.0, 24.0), lon=(-125.5, -66.5))
BBOX_AK = dict(lat=(72.0, 51.0), lon=(-180.0, -129.0))


def season_start(season: str, season_year: int) -> pd.Timestamp:
    """First calendar month of a meteorological season.

    The DJF case is the trap: DJF of `season_year` begins in **December of
    `season_year - 1`**, matching how the cleaning step assigned season labels.
    Getting this wrong shifts the whole winter pre-season window forward by a
    year and leaks 12 months of future climate into the feature.
    """
    if season == "DJF":
        return pd.Timestamp(year=season_year - 1, month=12, day=1)
    first_month = {"MAM": 3, "JJA": 6, "SON": 9}[season]
    return pd.Timestamp(year=season_year, month=first_month, day=1)


def preseason_months(season: str, season_year: int, lag_months: int) -> list[pd.Timestamp]:
    """The `lag_months` months immediately BEFORE the target season starts.

    Returned newest-last. This function is the leakage rule: the window ends one
    month before `season_start`, so no month of the target season can appear.
    """
    start = season_start(season, season_year)
    last = start - pd.DateOffset(months=1)
    return [last - pd.DateOffset(months=k) for k in range(lag_months - 1, -1, -1)]


def season_index(season: str, season_year: int) -> int:
    """Project-standard sequential season-year index (0..116)."""
    return (season_year - BASE_YEAR) * 4 + SEASON_OFFSET[season]


def load_regions(data_dir: Path):
    """Ecoregion polygons for CONUS + AK, keyed by Level III name.

    Returns a GeoDataFrame in EPSG:4326 (TerraClimate's native CRS) with a
    `region` column matching the analysis grain's key. The two shapefiles carry
    different projections and are reprojected before the concat.

    Deliberately NOT dissolved to one geometry per name. Both shapefiles ship
    polygons split by state, and unioning them raises a GEOS side-location
    conflict on an invalid self-intersecting polygon in SE Alaska. The dissolve
    buys nothing here anyway: `_region_masks` groups the point-in-polygon hits
    by `region` afterwards, so multi-part regions merge at the mask level and
    the invalid-geometry repair is never needed.
    """
    import geopandas as gpd

    conus = gpd.read_file(data_dir / "us_eco_l3_state_boundaries").to_crs(4326)
    ak = gpd.read_file(data_dir / "ak_eco_l3").to_crs(4326)
    both = pd.concat(
        [conus[["US_L3NAME", "geometry"]], ak[["US_L3NAME", "geometry"]]],
        ignore_index=True,
    )
    both = gpd.GeoDataFrame(both, geometry="geometry", crs=4326)
    return both.rename(columns={"US_L3NAME": "region"})


def _region_masks(regions, lats: np.ndarray, lons: np.ndarray) -> dict[str, np.ndarray]:
    """Boolean grid mask per region: which grid-cell centers fall in the polygon.

    Built once per bounding box and reused across every variable and year, since
    the grid is identical throughout the archive. Point-in-polygon over the full
    grid via a spatial join - the cost is paid once, not per year.
    """
    import geopandas as gpd

    lon_g, lat_g = np.meshgrid(lons, lats)
    pts = gpd.GeoDataFrame(
        {"row": np.repeat(np.arange(len(lats)), len(lons)),
         "col": np.tile(np.arange(len(lons)), len(lats))},
        geometry=gpd.points_from_xy(lon_g.ravel(), lat_g.ravel()),
        crs=4326,
    )
    hit = gpd.sjoin(pts, regions[["region", "geometry"]], how="inner", predicate="within")

    masks: dict[str, np.ndarray] = {}
    for region, grp in hit.groupby("region"):
        m = np.zeros((len(lats), len(lons)), dtype=bool)
        m[grp["row"].to_numpy(), grp["col"].to_numpy()] = True
        masks[region] = m
    return masks


def _open(var: str, year: int, bbox: dict):
    """Open one TerraClimate year, subset server-side to `bbox`."""
    import xarray as xr

    ds = xr.open_dataset(THREDDS.format(var=var, year=year))
    return ds[var].sel(lat=slice(*bbox["lat"]), lon=slice(*bbox["lon"]))


def fetch_monthly(
    var: str,
    years: Iterable[int],
    regions,
    bbox: dict,
    *,
    cache_dir: Path | None = None,
    tag: str = "",
    verbose: bool = True,
) -> pd.DataFrame:
    """Area-weighted monthly means of `var` per region, over `years`.

    Returns tidy rows: `region`, `month` (Timestamp, month start), `value`.
    Weights are cos(latitude), so northern grid cells are not over-counted -
    material for the Alaska regions.

    Checkpointing. When `cache_dir` is given, each (var, bbox, year) is written
    to its own small parquet as soon as it is reduced, and an existing file is
    reloaded instead of re-fetched. The unit of work is one variable-year - the
    same unit that costs ~20s of network - so a crash, a dropped connection or a
    deliberate interrupt loses at most one of them rather than the whole run.

    This also decouples the download from the lag choice: `to_region_season` is a
    pure local re-aggregation of these monthly values, so sweeping `lag_months`
    re-reads the cache and never touches the network.
    """
    years = list(years)
    masks = None
    wlat = None

    out: list[pd.DataFrame] = []
    for year in years:
        ckpt = None if cache_dir is None else cache_dir / f"{var}_{tag}_{year}.parquet"
        if ckpt is not None and ckpt.exists():
            out.append(pd.read_parquet(ckpt))
            if verbose:
                print(f"    {var} {tag} {year} cached", flush=True)
            continue

        da = _open(var, year, bbox)
        if masks is None:                     # grid is identical across the archive
            lats = da["lat"].values
            lons = da["lon"].values
            masks = _region_masks(regions, lats, lons)
            wlat = np.cos(np.deg2rad(lats))[:, None]      # broadcast over lon
            if verbose:
                print(f"  {var} {tag}: grid {len(lats)}x{len(lons)}, "
                      f"{len(masks)} regions intersected", flush=True)

        arr = da.values                      # (time, lat, lon)
        times = pd.to_datetime(da["time"].values)
        valid = np.isfinite(arr)

        year_rows: list[pd.DataFrame] = []
        for region, mask in masks.items():
            w = np.where(mask, wlat, 0.0)[None, :, :]     # (1, lat, lon)
            ww = np.where(valid, w, 0.0)
            num = np.nansum(np.where(valid, arr, 0.0) * ww, axis=(1, 2))
            den = ww.sum(axis=(1, 2))
            vals = np.divide(num, den, out=np.full(num.shape, np.nan), where=den > 0)
            year_rows.append(pd.DataFrame({"region": region, "month": times, "value": vals}))

        year_df = pd.concat(year_rows, ignore_index=True)
        if ckpt is not None:
            # Write to a temp name then rename: a crash mid-write can never leave a
            # truncated parquet that a later run would trust as complete.
            tmp = ckpt.with_suffix(".parquet.tmp")
            year_df.to_parquet(tmp, index=False)
            tmp.replace(ckpt)
        out.append(year_df)
        if verbose:
            print(f"    {var} {tag} {year} done", flush=True)

    return pd.concat(out, ignore_index=True)


def to_region_season(
    monthly: pd.DataFrame,
    col: str,
    *,
    lag_months: int = 3,
    years: Sequence[int] | None = None,
) -> pd.DataFrame:
    """Collapse monthly region values onto the region-season cell, pre-season only.

    For every (region, season, season_year) the value is the mean of `monthly`
    over `preseason_months(...)` - strictly prior to the season start. Cells whose
    full window is not covered by the fetched months are returned as NaN rather
    than a partial mean, so a short window can never masquerade as a real value.
    """
    if years is None:
        years = sorted({t.year for t in monthly["month"]})
    lut = monthly.set_index(["region", "month"])["value"]

    rows = []
    for season_year in years:
        for season in ("DJF", "MAM", "JJA", "SON"):
            window = preseason_months(season, season_year, lag_months)
            for region in monthly["region"].unique():
                keys = [(region, m) for m in window]
                vals = pd.Series([lut.get(k, np.nan) for k in keys], dtype="float64")
                rows.append(
                    {
                        "region": region,
                        "season": season,
                        "season_year": season_year,
                        "season_idx": season_index(season, season_year),
                        col: np.nan if vals.isna().any() else vals.mean(),
                    }
                )
    return pd.DataFrame(rows)


def build(
    data_dir: Path,
    *,
    years: Sequence[int] = range(1991, 2021),
    lag_months: int = 3,
    out_name: str = "region_season_climate.parquet",
    cache_dir: Path | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """Fetch every covariate for CONUS+AK and write the region-season table.

    `years` starts at 1991 by default, one year before the fire record: the DJF
    1992 pre-season window reaches back into 1991, so without that extra year
    the earliest winter cells would be NaN.

    Resumable. Every variable-year is checkpointed under `cache_dir` (default
    `data/terraclimate_cache/`), so re-running after a crash or an interrupt
    skips everything already fetched and picks up where it stopped. The full run
    is ~40 minutes of network; the checkpoint granularity means an interruption
    costs ~20 seconds of it. Delete the cache directory to force a clean refetch.
    """
    regions = load_regions(data_dir)
    cache_dir = data_dir / "terraclimate_cache" if cache_dir is None else cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    if verbose:
        # Polygon count, not region count: both shapefiles ship polygons split by
        # state, which collapse to the unique Level III names at the mask level.
        print(f"regions: {regions['region'].nunique()} Level III names "
              f"({len(regions)} state-split polygons, CONUS + AK)")
        print(f"checkpoints: {cache_dir}", flush=True)

    frames: list[pd.DataFrame] = []
    for var, (col, _why) in COVARIATES.items():
        if verbose:
            print(f"\n{var} -> {col}", flush=True)
        parts = [
            fetch_monthly(var, years, regions, bbox,
                          cache_dir=cache_dir, tag=tag, verbose=verbose)
            for tag, bbox in (("conus", BBOX_CONUS), ("ak", BBOX_AK))
        ]
        monthly = pd.concat(parts, ignore_index=True)
        # A region straddling both boxes would appear twice; average the duplicates.
        monthly = monthly.groupby(["region", "month"], as_index=False)["value"].mean()
        frames.append(to_region_season(monthly, col, lag_months=lag_months, years=years))

    merged = frames[0]
    for f in frames[1:]:
        merged = merged.merge(f, on=["region", "season", "season_year", "season_idx"], how="outer")

    # Trim to the fire record's spine and drop the two partial winters, matching
    # 05_features.ipynb / 06_analysis.ipynb exactly.
    merged = merged[(merged["season_year"] >= 1992) & (merged["season_year"] <= 2020)]
    merged = merged[~merged["season_idx"].isin([0, 116])]
    merged = merged.sort_values(["region", "season_idx"]).reset_index(drop=True)

    out_path = data_dir / out_name
    merged.to_parquet(out_path, index=False)
    if verbose:
        print(f"\nwrote {out_path}  {merged.shape}")
    return merged


def _self_check() -> None:
    """Assert the leakage rule holds, especially the DJF year boundary."""
    # JJA 2015 pre-season (3 months) must be Mar/Apr/May 2015 - never June.
    w = preseason_months("JJA", 2015, 3)
    assert [m.strftime("%Y-%m") for m in w] == ["2015-03", "2015-04", "2015-05"], w

    # DJF 2015 starts Dec 2014, so its window is Sep/Oct/Nov *2014*.
    w = preseason_months("DJF", 2015, 3)
    assert [m.strftime("%Y-%m") for m in w] == ["2014-09", "2014-10", "2014-11"], w

    # No window may reach into its own season, at any lag.
    for season in ("DJF", "MAM", "JJA", "SON"):
        for lag in (1, 3, 6, 12):
            assert max(preseason_months(season, 2000, lag)) < season_start(season, 2000)

    assert season_index("DJF", 1992) == 0 and season_index("SON", 2020) == 115
    print("terraclimate self-check passed (leakage rule + season spine)")


if __name__ == "__main__":
    _self_check()
