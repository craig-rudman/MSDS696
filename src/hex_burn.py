"""Distribute each fire's acreage across an H3 hexgrid — area, not point.

The primitive the W5 hexgrid probe rests on. It exists because of one defect in
FPA-FOD that only becomes material below ecoregion grain:

    the record stores a fire as a POINT, but FIRE_SIZE describes an AREA.

At EPA Level III grain that error mostly stays inside the polygon, so the
published region-season numbers are unaffected. At hex grain it becomes the
dominant artifact: a 2.8M-acre fire spans dozens of res-5 hexes (a res-5 hex is
~62,494 acres), yet the record credits every one of those acres to the single hex
containing the ignition point. A hex-level burned-area target built that way
measures point-attribution error, not fire behavior — so it would be measuring
the defect, not the phenomenon.

The fix is a join, not a new dataset
------------------------------------
FPA-FOD carries `MTBS_ID`, a foreign key into the MTBS burned-area perimeters.
It resolves for only 0.6% of fires — but those fires hold **81.6% of all burned
acres** nationally, and **96.0% of acres in the three W5 proof-of-concept
ecoregions** over the MODIS era. The complement is not a problem: the 2.29M
point-only fires average 14 acres, which is far smaller than a res-5 hex, so
crediting them wholly to their containing hex is accurate rather than a
concession.

Hence the hybrid rule implemented here:

    perimeter-backed fire -> split acres across hexes by intersected area
    point-only fire       -> all acres to the containing hex

Acre conservation is the invariant
----------------------------------
For every fire the per-hex weights sum to 1, so the distributed acres sum back to
that fire's `FIRE_SIZE`. This is deliberate and load-bearing: it means a hex panel
built from this frame reconciles **exactly** to `region_season_cause.parquet`, and
any failure of that reconciliation is a bug here rather than a modeling choice.

The weights come from the perimeter's *shape* but the magnitude always comes from
FPA-FOD's `FIRE_SIZE`. MTBS `burnbndac` agrees with computed polygon area to ~0.1%
in EPSG:5070, but the two sources are not identical and `FIRE_SIZE` is the quantity
every published project number is denominated in. Rescaling to `FIRE_SIZE` keeps
this module a *redistribution* of existing acres and never a restatement of them.

CRS discipline
--------------
All area arithmetic happens in **EPSG:5070** (CONUS Albers equal-area). Computing
intersection areas in a geographic CRS (EPSG:4269, MTBS's native) would weight
hexes by a latitude-varying factor and quietly bias the split. H3 cell boundaries
are generated in lat/lon and reprojected to match, never the reverse.

The CRS is a **parameter**, not a constant, because EPSG:5070 is invalid at
Alaska's latitudes and Alaska carries 20.4% of all burned acres — too much to
drop from a national build. A national grid therefore runs each landmass in its
own equal-area CRS (`ALBERS_CONUS` / `ALBERS_AK`) and concatenates, exactly as
`cleaning.EcoregionJoiner` already does for the ecoregion join. `hex_id` is
globally unique in H3, so the concatenated grid needs no re-keying; only the
geometry column is CRS-specific, which is why `build_national_grid` returns
`land_area_acres` (already reduced to a number) alongside it.
"""
from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd

# Equal-area CRS for every area computation. See "CRS discipline" above.
# EPSG:5070 (CONUS Albers) is not valid at Alaska's latitudes; EPSG:3338 (Alaska
# Albers) is. `cleaning.EcoregionJoiner` already splits by landmass for the same
# reason, so a national build runs each landmass in its own CRS and concatenates.
# Alaska is not optional at national scope: it holds 20.4% of all burned acres.
ALBERS_CONUS = 5070
ALBERS_AK = 3338

# MTBS ships perimeters in NAD83 geographic.
MTBS_CRS = 4269

SQM_PER_ACRE = 4046.8564224

# H3 resolutions used by the probe. res 5 is the MVP grain; res 4 is the coarse
# comparator and res 6 the escalation if res 5 proves too sparse. Areas are
# measured from h3 4.5.0 rather than derived from edge length, which is how an
# earlier draft of the plan got them ~3x wrong.
HEX_RES_COARSE = 4   # ~1,770 km2  (~437,462 ac), 26.1 km edge
HEX_RES_MVP = 5      # ~  252.9 km2 (~ 62,494 ac),  9.9 km edge
HEX_RES_FINE = 6     # ~   36.1 km2 (~  8,928 ac),  3.7 km edge


def hex_area_acres(resolution: int) -> float:
    """Average area of an H3 cell at `resolution`, in acres."""
    import h3

    return h3.average_hexagon_area(resolution, unit="km^2") * 1e6 / SQM_PER_ACRE


