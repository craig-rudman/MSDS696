"""The hex-season modelling panel: one assembly, one baseline, one scorer.

This module exists because of a specific failure. Across the W6 modelling work
the persistence baseline was re-typed inline roughly eight times — the same
`groupby -> shift(1) -> rolling(k).mean()` idiom, each time in a throwaway
script. The ablation numbers moved between runs (the same burn-history rung
scored -30%, -115% and +3.4%) and the cause was not the data: it was the harness
being rewritten on every invocation.

That is the *identical* hazard `src/trailing.py` was extracted to kill at region
grain in W5, and the fix is the same one — so this module **calls
`trailing.TrailingMean` rather than reimplementing it**. The sort-invariant
assertion and index-aligned output documented there apply here unchanged; the
only thing that differs at hex grain is the grouping key.

    region grain : group by (region, season)
    hex grain    : group by (hex_id, season_ord)

`season_ord` rather than `season`: the hex panel carries the season as its
ordinal (season_idx % 4) rather than a label, and persistence must compare a
season to *the same season* in earlier years — a summer's history is other
summers, not the spring before it.

Scoring: rank, not deviance
---------------------------
The target is 85-96% zeros and 4.3-9.3x overdispersed relative to Poisson, which
makes Poisson deviance an unreliable comparator (measured in
`12_hex_ignition_baselines.ipynb`). Spearman is used instead, and the choice is
substantive rather than defensive:

1. It is invariant to monotone transforms, so it does not care which link or
   loss a rung happens to use. Verified: a tree given only persistence scores an
   identical 0.3435 under Poisson, squared-error and a hurdle classifier.
2. It matches the decision. The product is a *siting* ranking — which hexes to
   treat first — so rank accuracy is the quantity a planner consumes, while the
   absolute expected count is not.

`n_test` is reported alongside every score because the covariate rungs drop the
805 hex-seasons with no TerraClimate coverage, and a comparison across different
cell populations is not a comparison.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from config import ProjectConfig
from trailing import TrailingMean

# The hex-grain analogue of trailing.GROUP_KEYS. A hex's history is its own
# same-season history.
HEX_GROUP_KEYS: tuple[str, str] = ("hex_id", "season_ord")

# Sort order the shift/rolling idiom depends on. Same contract as
# config.SORT_KEYS at region grain: wrong order silently attaches one hex's
# history to another's rows.
HEX_SORT_KEYS: tuple[str, str, str] = ("hex_id", "season_ord", "season_idx")

CLIMATE_COVS: tuple[str, ...] = ("pdsi", "soil_moisture", "water_deficit", "vpd")
BURN_COVS: tuple[str, ...] = ("any_burn_lag4", "any_burn_lag12", "burned_frac_lag12")

# Trailing window for the starts baseline. Named for its target, per the
# convention in config.py — k is tuned per target and a generic `default_k`
# would erase that.
STARTS_K = 7


def load(
    data_dir: Path,
    *,
    cfg: ProjectConfig | None = None,
    with_climate: bool = True,
    with_burn: bool = True,
) -> pd.DataFrame:
    """Assemble the hex-season panel: target, covariates, derived keys.

    Left-joins onto the ignition panel, so the target's cell population is
    authoritative and a covariate gap surfaces as NaN rather than as a dropped
    row. Per the project's method commitments, missing external data is never
    imputed to zero — a zero anomaly reads as "average", a fabricated
    observation.
    """
    cfg = ProjectConfig() if cfg is None else cfg
    panel = pd.read_parquet(data_dir / "hex_ignitions.parquet")

    if with_climate:
        clim = pd.read_parquet(data_dir / "hex_season_climate.parquet")
        clim = clim.drop(columns=[c for c in ("season", "season_year") if c in clim])
        panel = panel.merge(clim, on=["hex_id", "season_idx"], how="left")
    if with_burn:
        burn = pd.read_parquet(data_dir / "hex_burn_history.parquet")
        panel = panel.merge(burn, on=["hex_id", "season_idx"], how="left")

    panel["season_year"] = cfg.base_year + (panel["season_idx"] // 4)
    panel["season_ord"] = panel["season_idx"] % 4
    return panel.sort_values(list(HEX_SORT_KEYS)).reset_index(drop=True)


def add_persistence(
    panel: pd.DataFrame,
    targets: Sequence[str] = ("starts_natural", "starts_human"),
    *,
    k: int = STARTS_K,
) -> pd.DataFrame:
    """Attach the trailing-mean persistence baseline for each target.

    Delegates to `trailing.TrailingMean`, which asserts the sort invariant and
    returns index-aligned output. Writing the shift/rolling idiom here instead
    would recreate the duplication this module exists to remove.
    """
    out = panel.copy()
    pred = TrailingMean(k=k).predict(out, list(targets), group_keys=HEX_GROUP_KEYS)
    for t in targets:
        out[f"pers_{t.replace('starts_', '')}"] = pred[t]
    return out


def add_climate_anomalies(
    panel: pd.DataFrame,
    covs: Sequence[str] = CLIMATE_COVS,
    *,
    cfg: ProjectConfig | None = None,
    suffix: str = "_anom",
) -> pd.DataFrame:
    """Within-hex climate anomalies: this hex against its own normal.

    The raw covariates are dominated by *cross-sectional* variation — deserts
    are dry every year — which is static geography that persistence already
    encodes. The anomaly isolates the *temporal* part, which is the only
    component that could tell a planner something a hex's own history cannot.

    Hex means are computed on **training years only**. Using the full record
    would let the held-out period's own climate define the normal it is measured
    against, which is a leak.
    """
    cfg = ProjectConfig() if cfg is None else cfg
    out = panel.copy()
    train = out["season_year"] < cfg.test_start
    mu = out.loc[train].groupby("hex_id")[list(covs)].mean()
    for c in covs:
        out[f"{c}{suffix}"] = out[c] - out["hex_id"].map(mu[c])
    return out


def split(panel: pd.DataFrame, *, cfg: ProjectConfig | None = None):
    """Forward-chaining temporal split as boolean masks."""
    cfg = ProjectConfig() if cfg is None else cfg
    train = (panel["season_year"] < cfg.test_start).to_numpy()
    return train, ~train


def rank_score(y: np.ndarray, pred: np.ndarray) -> float:
    """Spearman rank correlation — the siting metric. See module docstring."""
    return float(spearmanr(y, pred).statistic)


def ladder(
    panel: pd.DataFrame,
    target: str,
    rungs: dict[str, Sequence[str]],
    *,
    cfg: ProjectConfig | None = None,
    season_ord: int | None = None,
    model_factory=None,
) -> pd.DataFrame:
    """Score persistence, then each covariate rung, on one cell population.

    `rungs` maps a label to the extra feature columns added on top of the
    persistence prediction. The floor row is always computed first and every
    rung's delta is measured against it.

    `season_ord` optionally restricts to one meteorological season — used for
    JJA, which carries the overwhelming majority of natural ignitions and where
    an all-season pooled fit is diluted by three seasons in which almost nothing
    burns.
    """
    from sklearn.ensemble import HistGradientBoostingRegressor

    cfg = ProjectConfig() if cfg is None else cfg
    if model_factory is None:
        def model_factory():
            return HistGradientBoostingRegressor(
                loss="poisson", max_depth=3, max_iter=200, learning_rate=0.05,
                l2_regularization=1.0, min_samples_leaf=200, random_state=0,
            )

    train, test = split(panel, cfg=cfg)
    if season_ord is not None:
        keep = (panel["season_ord"] == season_ord).to_numpy()
        train, test = train & keep, test & keep

    y = panel[target].to_numpy(float)
    pers = panel[f"pers_{target.replace('starts_', '')}"].to_numpy()
    base_ok = test & np.isfinite(pers)

    rows = [{
        "rung": f"persistence k={STARTS_K} (floor)",
        "n_test": int(base_ok.sum()),
        "spearman": rank_score(y[base_ok], pers[base_ok]),
    }]
    floor = rows[0]["spearman"]

    for label, feats in rungs.items():
        X = np.column_stack([pers] + [panel[c].to_numpy() for c in feats])
        ok = np.isfinite(X).all(axis=1)
        tr, te = train & ok, test & ok & np.isfinite(pers)
        model = model_factory()
        model.fit(X[tr], y[tr])
        pred = model.predict(X[te])
        rows.append({
            "rung": label,
            "n_test": int(te.sum()),
            "spearman": rank_score(y[te], pred),
        })

    out = pd.DataFrame(rows)
    out["delta_vs_floor"] = out["spearman"] - floor
    return out


def marginal_signal(
    panel: pd.DataFrame,
    target: str,
    covs: Sequence[str],
    *,
    cfg: ProjectConfig | None = None,
    season_ord: int | None = 2,
) -> pd.DataFrame:
    """Raw per-covariate rank correlation with the target — model-free.

    A model that fails to use a covariate and a covariate that carries no signal
    look identical in an ablation. This separates them: it asks what is in the
    covariate before any learner touches it.
    """
    cfg = ProjectConfig() if cfg is None else cfg
    sub = panel[panel["season_year"] >= cfg.test_start]
    if season_ord is not None:
        sub = sub[sub["season_ord"] == season_ord]

    rows = []
    for c in covs:
        s = sub[[c, target]].dropna()
        rows.append({"covariate": c, "n": len(s),
                     "spearman": rank_score(s[c].to_numpy(), s[target].to_numpy())})
    return pd.DataFrame(rows)


def _self_check() -> None:
    """Assert the baseline is the trailing one, and that anomalies are leak-free."""
    # Two hexes, four summers each, so persistence has history to work with.
    frame = pd.DataFrame({
        "hex_id": ["a"] * 4 + ["b"] * 4,
        "season_idx": [2, 6, 10, 14] * 2,
        "starts_natural": [1.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0, 40.0],
        "starts_human": 0.0,
        "season_year": [1992, 1993, 1994, 1995] * 2,
        "pdsi": [1.0, 2.0, 3.0, 100.0, 1.0, 2.0, 3.0, 100.0],
    })
    frame["season_ord"] = frame["season_idx"] % 4
    frame = frame.sort_values(list(HEX_SORT_KEYS)).reset_index(drop=True)

    out = add_persistence(frame, targets=("starts_natural",))
    p = out["pers_natural"].to_numpy()

    # First occurrence has no history; later rows are the mean of strictly
    # earlier same-hex values. A leak would show up as row 1 seeing its own 3.0.
    assert np.isnan(p[0]), "first occurrence must have no prediction"
    assert p[1] == 1.0, f"expected mean of [1.0], got {p[1]}"
    assert p[2] == 2.0, f"expected mean of [1,3], got {p[2]}"
    assert p[4:5].tolist() == [np.nan] or np.isnan(p[4]), "hex b must start fresh"
    assert p[5] == 10.0, f"hex b history leaked from hex a: {p[5]}"

    # Anomalies must use train-period means only. With test_start=1995, the
    # normal for hex a is mean(1,2,3)=2.0, so the 1995 value of 100 is +98 —
    # not the +75.5 a full-record mean would give.
    cfg = ProjectConfig()
    assert cfg.test_start == 2010, "self-check assumes the project default"
    anom = add_climate_anomalies(frame, covs=("pdsi",),
                                 cfg=ProjectConfig(test_start=1995))
    a = anom.loc[anom["season_year"] == 1995, "pdsi_anom"].to_numpy()
    assert np.allclose(a, 98.0), f"anomaly used test-period data: {a}"

    print("hex_panel._self_check passed")


if __name__ == "__main__":
    _self_check()


# --- caching -------------------------------------------------------------
# The assembled panel takes ~90s to build (three parquet joins plus the
# trailing baseline over 4.2M rows). Nothing in it depends on a model, so it is
# a pure function of the three source artifacts and is safe to persist. Caching
# it is also what stops the baseline being recomputed — and therefore silently
# re-specified — on every invocation, which is the failure this module exists
# to prevent.

PANEL_CACHE = "hex_panel_modelling.parquet"
LADDER_CACHE = "hex_ladder_scores.csv"


def build_cached(
    data_dir: Path,
    *,
    cfg: ProjectConfig | None = None,
    rebuild: bool = False,
    verbose: bool = True,
) -> pd.DataFrame:
    """Load the assembled panel from cache, building it once if absent.

    Returns the panel with persistence and climate anomalies already attached,
    so every caller shares one baseline rather than each deriving its own.
    """
    cache = data_dir / PANEL_CACHE
    if cache.exists() and not rebuild:
        if verbose:
            print(f"panel: loaded from {cache.name}")
        return pd.read_parquet(cache)

    panel = load(data_dir, cfg=cfg)
    panel = add_persistence(panel)
    panel = add_climate_anomalies(panel, cfg=cfg)
    panel.to_parquet(cache, index=False)
    if verbose:
        print(f"panel: built and cached to {cache.name}  {panel.shape}")
    return panel


def baseline_scores(
    data_dir: Path,
    *,
    cfg: ProjectConfig | None = None,
    rebuild: bool = False,
) -> pd.DataFrame:
    """The persistence floor per branch — cached, so it is quoted not recomputed."""
    cache = data_dir / "hex_baseline_scores.csv"
    if cache.exists() and not rebuild:
        return pd.read_csv(cache)

    panel = build_cached(data_dir, cfg=cfg, rebuild=rebuild, verbose=False)
    _, test = split(panel, cfg=cfg)
    rows = []
    for target in ("starts_natural", "starts_human"):
        y = panel[target].to_numpy(float)
        pers = panel[f"pers_{target.replace('starts_', '')}"].to_numpy()
        for label, mask in (("all seasons", test),
                            ("JJA only", test & (panel["season_ord"] == 2).to_numpy())):
            ok = mask & np.isfinite(pers)
            rows.append({"target": target, "scope": label, "n_test": int(ok.sum()),
                         "spearman": rank_score(y[ok], pers[ok])})
    out = pd.DataFrame(rows)
    out.to_csv(cache, index=False)
    return out
