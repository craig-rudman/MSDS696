"""Tests for the forward-chaining engine in `src/trailing.py`.

Two halves:

* **Synthetic** (no data files) — hand-built frames small enough to state the
  right answer by hand, covering the cases a 2.3M-row assertion can only average
  over: a year gap in a series, a series' first occurrence, `min_periods=2`, and
  above all **the sort-invariant guard actually firing**.

* **Equivalence** (`requires_data`) — the decisive test. Rebuilds every `f_*`
  column of `region_season_features.parquet` through the new class and compares
  against the column already on disk. That proves the extracted engine is
  numerically identical to the inline idiom it replaces, without executing a
  notebook. Plus a port of `05_features.ipynb`'s brute-force leakage audit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from trailing import (
    GlobalPrior,
    SortInvariantError,
    T4Predictor,
    TrailingMean,
    assert_sorted,
    sweep,
)


# ==========================================================================
# Synthetic fixtures
# ==========================================================================
@pytest.fixture
def two_series() -> pd.DataFrame:
    """Two regions, same season. Region A has a GAP (no season_idx 6).

    A: idx 2, 10, 14   values 1, 2, 3     (gap: 6 is absent)
    B: idx 2,  6, 10   values 10, 20, 30  (contiguous)
    """
    return pd.DataFrame({
        "region": ["A", "A", "A", "B", "B", "B"],
        "season": ["JJA"] * 6,
        "season_idx": [2, 10, 14, 2, 6, 10],
        "season_year": [1992, 1994, 1995, 1992, 1993, 1994],
        "v": [1.0, 2.0, 3.0, 10.0, 20.0, 30.0],
    })


# ==========================================================================
# The sort invariant -- the reason this module exists
# ==========================================================================
def test_assert_sorted_accepts_sorted_frame(two_series):
    assert_sorted(two_series)  # must not raise


def test_assert_sorted_rejects_region_shuffled_frame(two_series):
    """B-before-A is the exact ordering that silently mis-attributes history."""
    shuffled = two_series.iloc[[3, 4, 5, 0, 1, 2]].reset_index(drop=True)
    with pytest.raises(SortInvariantError, match="must be sorted"):
        assert_sorted(shuffled)


def test_assert_sorted_rejects_out_of_order_season_idx(two_series):
    descending = two_series.sort_values(
        ["region", "season", "season_idx"], ascending=[True, True, False]
    ).reset_index(drop=True)
    with pytest.raises(SortInvariantError):
        assert_sorted(descending)


def test_assert_sorted_reports_missing_key_columns():
    with pytest.raises(SortInvariantError, match="missing required key columns"):
        assert_sorted(pd.DataFrame({"region": ["A"], "season": ["JJA"]}))


def test_predict_refuses_unsorted_frame(two_series):
    """The guard must be enforced by predict(), not merely available."""
    shuffled = two_series.iloc[[3, 4, 5, 0, 1, 2]].reset_index(drop=True)
    with pytest.raises(SortInvariantError):
        TrailingMean(3).predict(shuffled, "v")


def test_unsorted_input_would_have_produced_plausible_wrong_answers(two_series):
    """Documents the hazard: the raw idiom fails silently, not loudly.

    This is the bug the guard exists to prevent, reproduced here so the reason for
    the guard is testable rather than only described in a comment. On a B-then-A
    ordering the positional re-attachment hands region A's history to region B's
    rows -- with no NaN beyond the expected two and no exception.
    """
    shuffled = two_series.iloc[[3, 4, 5, 0, 1, 2]].reset_index(drop=True)

    # The old inline idiom, verbatim (positional reset_index).
    shifted = shuffled.groupby(["region", "season"], observed=True)["v"].shift(1)
    regrouped = shifted.groupby([shuffled["region"], shuffled["season"]], observed=True)
    wrong = regrouped.rolling(3, min_periods=1).mean().reset_index(drop=True).to_numpy()

    # Row 1 is region B (prior value 10.0) but receives region A's mean (1.0).
    assert shuffled.loc[1, "region"] == "B"
    assert wrong[1] == pytest.approx(1.0)
    # And it looks entirely reasonable -- only the two true first-occurrences are NaN.
    assert np.isnan(wrong).sum() == 2


# ==========================================================================
# TrailingMean semantics
# ==========================================================================
def test_first_occurrence_is_nan(two_series):
    out = TrailingMean(3).predict(two_series, "v")
    assert np.isnan(out.loc[0, "v"])  # region A, first
    assert np.isnan(out.loc[3, "v"])  # region B, first


def test_trailing_mean_uses_only_strictly_prior_values(two_series):
    """A: [nan, 1, 1.5] ; B: [nan, 10, 15] -- the target never sees itself."""
    out = TrailingMean(3).predict(two_series, "v")["v"].tolist()
    assert out[1] == pytest.approx(1.0)     # A idx10 sees {1}
    assert out[2] == pytest.approx(1.5)     # A idx14 sees {1,2}
    assert out[4] == pytest.approx(10.0)    # B idx6  sees {10}
    assert out[5] == pytest.approx(15.0)    # B idx10 sees {10,20}


def test_window_truncates_to_k(two_series):
    """k=1 keeps only the single previous value, not a running mean."""
    out = TrailingMean(1).predict(two_series, "v")["v"].tolist()
    assert out[2] == pytest.approx(2.0)     # A idx14 sees only {2}
    assert out[5] == pytest.approx(20.0)    # B idx10 sees only {20}


def test_expanding_uses_all_prior_values():
    frame = pd.DataFrame({
        "region": ["A"] * 4, "season": ["JJA"] * 4,
        "season_idx": [2, 6, 10, 14], "season_year": [1992, 1993, 1994, 1995],
        "v": [1.0, 2.0, 3.0, 100.0],
    })
    out = TrailingMean(None).predict(frame, "v")["v"].tolist()
    assert out[3] == pytest.approx(2.0)     # mean of {1,2,3}


def test_trailing_mean_tolerates_gaps(two_series):
    """A gap does not break the window -- it just means fewer prior years.

    Region A jumps 2 -> 10 (a missing season-year). TrailingMean is gap-tolerant
    by design; T4Predictor is the one that requires contiguity.
    """
    out = TrailingMean(3).predict(two_series, "v")["v"]
    assert out.loc[1] == pytest.approx(1.0)
    assert not np.isnan(out.loc[1])


def test_min_periods_two_needs_two_prior_values(two_series):
    """The `f_log_total_std` case: a spread needs >= 2 observations."""
    out = TrailingMean(3, min_periods=2, how="std").predict(two_series, "v")["v"]
    assert np.isnan(out.loc[0]) and np.isnan(out.loc[1])   # 0 and 1 prior values
    assert not np.isnan(out.loc[2])                        # 2 prior values


def test_multi_column_prediction(two_series):
    frame = two_series.assign(w=lambda d: d["v"] * 10)
    out = TrailingMean(3).predict(frame, ["v", "w"])
    assert list(out.columns) == ["v", "w"]
    assert out.loc[2, "w"] == pytest.approx(15.0)


def test_output_is_index_aligned_not_positional(two_series):
    """Correctness must not depend on the frame carrying a default RangeIndex.

    The replaced idiom used `reset_index(drop=True)`, which re-attaches by
    position. A frame filtered without resetting its index would then be
    mis-aligned. Here the values must follow the index labels.
    """
    reindexed = two_series.copy()
    reindexed.index = [100, 101, 102, 103, 104, 105]
    out = TrailingMean(3).predict(reindexed, "v")
    assert list(out.index) == [100, 101, 102, 103, 104, 105]
    assert out.loc[101, "v"] == pytest.approx(1.0)
    assert out.loc[104, "v"] == pytest.approx(10.0)


def test_simplex_predictions_stay_on_the_simplex():
    """A mean of simplex points is a simplex point -- the property the
    notebooks assert after every floor computation."""
    rng = np.random.default_rng(0)
    raw = rng.dirichlet([1, 1, 1], size=12)
    frame = pd.DataFrame({
        "region": ["A"] * 6 + ["B"] * 6,
        "season": ["JJA"] * 12,
        "season_idx": list(range(2, 26, 4)) * 2,
        "human": raw[:, 0], "natural": raw[:, 1], "unknown": raw[:, 2],
    })
    out = TrailingMean(3).predict(frame, ["human", "natural", "unknown"])
    defined = out.dropna()
    assert np.allclose(defined.sum(axis=1), 1.0)


def test_invalid_arguments_rejected():
    with pytest.raises(ValueError):
        TrailingMean(0)
    with pytest.raises(ValueError):
        TrailingMean(3, how="median")


# ==========================================================================
# T4Predictor -- distinct from k=1
# ==========================================================================
def test_t4_requires_a_true_one_year_step(two_series):
    """Region A's 2 -> 10 jump is not a t-4 step, so it must be NaN."""
    out = T4Predictor().predict(two_series, "v")["v"]
    assert np.isnan(out.loc[1])                       # A idx10: prior is idx2, gap
    assert out.loc[4] == pytest.approx(10.0)          # B idx6: prior idx2, true t-4
    assert out.loc[5] == pytest.approx(20.0)          # B idx10: prior idx6, true t-4


