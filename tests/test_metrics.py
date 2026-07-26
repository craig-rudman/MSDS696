"""Metric pins: the headline numbers the refactor must not move.

Tier 3 of the suite. Each test re-derives a published metric from the artifacts
and compares it to the value captured from the pre-refactor notebook outputs
(`tests/golden_metrics.json`, written by `capture_baseline.py` in Phase 0).

Two deliberate choices about tolerance:

  * metrics use `pytest.approx` at the precision the notebooks actually print
    (4 decimals). Float accumulation order can shift a sum at ~1e-15, and that
    is not a finding; a change at the 4th decimal is.
  * `n_cells` is pinned EXACTLY. A silently-changed scorable-cell population is
    the likeliest way a refactor corrupts a result, and it shows up in the count
    before it shows up in the metric. This is the canary.

These tests are marked `slow` because the learned rungs fit gradient-boosted
models. The models are seeded (`random_state=0`), so they are deterministic.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytestmark = [pytest.mark.requires_data, pytest.mark.slow]

TOL = 1e-4  # the printed precision of the notebook tables


# --------------------------------------------------------------------------
# Helpers that mirror the notebook recipes exactly.
# --------------------------------------------------------------------------
def _tier1_from_agg(agg: pd.DataFrame, cfg) -> pd.DataFrame:
    """Rebuild the Tier-1 composition target, as 06_analysis.ipynb does."""
    rsc = agg[~agg["season_idx"].isin(cfg.partial_winters)].copy()
    rsc["coarse"] = rsc["cause"].map(lambda c: "Natural" if c == "Natural" else "Human")
    classes = list(cfg.tier1_classes)

    resolved = (
        rsc.groupby(["region", "season", "season_idx", "season_year", "coarse"],
                    observed=True)["acres"]
        .sum().unstack("coarse", fill_value=0.0)
        .rename(columns={"Human": "human_ac", "Natural": "natural_ac"})
        .reset_index()
    )
    # Per-cell quantity: deduplicate, never sum (it repeats across cause rows).
    unk = rsc.drop_duplicates(["region", "season_idx"])[
        ["region", "season_idx", "missing_acres"]]
    t1 = (resolved.merge(unk, on=["region", "season_idx"], how="left")
          .rename(columns={"missing_acres": "unknown_ac"}))
    t1["total_ac"] = t1[["human_ac", "natural_ac", "unknown_ac"]].sum(axis=1)
    t1 = t1[t1["total_ac"] > 0].copy()
    for c, ac in zip(classes, ["human_ac", "natural_ac", "unknown_ac"]):
        t1[c] = t1[ac] / t1["total_ac"]
    return t1.sort_values(list(cfg.sort_keys)).reset_index(drop=True)


def _trailing(frame: pd.DataFrame, cols, k):
    """shift(1) then a k-window trailing mean within (region, season).

    Requires `frame` to be sorted by (region, season, season_idx) -- see
    tests/test_trailing.py for why that precondition is load-bearing.
    """
    shifted = frame.groupby(["region", "season"], observed=True)[cols].shift(1)
    sg = shifted.groupby([frame["region"], frame["season"]], observed=True)
    if k is None:
        return sg.expanding(min_periods=1).mean().reset_index(drop=True)
    return sg.rolling(window=k, min_periods=1).mean().reset_index(drop=True)


def _score_masked(metric_vec, weights, in_test):
    """(n_cells, unweighted, acre-weighted) over scorable test cells."""
    m = in_test & ~np.isnan(metric_vec)
    return (int(m.sum()),
            float(metric_vec[m].mean()),
            float(np.average(metric_vec[m], weights=weights[m])))


# --------------------------------------------------------------------------
# Tier 1 -- the coarse allocator
# --------------------------------------------------------------------------
def test_tier1_cell_count(agg, cfg, golden):
    t1 = _tier1_from_agg(agg, cfg)
    want = golden["notebooks"]["06_analysis"]["scalars"]["tier1_cells"]
    assert len(t1) == int(want)


def test_tier1_class_share_snapshot(agg, cfg):
    """Natural 58.9% / Human 22.6% / Unknown 18.5% of 179.12M acres.

    Pinned from the notebook output. Note the project prose rounds Human to 22.7%
    and the total to 179.3M; the notebook's own printed figures are the pin here.
    """
    rsc = agg[~agg["season_idx"].isin(cfg.partial_winters)].copy()
    rsc["coarse"] = rsc["cause"].map(lambda c: "Natural" if c == "Natural" else "Human")
    hn = rsc.groupby("coarse")["acres"].sum()
    unknown = rsc.drop_duplicates(["region", "season_year", "season"])["missing_acres"].sum()
    total = hn["Human"] + hn["Natural"] + unknown

    assert total / 1e6 == pytest.approx(179.12, abs=0.01)
    assert hn["Natural"] / total == pytest.approx(0.589, abs=0.001)
    assert hn["Human"] / total == pytest.approx(0.226, abs=0.001)
    assert unknown / total == pytest.approx(0.185, abs=0.001)


def test_tier1_shares_k_sweep(agg, cfg, golden):
    """The full k=1..8 + expanding TVD sweep, including n_cells."""
    t1 = _tier1_from_agg(agg, cfg)
    classes = list(cfg.tier1_classes)
    actual = t1[classes].to_numpy()
    in_test = (t1["season_year"] >= cfg.test_start).to_numpy()
    w = t1["total_ac"].to_numpy()

    want = golden["notebooks"]["06_analysis"]["metric_tables"]["cell_12"]
    for label, expected in want.items():
        k = None if label == "expanding" else int(label.split("=")[1])
        P = _trailing(t1, classes, k).to_numpy()
        tvd = 0.5 * np.abs(P - actual).sum(axis=1)
        n, unw, wtd = _score_masked(tvd, w, in_test)
        assert n == int(expected["n_cells"]), f"{label}: n_cells drifted"
        assert unw == pytest.approx(expected["TVD_unweighted"], abs=TOL), f"{label} unweighted"
        assert wtd == pytest.approx(expected["TVD_acre_wtd"], abs=TOL), f"{label} acre-weighted"


def test_tier1_locked_shares_k_is_acre_weighted_argmin(agg, cfg):
    """k=7 must remain the acre-weighted minimum -- it is why cfg.shares_k is 7."""
    t1 = _tier1_from_agg(agg, cfg)
    classes = list(cfg.tier1_classes)
    actual = t1[classes].to_numpy()
    in_test = (t1["season_year"] >= cfg.test_start).to_numpy()
    w = t1["total_ac"].to_numpy()

    scores = {}
    for k in range(1, 9):
        P = _trailing(t1, classes, k).to_numpy()
        tvd = 0.5 * np.abs(P - actual).sum(axis=1)
        scores[k] = _score_masked(tvd, w, in_test)[2]
    assert min(scores, key=scores.get) == cfg.shares_k


def test_tier1_level_sweep_best_is_k6(agg, cfg, golden):
    """The level re-sweeps independently of the shares and lands on k=6."""
    t1 = _tier1_from_agg(agg, cfg)
    t1["log_total"] = np.log10(t1["total_ac"])
    in_test = (t1["season_year"] >= cfg.test_start).to_numpy()
    w = t1["total_ac"].to_numpy()
    log_actual = t1["log_total"].to_numpy()

    want = golden["notebooks"]["06_analysis"]["metric_tables"]["cell_15"]
    wtd_by_label = {}
    for label, expected in want.items():
        k = None if label == "expanding" else int(label.split("=")[1])
        p = _trailing(t1, ["log_total"], k)["log_total"].to_numpy()
        err = np.abs(p - log_actual)
        n, unw, wtd = _score_masked(err, w, in_test)
        wtd_by_label[label] = wtd
        assert n == int(expected["n_cells"]), f"{label}: n_cells drifted"
        assert unw == pytest.approx(expected["logMAE_unwtd"], abs=TOL), f"{label} unweighted"
        assert wtd == pytest.approx(expected["logMAE_acre_wtd"], abs=TOL), f"{label} acre-wtd"

    assert min(wtd_by_label, key=wtd_by_label.get) == "k=6"


# --------------------------------------------------------------------------
# The Human branch
# --------------------------------------------------------------------------
def _human_target(agg, cfg):
    rsc = agg[~agg["season_idx"].isin(cfg.partial_winters)].copy()
    human = rsc[rsc["cause"] != "Natural"].copy()
    subcauses = sorted(human["cause"].unique())
    keys = list(cfg.cell_keys)
    wide = (human.groupby(keys + ["cause"], observed=True)["acres"].sum()
            .unstack("cause", fill_value=0.0).reset_index())
    wide["human_total_ac"] = wide[subcauses].sum(axis=1)
    wide = wide[wide["human_total_ac"] > 0].copy()
    shares = wide[subcauses].div(wide["human_total_ac"], axis=0)
    shares.columns = [f"sh_{c}" for c in subcauses]
    hc = pd.concat([wide[keys + ["human_total_ac"]], shares], axis=1)
    return hc.sort_values(list(cfg.sort_keys)).reset_index(drop=True), list(shares.columns)


def test_human_branch_cell_count(agg, cfg, golden):
    hc, _ = _human_target(agg, cfg)
    want = golden["notebooks"]["08_human_cause"]["scalars"]["human_cells"]
    assert len(hc) == int(want)


def test_human_persistence_floor(agg, cfg, golden):
    """TVD 0.4415/0.4887 and top-1 0.5169/0.5405 on 3,850 held-out cells."""
    hc, shcols = _human_target(agg, cfg)
    P = _trailing(hc, shcols, cfg.shares_k).to_numpy()
    actual = hc[shcols].to_numpy()
    w = hc["human_total_ac"].to_numpy()
    in_test = (hc["season_year"] >= cfg.test_start).to_numpy()

    tvd = 0.5 * np.abs(P - actual).sum(axis=1)
    n, unw, wtd = _score_masked(tvd, w, in_test)
    m = in_test & ~np.isnan(tvd)
    hit = np.nanargmax(P[m], axis=1) == actual[m].argmax(axis=1)

    want = golden["notebooks"]["08_human_cause"]["keyvalue_blocks"]["cell_5"]
    assert n == int(want["n_cells"])
    assert unw == pytest.approx(want["TVD_unweighted"], abs=TOL)
    assert wtd == pytest.approx(want["TVD_acre_wtd"], abs=TOL)
    assert float(hit.mean()) == pytest.approx(want["top1_hit_unwtd"], abs=TOL)
    assert float(np.average(hit, weights=w[m])) == pytest.approx(
        want["top1_hit_acre_wtd"], abs=TOL)


# --------------------------------------------------------------------------
# The Unknown branch
# --------------------------------------------------------------------------
def test_unknown_dataquality_mae(agg, cfg, golden):
    """Persistence 0.2012/0.1665 beats the global mean 0.2230/0.2398."""
    rsc = agg[~agg["season_idx"].isin(cfg.partial_winters)].copy()
    rsc["coarse"] = rsc["cause"].map(lambda c: "Natural" if c == "Natural" else "Human")
    keys = list(cfg.cell_keys)
    res = (rsc.groupby(keys + ["coarse"], observed=True)["acres"].sum()
           .unstack("coarse", fill_value=0.0).reset_index())
    mk = rsc.drop_duplicates(keys)[keys + ["missing_acres", "missing_acre_frac"]]
    cell = res.merge(mk, on=keys, how="left")
    cell["total_ac"] = cell["Human"] + cell["Natural"] + cell["missing_acres"]
    cell = cell[cell["total_ac"] > 0].copy()
    cell = cell.sort_values(list(cfg.sort_keys)).reset_index(drop=True)

    actual = cell["missing_acre_frac"].to_numpy()
    w = cell["total_ac"].to_numpy()
    in_test = (cell["season_year"] >= cfg.test_start).to_numpy()
    train = (cell["season_year"] < cfg.test_start).to_numpy()

    want = golden["notebooks"]["09_unknown_dataquality"]["metric_tables"]["cell_3"]

    pred_trail = _trailing(cell, ["missing_acre_frac"], cfg.shares_k)["missing_acre_frac"].to_numpy()
    n, unw, wtd = _score_masked(np.abs(pred_trail - actual), w, in_test)
    exp_p = want[f"persistence (k={cfg.shares_k})"]
    assert n == int(exp_p["n_cells"])
    assert unw == pytest.approx(exp_p["MAE_unwtd"], abs=TOL)
    assert wtd == pytest.approx(exp_p["MAE_acre_wtd"], abs=TOL)

    pred_global = np.full(len(cell), actual[train].mean())
    n, unw, wtd = _score_masked(np.abs(pred_global - actual), w, in_test)
    exp_g = want["global mean"]
    assert n == int(exp_g["n_cells"])
    assert unw == pytest.approx(exp_g["MAE_unwtd"], abs=TOL)
    assert wtd == pytest.approx(exp_g["MAE_acre_wtd"], abs=TOL)


# --------------------------------------------------------------------------
# The Natural branch
# --------------------------------------------------------------------------
def test_natural_branch_baselines(agg, cfg, golden):
    """Persistence wins unweighted (0.9141) but LOSES acre-weighted (1.1463 vs
    0.4998) -- the metric disagreement that is the branch's headline finding."""
    rsc = agg[~agg["season_idx"].isin(cfg.partial_winters)].copy()
    keys = list(cfg.cell_keys)
    nat = (rsc[rsc["cause"] == "Natural"].groupby(keys, observed=True)["acres"].sum()
           .rename("nat_ac").reset_index())
    natp = nat[nat["nat_ac"] > 0].copy()
    natp["log_nat"] = np.log10(natp["nat_ac"])
    natp = natp.sort_values(list(cfg.sort_keys)).reset_index(drop=True)

    actual = natp["log_nat"].to_numpy()
    w = natp["nat_ac"].to_numpy()
    in_test = (natp["season_year"] >= cfg.test_start).to_numpy()
    train = (natp["season_year"] < cfg.test_start).to_numpy()

    want = golden["notebooks"]["07_natural_location"]["metric_tables"]["cell_5"]

    pred_trail = _trailing(natp, ["log_nat"], cfg.shares_k)["log_nat"].to_numpy()
    n, unw, wtd = _score_masked(np.abs(pred_trail - actual), w, in_test)
    exp_p = want[f"persistence (k={cfg.shares_k})"]
    assert n == int(exp_p["n_cells"])
    assert unw == pytest.approx(exp_p["logMAE_unwtd"], abs=TOL)
    assert wtd == pytest.approx(exp_p["logMAE_acre_wtd"], abs=TOL)

    global_log = np.average(actual[train], weights=w[train])
    n, unw, wtd = _score_masked(np.abs(np.full(len(natp), global_log) - actual), w, in_test)
    exp_g = want["global prior (train mean)"]
    assert n == int(exp_g["n_cells"])
    assert unw == pytest.approx(exp_g["logMAE_unwtd"], abs=TOL)
    assert wtd == pytest.approx(exp_g["logMAE_acre_wtd"], abs=TOL)

    # The finding itself: the two metrics disagree about which predictor wins.
    assert exp_p["logMAE_unwtd"] < exp_g["logMAE_unwtd"]
    assert exp_p["logMAE_acre_wtd"] > exp_g["logMAE_acre_wtd"]


