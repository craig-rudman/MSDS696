"""Tests for `src/cleaning.py`.

Mostly synthetic, and deliberately so: every function here has a failure mode that
a 2.3M-row aggregate assertion can detect but not localize. A hand-built frame with
`2005-12-15` in it pins the December rule exactly; two toy polygon layers in
different CRSs test the shared-edge and offshore-stray cases that are ~0.001% of
the real data; a 3-cell frame makes the densification and the 100%-missing "orphan"
cell obvious.

One data-backed test does the heavy lifting for free: `build_aggregate` is re-run
from the *fire-level* parquet and compared to the aggregate on disk, which
re-verifies the entire second half of the cleaning pipeline in seconds without
touching the 918 MB SQLite or repeating a spatial join.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cleaning import (
    EcoregionJoiner,
    apply_exclusion,
    build_aggregate,
    derive_temporal_spine,
    exclusion_mask,
    series_support,
)
from config import MISSING, ProjectConfig


# ==========================================================================
# Exclusion
# ==========================================================================
@pytest.fixture
def exclusion_frame() -> pd.DataFrame:
    """One row per case the rule has to handle, including the PR+IA overlap."""
    return pd.DataFrame({
        "FOD_ID": range(1, 8),
        "STATE": ["PR", "HI", "CA", "PR", "AK", "TX", "OR"],
        "NWCG_REPORTING_AGENCY": ["ST/L", "ST/L", "IA", "IA", "ST/L", "FS", "BLM"],
    })


def test_exclusion_drops_pr_hi_and_ia(exclusion_frame):
    kept = apply_exclusion(exclusion_frame)
    assert kept["FOD_ID"].tolist() == [5, 6, 7]     # AK, TX, OR survive


def test_exclusion_counts_overlap_once(exclusion_frame):
    """FOD_ID 4 is both PR and IA; the mask must not double-count it."""
    mask = exclusion_mask(exclusion_frame)
    assert mask.sum() == 4
    pr_hi = exclusion_frame["STATE"].isin(["PR", "HI"])
    ia = exclusion_frame["NWCG_REPORTING_AGENCY"] == "IA"
    assert (pr_hi & ia).sum() == 1


def test_exclusion_retains_alaska(exclusion_frame):
    """AK is deliberately kept -- losing it silently is the failure 04 prevents."""
    assert (apply_exclusion(exclusion_frame)["STATE"] == "AK").sum() == 1


# ==========================================================================
# Temporal spine -- the December rule
# ==========================================================================
def test_december_belongs_to_next_years_winter():
    """Dec 2005 is part of winter 2006. This is the trap the whole spine rests on."""
    df = pd.DataFrame({"DISCOVERY_DATE": ["2005-12-15", "2006-01-15", "2006-02-28"]})
    out = derive_temporal_spine(df)
    assert out["season"].tolist() == ["DJF", "DJF", "DJF"]
    assert out["season_year"].tolist() == [2006, 2006, 2006]
    # All three are the same winter, so all three share one season_idx.
    assert out["season_idx"].nunique() == 1


def test_season_labels_by_month():
    dates = [f"2000-{m:02d}-15" for m in range(1, 13)]
    out = derive_temporal_spine(pd.DataFrame({"DISCOVERY_DATE": dates}))
    assert out["season"].tolist() == (
        ["DJF", "DJF"] + ["MAM"] * 3 + ["JJA"] * 3 + ["SON"] * 3 + ["DJF"])


def test_record_boundary_winters():
    """The two partial winters the boundary rule later drops.

    1992-01-01 has no preceding December (record start); 2020-12-31 rolls into
    season_year 2021, whose Jan-Feb is past the record end.
    """
    out = derive_temporal_spine(pd.DataFrame(
        {"DISCOVERY_DATE": ["1992-01-01", "2020-12-31"]}))
    cfg = ProjectConfig()
    assert out["season_idx"].tolist() == [0, 116]
    assert all(cfg.is_partial_winter(i) for i in out["season_idx"])


def test_season_idx_arithmetic_is_monotonic():
    """+4 must be the same season next year -- the lag arithmetic depends on it."""
    out = derive_temporal_spine(pd.DataFrame(
        {"DISCOVERY_DATE": ["2000-07-15", "2001-07-15"]}))
    assert out["season_idx"].diff().iloc[1] == 4


def test_leap_day_and_mixed_date_formats():
    """`format="mixed"` handles the source's inconsistent date strings."""
    out = derive_temporal_spine(pd.DataFrame(
        {"DISCOVERY_DATE": ["2000-02-29", "3/15/2001", "2001-06-01 00:00:00"]}))
    assert out["season"].tolist() == ["DJF", "MAM", "JJA"]
    assert out["season_year"].tolist() == [2000, 2001, 2001]