def hexes_for_polygon(geom, resolution: int) -> list[str]:
    """H3 cells covering a single (Multi)Polygon given in EPSG:4326.

    Uses the h3 **v4** API (`h3shape_to_cells`); v3's `polyfill` took a different
    argument order and a GeoJSON dict, so a v3-era call silently returns nothing
    here rather than raising.
    """
    import h3

    shp = h3.geo_to_h3shape(geom.__geo_interface__)
    return list(h3.h3shape_to_cells(shp, resolution))


def build_hexgrid(regions, resolution: int = HEX_RES_MVP, *, crs: int = ALBERS_CONUS):
    """Hexgrid covering `regions`, clipped to their boundary.

    Parameters
    ----------
    regions
        GeoDataFrame with a `region` column, one or more rows per region.
    resolution
        H3 resolution. Default is the MVP grain (res 5).

    Returns
    -------
    GeoDataFrame in EPSG:5070 with `hex_id`, `region`, and `land_area_acres` —
    the area of the hex **inside** the region boundary, not the full hex. Edge
    hexes are partially covered, and using the full hex area as a denominator
    would understate `burned_frac` exactly at the boundary. A hex spanning two
    regions is assigned to the region holding more of its area, so `hex_id` stays
    a unique key.
    """
    import geopandas as gpd
    from shapely.geometry import Polygon

    import h3

    reg = regions.to_crs(4326)
    # The AK Level III layer ships at least one self-intersecting polygon in SE
    # Alaska; dissolving it raises a GEOS side-location conflict at
    # (-135.338, 57.255). `src/terraclimate.py` dodged this by not dissolving at
    # all, but the hexgrid genuinely needs one geometry per region to tessellate
    # and clip against. So repair first: `make_valid` on the invalid rows only,
    # which is a no-op on the CONUS layer.
    bad = ~reg.geometry.is_valid
    if bad.any():
        reg = reg.copy()
        reg.loc[bad, "geometry"] = reg.loc[bad, "geometry"].make_valid()
        reg = reg[~reg.geometry.is_empty & reg.geometry.notna()]
    dissolved = reg.dissolve(by="region", as_index=False)[["region", "geometry"]]

    rows: list[dict] = []
    for _, r in dissolved.iterrows():
        for hid in hexes_for_polygon(r.geometry, resolution):
            boundary = h3.cell_to_boundary(hid)          # ((lat, lng), ...)
            rows.append(
                {
                    "hex_id": hid,
                    "region": r["region"],
                    "geometry": Polygon([(lng, lat) for lat, lng in boundary]),
                }
            )

    grid = gpd.GeoDataFrame(rows, geometry="geometry", crs=4326).to_crs(crs)
    bounds = dissolved.to_crs(crs)

    # Clip to the region boundary so edge hexes carry only their land area.
    clipped = gpd.overlay(grid, bounds[["region", "geometry"]], how="intersection")
    clipped = clipped[clipped["region_1"] == clipped["region_2"]].copy()
    clipped["land_area_acres"] = clipped.geometry.area / SQM_PER_ACRE
    clipped = clipped.rename(columns={"region_1": "region"}).drop(columns=["region_2"])

    # A hex may straddle two regions; keep it once, with the region holding most of it.
    clipped = (
        clipped.sort_values("land_area_acres", ascending=False)
        .drop_duplicates(subset="hex_id", keep="first")
        .reset_index(drop=True)
    )
    return clipped[["hex_id", "region", "land_area_acres", "geometry"]]


def _repair(gdf):
    """Make geometries valid in place-ish; MTBS ships a small number of invalid ones.

    Measured on an 800-row sample: 1 invalid polygon. `buffer(0)` is the standard
    repair and is a no-op on already-valid geometry, so it is applied unconditionally
    rather than behind a check that would itself have to scan every row.
    """
    out = gdf.copy()
    bad = ~out.geometry.is_valid
    if bad.any():
        out.loc[bad, "geometry"] = out.loc[bad, "geometry"].buffer(0)
    return out[~out.geometry.is_empty & out.geometry.notna()]