# --------------------------------------------------------------------------
# The learned rung (fits gradient-boosted models)
# --------------------------------------------------------------------------
def test_tier1_learned_shares_head_to_head(agg, features, cfg, golden):
    """Floor 0.2676/0.2659 vs learned 0.3141/0.2894 on 3,941 cells.

    Also pins the train/test split sizes (5,399/3,941) and the one-hot feature
    column order, which a panel refactor could reorder unnoticed.
    """
    from sklearn.ensemble import HistGradientBoostingRegressor

    t1 = _tier1_from_agg(agg, cfg)
    classes = list(cfg.tier1_classes)
    pred_share = _trailing(t1, classes, cfg.shares_k)

    key = ["region", "season", "season_idx"]
    floor_df = t1[key].copy()
    for c in classes:
        floor_df[f"floor_{c}"] = pred_share[c].to_numpy()
    feats = features.merge(floor_df, on=key, how="left", validate="one_to_one")

    featcols = [c for c in feats.columns if c.startswith("f_")]
    X_all = pd.get_dummies(feats[featcols + ["season"]], columns=["season"], dtype=float)
    assert list(X_all.columns) == featcols + ["season_DJF", "season_JJA",
                                              "season_MAM", "season_SON"]

    has_feat = feats[featcols].notna().all(axis=1).to_numpy()
    tr = (feats["season_year"] < cfg.test_start).to_numpy() & has_feat
    te = (feats["season_year"] >= cfg.test_start).to_numpy() & has_feat
    sc = golden["notebooks"]["06_analysis"]["scalars"]
    assert int(te.sum()) == int(sc["shares_test_cells"])
    assert int(tr.sum()) == 5399

    wt = feats["total_ac"].to_numpy()
    Xtr, Xte = X_all.to_numpy()[tr], X_all.to_numpy()[te]
    Ytr = feats[classes].to_numpy()[tr]

    parts = []
    for j in range(len(classes)):
        model = HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.05, max_leaf_nodes=31, random_state=0)
        model.fit(Xtr, Ytr[:, j], sample_weight=wt[tr])
        parts.append(model.predict(Xte))
    P_learn = np.clip(np.vstack(parts).T, 0, None)
    P_learn = P_learn / P_learn.sum(axis=1, keepdims=True)
    assert np.allclose(P_learn.sum(axis=1), 1.0), "learned predictions must be simplex points"

    A_te = feats[classes].to_numpy()[te]
    w_te = wt[te]
    P_floor = feats[[f"floor_{c}" for c in classes]].to_numpy()[te]
    assert not np.isnan(P_floor).all(), "floor merged to all-NaN -- key dtype drift"

    want = golden["notebooks"]["06_analysis"]["metric_tables"]["cell_22"]
    for P, label in [(P_floor, "persistence floor (k=7)"),
                     (P_learn, "learned (gradient boosting)")]:
        tvd = 0.5 * np.abs(P - A_te).sum(axis=1)
        assert float(tvd.mean()) == pytest.approx(want[label]["TVD_unweighted"], abs=TOL)
        assert float(np.average(tvd, weights=w_te)) == pytest.approx(
            want[label]["TVD_acre_wtd"], abs=TOL)