def test_unparseable_date_raises():
    with pytest.raises(ValueError, match="unparseable"):
        derive_temporal_spine(pd.DataFrame({"DISCOVERY_DATE": ["not a date"]}))


def test_fire_year_is_not_used_and_not_modified():
    """A 2006-12-31 discovery filed under FIRE_YEAR 2007 is a source quirk; the
    keys follow the date and FIRE_YEAR is preserved untouched."""
    df = pd.DataFrame({"DISCOVERY_DATE": ["2006-12-31"], "FIRE_YEAR": [2007]})
    out = derive_temporal_spine(df)
    assert out["season_year"].iloc[0] == 2007      # Dec 2006 -> winter 2007
    assert out["FIRE_YEAR"].iloc[0] == 2007        # unchanged
    df2 = pd.DataFrame({"DISCOVERY_DATE": ["2006-11-30"], "FIRE_YEAR": [2007]})
    assert derive_temporal_spine(df2)["season_year"].iloc[0] == 2006   # date wins


# ==========================================================================
# The aggregate
# ==========================================================================
@pytest.fixture
def geo_fires() -> pd.DataFrame:
    """Fire-level rows covering the aggregate's awkward cases.

    R1/JJA/1992 : Natural 100, Arson 40, plus a 25-acre missing-cause fire
    R2/JJA/1992 : Arson 30 only -> the Natural column must densify to zero
    R3/JJA/1992 : missing-cause ONLY -> the documented 'orphan' cell, no row at all
    """
    rows = [
        ("R1", "Natural", 100.0), ("R1", "Arson/incendiarism", 40.0), ("R1", MISSING, 25.0),
        ("R2", "Arson/incendiarism", 30.0),
        ("R3", MISSING, 500.0),
    ]
    return pd.DataFrame([
        {"region": r, "season": "JJA", "season_year": 1992, "season_idx": 2,
         "NWCG_GENERAL_CAUSE": c, "FIRE_SIZE": a}
        for r, c, a in rows
    ])


def test_aggregate_densifies_the_cause_vocabulary(geo_fires):
    """Every cell carries every attributed cause, so shares sum to 1."""
    agg = build_aggregate(geo_fires)
    assert set(agg["cause"]) == {"Natural", "Arson/incendiarism"}
    assert agg.groupby("region")["cause"].size().eq(2).all()
    r2 = agg[(agg["region"] == "R2") & (agg["cause"] == "Natural")]
    assert r2["acres"].iloc[0] == 0.0      # densified zero, not a missing row


def test_aggregate_excludes_missing_from_the_cause_column(geo_fires):
    assert MISSING not in set(build_aggregate(geo_fires)["cause"])


def test_cause_share_is_within_attributed_acres(geo_fires):
    """R1: 140 attributed acres -> Natural 100/140, Arson 40/140. The 25 missing
    acres are NOT in the denominator."""
    agg = build_aggregate(geo_fires).set_index(["region", "cause"])
    assert agg.loc[("R1", "Natural"), "cause_share"] == pytest.approx(100 / 140)
    assert agg.loc[("R1", "Arson/incendiarism"), "cause_share"] == pytest.approx(40 / 140)
    assert agg.loc[("R1", "Natural"), "cell_acres"] == pytest.approx(140.0)


def test_missing_weight_is_carried_per_cell(geo_fires):
    """R1 has 25 missing acres against 140 attributed -> frac 25/165."""
    agg = build_aggregate(geo_fires).set_index(["region", "cause"])
    assert agg.loc[("R1", "Natural"), "missing_acres"] == pytest.approx(25.0)
    assert agg.loc[("R1", "Natural"), "missing_acre_frac"] == pytest.approx(25 / 165)
    # R2 has no missing fires at all.
    assert agg.loc[("R2", "Natural"), "missing_acres"] == pytest.approx(0.0)


def test_missing_columns_are_constant_within_a_cell(geo_fires):
    """The property that makes downstream dedup correct rather than arbitrary."""
    agg = build_aggregate(geo_fires)
    nuniq = agg.groupby("region")[["missing_acres", "missing_fires"]].nunique()
    assert nuniq.eq(1).all().all()