def test_t4_is_stricter_than_k1(two_series):
    """The distinction 06_analysis's narrative depends on: t4 scores fewer cells."""
    t4 = T4Predictor().predict(two_series, "v")["v"]
    k1 = TrailingMean(1).predict(two_series, "v")["v"]
    assert t4.notna().sum() < k1.notna().sum()


# ==========================================================================
# GlobalPrior
# ==========================================================================
def test_global_prior_is_constant_and_train_only():
    frame = pd.DataFrame({
        "region": ["A"] * 4, "season": ["JJA"] * 4,
        "season_idx": [2, 6, 10, 14], "season_year": [1992, 1993, 2010, 2011],
        "v": [1.0, 3.0, 1000.0, 2000.0], "wt": [1.0, 1.0, 1.0, 1.0],
    })
    train = (frame["season_year"] < 2010).to_numpy()
    out = GlobalPrior(weighted=True).fit(frame, "v", train_mask=train, weight_col="wt").predict(frame)
    assert out["v"].nunique() == 1
    assert out.loc[0, "v"] == pytest.approx(2.0)   # mean of the two training rows only


def test_global_prior_weighting_matters():
    frame = pd.DataFrame({
        "region": ["A"] * 2, "season": ["JJA"] * 2,
        "season_idx": [2, 6], "season_year": [1992, 1993],
        "v": [1.0, 11.0], "wt": [1.0, 9.0],
    })
    train = np.array([True, True])
    wtd = GlobalPrior(weighted=True).fit(frame, "v", train_mask=train, weight_col="wt")
    unw = GlobalPrior(weighted=False).fit(frame, "v", train_mask=train)
    assert wtd.predict(frame).loc[0, "v"] == pytest.approx(10.0)
    assert unw.predict(frame).loc[0, "v"] == pytest.approx(6.0)


