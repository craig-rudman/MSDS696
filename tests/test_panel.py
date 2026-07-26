"""Tests for `src/panel.py`.

The synthetic half exercises the coarse mapping and the dedup-don't-sum rule on a
frame small enough to state the right answer by hand. The `requires_data` half
pins each target builder's row count and values against the numbers the notebooks
printed pre-refactor -- the differing populations across branches are load-bearing
(07 computes its split masks on the Natural-positive subset), so they are asserted
rather than assumed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from config import ProjectConfig
from panel import RegionSeasonPanel


# ==========================================================================
# Synthetic
# ==========================================================================
@pytest.fixture
def tiny_cfg() -> ProjectConfig:
    """Boundary rule targets season_idx 0 only, so the fixture stays small."""
    return ProjectConfig(partial_winters=(0,))


@pytest.fixture
def tiny_rsc() -> pd.DataFrame:
    """Three cells x three causes, with the awkward cases represented.

    R1/JJA/idx2 : Natural 100 ac, Arson 40, Other 10  -> resolved 150, missing 50
    R2/JJA/idx2 : Natural 0,      Arson 30, Other 0   -> resolved  30, missing  0
    R1/DJF/idx0 : partial winter, must be dropped by the boundary rule
    """
    rows = []
    for region, season, idx, year, missing, causes in [
        ("R1", "JJA", 2, 1992, 50.0, {"Natural": 100.0, "Arson/incendiarism": 40.0, "Other causes": 10.0}),
        ("R2", "JJA", 2, 1992, 0.0, {"Natural": 0.0, "Arson/incendiarism": 30.0, "Other causes": 0.0}),
        ("R1", "DJF", 0, 1992, 7.0, {"Natural": 5.0, "Arson/incendiarism": 5.0, "Other causes": 0.0}),
    ]:
        cell_acres = sum(causes.values())
        for cause, acres in causes.items():
            rows.append({
                "region": region, "season": season, "season_idx": idx, "season_year": year,
                "cause": cause, "acres": acres, "fires": int(acres // 10),
                "cell_acres": cell_acres, "missing_acres": missing, "missing_fires": missing // 10,
                "missing_acre_frac": missing / (missing + cell_acres) if (missing + cell_acres) else np.nan,
            })
    return pd.DataFrame(rows)


def test_boundary_rule_drops_partial_winter(tiny_rsc, tiny_cfg):
    panel = RegionSeasonPanel(tiny_rsc, tiny_cfg)
    assert panel.cells_dropped == 1
    assert not panel.rsc["season_idx"].isin(tiny_cfg.partial_winters).any()


def test_coarse_mapping_puts_other_causes_in_human(tiny_rsc, tiny_cfg):
    """'Other causes' is a RESOLVED determination, so it belongs to Human."""
    panel = RegionSeasonPanel(tiny_rsc, tiny_cfg)
    mapping = panel.rsc.drop_duplicates("cause").set_index("cause")["coarse"]
    assert mapping["Natural"] == "Natural"
    assert mapping["Arson/incendiarism"] == "Human"
    assert mapping["Other causes"] == "Human"


def test_tier1_shares_on_total_acres_denominator(tiny_rsc, tiny_cfg):
    """R1/JJA: human 50, natural 100, unknown 50 of 200 total."""
    panel = RegionSeasonPanel(tiny_rsc, tiny_cfg)
    t1 = panel.tier1_composition().set_index(["region", "season"])
    row = t1.loc[("R1", "JJA")]
    assert row["total_ac"] == pytest.approx(200.0)
    assert row["human"] == pytest.approx(0.25)     # 40 + 10
    assert row["natural"] == pytest.approx(0.50)
    assert row["unknown"] == pytest.approx(0.25)
    assert np.allclose(t1[["human", "natural", "unknown"]].sum(axis=1), 1.0)


def test_unknown_mass_is_deduplicated_not_summed(tiny_rsc, tiny_cfg):
    """The 12x-inflation trap, on a frame where the wrong answer is obvious.

    R1/JJA has missing_acres=50 repeated across 3 cause rows. Summing yields 150
    and would push total_ac to 300; deduplicating yields the correct 50 / 200.
    """
    panel = RegionSeasonPanel(tiny_rsc, tiny_cfg)
    t1 = panel.tier1_composition().set_index(["region", "season"])
    assert t1.loc[("R1", "JJA"), "unknown_ac"] == pytest.approx(50.0)

    naive_sum = tiny_rsc[tiny_rsc["season_idx"] == 2]
    naive_sum = naive_sum[naive_sum["region"] == "R1"]["missing_acres"].sum()
    assert naive_sum == pytest.approx(150.0)  # what the wrong reduction would give


def test_non_constant_missing_acres_is_rejected(tiny_rsc, tiny_cfg):
    """Deduplication is only valid because the column is constant within a cell."""
    corrupted = tiny_rsc.copy()
    corrupted.loc[0, "missing_acres"] = 999.0
    with pytest.raises(AssertionError, match="non-constant"):
        RegionSeasonPanel(corrupted, tiny_cfg)


def test_human_shares_use_human_only_denominator(tiny_rsc, tiny_cfg):
    """R1/JJA human burn is 50 ac (40 arson + 10 other) -- lightning excluded."""
    panel = RegionSeasonPanel(tiny_rsc, tiny_cfg)
    hc, cols = panel.human_subcause_shares()
    assert "sh_Natural" not in cols
    row = hc.set_index(["region", "season"]).loc[("R1", "JJA")]
    assert row["human_total_ac"] == pytest.approx(50.0)
    assert row["sh_Arson/incendiarism"] == pytest.approx(0.8)
    assert row["sh_Other causes"] == pytest.approx(0.2)
    assert np.allclose(hc[cols].sum(axis=1), 1.0)


def test_cell_with_no_human_burn_is_dropped_from_human_branch():
    """A composition needs a positive denominator."""
    rows = [{"region": "R", "season": "JJA", "season_idx": 2, "season_year": 1992,
             "cause": c, "acres": a, "fires": 1, "cell_acres": 10.0,
             "missing_acres": 0.0, "missing_fires": 0, "missing_acre_frac": 0.0}
            for c, a in [("Natural", 10.0), ("Arson/incendiarism", 0.0)]]
    panel = RegionSeasonPanel(pd.DataFrame(rows), ProjectConfig(partial_winters=()))
    hc, _ = panel.human_subcause_shares()
    assert len(hc) == 0


def test_natural_acres_keeps_zero_cells(tiny_rsc, tiny_cfg):
    """Filtering to nat_ac > 0 is the caller's job -- 07 needs the unfiltered frame
    to compute its masks on the positive subset itself."""
    panel = RegionSeasonPanel(tiny_rsc, tiny_cfg)
    nat = panel.natural_acres()
    assert len(nat) == 2
    assert nat.set_index("region").loc["R2", "nat_ac"] == pytest.approx(0.0)


def test_attribution_quality_fraction_and_nat_share(tiny_rsc, tiny_cfg):
    panel = RegionSeasonPanel(tiny_rsc, tiny_cfg)
    q = panel.attribution_quality().set_index(["region", "season"])
    r1 = q.loc[("R1", "JJA")]
    assert r1["missing_acre_frac"] == pytest.approx(0.25)   # 50 / 200
    assert r1["nat_share"] == pytest.approx(0.50)           # 100 / 200


def test_targets_are_sorted_for_the_trailing_engine(tiny_rsc, tiny_cfg):
    """Every builder must return a frame the trailing predictors will accept."""
    from trailing import assert_sorted

    panel = RegionSeasonPanel(tiny_rsc, tiny_cfg)
    hc, _ = panel.human_subcause_shares()
    for frame in (panel.tier1_composition(), hc,
                  panel.natural_acres(), panel.attribution_quality()):
        assert_sorted(frame)   # must not raise


# ==========================================================================
# Against the real panel
# ==========================================================================
@pytest.mark.requires_data
def test_boundary_rule_matches_notebook_counts(agg, cfg):
    panel = RegionSeasonPanel(agg, cfg)
    assert panel.cells_before == 10276
    assert panel.cells_after == 10135
    assert panel.cells_dropped == 141


@pytest.mark.requires_data
def test_target_populations_differ_as_designed(agg, cfg):
    """The four builders return DIFFERENT row counts. That is the design.

    Unifying them would change 07's numbers, since its train/test masks are
    computed on the Natural-positive subset.
    """
    panel = RegionSeasonPanel(agg, cfg)
    hc, _ = panel.human_subcause_shares()
    nat = panel.natural_acres()

    assert len(panel.tier1_composition()) == 10135
    assert len(hc) == 9924
    assert len(nat) == 10135
    assert int((nat["nat_ac"] > 0).sum()) == 6662
    assert len(panel.attribution_quality()) == 10135


@pytest.mark.requires_data
def test_class_snapshot_matches_notebook(agg, cfg):
    """58.9% Natural / 22.6% Human / 18.5% Unknown of 179.12M acres."""
    snap = RegionSeasonPanel(agg, cfg).class_acre_snapshot()
    assert snap["acres"].sum() / 1e6 == pytest.approx(179.12, abs=0.01)
    assert snap.loc["Natural", "share"] == pytest.approx(0.589, abs=0.001)
    assert snap.loc["Human", "share"] == pytest.approx(0.226, abs=0.001)
    assert snap.loc["Unknown", "share"] == pytest.approx(0.185, abs=0.001)


@pytest.mark.requires_data
def test_dedup_key_choice_is_immaterial(agg, cfg):
    """`_per_cell` keys on (region, season_idx); the notebooks variously used that
    or all four cell keys. season_idx determines season and season_year, so the two
    must agree -- verified rather than assumed."""
    panel = RegionSeasonPanel(agg, cfg)
    narrow = panel.rsc.drop_duplicates(["region", "season_idx"])["missing_acres"].sum()
    wide = panel.rsc.drop_duplicates(list(cfg.cell_keys))["missing_acres"].sum()
    assert narrow == pytest.approx(wide)


@pytest.mark.requires_data
def test_tier1_reproduces_the_feature_table_targets(agg, features, cfg):
    """The panel's Tier-1 targets must equal the ones already in the parquet."""
    panel = RegionSeasonPanel(agg, cfg)
    t1 = panel.tier1_composition(with_counts=True)
    key = ["region", "season", "season_idx"]
    merged = t1.merge(features, on=key, how="inner", suffixes=("_panel", "_disk"))
    assert len(merged) == len(features)

    for c in cfg.tier1_classes:
        pd.testing.assert_series_equal(
            merged[f"{c}_panel"], merged[f"{c}_disk"], check_names=False, obj=c)
    pd.testing.assert_series_equal(
        merged["log_total_panel"], merged["log_total_disk"], check_names=False)
    pd.testing.assert_series_equal(
        merged["total_ac_panel"], merged["total_ac_disk"], check_names=False)