def distribute_perimeter_acres(perims, hexgrid, *, id_col: str = "event_id",
                               acres_col: str = "FIRE_SIZE",
                               crs: int | None = None) -> pd.DataFrame:
    """Split each perimeter's acreage across the hexes it intersects.

    `perims` must carry `id_col`, `acres_col` (the FPA-FOD `FIRE_SIZE` to be
    redistributed) and a geometry. Returns tidy rows:
    `(fire_key, hex_id, hex_acres, w)`.

    The weight `w` is intersected area / total intersected area — normalized over
    the *intersection*, not the raw polygon. That distinction matters at the study
    boundary: a fire straddling the region edge has part of its footprint outside
    the hexgrid, and normalizing by raw polygon area would silently drop those
    acres. Normalizing by intersected area instead keeps every fire's acres summing
    to `FIRE_SIZE` within the modeled extent, and the share falling outside is
    reported separately by `coverage_report`.
    """
    import geopandas as gpd

    p = _repair(perims.to_crs(crs or hexgrid.crs))
    g = hexgrid[["hex_id", "geometry"]]

    inter = gpd.overlay(
        p[[id_col, acres_col, "geometry"]], g, how="intersection", keep_geom_type=True
    )
    if inter.empty:
        return pd.DataFrame(columns=["fire_key", "hex_id", "hex_acres", "w"])

    inter["_a"] = inter.geometry.area
    tot = inter.groupby(id_col)["_a"].transform("sum")
    inter = inter[tot > 0].copy()
    inter["w"] = inter["_a"] / inter.groupby(id_col)["_a"].transform("sum")
    inter["hex_acres"] = inter["w"] * inter[acres_col]

    out = inter[[id_col, "hex_id", "hex_acres", "w"]].rename(columns={id_col: "fire_key"})
    return out.reset_index(drop=True)


def assign_point_acres(fires: pd.DataFrame, hexgrid, *, resolution: int = HEX_RES_MVP,
                       id_col: str = "FOD_ID", acres_col: str = "FIRE_SIZE",
                       lat_col: str = "LATITUDE", lon_col: str = "LONGITUDE") -> pd.DataFrame:
    """Assign each point-only fire's full acreage to its containing hex.

    Uses H3's direct lat/lng -> cell lookup rather than a spatial join: it is exact
    for point containment, and orders of magnitude cheaper over ~2M rows. Fires
    whose cell is not in `hexgrid` (outside the study regions) are dropped, and are
    accounted for by `coverage_report`.
    """
    import h3

    f = fires[[id_col, acres_col, lat_col, lon_col]].dropna(subset=[lat_col, lon_col])
    hid = [
        h3.latlng_to_cell(la, lo, resolution)
        for la, lo in zip(f[lat_col].to_numpy(), f[lon_col].to_numpy())
    ]
    out = pd.DataFrame(
        {"fire_key": f[id_col].to_numpy(), "hex_id": hid, "hex_acres": f[acres_col].to_numpy()}
    )
    out["w"] = 1.0
    return out[out["hex_id"].isin(set(hexgrid["hex_id"]))].reset_index(drop=True)


