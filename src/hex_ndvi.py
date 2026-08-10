"""Pre-season MODIS vegetation indices at hex grain: the fuel-density probe.

The rung deferred since W5. Everything before it measured fuel *history* (has
this hex burned — `src/burn_history.py`) or fuel *dryness* (`src/hex_climate.py`).
Neither measures how much combustible material is actually standing there. NDVI
and EVI do, directly, and their interannual movement is the one mechanism the
other layers cannot see: a wet spring that produces a heavy grass load.

Why the Planetary Computer, and not Earthdata or GEE
-----------------------------------------------------
This rung was blocked from W5 through W6 on credentials — no Earthdata account,
no Google Earth Engine registration on this machine. Microsoft's Planetary
Computer serves the same MODIS collections through a **public STAC API with
anonymous read**: no account, no API key, no OAuth. `planetary_computer.sign_inplace`
attaches short-lived read tokens to blob URLs automatically. That removes the
blocker outright rather than working around it.

Collection: `modis-13A1-061` (MOD13A1 v6.1) — 500 m, 16-day composites, 2000-present.

What is being tested, and the prior against it
-----------------------------------------------
Two W6 results argue this rung will also come back null, and stating them up
front is what keeps a null honest rather than disappointing:

1. **The climate null** (`12_hex_ignition_baselines.ipynb`). Pre-season dryness
   failed because its signal is *cross-sectional* — it identifies dry places, not
   dry years. Raw `pdsi` correlates -0.137 with JJA natural starts but only
   -0.073 as a within-hex anomaly. NDVI has exactly the same structure: forests
   are green and deserts are not, every year.
2. **The prior-burn result.** Burn history *is* a fuel-density proxy, and it
   showed no depletion effect at all — the ignition rate in recently-burned hexes
   is flat from year 0 to year 18.

So both feature forms are built, and the **gap between them is the finding**:

    ndvi        - raw pre-season mean. Mostly "what grows here" = static geography.
    ndvi_anom   - this hex against its own normal. The interannual part, and the
                  only component persistence cannot already encode.

Anomaly baselines are computed on training years only, by
`hex_panel.add_climate_anomalies`, for the same no-leak reason documented there.

The pre-season window
---------------------
Composites are aggregated over the months returned by
`terraclimate.preseason_months` — imported, never reimplemented, so the DJF
year-boundary rule has one definition in this project. A window overlapping the
target season would read the burn scar itself and produce a spectacular,
circular result.

MODIS begins in 2000, so the panel truncates from 29 season-years to 21. The
held-out period (`cfg.test_start` = 2010 onward) is unaffected, so the ablation
remains valid; only the training span shortens.

Spatial reduction: an interior sample, NOT a true H3 aggregate
---------------------------------------------------------------
This differs from `src/hex_climate.py` and the difference is deliberate, so it
must not be read as parity. `hex_climate` maps every TerraClimate grid cell to
its containing hex with `latlng_to_cell` and averages what falls inside — an
exact H3 reduction. This module instead samples a **10 x 10 km box centered on
the hex centroid**:

    box            100.0 km2
    res-5 hex      252.9 km2   (edge 9.85 km, inscribed radius 8.53 km)
    coverage       ~40% of the cell, square sample of a hexagonal footprint

Why: MODIS ships in sinusoidal projection at 500 m, and running `latlng_to_cell`
per pixel across 2400x2400 tiles is far slower than a windowed COG read. The
speed difference is what makes 126 region-years affordable at all.

Why it is acceptable here (student decision, W6 — "good enough"):

- Vegetation is strongly spatially autocorrelated at 10 km, so ~6,000 sampled
  pixels are representative of the cell.
- The **anomaly** form is the rung the hypothesis rests on, and it is near-immune
  to this: a fixed centring bias cancels when a hex is differenced against its
  own history.

Where it could bite, stated so a reviewer does not have to find it: heterogeneous
hexes — half forest, half burn scar — where an interior sample misses the edges.
Those are exactly the cells a fuel-density hypothesis cares most about. If the
raw (non-anomaly) NDVI rung ever carries a result, this approximation is the
first thing to re-examine.

Scope: six forest ecoregions
-----------------------------
2,663 res-5 hexes across Klamath, Northern Rockies, Idaho Batholith, Blue
Mountains, North Cascades and Northwestern Great Plains. These are the regions
where `07_natural_location.ipynb` measured genuine per-region climate signal
(|rho| 0.37-0.53 with physically correct signs on 4/4 covariates). If a fuel
signal exists anywhere in this record it should be here, which is what makes a
null here decisive rather than merely regional.

Resumability
------------
Same contract as `src/hex_climate.py`, and for the same reason — this is a long
network job that must survive interruption. The checkpoint unit is one
**(region, season_year)**: 6 x 21 = 126 units. Writes are atomic (`.tmp` then
rename) so a crash cannot leave a truncated parquet a later run would trust, and
a failed unit is recorded and skipped rather than aborting the run.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from terraclimate import preseason_months, season_index

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "modis-13A1-061"

# MODIS VI products ship as scaled 16-bit integers.
NDVI_SCALE = 0.0001

# Asset keys on the collection. EVI is carried alongside NDVI because it is less
# prone to saturating over dense canopy, which is most of the forest in scope.
ASSETS: dict[str, str] = {
    "500m_16_days_NDVI": "ndvi",
    "500m_16_days_EVI": "evi",
}

CACHE_NAME = "hex_ndvi_cache"

# The six forest ecoregions. See "Scope" in the module docstring.
FOREST_REGIONS: tuple[str, ...] = (
    "Klamath Mountains/California High North Coast Range",
    "Northern Rockies",
    "Idaho Batholith",
    "Blue Mountains",
    "North Cascades",
    "Northwestern Great Plains",
)

# Half-width in metres of the sampling window around a hex center. This makes the
# sample a 10x10 km box = 100 km2 against the res-5 hex's 252.9 km2, so it covers
# ~40% of the cell and is an *interior sample*, not a full aggregate — see
# "Spatial reduction" in the module docstring for why that is accepted here and
# where it could matter. Widening toward the 8.53 km inscribed radius would raise
# coverage but start bleeding into neighboring cells at the corners.
HALF_WIN_M = 5000


def hex_centroids(hexgrid: pd.DataFrame, regions: Sequence[str]) -> pd.DataFrame:
    """Lat/lon center of every hex in `regions`, inverted from the H3 id."""
    import h3

    sub = hexgrid[hexgrid["region"].isin(regions)]
    ll = [h3.cell_to_latlng(h) for h in sub["hex_id"]]
    return pd.DataFrame({
        "hex_id": sub["hex_id"].to_numpy(),
        "region": sub["region"].to_numpy(),
        "lat": [a for a, _ in ll],
        "lon": [b for _, b in ll],
    })


def _catalog():
    import planetary_computer as pc
    import pystac_client

    return pystac_client.Client.open(STAC_URL, modifier=pc.sign_inplace)


def fetch_region_year(
    catalog,
    centroids: pd.DataFrame,
    region: str,
    season_year: int,
    *,
    season: str = "JJA",
    lag_months: int = 3,
    half_win_m: int = HALF_WIN_M,
    verbose: bool = True,
) -> pd.DataFrame | None:
    """One checkpoint unit: pre-season hex means for a region-year.

    Returns tidy `(hex_id, season_year, season, season_idx, ndvi, evi, n_px)`, or
    None if the fetch failed — the caller records the gap and continues.

    The composites in the pre-season window are averaged per hex. A hex whose
    window returns no valid pixels is emitted as NaN rather than dropped, so a
    coverage gap stays visible downstream instead of silently shrinking the panel.
    """
    import pyproj
    import rioxarray  # noqa: F401  (registers the .rio accessor)

    sub = centroids[centroids["region"] == region]
    if sub.empty:
        return None

    window = preseason_months(season, season_year, lag_months)
    start, end = window[0], window[-1] + pd.offsets.MonthEnd(1)

    lon0, lat0 = sub["lon"].min(), sub["lat"].min()
    lon1, lat1 = sub["lon"].max(), sub["lat"].max()
    pad = 0.3
    try:
        search = catalog.search(
            collections=[COLLECTION],
            bbox=[lon0 - pad, lat0 - pad, lon1 + pad, lat1 + pad],
            datetime=f"{start:%Y-%m-%d}/{end:%Y-%m-%d}",
        )
        items = list(search.items())
    except Exception as e:
        print(f"    {region[:24]:24} {season_year} SEARCH FAILED: "
              f"{type(e).__name__}: {e}", flush=True)
        return None
    if not items:
        return None

    # Accumulate per hex across composites: sum and count, so the mean is a
    # pixel-weighted average over the whole window rather than a mean of means.
    acc: dict[str, dict[str, float]] = {
        h: {"ndvi": 0.0, "evi": 0.0, "n": 0.0} for h in sub["hex_id"]
    }

    # Windowed reads, NOT a full-array load. These are cloud-optimised GeoTIFFs,
    # so `.sel(...).values` fetches only the byte ranges covering the requested
    # window: measured at ~0.00s against 3.85s to materialise the full
    # 2400x2400 tile. An earlier version loaded each raster once and indexed it
    # in NumPy on the theory that per-hex reads were the bottleneck; that made a
    # region-year *slower* (74s -> 170s), because the full load costs ~5000x a
    # single windowed read and there are only ~140-1429 hexes to amortise it
    # over. The real cost driver is the number of rasters, not the number of
    # hexes -- 1,429 hexes took 273s against 170s for 140.
    hex_ids = sub["hex_id"].to_numpy()
    lats = sub["lat"].to_numpy()
    lons = sub["lon"].to_numpy()

    for item in items:
        for asset_key, col in ASSETS.items():
            if asset_key not in item.assets:
                continue
            try:
                import rioxarray
                da = rioxarray.open_rasterio(item.assets[asset_key].href, masked=True)
            except Exception:
                continue

            transformer = pyproj.Transformer.from_crs(4326, da.rio.crs, always_xy=True)
            xs, ys = transformer.transform(lons, lats)

            for hid, x, y in zip(hex_ids, xs, ys):
                try:
                    win = da.sel(x=slice(x - half_win_m, x + half_win_m),
                                 y=slice(y + half_win_m, y - half_win_m)).values
                except Exception:
                    continue
                v = win[np.isfinite(win)]
                if v.size == 0:
                    continue
                acc[hid][col] += float(v.sum()) * NDVI_SCALE
                if col == "ndvi":
                    acc[hid]["n"] += v.size
            del da

    rows = []
    for hid, a in acc.items():
        n = a["n"]
        rows.append({
            "hex_id": hid,
            "season_year": season_year,
            "season": season,
            "season_idx": season_index(season, season_year),
            "ndvi": a["ndvi"] / n if n else np.nan,
            "evi": a["evi"] / n if n else np.nan,
            "n_px": int(n),
        })
    out = pd.DataFrame(rows)
    if verbose:
        ok = out["ndvi"].notna().sum()
        print(f"    {region[:24]:24} {season_year}: {ok}/{len(out)} hexes, "
              f"{len(items)} composites", flush=True)
    return out


def build(
    data_dir: Path,
    *,
    regions: Sequence[str] = FOREST_REGIONS,
    years: Iterable[int] = range(2000, 2021),
    season: str = "JJA",
    lag_months: int = 3,
    out_name: str = "hex_season_ndvi.parquet",
    cache_dir: Path | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """Fetch pre-season NDVI/EVI for every region-year and write the panel.

    Resumable at (region, season_year) granularity. Re-run to fill any units that
    failed; delete `cache_dir` to force a clean refetch.
    """
    cache_dir = data_dir / CACHE_NAME if cache_dir is None else cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    hexgrid = pd.read_parquet(data_dir / "hex_grid_res5.parquet")
    centroids = hex_centroids(hexgrid, regions)
    years = list(years)

    if verbose:
        print(f"regions: {len(regions)} | hexes: {len(centroids):,}")
        print(f"units: {len(regions) * len(years)} (region x season_year)")
        print(f"checkpoints: {cache_dir}", flush=True)

    catalog = _catalog()
    frames, failures = [], []

    for region in regions:
        slug = region.split("/")[0].replace(" ", "_")[:24]
        if verbose:
            print(f"\n{region}", flush=True)
        for year in years:
            ckpt = cache_dir / f"{slug}_{year}.parquet"
            if ckpt.exists():
                frames.append(pd.read_parquet(ckpt))
                if verbose:
                    print(f"    {region[:24]:24} {year}: cached", flush=True)
                continue

            got = fetch_region_year(
                catalog, centroids, region, year,
                season=season, lag_months=lag_months, verbose=verbose,
            )
            if got is None or got.empty:
                failures.append((region, year))
                continue
            tmp = ckpt.with_suffix(".parquet.tmp")
            got.to_parquet(tmp, index=False)
            tmp.replace(ckpt)
            frames.append(got)

    if not frames:
        raise RuntimeError("no region-year completed; nothing to write")

    panel = pd.concat(frames, ignore_index=True)
    panel = panel.sort_values(["hex_id", "season_idx"]).reset_index(drop=True)
    out_path = data_dir / out_name
    panel.to_parquet(out_path, index=False)

    if verbose:
        print(f"\nwrote {out_path}  {panel.shape}")
        print(f"hexes {panel['hex_id'].nunique():,} | "
              f"years {panel['season_year'].min()}-{panel['season_year'].max()}")
        if failures:
            print(f"INCOMPLETE — {len(failures)} unit(s) failed; re-run to fill: "
                  f"{failures[:6]}{'...' if len(failures) > 6 else ''}")
    return panel


def _self_check() -> None:
    """Assert the pre-season window rule; the DJF trap is checked upstream."""
    import terraclimate as tc

    tc._self_check()

    # JJA 2015 with a 3-month lag must be Mar/Apr/May 2015 — never June, which
    # would read vegetation from inside the target season.
    w = preseason_months("JJA", 2015, 3)
    assert [m.month for m in w] == [3, 4, 5], f"pre-season window wrong: {w}"
    assert all(m.year == 2015 for m in w), f"pre-season year wrong: {w}"
    assert max(w) < pd.Timestamp(2015, 6, 1), "window overlaps the target season"

    print("hex_ndvi._self_check passed")


if __name__ == "__main__":
    _self_check()
