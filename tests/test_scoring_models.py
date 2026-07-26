"""Tests for `src/scoring.py` and `src/models.py`.

Mostly synthetic: these are small pure functions whose edge cases (NaN handling,
the mask population, the simplex projection) are exactly what a hand-built frame
can pin precisely. Two data-backed tests confirm the helpers reproduce the
published Tier-1 and Human numbers.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from models import SimplexRegressor
from scoring import absolute_error, ladder, score_masked, top1_hit, tvd


# ==========================================================================
# Metric arithmetic
# ==========================================================================
def test_tvd_identical_compositions_is_zero():
    P = np.array([[0.2, 0.3, 0.5]])
    assert tvd(P, P)[0] == pytest.approx(0.0)


def test_tvd_disjoint_compositions_is_one():
    P = np.array([[1.0, 0.0, 0.0]])
    A = np.array([[0.0, 1.0, 0.0]])
    assert tvd(P, A)[0] == pytest.approx(1.0)


def test_tvd_known_value():
    """Half the L1 distance: |0.5-0.2| + |0.3-0.5| + |0.2-0.3| = 0.6 -> 0.3."""
    P = np.array([[0.5, 0.3, 0.2]])
    A = np.array([[0.2, 0.5, 0.3]])
    assert tvd(P, A)[0] == pytest.approx(0.3)


def test_tvd_is_per_row():
    P = np.array([[1.0, 0.0], [0.5, 0.5]])
    A = np.array([[0.0, 1.0], [0.5, 0.5]])
    assert tvd(P, A).tolist() == pytest.approx([1.0, 0.0])


def test_absolute_error():
    assert absolute_error(np.array([2.0, -1.0]), np.array([0.5, 0.5])).tolist() == \
        pytest.approx([1.5, 1.5])


def test_top1_hit_identifies_dominant_class():
    P = np.array([[0.6, 0.3, 0.1], [0.1, 0.2, 0.7]])
    A = np.array([[0.9, 0.05, 0.05], [0.5, 0.3, 0.2]])
    assert top1_hit(P, A).tolist() == [True, False]


# ==========================================================================
# score_masked -- the boilerplate that was duplicated five times
# ==========================================================================
def test_score_masked_excludes_nan_and_train_rows():
    metric = np.array([np.nan, 1.0, 3.0, 5.0])
    weights = np.array([1.0, 1.0, 1.0, 1.0])
    in_test = np.array([True, True, True, False])   # last row is a training row
    out = score_masked(metric, weights, in_test)
    assert out["n_cells"] == 2                      # NaN row and train row both dropped
    assert out["unweighted"] == pytest.approx(2.0)  # mean of {1, 3}


def test_score_masked_weighting():
    metric = np.array([1.0, 11.0])
    weights = np.array([1.0, 9.0])
    in_test = np.array([True, True])
    out = score_masked(metric, weights, in_test)
    assert out["unweighted"] == pytest.approx(6.0)
    assert out["weighted"] == pytest.approx(10.0)


def test_score_masked_extra_uses_the_same_mask():
    """A second metric must never be averaged over a different cell population."""
    metric = np.array([np.nan, 1.0, 3.0])
    weights = np.array([1.0, 1.0, 1.0])
    in_test = np.array([True, True, True])
    hits = np.array([True, True, False])
    out = score_masked(metric, weights, in_test, extra={"top1": hits})
    assert out["n_cells"] == 2
    # Only rows 1 and 2 are scorable -> hits {True, False} -> 0.5, not 2/3.
    assert out["top1_unweighted"] == pytest.approx(0.5)


def test_score_masked_handles_empty_mask():
    out = score_masked(np.array([1.0]), np.array([1.0]), np.array([False]))
    assert out == {"n_cells": 0}


# ==========================================================================
# ladder
# ==========================================================================
def test_ladder_delta_sign_convention():
    """Negative delta = beats the baseline, since all metrics here are errors."""
    rows = {
        "persistence floor (k=7)": {"n_cells": 100, "weighted": 0.30},
        "learned": {"n_cells": 100, "weighted": 0.25},
    }
    out = ladder(rows, baseline="persistence floor (k=7)")
    assert out.loc["learned", "delta_vs_floor"] == pytest.approx(-0.05)
    assert out.loc["persistence floor (k=7)", "delta_vs_floor"] == pytest.approx(0.0)


def test_ladder_rejects_unknown_baseline():
    with pytest.raises(KeyError):
        ladder({"a": {"weighted": 1.0}}, baseline="nope")


# ==========================================================================
# SimplexRegressor
# ==========================================================================
@pytest.fixture
def simplex_problem():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 4))
    # A learnable composition: class shares driven by the first two features.
    raw = np.column_stack([
        1.0 + X[:, 0], 1.0 + X[:, 1], np.full(len(X), 1.0),
    ])
    raw = np.clip(raw, 0.01, None)
    Y = raw / raw.sum(axis=1, keepdims=True)
    return X, Y


def test_predictions_are_simplex_points(simplex_problem):
    X, Y = simplex_problem
    P = SimplexRegressor(max_iter=30).fit(X, Y).predict(X)
    assert P.shape == Y.shape
    assert np.all(P >= 0)
    assert np.allclose(P.sum(axis=1), 1.0)


def test_fits_one_model_per_class(simplex_problem):
    X, Y = simplex_problem
    model = SimplexRegressor(max_iter=10).fit(X, Y)
    assert len(model.models_) == Y.shape[1]


def test_seeded_and_deterministic(simplex_problem):
    X, Y = simplex_problem
    a = SimplexRegressor(max_iter=20).fit(X, Y).predict(X)
    b = SimplexRegressor(max_iter=20).fit(X, Y).predict(X)
    assert np.array_equal(a, b)


def test_sample_weight_changes_the_fit(simplex_problem):
    X, Y = simplex_problem
    w = np.where(X[:, 0] > 0, 100.0, 1.0)
    plain = SimplexRegressor(max_iter=30).fit(X, Y).predict(X)
    wtd = SimplexRegressor(max_iter=30).fit(X, Y, sample_weight=w).predict(X)
    assert not np.allclose(plain, wtd)


def test_negative_raw_predictions_are_clipped():
    """A regressor can predict below zero; the projection must absorb that."""
    X = np.linspace(-3, 3, 120).reshape(-1, 1)
    Y = np.column_stack([np.linspace(0.0, 1.0, 120), np.linspace(1.0, 0.0, 120)])
    P = SimplexRegressor(max_iter=40).fit(X, Y).predict(X)
    assert np.all(P >= 0)
    assert np.allclose(P.sum(axis=1), 1.0)


def test_requires_fit_before_predict():
    with pytest.raises(RuntimeError, match="must be fit"):
        SimplexRegressor().predict(np.zeros((2, 2)))


def test_rejects_one_dimensional_target():
    with pytest.raises(ValueError, match="2-D"):
        SimplexRegressor().fit(np.zeros((4, 2)), np.zeros(4))


# ==========================================================================
# Against the published numbers
# ==========================================================================
@pytest.mark.requires_data
@pytest.mark.slow
def test_helpers_reproduce_tier1_floor_and_learned(agg, features, cfg, golden):
    """Floor 0.2676/0.2659 and learned 0.3141/0.2894 via scoring + SimplexRegressor."""
    from panel import RegionSeasonPanel
    from trailing import TrailingMean

    panel = RegionSeasonPanel(agg, cfg)
    t1 = panel.tier1_composition()
    classes = list(cfg.tier1_classes)
    pred_share = TrailingMean(cfg.shares_k).predict(t1, classes)

    key = ["region", "season", "season_idx"]
    floor_df = t1[key].copy()
    for c in classes:
        floor_df[f"floor_{c}"] = pred_share[c].to_numpy()
    feats = features.merge(floor_df, on=key, how="left", validate="one_to_one")

    featcols = [c for c in feats.columns if c.startswith("f_")]
    X_all = pd.get_dummies(feats[featcols + ["season"]], columns=["season"], dtype=float)
    has_feat = feats[featcols].notna().all(axis=1).to_numpy()
    tr = (feats["season_year"] < cfg.test_start).to_numpy() & has_feat
    te = (feats["season_year"] >= cfg.test_start).to_numpy() & has_feat
    wt = feats["total_ac"].to_numpy()

    P_learn = (SimplexRegressor()
               .fit(X_all.to_numpy()[tr], feats[classes].to_numpy()[tr], sample_weight=wt[tr])
               .predict(X_all.to_numpy()[te]))
    A_te = feats[classes].to_numpy()[te]
    P_floor = feats[[f"floor_{c}" for c in classes]].to_numpy()[te]

    want = golden["notebooks"]["06_analysis"]["metric_tables"]["cell_22"]
    all_test = np.ones(te.sum(), dtype=bool)
    for P, label in [(P_floor, "persistence floor (k=7)"),
                     (P_learn, "learned (gradient boosting)")]:
        got = score_masked(tvd(P, A_te), wt[te], all_test)
        assert got["unweighted"] == pytest.approx(want[label]["TVD_unweighted"], abs=1e-4)
        assert got["weighted"] == pytest.approx(want[label]["TVD_acre_wtd"], abs=1e-4)


@pytest.mark.requires_data
def test_helpers_reproduce_human_floor(agg, cfg, golden):
    """The Human floor's five numbers via tvd + top1_hit + score_masked."""
    from panel import RegionSeasonPanel
    from trailing import TrailingMean

    panel = RegionSeasonPanel(agg, cfg)
    hc, shcols = panel.human_subcause_shares()
    P = TrailingMean(cfg.shares_k).predict(hc, shcols).to_numpy()
    actual = hc[shcols].to_numpy()
    w = hc["human_total_ac"].to_numpy()
    in_test = (hc["season_year"] >= cfg.test_start).to_numpy()

    metric = tvd(P, actual)
    mask = in_test & ~np.isnan(metric)
    got = score_masked(metric, w, in_test,
                       extra={"top1": top1_hit(P[mask], actual[mask])})

    want = golden["notebooks"]["08_human_cause"]["keyvalue_blocks"]["cell_5"]
    assert got["n_cells"] == int(want["n_cells"])
    assert got["unweighted"] == pytest.approx(want["TVD_unweighted"], abs=1e-4)
    assert got["weighted"] == pytest.approx(want["TVD_acre_wtd"], abs=1e-4)
    assert got["top1_unweighted"] == pytest.approx(want["top1_hit_unwtd"], abs=1e-4)
    assert got["top1_weighted"] == pytest.approx(want["top1_hit_acre_wtd"], abs=1e-4)