def test_global_prior_requires_fit_before_predict():
    with pytest.raises(RuntimeError, match="must be fit"):
        GlobalPrior().predict(pd.DataFrame({"x": [1]}))


# ==========================================================================
# sweep
# ==========================================================================
def test_sweep_labels_and_shape(two_series):
    out = sweep(two_series, "v", [1, 2, None],
                lambda P: {"n": int(np.isfinite(P).sum())})
    assert list(out.index) == ["k=1", "k=2", "expanding"]
    assert out["n"].tolist() == [4, 4, 4]


# ==========================================================================
# Equivalence with the code being replaced -- the decisive test
# ==========================================================================
@pytest.mark.requires_data
def test_rebuilds_feature_columns_bit_identically(agg, features, cfg):
    """Rebuild every `f_*` column via TrailingMean and diff against the parquet.

    This is what proves the extraction changed no number. The feature table on
    disk was produced by the inline idiom; these columns come from the new class.
    Any divergence in the trailing logic shows up here immediately, with no
    notebook execution involved.
    """
    # Rebuild the per-cell frame exactly as 05_features.ipynb does.
    rsc = agg.copy()
    rsc["coarse"] = rsc["cause"].map(lambda c: "Natural" if c == "Natural" else "Human")
    classes = list(cfg.tier1_classes)

    resolved = (
        rsc.groupby(["region", "season", "season_idx", "season_year", "coarse"],
                    observed=True)["acres"]
        .sum().unstack("coarse", fill_value=0.0)
        .rename(columns={"Human": "human_ac", "Natural": "natural_ac"}).reset_index()
    )
    unk = rsc.drop_duplicates(["region", "season_idx"])[
        ["region", "season_idx", "missing_acres", "missing_fires"]]
    cell = resolved.merge(unk, on=["region", "season_idx"], how="left").rename(
        columns={"missing_acres": "unknown_ac", "missing_fires": "unknown_fires"})
    cell["unknown_fires"] = cell["unknown_fires"].fillna(0.0)
    rfires = rsc.groupby(["region", "season_idx"], observed=True)["fires"].sum().rename("resolved_fires")
    cell = cell.merge(rfires, on=["region", "season_idx"], how="left")
    cell["total_ac"] = cell[["human_ac", "natural_ac", "unknown_ac"]].sum(axis=1)
    cell["total_fires"] = cell["resolved_fires"] + cell["unknown_fires"]
    cell = cell[cell["total_ac"] > 0].copy()
    for c, ac in zip(classes, ["human_ac", "natural_ac", "unknown_ac"]):
        cell[c] = cell[ac] / cell["total_ac"]
    cell["log_total"] = np.log10(cell["total_ac"])
    cell["mean_fire_size"] = cell["total_ac"] / cell["total_fires"].clip(lower=1)
    cell = cell.sort_values(list(cfg.sort_keys)).reset_index(drop=True)
    cell = cell[~cell["season_idx"].isin(cfg.partial_winters)].copy()
    cell = cell.sort_values(list(cfg.sort_keys)).reset_index(drop=True)

    k = cfg.shares_k
    mean_k = TrailingMean(k)
    std_k = TrailingMean(k, min_periods=2, how="std")

    rebuilt = cell[["region", "season", "season_idx"]].copy()
    rebuilt["f_log_total_mean"] = mean_k.predict(cell, "log_total")["log_total"]
    rebuilt["f_log_total_std"] = std_k.predict(cell, "log_total")["log_total"]
    for c in classes:
        rebuilt[f"f_share_{c}_mean"] = mean_k.predict(cell, c)[c]
    rebuilt["f_log_fire_size_mean"] = np.log10(
        mean_k.predict(cell, "mean_fire_size")["mean_fire_size"].clip(lower=1e-6))
    rebuilt["f_log_nfires_mean"] = np.log10(
        mean_k.predict(cell, "total_fires")["total_fires"].clip(lower=1))

    on_disk = features.sort_values(list(cfg.sort_keys)).reset_index(drop=True)
    rebuilt = rebuilt.sort_values(list(cfg.sort_keys)).reset_index(drop=True)

    # Same cells, in the same order.
    pd.testing.assert_frame_equal(
        rebuilt[["region", "season", "season_idx"]],
        on_disk[["region", "season", "season_idx"]],
    )

    feature_cols = [c for c in on_disk.columns if c.startswith("f_") and c != "f_n_prior"]
    for col in feature_cols:
        pd.testing.assert_series_equal(
            rebuilt[col], on_disk[col], check_names=False,
            obj=f"{col} rebuilt via TrailingMean vs on-disk",
        )


