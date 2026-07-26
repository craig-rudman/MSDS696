"""Raw FPA-FOD -> the two analysis artifacts.

The computation behind `04_cleaning.ipynb`, extracted so its edge cases can be
tested on small synthetic inputs instead of only being averaged over 2.3M rows.
The notebook keeps every `print()` — the row accounting, the per-layer join
quality table, the Level-III support check, and the 40-assertion validation
roster are the graded deliverable. Only the transformations move here.

**Nothing in this module writes.** The `to_parquet` calls stay in the notebook,
where the student can see them, so importing this module can never overwrite an
artifact as a side effect.

Why synthetic tests matter more than a full re-run
--------------------------------------------------
Each function below has a failure mode that a 2.3M-row aggregate assertion cannot
localize:

* `derive_temporal_spine` — the December rule. Meteorological winter spans
  Dec-Jan-Feb, so December belongs to the winter *ending* the next calendar year.
  An off-by-one shifts every winter cell by a year. The notebook can only assert
  this in bulk; a hand-built frame with `2005-12-15` in it pins it exactly.
* `EcoregionJoiner` — two shapefiles in different CRSs, points on shared polygon
  edges that match twice, offshore strays that match nothing, and the EPA's `(?)`
  uncertainty annotation which, left in place, splits one Level-II parent into two
  literal values and makes a roll-up double-count. The real join takes minutes and
  these cases are ~0.001% of rows; in-memory toy polygons test them in
  milliseconds.
* `build_aggregate` — densification, the NaN placement of `cause_share`, and the
  documented "orphan" cell (a region-season that is 100% missing-cause and
  therefore carries no row at all).

`build_aggregate` is additionally verifiable against the real data for free: it
reads the *fire-level* artifact, which already exists on disk, so the entire
second half of the cleaning pipeline can be re-checked in seconds without
touching the 918 MB SQLite or re-running a spatial join.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import ProjectConfig

# Fields taken from each ecoregion layer. US_L3NAME becomes `region` (the analysis
# grain); NA_L2NAME is the Level-II parent kept as a documented coarser fallback.
ECO_FIELDS = ["US_L3NAME", "NA_L2NAME", "geometry"]

# States/territories and the reporting stream dropped by the documented exclusion.
EXCLUDED_STATES = ("PR", "HI")
EXCLUDED_AGENCY = "IA"


# --------------------------------------------------------------------------
# Exclusion
# --------------------------------------------------------------------------
def exclusion_mask(raw: pd.DataFrame) -> pd.Series:
    """Rows the documented exclusion drops: PR/HI **or** the IA stream.

    Returned as a mask rather than applied, so the notebook can report the two
    components and their overlap separately — the row accounting is part of the
    argument for the drop.

    Alaska is deliberately NOT here. It has no cause-attribution problem; its
    region key comes from the second ecoregion layer.
    """
    return (raw["STATE"].isin(EXCLUDED_STATES)
            | (raw["NWCG_REPORTING_AGENCY"] == EXCLUDED_AGENCY))


def apply_exclusion(raw: pd.DataFrame) -> pd.DataFrame:
    """Drop the no-cause-signal territories and the IA catch-all stream."""
    return raw.loc[~exclusion_mask(raw)].reset_index(drop=True)


# --------------------------------------------------------------------------
# Temporal spine
# --------------------------------------------------------------------------
def derive_temporal_spine(df: pd.DataFrame, cfg: ProjectConfig | None = None,
                          *, date_col: str = "DISCOVERY_DATE") -> pd.DataFrame:
    """Attach `season`, `season_year`, `season_idx`.

    Derived from the discovery *date*, not `DISCOVERY_DOY`, because the
    meteorological season is defined on the calendar month. `FIRE_YEAR` is left
    untouched: the two disagree on a handful of source records (e.g. a 2006-12-31
    discovery filed under FIRE_YEAR 2007), which is a source quirk, and the season
    keys follow the date.

    The December rule: meteorological winter is Dec-Jan-Feb, so December belongs to
    the winter that *ends* the following calendar year — Dec 2005 is part of winter
    2006. `season_idx` is then monotonic with 4 seasons per season-year, so `+1` is
    the next season and `+4` is the same season next year.
    """
    cfg = cfg or ProjectConfig()
    out = df.copy()

    discovered = pd.to_datetime(out[date_col], format="mixed", errors="coerce")
    if discovered.isna().any():
        raise ValueError(f"{discovered.isna().sum():,} unparseable dates in {date_col}")

    month = discovered.dt.month
    season_of_month = {m: "DJF" for m in (12, 1, 2)}
    season_of_month.update({m: "MAM" for m in (3, 4, 5)})
    season_of_month.update({m: "JJA" for m in (6, 7, 8)})
    season_of_month.update({m: "SON" for m in (9, 10, 11)})

    out["season"] = month.map(season_of_month)
    # December rolls forward into the next season-year.
    out["season_year"] = discovered.dt.year.where(month != 12, discovered.dt.year + 1)
    out["season_idx"] = (
        (out["season_year"] - cfg.base_year) * 4 + out["season"].map(dict(cfg.season_order))
    ).astype(int)
    return out


# --------------------------------------------------------------------------
# Region key
# --------------------------------------------------------------------------
class EcoregionJoiner:
    """Point-in-polygon join against the CONUS and Alaska ecoregion layers.

    Two layers because the standard EPA Level III shapefile is explicitly the
    *conterminous* US; Alaska ships separately with its own projection. Each join
    runs in its own layer's CRS, with the fire points reprojected to match — never
    the polygons, which would distort them.
    """

    def __init__(self, conus_layer, ak_layer):
        """Accepts paths or already-loaded GeoDataFrames (the latter for tests)."""
        self.conus_layer = conus_layer
        self.ak_layer = ak_layer

    @staticmethod
    def _clean_l2_names(eco):
        """Strip the EPA's `(?)` uncertainty annotation from Level-II names.

        The CONUS layer marks some Level-II assignments as uncertain with a
        trailing "(?)". Left in place it splits one parent into two literal values
        (e.g. UPPER GILA MOUNTAINS vs "UPPER GILA MOUNTAINS (?)"), which would make
        a Level-II roll-up double-count that parent. The uncertainty is a property
        of the source map, not a distinct region.
        """
        out = eco.copy()
        out["NA_L2NAME"] = (out["NA_L2NAME"].str.replace(r"\s*\(\?\)\s*$", "", regex=True)
                            .str.strip())
        return out

    def _load(self, layer):
        import geopandas as gpd

        eco = gpd.read_file(layer) if not hasattr(layer, "crs") else layer
        return self._clean_l2_names(eco[ECO_FIELDS])

    def _join_one(self, fires: pd.DataFrame, layer):
        import geopandas as gpd

        eco = self._load(layer)
        points = gpd.GeoDataFrame(
            fires[["FOD_ID"]],
            geometry=gpd.points_from_xy(fires["LONGITUDE"], fires["LATITUDE"]),
            crs="EPSG:4326",
        ).to_crs(eco.crs)
        joined = gpd.sjoin(points, eco, how="left", predicate="within")
        # A point exactly on a shared polygon edge matches twice; keep the first.
        joined = joined[~joined.index.duplicated(keep="first")]
        return joined[["FOD_ID", "US_L3NAME", "NA_L2NAME"]], eco.crs

    def join(self, clean: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        """Attach `region` and `na_l2name`. Returns `(frame, crs_info)`.

        Alaska rows go to the AK layer and everything else to the CONUS layer, so a
        silent loss of Alaska in the join — the failure the cleaning step exists to
        prevent — cannot happen unnoticed.
        """
        is_ak = clean["STATE"] == "AK"
        ak_join, ak_crs = self._join_one(clean[is_ak], self.ak_layer)
        conus_join, conus_crs = self._join_one(clean[~is_ak], self.conus_layer)

        eco = pd.concat([conus_join, ak_join], ignore_index=True)
        if not eco["FOD_ID"].is_unique:
            raise AssertionError("duplicate FOD_ID after join -- a fire matched twice")

        out = clean.merge(eco, on="FOD_ID", how="left", validate="one_to_one")
        out = out.rename(columns={"US_L3NAME": "region", "NA_L2NAME": "na_l2name"})

        matched = out["region"].notna()
        multi = out[matched].groupby("region")["na_l2name"].nunique()
        if (multi > 1).any():
            raise AssertionError(
                f"L3 regions with >1 L2 parent: {multi[multi > 1].index.tolist()}")

        return out, {"conus_crs": conus_crs, "ak_crs": ak_crs}


# --------------------------------------------------------------------------
# The analysis grain
# --------------------------------------------------------------------------
def build_aggregate(geo: pd.DataFrame, cfg: ProjectConfig | None = None) -> pd.DataFrame:
    """One row per region x season_year x season x cause.

    `geo` must be geo-matched fire-level rows (`region` non-null). Two conventions
    follow `03_missingness.ipynb`:

    * shares are computed within **attributed** fires, so the Missing category is
      not treated as a cause label;
    * each cell's missing-cause weight is carried alongside (`missing_acres`,
      `missing_fires`, `missing_acre_frac`) so downstream can down-weight poorly
      attributed region-seasons instead of trusting every cell equally.

    The grid is **densified**: every observed region-season carries the full cause
    vocabulary, so shares sum to 1 and an absent cause reads as the zero it is.

    Known and accepted gap: a region-season whose fires are 100% missing-cause has
    no attributed acres, so it gets no row at all and its missing acres are carried
    nowhere. That is by design — a cell with no attributed acres has no cause
    composition to predict — and the notebook quantifies the excluded volume.
    """
    cfg = cfg or ProjectConfig()
    keys = ["region", "season_year", "season", "season_idx"]
    attributed = geo[geo["NWCG_GENERAL_CAUSE"] != cfg.missing]

    agg = (
        attributed.groupby(keys + ["NWCG_GENERAL_CAUSE"], observed=True)
        .agg(acres=("FIRE_SIZE", "sum"), fires=("FIRE_SIZE", "size"))
        .reset_index()
        .rename(columns={"NWCG_GENERAL_CAUSE": "cause"})
    )

    # Densify against the full cause vocabulary.
    causes = sorted(attributed["NWCG_GENERAL_CAUSE"].unique())
    cells = agg[keys].drop_duplicates()
    grid = cells.merge(pd.DataFrame({"cause": causes}), how="cross")
    agg = grid.merge(agg, on=keys + ["cause"], how="left")
    agg[["acres", "fires"]] = agg[["acres", "fires"]].fillna(0)
    agg["fires"] = agg["fires"].astype(int)

    # Cell totals and the within-attributed share (the RQ's target).
    cell_total = agg.groupby(keys, observed=True)["acres"].transform("sum")
    agg["cell_acres"] = cell_total
    agg["cause_share"] = np.where(cell_total > 0, agg["acres"] / cell_total, np.nan)

    # The missing-cause weight, per cell.
    miss = (
        geo[geo["NWCG_GENERAL_CAUSE"] == cfg.missing]
        .groupby(keys, observed=True)
        .agg(missing_acres=("FIRE_SIZE", "sum"), missing_fires=("FIRE_SIZE", "size"))
        .reset_index()
    )
    agg = agg.merge(miss, on=keys, how="left")
    agg[["missing_acres", "missing_fires"]] = agg[["missing_acres", "missing_fires"]].fillna(0)
    agg["missing_acre_frac"] = (
        agg["missing_acres"] / (agg["missing_acres"] + agg["cell_acres"]).replace(0, np.nan)
    )

    agg = agg.sort_values(keys + ["cause"]).reset_index(drop=True)

    nonempty = agg[agg["cell_acres"] > 0].groupby(keys, observed=True)["cause_share"].sum()
    if not np.allclose(nonempty, 1.0):
        bad = int((~np.isclose(nonempty, 1.0)).sum())
        raise AssertionError(f"cause_share does not sum to 1 in {bad} cells")
    return agg


def series_support(agg: pd.DataFrame, group_cols=("region", "season")) -> pd.DataFrame:
    """Years-with-fire per region x season series, and the acres each carries.

    The check that decides whether Level III is a viable grain or the analysis has
    to coarsen to Level II: burned area is tail-driven, so many region-seasons may
    carry too little history to predict.
    """
    keys = ["region", "season_year", "season", "season_idx"]
    cells = agg[keys + ["cell_acres"]].drop_duplicates()
    return (
        cells.assign(has=cells["cell_acres"] > 0)
        .groupby(list(group_cols), observed=True)
        .agg(years_with_fire=("has", "sum"), total_acres=("cell_acres", "sum"))
        .reset_index()
    )
