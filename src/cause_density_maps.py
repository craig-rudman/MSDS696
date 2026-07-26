"""Point-density (hexbin) maps of wildfire location by cause, CONUS.

Extracted from an EDA experiment that asked whether the *spatial* distribution
of Missing-cause fires resembles that of Natural-cause fires (a circumstantial
check on the "Missing bucket absorbs would-be Natural fires" hypothesis). The
experiment was pulled from the notebook once the inquiry turned to *when and
through whom* the Missing bucket grew (an agency x year concentration question);
this module preserves the mapping method so the pooled geographic view can be
regenerated on demand without living in the notebook.

The loader also serves the ecoregion concentration analysis in the notebook:
each CONUS point is labeled with cause, fire year, and its EPA Level III
ecoregion (US_L3NAME) via spatial join, and cached so downstream region x year
aggregation is instant on reruns.

Two performance affordances, both material at ~2.3M rows:
  * a cheap vectorized bounding-box pre-filter drops AK/HI/PR and far-flung
    points before the spatial join, so the join runs only on the CONUS-bbox
    remainder;
  * the labeled CONUS points are cached to a parquet the first call writes, so
    later calls skip the geometry work entirely.

Honesty conventions consistent with the rest of the project:
  * the two panels share ONE color scale, so a color means the same fire count
    in both -- the panels are directly comparable rather than each self-scaled;
  * the map shows raw geography only. It does NOT, on its own, establish
    absorption: spatial co-location is necessary but not sufficient, and
    differential missingness is itself spatial, so similarity can be a reporting
    artifact. Read it as a locator, not a test.

Paths resolve relative to the project root so the module works whether called
from notebook/ or src/.
"""
from __future__ import annotations

import sqlite3
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LogNorm

# --- project paths (module lives in <root>/src) ---
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "FPA_FOD_20221014.sqlite"
ECO_PATH = ROOT / "data" / "us_eco_l3_state_boundaries" / "us_eco_l3_state_boundaries.shp"
# Cache carries cause + FIRE_YEAR + joined ecoregion (US_L3NAME) + geometry. The
# filename is versioned (v2) so an older 2-column cache is never mistaken for this
# richer schema.
CACHE_PATH = ROOT / "data" / "fires_conus_cache_v2.parquet"
IMG_DIR = ROOT / "img"

MISSING = "Missing data/not specified/undetermined"
GRIDSIZE = 90  # hexbin resolution


def load_conus_points(use_cache: bool = True):
    """Return (geo_conus, eco_boundary): CONUS fire points labeled by cause,
    fire year, and EPA Level III ecoregion, plus the dissolved CONUS boundary
    used as the geographic reference layer.

    `geo_conus` is a GeoDataFrame with columns NWCG_GENERAL_CAUSE, FIRE_YEAR,
    US_L3NAME, and geometry, in the ecoregion shapefile's CRS. Membership in
    CONUS is defined by joining to an ecoregion: a point that lands in an L3
    polygon is in-CONUS, so the spatial join both labels the region and drops
    AK/HI/PR in one step. A cheap vectorized bounding-box pre-filter runs first
    to shrink the join input from ~2.3M rows to the CONUS-bbox remainder. On the
    first call (or use_cache=False) the result is cached to CACHE_PATH; later
    calls load the cache.
    """
    eco_l3 = (
        gpd.read_file(ECO_PATH)[["US_L3NAME", "geometry"]]
        .dissolve("US_L3NAME")
        .reset_index()
    )
    eco_boundary = eco_l3.dissolve()  # single CONUS outline for the reference layer

    if use_cache and CACHE_PATH.exists():
        return gpd.read_parquet(CACHE_PATH), eco_boundary

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT NWCG_GENERAL_CAUSE, FIRE_YEAR, LATITUDE, LONGITUDE FROM Fires", conn
        )

    # Cheap bbox pre-filter (vectorized, no geometry engine) to drop AK/HI/PR and
    # any far-flung points before the spatial join -- shrinks the join input from
    # all ~2.3M rows down to only those near the CONUS bbox.
    minx, miny, maxx, maxy = eco_boundary.to_crs("EPSG:4326").total_bounds
    bbox_mask = df["LONGITUDE"].between(minx, maxx) & df["LATITUDE"].between(miny, maxy)
    candidates = df.loc[
        bbox_mask, ["NWCG_GENERAL_CAUSE", "FIRE_YEAR", "LATITUDE", "LONGITUDE"]
    ].dropna(subset=["LATITUDE", "LONGITUDE"])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pts = gpd.GeoDataFrame(
            candidates,
            geometry=gpd.points_from_xy(candidates["LONGITUDE"], candidates["LATITUDE"]),
            crs="EPSG:4326",
        ).to_crs(eco_l3.crs)
        # sjoin uses a spatial index (faster than within() vs a dissolved boundary)
        # and labels each point with its ecoregion in the same pass.
        joined = gpd.sjoin(pts, eco_l3, how="left", predicate="within")

    # Points that joined to an ecoregion are in-CONUS; the rest fall outside.
    geo_conus = joined.loc[
        joined["US_L3NAME"].notna(),
        ["NWCG_GENERAL_CAUSE", "FIRE_YEAR", "US_L3NAME", "geometry"],
    ].reset_index(drop=True)

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    geo_conus.to_parquet(CACHE_PATH)
    return geo_conus, eco_boundary