def test_all_missing_cell_is_an_orphan(geo_fires):
    """R3 is 100% missing-cause, so it has no cause composition and no row.

    This is the documented, accepted gap -- asserted so it stays deliberate.
    """
    agg = build_aggregate(geo_fires)
    assert "R3" not in set(agg["region"])


def test_series_support_counts_years_with_fire():
    fires = pd.DataFrame([
        {"region": "R1", "season": "JJA", "season_year": y, "season_idx": (y - 1992) * 4 + 2,
         "NWCG_GENERAL_CAUSE": "Natural", "FIRE_SIZE": 10.0}
        for y in (1992, 1993, 1995)
    ])
    support = series_support(build_aggregate(fires))
    assert support.loc[0, "years_with_fire"] == 3
    assert support.loc[0, "total_acres"] == pytest.approx(30.0)


# ==========================================================================
# The two-layer spatial join
# ==========================================================================
@pytest.fixture
def toy_layers():
    """Two adjacent unit squares per landmass, in DIFFERENT CRSs.

    CONUS layer in EPSG:4326; AK layer in EPSG:3338 (Alaska Albers), which is the
    case that matters -- if the joiner reprojected the polygons instead of the
    points, or skipped the reprojection, the AK join would silently match nothing.
    """
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import Polygon

    conus = gpd.GeoDataFrame(
        {
            "US_L3NAME": ["West", "East"],
            # 'East' carries the EPA's uncertainty annotation, which must be stripped
            # so both squares roll up to ONE Level-II parent.
            "NA_L2NAME": ["TOY PARENT", "TOY PARENT (?)"],
            "geometry": [
                Polygon([(-120, 35), (-119, 35), (-119, 36), (-120, 36)]),
                Polygon([(-119, 35), (-118, 35), (-118, 36), (-119, 36)]),
            ],
        },
        crs="EPSG:4326",
    )
    ak = gpd.GeoDataFrame(
        {
            "US_L3NAME": ["Toy Alaska"],
            "NA_L2NAME": ["TOY BOREAL"],
            "geometry": [Polygon([(-150, 64), (-148, 64), (-148, 65), (-150, 65)])],
        },
        crs="EPSG:4326",
    ).to_crs("EPSG:3338")
    return conus, ak


def test_join_matches_both_layers_in_their_own_crs(toy_layers):
    conus, ak = toy_layers
    fires = pd.DataFrame({
        "FOD_ID": [1, 2, 3],
        "STATE": ["CA", "CA", "AK"],
        "LONGITUDE": [-119.5, -118.5, -149.0],
        "LATITUDE": [35.5, 35.5, 64.5],
    })
    out, crs_info = EcoregionJoiner(conus, ak).join(fires)
    assert out.set_index("FOD_ID")["region"].to_dict() == {
        1: "West", 2: "East", 3: "Toy Alaska"}
    assert crs_info["ak_crs"] != crs_info["conus_crs"]


def test_join_strips_the_l2_uncertainty_annotation(toy_layers):
    """Left in place, "(?)" splits one parent in two and a roll-up double-counts."""
    conus, ak = toy_layers
    fires = pd.DataFrame({
        "FOD_ID": [1, 2], "STATE": ["CA", "CA"],
        "LONGITUDE": [-119.5, -118.5], "LATITUDE": [35.5, 35.5],
    })
    out, _ = EcoregionJoiner(conus, ak).join(fires)
    assert set(out["na_l2name"]) == {"TOY PARENT"}          # not two variants


def test_point_on_a_shared_edge_yields_one_row(toy_layers):
    """A point exactly on the shared x=-119 edge must produce exactly one output row.

    Documents the actual `predicate="within"` semantics, which are easy to get wrong:
    a boundary point is not *strictly inside* either polygon, so `within` matches
    NEITHER and the fire falls through as unmatched (verified directly: `within` ->
    0 matches, `intersects` -> 2). The production code uses `within` deliberately;
    the invariant that matters at this seam is one row per FOD_ID either way, so a
    fire can never be duplicated and have its acres counted twice.
    """
    conus, ak = toy_layers
    fires = pd.DataFrame({
        "FOD_ID": [1], "STATE": ["CA"], "LONGITUDE": [-119.0], "LATITUDE": [35.5],
    })
    out, _ = EcoregionJoiner(conus, ak).join(fires)
    assert len(out) == 1
    assert out["FOD_ID"].is_unique