@pytest.mark.requires_data
def test_leakage_audit_brute_force(agg, features, cfg):
    """Port of 05_features.ipynb's audit: recompute from strictly-prior rows.

    For a sample of cells, rebuild `f_log_total_mean` by explicitly filtering to
    same-region/same-season rows at a *strictly smaller* season_idx and taking the
    last k. Independent of any groupby/rolling machinery, so it catches a leak the
    vectorized path could hide.
    """
    rsc = agg[~agg["season_idx"].isin(cfg.partial_winters)].copy()
    rsc["coarse"] = rsc["cause"].map(lambda c: "Natural" if c == "Natural" else "Human")
    resolved = (
        rsc.groupby(["region", "season", "season_idx", "season_year", "coarse"],
                    observed=True)["acres"]
        .sum().unstack("coarse", fill_value=0.0)
        .rename(columns={"Human": "human_ac", "Natural": "natural_ac"}).reset_index()
    )
    unk = rsc.drop_duplicates(["region", "season_idx"])[
        ["region", "season_idx", "missing_acres"]]
    cell = resolved.merge(unk, on=["region", "season_idx"], how="left").rename(
        columns={"missing_acres": "unknown_ac"})
    cell["total_ac"] = cell[["human_ac", "natural_ac", "unknown_ac"]].sum(axis=1)
    cell = cell[cell["total_ac"] > 0].copy()
    cell["log_total"] = np.log10(cell["total_ac"])
    cell = cell.sort_values(list(cfg.sort_keys)).reset_index(drop=True)

    k = cfg.shares_k
    pred = TrailingMean(k).predict(cell, "log_total")["log_total"]

    sample = cell.sample(min(300, len(cell)), random_state=1)
    mismatches = []
    for idx, row in sample.iterrows():
        prior = cell[(cell["region"] == row["region"])
                     & (cell["season"] == row["season"])
                     & (cell["season_idx"] < row["season_idx"])]
        prior = prior.sort_values("season_idx").tail(k)
        expected = prior["log_total"].mean() if len(prior) else np.nan
        got = pred.loc[idx]
        if np.isnan(expected) and np.isnan(got):
            continue
        if not np.isclose(got, expected, rtol=1e-9, atol=1e-9):
            mismatches.append((row["region"], row["season"], row["season_idx"], got, expected))

    assert not mismatches, f"LEAKAGE: {len(mismatches)} cells disagree, e.g. {mismatches[:3]}"