def build_hex_acres(
    fires: pd.DataFrame,
    perims,
    hexgrid,
    *,
    resolution: int = HEX_RES_MVP,
    mtbs_id_col: str = "MTBS_ID",
    fod_id_col: str = "FOD_ID",
    acres_col: str = "FIRE_SIZE",
    event_id_col: str = "event_id",
) -> pd.DataFrame:
    """The hybrid target: perimeter-distributed where possible, point elsewhere.

    Returns `(fire_key, hex_id, hex_acres, w, source)` with
    `source in {"perimeter", "point"}`. `fire_key` is the FPA-FOD `FOD_ID` in both
    branches, so the result joins back to the fire record uniformly.

    A fire is routed to the perimeter branch **only if** its `MTBS_ID` actually
    resolves to a geometry. IDs that do not resolve — 478 agency-prefixed ones
    (`FS-`, `NP-`, `BL-`) that use a different scheme entirely, plus 666 geo-format
    IDs absent from the published set — fall back to point attribution rather than
    being dropped. Silently losing them would remove ~6.7M acres nationally, which
    is precisely the large-fire mass the probe is about.

    Fire complexes: many fires, one perimeter
    -----------------------------------------
    An `MTBS_ID` is **not unique per fire**. When several fires merge into one
    incident, MTBS maps the complex once while FPA-FOD keeps the constituent fires
    as separate rows. Nationally 381 IDs are shared by 959 fires carrying **14.3%
    of MTBS-linked acres**; in the three W5 regions it is 62 IDs and **34.6% of
    perimeter-linked acres**. The 2020 August Complex (`CA3966012280920200817`)
    alone binds 8 FPA-FOD rows spanning 1,220 to 589,368 acres.

    The naive join gives *every* constituent fire the *whole* complex footprint, so
    a 1,220-acre fire is spread across the same 26 hexes as a 589,368-acre one.
    Acre conservation still passes — each fire's weights sum to 1 — so the invariant
    does not catch it; only the implausible hex spans do.

    The rule implemented here: fires sharing a perimeter burned that footprint
    **once, collectively**. Their acres are pooled, distributed across the hexes by
    intersected area, and then split back to the individual fires **pro rata by
    `FIRE_SIZE`**. Each fire keeps its own acreage, the complex footprint is counted
    once, and the per-hex totals are unchanged by how many rows the record happens
    to use for one incident.
    """
    f = fires.copy()
    f["_mid"] = f[mtbs_id_col].fillna("").astype(str).str.strip() if mtbs_id_col in f else ""

    pm = perims.copy()
    pm[event_id_col] = pm[event_id_col].astype(str).str.strip()
    resolvable = set(pm[event_id_col])

    is_perim = f["_mid"].isin(resolvable)

    # --- perimeter branch ---
    # Pool acres per PERIMETER first (a complex is one footprint, however many
    # FPA-FOD rows describe it), distribute that pooled total across hexes, then
    # split each hex's acres back to the constituent fires pro rata by FIRE_SIZE.
    link = f.loc[is_perim, [fod_id_col, "_mid", acres_col]].copy()
    pooled = link.groupby("_mid", as_index=False)[acres_col].sum()

    pgeo = pm.merge(pooled, left_on=event_id_col, right_on="_mid", how="inner")
    per_perim = distribute_perimeter_acres(
        pgeo, hexgrid, id_col="_mid", acres_col=acres_col
    ).rename(columns={"fire_key": "_mid"})

    if per_perim.empty:
        perim_rows = pd.DataFrame(columns=["fire_key", "hex_id", "hex_acres", "w"])
    else:
        # pro-rata share of each constituent fire within its perimeter group
        link["_share"] = link[acres_col] / link.groupby("_mid")[acres_col].transform("sum")
        perim_rows = per_perim.merge(link[[fod_id_col, "_mid", "_share"]], on="_mid", how="inner")
        perim_rows["hex_acres"] = perim_rows["hex_acres"] * perim_rows["_share"]
        perim_rows["w"] = perim_rows["w"] * perim_rows["_share"]
        perim_rows = perim_rows[[fod_id_col, "hex_id", "hex_acres", "w"]].rename(
            columns={fod_id_col: "fire_key"}
        )
    perim_rows["source"] = "perimeter"

    # --- point branch: everything else, including unresolved MTBS_IDs ---
    point_rows = assign_point_acres(
        f.loc[~is_perim], hexgrid, resolution=resolution,
        id_col=fod_id_col, acres_col=acres_col,
    )
    point_rows["source"] = "point"

    return pd.concat([perim_rows, point_rows], ignore_index=True)


def coverage_report(fires: pd.DataFrame, hex_acres: pd.DataFrame, *,
                    acres_col: str = "FIRE_SIZE") -> dict:
    """Acre accounting: what went in, what landed on the grid, what fell outside.

    Returned rather than printed so a notebook can assert on it. `acres_outside`
    is expected to be non-zero — fires near the region boundary have footprints
    that leave the study extent — but it must be *small* and it must be **stated**,
    never silently absorbed.
    """
    total_in = float(fires[acres_col].sum())
    landed = float(hex_acres["hex_acres"].sum())
    by_src = hex_acres.groupby("source")["hex_acres"].sum().to_dict()
    return {
        "acres_in": total_in,
        "acres_on_grid": landed,
        "acres_outside": total_in - landed,
        "pct_on_grid": 100.0 * landed / total_in if total_in else float("nan"),
        "acres_perimeter": float(by_src.get("perimeter", 0.0)),
        "acres_point": float(by_src.get("point", 0.0)),
        "pct_perimeter": 100.0 * by_src.get("perimeter", 0.0) / landed if landed else float("nan"),
        "n_rows": int(len(hex_acres)),
        "n_hexes_touched": int(hex_acres["hex_id"].nunique()),
    }


def assert_acres_conserved(fires: pd.DataFrame, hex_acres: pd.DataFrame, *,
                           fod_id_col: str = "FOD_ID", acres_col: str = "FIRE_SIZE",
                           rtol: float = 1e-6) -> None:
    """Verify each fire's distributed acres sum back to its `FIRE_SIZE`.

    This is the module's central invariant and the reason a hex panel reconciles to
    `region_season_cause.parquet`. Fires whose footprint leaves the grid are excluded
    from the check — their acres legitimately do not all land — and are reported by
    `coverage_report` instead.

    Raises `AssertionError` naming the worst offender, because a silent violation
    here would corrupt every downstream number while still looking plausible.
    """
    got = hex_acres.groupby("fire_key")["hex_acres"].sum()
    want = fires.set_index(fod_id_col)[acres_col]
    common = got.index.intersection(want.index)
    g, w = got.loc[common], want.loc[common]

    # Only fires fully inside the grid are expected to conserve exactly.
    inside = g >= w * (1 - 1e-3)
    if not inside.any():
        return
    diff = (g[inside] - w[inside]).abs()
    rel = diff / w[inside].where(w[inside] > 0, np.nan)
    worst = rel.idxmax()
    assert rel.max() <= rtol, (
        f"acre conservation violated: fire {worst} has {g.loc[worst]:,.4f} "
        f"distributed acres vs FIRE_SIZE {w.loc[worst]:,.4f} "
        f"(rel err {rel.max():.2e} > {rtol:.1e})"
    )