@pytest.mark.requires_data
def test_merge_keys_keep_stable_dtypes(agg, cfg):
    """Guards a silent failure mode: if a builder returned `season` as a category
    while the parquet reads it back as object, the floor merges in 06/08 would
    yield all-NaN and the head-to-head would compare against nothing."""
    panel = RegionSeasonPanel(agg, cfg)
    hc, _ = panel.human_subcause_shares()
    for frame in (panel.tier1_composition(), hc,
                  panel.natural_acres(), panel.attribution_quality()):
        assert frame["region"].dtype == agg["region"].dtype
        assert frame["season"].dtype == agg["season"].dtype
        assert frame["season_idx"].dtype == agg["season_idx"].dtype


@pytest.mark.requires_data
def test_human_branch_acre_weighted_mix(agg, cfg):
    """Arson 26.5% / Equipment 24.4% / Debris 19.1% -- the orientation table."""
    panel = RegionSeasonPanel(agg, cfg)
    hc, cols = panel.human_subcause_shares()
    mix = hc[cols].mul(hc["human_total_ac"], axis=0).sum() / hc["human_total_ac"].sum()
    assert mix["sh_Arson/incendiarism"] * 100 == pytest.approx(26.5, abs=0.05)
    assert mix["sh_Equipment and vehicle use"] * 100 == pytest.approx(24.4, abs=0.05)
    assert mix["sh_Debris and open burning"] * 100 == pytest.approx(19.1, abs=0.05)


@pytest.mark.requires_data
def test_unknown_branch_negative_correlation_holds(agg, cfg):
    """The W4 correction: missing share correlates NEGATIVELY with Natural share
    across ecoregions (Pearson about -0.64), so the Unknown mass sits in
    human-dominated regions, not the high-Natural West."""
    panel = RegionSeasonPanel(agg, cfg)
    cell = panel.attribution_quality()
    reg = cell.groupby("region").agg(
        nat=("Natural", "sum"), hum=("Human", "sum"), miss=("missing_acres", "sum")).reset_index()
    reg["tot"] = reg["nat"] + reg["hum"] + reg["miss"]
    reg = reg[reg["tot"] > 0]
    pearson = (reg["nat"] / reg["tot"]).corr(reg["miss"] / reg["tot"])
    assert pearson == pytest.approx(-0.636, abs=0.005)
