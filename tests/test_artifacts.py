"""Artifact regression: everything downstream assumes about the pipeline parquets.

Ported from the 176-line validation cell at the end of `04_cleaning.ipynb`. That
cell collects ~40 named assertions via a `check(name, condition, detail)` helper
and reports a PASS/FAIL roster. Here each check becomes its own test, which is a
strict improvement in two ways: pytest isolates failures naturally (no need for
the collect-then-report pattern), and the suite is runnable by an agent at any
time, not only as a side effect of re-executing an expensive notebook.

The notebook cell is deliberately KEPT as-is. Its PASS/FAIL roster is graded
evidence for a human reader; this file is the machine-checkable gate. The
duplication is intentional and the two must agree.

Three checks in the original cannot be expressed against the artifacts alone
because they close over in-memory notebook state -- `len(raw)` and `drop.sum()`
from the SQLite load, which do not exist on disk. Those are marked
`requires_raw` and re-derive the numbers from the source database.

Also here: the content fingerprints captured in Phase 0. Those are what prove a
post-refactor rebuild of the artifacts is content-identical to the pre-refactor
ones, without a byte comparison (parquet writes are not byte-deterministic).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.requires_data


FIRE_REQUIRED = [
    "FOD_ID", "FIRE_YEAR", "STATE", "FIRE_SIZE", "NWCG_GENERAL_CAUSE",
    "region", "na_l2name", "season", "season_year", "season_idx",
]
AGG_REQUIRED = [
    "region", "season_year", "season", "season_idx", "cause", "acres", "fires",
    "cell_acres", "cause_share", "missing_acres", "missing_fires", "missing_acre_frac",
]


# ==========================================================================
# Schema
# ==========================================================================
def test_fires_required_columns(fires):
    missing = sorted(set(FIRE_REQUIRED) - set(fires.columns))
    assert not missing, f"fire-level artifact missing columns: {missing}"


def test_agg_required_columns(agg):
    missing = sorted(set(AGG_REQUIRED) - set(agg.columns))
    assert not missing, f"aggregate missing columns: {missing}"


def test_fod_id_unique_and_non_null(fires):
    assert fires["FOD_ID"].is_unique
    assert fires["FOD_ID"].notna().all()


def test_fires_no_null_analysis_keys(fires):
    """`region` may be null on offshore strays; the rest never may."""
    cols = ["season", "season_year", "season_idx", "FIRE_SIZE"]
    assert fires[cols].notna().all().all()


# ==========================================================================
# The documented exclusion rule
# ==========================================================================
def test_exclusion_no_pr_hi(fires):
    assert not fires["STATE"].isin(["PR", "HI"]).any()


def test_exclusion_no_ia_reporting_stream(fires):
    assert not (fires["NWCG_REPORTING_AGENCY"] == "IA").any()


def test_exclusion_alaska_retained(fires):
    """AK is deliberately kept -- it has no cause-attribution problem.

    Losing Alaska silently in the two-layer spatial join is precisely the failure
    the cleaning notebook exists to prevent, so it is asserted rather than assumed.
    """
    assert (fires["STATE"] == "AK").sum() > 0


# ==========================================================================
# Temporal spine
# ==========================================================================
def test_season_labels_are_the_four_meteorological_seasons(fires, cfg):
    assert set(fires["season"].unique()) == set(cfg.seasons)


def test_season_idx_reconstructible(fires, cfg):
    """season_idx must be a pure function of (season_year, season)."""
    recon = ((fires["season_year"] - fires["season_year"].min()) * 4
             + fires["season"].map(dict(cfg.season_order)))
    assert (recon == fires["season_idx"]).all()


def test_season_idx_contiguous(fires):
    """A gap would silently break the +1 next-season step and the shift(1) lag."""
    present = np.sort(fires["season_idx"].unique())
    assert np.array_equal(present, np.arange(present.min(), present.max() + 1))


def test_season_idx_monotone_in_season_year(fires):
    assert fires.groupby("season_idx")["season_year"].nunique().eq(1).all()


def test_december_rule(fires):
    """December belongs to DJF of the FOLLOWING calendar year.

    Meteorological winter spans Dec-Jan-Feb, so Dec 2005 is part of the winter
    labelled 2006. An off-by-one here shifts every winter cell by a year.
    """
    disc = pd.to_datetime(fires["DISCOVERY_DATE"], format="mixed", errors="coerce")
    dec = disc.dt.month == 12
    assert dec.any(), "no December fires found -- the rule would be untested"
    assert (fires.loc[dec, "season"] == "DJF").all()
    assert (fires.loc[dec, "season_year"] == disc.dt.year[dec] + 1).all()


def test_non_december_season_year_is_discovery_year(fires):
    disc = pd.to_datetime(fires["DISCOVERY_DATE"], format="mixed", errors="coerce")
    dec = disc.dt.month == 12
    assert (fires.loc[~dec, "season_year"] == disc.dt.year[~dec]).all()


def test_season_year_is_pure_function_of_discovery_date(fires):
    """Keys follow DISCOVERY_DATE, never FIRE_YEAR.

    The two disagree on a handful of source records (e.g. a 2006-12-31 discovery
    filed under FIRE_YEAR 2007). That is a source quirk; FIRE_YEAR is preserved
    untouched and the season keys are derived from the date.
    """
    disc = pd.to_datetime(fires["DISCOVERY_DATE"], format="mixed", errors="coerce")
    dec = (disc.dt.month == 12).astype(int)
    assert (fires["season_year"] == disc.dt.year + dec).all()


# ==========================================================================
# Region key (two-layer ecoregion join)
# ==========================================================================
def test_every_l3_region_has_exactly_one_l2_parent(fires):
    """Otherwise a Level II roll-up (the documented fallback grain) is ill-defined."""
    geo = fires[fires["region"].notna()]
    multi = geo.groupby("region")["na_l2name"].nunique()
    assert (multi <= 1).all(), f"L3 regions with >1 L2 parent: {multi[multi > 1].index.tolist()}"


def test_l2_present_wherever_region_is(fires):
    geo = fires[fires["region"].notna()]
    assert geo["na_l2name"].notna().all()


def test_spatial_join_retains_almost_all_burned_acres(fires):
    """Unmatched points should be rare coastal/offshore strays, not real acreage."""
    geo = fires[fires["region"].notna()]
    share = geo["FIRE_SIZE"].sum() / fires["FIRE_SIZE"].sum()
    assert share >= 0.999, f"only {share:.4%} of burned acres matched a region"


def test_alaska_fires_carry_a_region(fires):
    """Proves the second (AK) ecoregion layer actually joined."""
    ak = fires.loc[fires["STATE"] == "AK", "region"]
    assert ak.notna().mean() > 0.97


# ==========================================================================
# Aggregate grain
# ==========================================================================
def test_aggregate_grain_is_unique(agg, cfg):
    keys = ["region", "season_year", "season", "season_idx", "cause"]
    assert not agg.duplicated(keys).any()


def test_missing_cause_excluded_from_cause_column(agg, cfg):
    """The Missing bucket is the Unknown *mass* (missing_acres), not a cause row."""
    assert cfg.missing not in set(agg["cause"].unique())


def test_aggregate_is_dense(agg, cfg):
    """Every cell carries the full cause vocabulary, so shares sum to 1 and an
    absent cause reads as the zero it is."""
    keys = list(cfg.cell_keys)
    n_causes = agg["cause"].nunique()
    assert agg.groupby(keys, observed=True)["cause"].size().eq(n_causes).all()


def test_no_negative_quantities(agg):
    cols = ["acres", "fires", "cell_acres", "missing_acres", "missing_fires"]
    assert (agg[cols] >= 0).all().all()


def test_cause_share_sums_to_one_in_non_empty_cells(agg, cfg):
    keys = list(cfg.cell_keys)
    nonempty = agg[agg["cell_acres"] > 0]
    sums = nonempty.groupby(keys, observed=True)["cause_share"].sum()
    assert np.allclose(sums, 1.0)


def test_cause_share_within_unit_interval(agg):
    nonempty = agg[agg["cell_acres"] > 0]
    assert nonempty["cause_share"].between(0, 1).all()


def test_cause_share_nan_exactly_where_cell_has_no_attributed_acres(agg):
    assert agg["cause_share"].isna().equals(agg["cell_acres"] <= 0)


def test_cell_acres_equals_summed_cause_acres(agg, cfg):
    keys = list(cfg.cell_keys)
    recomputed = agg.groupby(keys, observed=True)["acres"].transform("sum")
    assert np.allclose(recomputed, agg["cell_acres"])


def test_missing_acre_frac_within_unit_interval(agg):
    assert agg["missing_acre_frac"].dropna().between(0, 1).all()


def test_missing_columns_constant_within_a_cell(agg, cfg):
    """The dedup-don't-sum invariant.

    `missing_acres` is a per-cell quantity repeated across the cell's 12 cause
    rows. Downstream code must deduplicate, never sum -- summing inflates the
    Unknown mass 12x and corrupts Tier 1, the feature table, and the Unknown
    branch simultaneously. This asserts the property that makes dedup correct.
    """
    keys = list(cfg.cell_keys)
    nuniq = agg.groupby(keys, observed=True)[["missing_acres", "missing_fires"]].nunique()
    assert nuniq.eq(1).all().all()


# ==========================================================================
# Cross-artifact reconciliation -- ties the two files to each other
# ==========================================================================
def test_attributed_acres_agree_between_artifacts(fires, agg, cfg):
    src = fires[fires["region"].notna()]
    attributed = src[src["NWCG_GENERAL_CAUSE"] != cfg.missing]
    assert np.isclose(agg["acres"].sum(), attributed["FIRE_SIZE"].sum())


def test_attributed_fire_counts_agree_between_artifacts(fires, agg, cfg):
    src = fires[fires["region"].notna()]
    attributed = src[src["NWCG_GENERAL_CAUSE"] != cfg.missing]
    assert agg["fires"].sum() == len(attributed)


def test_per_cell_attributed_acres_agree(fires, agg, cfg):
    """Per-cell, not just in total: a compensating error in the densify step would
    pass a grand-total check but fail here."""
    keys = list(cfg.cell_keys)
    src = fires[fires["region"].notna()]
    attributed = src[src["NWCG_GENERAL_CAUSE"] != cfg.missing]
    by_cell = (attributed.groupby(keys, observed=True)["FIRE_SIZE"].sum()
               .rename("src_acres").reset_index())
    per_cell = (agg.groupby(keys, observed=True)["acres"].sum().rename("agg_acres")
                .reset_index().merge(by_cell, on=keys, how="inner"))
    assert np.allclose(per_cell["agg_acres"], per_cell["src_acres"])


def test_aggregate_covers_exactly_the_non_empty_cells(fires, agg, cfg):
    keys = list(cfg.cell_keys)
    src = fires[fires["region"].notna()]
    attributed = src[src["NWCG_GENERAL_CAUSE"] != cfg.missing]
    by_cell = attributed.groupby(keys, observed=True)["FIRE_SIZE"].sum().reset_index()
    agg_cells = agg[keys].drop_duplicates()
    merged = agg_cells.merge(by_cell, on=keys, how="outer", indicator=True)
    assert (merged["_merge"] == "both").all()


def test_missing_acres_agree_on_covered_cells(fires, agg, cfg):
    keys = list(cfg.cell_keys)
    src = fires[fires["region"].notna()]
    miss = src[src["NWCG_GENERAL_CAUSE"] == cfg.missing]
    cell_key = agg[keys + ["missing_acres"]].drop_duplicates(keys)
    by_cell = (miss.groupby(keys, observed=True)["FIRE_SIZE"].sum()
               .rename("src_missing").reset_index())
    shared = cell_key.merge(by_cell, on=keys, how="inner")
    assert np.allclose(shared["missing_acres"], shared["src_missing"])


def test_orphan_all_missing_cells_are_negligible(fires, agg, cfg):
    """KNOWN AND ACCEPTED GAP, asserted so it stays small.

    A region-season whose fires are 100% missing-cause has no attributed acres,
    so it has no cause composition to predict and gets no row in the aggregate.
    Its missing acres are therefore carried nowhere. That is by design; this
    bounds the excluded volume rather than letting it drift silently upward.
    """
    keys = list(cfg.cell_keys)
    src = fires[fires["region"].notna()]
    miss = src[src["NWCG_GENERAL_CAUSE"] == cfg.missing]
    by_cell = (miss.groupby(keys, observed=True)["FIRE_SIZE"].sum()
               .rename("src_missing").reset_index())
    agg_cells = agg[keys].drop_duplicates()
    orphan = by_cell.merge(agg_cells, on=keys, how="left", indicator=True)
    orphan = orphan[orphan["_merge"] == "left_only"]
    share = orphan["src_missing"].sum() / src["FIRE_SIZE"].sum()
    assert share < 0.001, f"orphan cells now carry {share:.4%} of burned acres"


def test_aggregate_invents_no_missing_acres(fires, agg, cfg):
    keys = list(cfg.cell_keys)
    src = fires[fires["region"].notna()]
    miss = src[src["NWCG_GENERAL_CAUSE"] == cfg.missing]
    cell_key = agg[keys + ["missing_acres"]].drop_duplicates(keys)
    by_cell = (miss.groupby(keys, observed=True)["FIRE_SIZE"].sum()
               .rename("src_missing").reset_index())
    merged = cell_key.merge(by_cell, on=keys, how="left", indicator=True)
    invented = merged.loc[merged["_merge"] == "left_only", "missing_acres"].fillna(0).sum()
    assert np.isclose(invented, 0.0)


def test_aggregate_regions_subset_of_fire_level_regions(fires, agg):
    geo = fires[fires["region"].notna()]
    assert set(agg["region"]) <= set(geo["region"])


def test_cause_vocabulary_matches(fires, agg, cfg):
    src = fires[fires["region"].notna()]
    attributed = src[src["NWCG_GENERAL_CAUSE"] != cfg.missing]
    assert set(agg["cause"]) == set(attributed["NWCG_GENERAL_CAUSE"].unique())


# ==========================================================================
# Feature table
# ==========================================================================
def test_features_one_row_per_cell(features, cfg):
    assert not features.duplicated(["region", "season", "season_idx"]).any()


def test_features_boundary_rule_applied(features, cfg):
    """The partial winters must already be gone, so the feature table and the
    baselines are built on an identical cell set."""
    assert not features["season_idx"].isin(cfg.partial_winters).any()


def test_tier1_targets_sum_to_one(features, cfg):
    classes = list(cfg.tier1_classes)
    assert np.allclose(features[classes].sum(axis=1), 1.0)


def test_first_occurrence_cells_have_nan_features(features):
    """Cells with no prior history carry NaN -- exactly the cells the baselines
    leave unscored. If these diverged, the floor and the learned rung would be
    scored on different populations."""
    no_history = features["f_n_prior"] == 0
    assert (no_history == features["f_log_total_mean"].isna()).all()


# ==========================================================================
# Content fingerprints (Phase 0) -- the post-refactor equivalence gate
# ==========================================================================
@pytest.mark.parametrize("name,fixture_name", [
    ("fires_clean", "fires"),
    ("region_season_cause", "agg"),
    ("region_season_features", "features"),
])
def test_artifact_fingerprint_unchanged(name, fixture_name, fingerprints, request):
    """The artifact still has the same content as when the baseline was captured.

    Compared by row count, schema, an order-independent content hash, and grand
    totals -- not by file bytes, since parquet serialization is not deterministic
    across writes and a byte comparison would false-alarm on an identical rebuild.
    """
    if name not in fingerprints:
        pytest.skip(f"no baseline fingerprint recorded for {name}")
    expected = fingerprints[name]
    df = request.getfixturevalue(fixture_name)

    assert len(df) == expected["n_rows"], (
        f"{name}: row count changed {expected['n_rows']:,} -> {len(df):,}")
    assert list(df.columns) == expected["columns"], f"{name}: column set/order changed"

    actual_hash = int(pd.util.hash_pandas_object(df, index=False).sum())
    assert actual_hash == expected["content_hash"], (
        f"{name}: content hash changed -- some value in the artifact differs")

    for col, want in expected["sums"].items():
        assert np.isclose(float(df[col].sum()), want, rtol=1e-9), f"{name}.{col} sum changed"
    for col, want in expected["nunique"].items():
        assert int(df[col].nunique()) == want, f"{name}.{col} cardinality changed"


# ==========================================================================
# Checks that need the raw source (excluded by default)
# ==========================================================================
@pytest.mark.requires_raw
def test_row_count_matches_raw_minus_documented_drop(fires, cfg):
    """Ported from the notebook check that closed over `len(raw)` and `drop.sum()`.

    Those are in-memory values from the SQLite load, so reproducing this check
    outside the notebook means re-reading the source database.
    """
    import sqlite3

    if not cfg.fires_db.exists():
        pytest.skip("source SQLite not present")
    with sqlite3.connect(f"file:{cfg.fires_db}?mode=ro", uri=True) as conn:
        n_raw = pd.read_sql_query("SELECT COUNT(*) AS n FROM Fires", conn)["n"].iloc[0]
        n_dropped = pd.read_sql_query(
            "SELECT COUNT(*) AS n FROM Fires "
            "WHERE STATE IN ('PR','HI') OR NWCG_REPORTING_AGENCY = 'IA'", conn
        )["n"].iloc[0]
    assert len(fires) == n_raw - n_dropped, (
        f"clean={len(fires):,} but raw={n_raw:,} - dropped={n_dropped:,}")