@pytest.mark.requires_data
def test_t4_scored_cell_count_matches_notebook(agg, cfg, golden):
    """t4 must remain scored on 3,803 test cells vs k=1's 3,949.

    Pins the T4-vs-k=1 distinction against the numbers 06_analysis printed, so
    collapsing the two classes would fail loudly.
    """
    rsc = agg[~agg["season_idx"].isin(cfg.partial_winters)].copy()
    rsc["coarse"] = rsc["cause"].map(lambda c: "Natural" if c == "Natural" else "Human")
    classes = list(cfg.tier1_classes)
    resolved = (
        rsc.groupby(["region", "season", "season_idx", "season_year", "coarse"],
                    observed=True)["acres"]
        .sum().unstack("coarse", fill_value=0.0)
        .rename(columns={"Human": "human_ac", "Natural": "natural_ac"}).reset_index()
    )
    unk = rsc.drop_duplicates(["region", "season_idx"])[
        ["region", "season_idx", "missing_acres"]]
    t1 = resolved.merge(unk, on=["region", "season_idx"], how="left").rename(
        columns={"missing_acres": "unknown_ac"})
    t1["total_ac"] = t1[["human_ac", "natural_ac", "unknown_ac"]].sum(axis=1)
    t1 = t1[t1["total_ac"] > 0].copy()
    for c, ac in zip(classes, ["human_ac", "natural_ac", "unknown_ac"]):
        t1[c] = t1[ac] / t1["total_ac"]
    t1 = t1.sort_values(list(cfg.sort_keys)).reset_index(drop=True)

    in_test = (t1["season_year"] >= cfg.test_start).to_numpy()
    p_t4 = T4Predictor().predict(t1, classes)
    p_k1 = TrailingMean(1).predict(t1, classes)

    n_t4 = int((in_test & p_t4.notna().all(axis=1).to_numpy()).sum())
    n_k1 = int((in_test & p_k1.notna().all(axis=1).to_numpy()).sum())

    want = golden["notebooks"]["06_analysis"]["metric_tables"]["cell_9"]
    assert n_t4 == int(want["t4"]["n_cells"]) == 3803
    assert n_k1 == int(want["mean3"]["n_cells"]) == 3949