def build_national_grid(conus_layer, ak_layer, resolution: int = HEX_RES_MVP,
                        *, verbose: bool = True):
    """Hexgrid over every EPA Level III ecoregion in CONUS **and** Alaska.

    Each landmass is tessellated and clipped in its own equal-area CRS, then the
    two are concatenated with geometry dropped. Geometry is deliberately NOT
    returned: the two halves are in different CRSs, so a single GeoDataFrame would
    silently mix EPSG:5070 and EPSG:3338 coordinates in one column. Callers that
    need shapes should rebuild one landmass at a time with `build_hexgrid`.

    Returns a plain DataFrame: `hex_id`, `region`, `land_area_acres`, `landmass`.
    """
    import geopandas as gpd

    out = []
    for layer, crs, tag in ((conus_layer, ALBERS_CONUS, "CONUS"),
                            (ak_layer, ALBERS_AK, "AK")):
        eco = gpd.read_file(layer) if not hasattr(layer, "crs") else layer
        eco = eco.rename(columns={"US_L3NAME": "region"})[["region", "geometry"]]
        g = build_hexgrid(eco, resolution, crs=crs)
        g = pd.DataFrame(g.drop(columns="geometry"))
        g["landmass"] = tag
        out.append(g)
        if verbose:
            print(f"  {tag}: {len(g):,} hexes over {g['region'].nunique()} regions "
                  f"({g['land_area_acres'].sum() / 1e6:,.1f}M acres)", flush=True)

    grid = pd.concat(out, ignore_index=True)
    # H3 ids are globally unique, so a duplicate across landmasses would mean a
    # region was assigned to both layers -- a real error, not a tie to break.
    dupes = grid["hex_id"].duplicated().sum()
    assert dupes == 0, f"{dupes} hex_ids appear in both landmasses"
    return grid


def build_national_acres(fires: pd.DataFrame, perims, conus_layer, ak_layer,
                         resolution: int = HEX_RES_MVP, *, verbose: bool = True):
    """Perimeter-corrected burned acres per hex, nationally.

    Runs `build_hex_acres` once per landmass so every intersection happens in a
    valid equal-area CRS, then concatenates. Returns
    `(hex_acres, grid, coverage)` where `coverage` is the per-landmass acre
    accounting from `coverage_report`.
    """
    import geopandas as gpd

    ak_states = {"AK"}
    frames, grids, cov = [], [], {}

    for layer, crs, tag, mask in (
        (conus_layer, ALBERS_CONUS, "CONUS", ~fires["STATE"].isin(ak_states)),
        (ak_layer, ALBERS_AK, "AK", fires["STATE"].isin(ak_states)),
    ):
        sub = fires[mask]
        if sub.empty:
            continue
        eco = gpd.read_file(layer) if not hasattr(layer, "crs") else layer
        eco = eco.rename(columns={"US_L3NAME": "region"})[["region", "geometry"]]
        eco = eco[eco["region"].isin(set(sub["region"]))]

        g = build_hexgrid(eco, resolution, crs=crs)
        want = set(sub["MTBS_ID"].fillna("").astype(str).str.strip()) - {""}
        pm = perims[perims["event_id"].astype(str).str.strip().isin(want)]

        ha = build_hex_acres(sub, pm, g, resolution=resolution)
        ha["landmass"] = tag
        frames.append(ha)
        gg = pd.DataFrame(g.drop(columns="geometry"))
        gg["landmass"] = tag
        grids.append(gg)
        cov[tag] = coverage_report(sub, ha)
        if verbose:
            c = cov[tag]
            print(f"  {tag}: {len(g):,} hexes | {c['pct_on_grid']:.2f}% of acres on grid "
                  f"| {c['pct_perimeter']:.1f}% perimeter-derived", flush=True)

    return (pd.concat(frames, ignore_index=True),
            pd.concat(grids, ignore_index=True),
            cov)