def test_duplicate_polygon_match_is_deduplicated(toy_layers):
    """The dedup guard itself: overlapping polygons must not duplicate a fire.

    The real layers ship polygons split by state, so a point can land inside two
    records of the same layer. Here two genuinely overlapping polygons make the
    double-match happen under `within`, which is the case
    `~index.duplicated(keep="first")` exists to absorb.
    """
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import Polygon

    _, ak = toy_layers
    overlapping = gpd.GeoDataFrame(
        {
            "US_L3NAME": ["Split A", "Split B"],
            "NA_L2NAME": ["TOY PARENT", "TOY PARENT"],
            "geometry": [
                Polygon([(-120, 35), (-118, 35), (-118, 36), (-120, 36)]),
                Polygon([(-120, 35), (-118, 35), (-118, 36), (-120, 36)]),
            ],
        },
        crs="EPSG:4326",
    )
    fires = pd.DataFrame({
        "FOD_ID": [1], "STATE": ["CA"], "LONGITUDE": [-119.0], "LATITUDE": [35.5],
    })
    out, _ = EcoregionJoiner(overlapping, ak).join(fires)
    assert len(out) == 1
    assert out["region"].iloc[0] == "Split A"      # first match wins


def test_offshore_stray_gets_a_null_region(toy_layers):
    """Unmatched points are expected; they must be null, not silently dropped."""
    conus, ak = toy_layers
    fires = pd.DataFrame({
        "FOD_ID": [1, 2], "STATE": ["CA", "CA"],
        "LONGITUDE": [-119.5, -130.0], "LATITUDE": [35.5, 35.5],
    })
    out, _ = EcoregionJoiner(conus, ak).join(fires)
    assert len(out) == 2
    assert out.set_index("FOD_ID").loc[2, "region"] is None or pd.isna(
        out.set_index("FOD_ID").loc[2, "region"])


def test_join_rejects_an_l3_region_with_two_l2_parents(toy_layers):
    """Guards the Level-II fallback: the roll-up would be ill-defined."""
    conus, ak = toy_layers
    broken = conus.copy()
    broken["US_L3NAME"] = ["Same", "Same"]          # one L3 name...
    broken["NA_L2NAME"] = ["PARENT A", "PARENT B"]  # ...under two L2 parents
    fires = pd.DataFrame({
        "FOD_ID": [1, 2], "STATE": ["CA", "CA"],
        "LONGITUDE": [-119.5, -118.5], "LATITUDE": [35.5, 35.5],
    })
    with pytest.raises(AssertionError, match="L2 parent"):
        EcoregionJoiner(broken, ak).join(fires)


# ==========================================================================
# Against the real data -- no SQLite, no spatial join
# ==========================================================================
@pytest.mark.requires_data
@pytest.mark.slow
def test_build_aggregate_reproduces_the_artifact(fires, agg, cfg):
    """Rebuild the aggregate from fires_clean.parquet and compare to disk.

    This re-verifies the entire second half of 04_cleaning in seconds: the
    fire-level artifact already carries the region and season keys, so no SQLite
    read and no spatial join are needed.
    """
    geo = fires[fires["region"].notna()]
    rebuilt = build_aggregate(geo, cfg)

    keys = ["region", "season_year", "season", "season_idx", "cause"]
    left = rebuilt.sort_values(keys).reset_index(drop=True)
    right = agg.sort_values(keys).reset_index(drop=True)

    assert len(left) == len(right), f"row count {len(left):,} vs {len(right):,}"
    for col in ["acres", "fires", "cell_acres", "cause_share",
                "missing_acres", "missing_fires", "missing_acre_frac"]:
        pd.testing.assert_series_equal(
            left[col], right[col], check_names=False, check_dtype=False, obj=col)


@pytest.mark.requires_data
def test_temporal_spine_reproduces_the_artifact_keys(fires, cfg):
    """The spine derived here must equal the keys already in fires_clean.parquet."""
    sample = fires.sample(min(50_000, len(fires)), random_state=0)
    out = derive_temporal_spine(sample[["DISCOVERY_DATE"]], cfg)
    assert (out["season"].to_numpy() == sample["season"].to_numpy()).all()
    assert (out["season_year"].to_numpy() == sample["season_year"].to_numpy()).all()
    assert (out["season_idx"].to_numpy() == sample["season_idx"].to_numpy()).all()


@pytest.mark.requires_data
def test_exclusion_already_applied_to_the_artifact(fires):
    assert not exclusion_mask(fires).any()