def render_cause_density(geo_conus, eco_boundary, causes=("Natural", MISSING),
                         save=True, filename="cause_density_conus.png", dpi=130):
    """Side-by-side hexbin density maps for the given causes, shared color scale.

    `causes` is an ordered pair of NWCG_GENERAL_CAUSE values (defaults to Natural
    vs Missing). Returns the figure.
    """
    minx, miny, maxx, maxy = eco_boundary.total_bounds
    extent = (minx, maxx, miny, maxy)
    map_aspect = (maxy - miny) / (maxx - minx)  # height / width of one CONUS panel

    # Size the figure to the map's true aspect so set_aspect("equal") does not leave
    # a tall empty band (which would float the titles and drop the colorbar into
    # whitespace). A dedicated short bottom row holds the shared colorbar.
    panel_w = 6.6
    fig_w = panel_w * 2 + 0.6
    map_h = panel_w * map_aspect
    fig = plt.figure(figsize=(fig_w, map_h + 1.0))
    gs = fig.add_gridspec(2, 2, height_ratios=[map_h, 0.35], hspace=0.05, wspace=0.05)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1], sharex=ax_a, sharey=ax_a)
    cax = fig.add_subplot(gs[1, :])

    subsets = [geo_conus.loc[geo_conus["NWCG_GENERAL_CAUSE"] == c] for c in causes]
    panels = list(zip(causes, subsets, (ax_a, ax_b)))

    # Shared color scale: hexbin normalizes to each panel's own max by default, which
    # would make the same color mean different counts per panel. Bin both first to find
    # the global per-hex max, then re-draw with one LogNorm so a color means one count.
    peak = 1
    for _, pts, ax in panels:
        hb = ax.hexbin(pts.geometry.x, pts.geometry.y, gridsize=GRIDSIZE,
                       extent=extent, mincnt=1)
        peak = max(peak, hb.get_array().max())
        hb.remove()  # discard the probe; the real draw with the shared norm follows

    shared_norm = LogNorm(vmin=1, vmax=peak)
    last_hb = None
    for cause, pts, ax in panels:
        eco_boundary.boundary.plot(ax=ax, color="#c9c8c3", linewidth=0.8, zorder=1)
        last_hb = ax.hexbin(
            pts.geometry.x, pts.geometry.y, gridsize=GRIDSIZE, extent=extent,
            norm=shared_norm, cmap="viridis", mincnt=1, zorder=2,
        )
        label = "Missing-cause fires" if cause == MISSING else f"{cause}-cause fires"
        ax.set_title(f"{label}  (n={len(pts):,})", fontsize=12, loc="left")
        ax.set_axis_off()
        ax.set_aspect("equal")
        ax.margins(0.01)

    fig.colorbar(last_hb, cax=cax, orientation="horizontal",
                 label="Fires per hex (log scale, shared across panels)")
    fig.suptitle("Fire density by cause, CONUS, 1992-2020", fontsize=13, x=0.01, ha="left")

    if save:
        IMG_DIR.mkdir(exist_ok=True)
        fig.savefig(IMG_DIR / filename, dpi=dpi, bbox_inches="tight")
    return fig
