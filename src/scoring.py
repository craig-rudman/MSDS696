"""Metrics and the mask/weight boilerplate they all share.

Free functions, deliberately not a `Scorer` class hierarchy. TVD is one line and
log-MAE is one line; there is no state to carry and no call site that receives an
unknown scorer and dispatches on it. A hierarchy here would only add a layer of
indirection over the exact arithmetic a reader needs to see to trust the result.

What *was* worth extracting is `score_masked`. That mask-then-average pattern
appeared five times across 06-09, and every copy had to get the NaN handling
right or it would silently score a different number of cells:

    m = in_test & ~np.isnan(metric_vec)
    unweighted = metric_vec[m].mean()
    weighted   = np.average(metric_vec[m], weights=w[m])

A changed scorable-cell population is the likeliest way a refactor corrupts a
published metric, and it shows up in the count before it shows up in the value --
so `score_masked` always returns `n_cells` alongside the metrics, and the tests
pin that count exactly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def tvd(pred: np.ndarray, actual: np.ndarray) -> np.ndarray:
    """Per-row total variation distance between two compositions.

    Half the L1 distance across the classes -- the natural distance on the
    simplex, in [0, 1]: 0 means identical composition, 1 means disjoint. Reads as
    "the share of the composition sitting in the wrong class".
    """
    return 0.5 * np.abs(np.asarray(pred) - np.asarray(actual)).sum(axis=1)


def absolute_error(pred: np.ndarray, actual: np.ndarray) -> np.ndarray:
    """Per-row |pred - actual|.

    Used directly for the Unknown branch (a bounded fraction, so raw points are
    the natural unit) and in log space for the level and Natural targets, where
    it reads as an error in orders of magnitude.
    """
    return np.abs(np.asarray(pred) - np.asarray(actual))


def top1_hit(pred: np.ndarray, actual: np.ndarray) -> np.ndarray:
    """Per-row: does the predicted argmax class match the actual argmax?

    The profile's headline is *which* class or cause to target, so this is its
    most legible skill check. `nanargmax` on the prediction side mirrors the
    notebooks -- rows with any NaN are excluded by the caller's mask anyway.
    """
    pred = np.asarray(pred)
    actual = np.asarray(actual)
    return np.nanargmax(pred, axis=1) == actual.argmax(axis=1)


def score_masked(
    metric_vec: np.ndarray,
    weights: np.ndarray,
    in_test: np.ndarray,
    *,
    extra: dict[str, np.ndarray] | None = None,
) -> dict[str, float | int]:
    """Average `metric_vec` over scorable test rows, unweighted and weighted.

    Scorable = in the held-out tail AND not NaN. A row is unpredictable when the
    cell has no prior history; those are excluded rather than imputed, which is
    what keeps the floor and the learned rungs scored on the same population.

    `extra` carries additional per-row boolean/float vectors (e.g. a top-1 hit
    indicator) to be averaged over the identical mask, so a second metric can
    never be computed over a different set of cells than the first.
    """
    metric_vec = np.asarray(metric_vec, dtype=float)
    weights = np.asarray(weights, dtype=float)
    mask = np.asarray(in_test, dtype=bool) & ~np.isnan(metric_vec)

    out: dict[str, float | int] = {"n_cells": int(mask.sum())}
    if not mask.any():
        return out
    out["unweighted"] = float(metric_vec[mask].mean())
    out["weighted"] = float(np.average(metric_vec[mask], weights=weights[mask]))
    for name, vec in (extra or {}).items():
        vec = np.asarray(vec, dtype=float)
        sub = vec[mask] if len(vec) == len(mask) else vec
        out[f"{name}_unweighted"] = float(sub.mean())
        out[f"{name}_weighted"] = float(np.average(sub, weights=weights[mask]))
    return out


def ladder(rows: dict[str, dict], *, baseline: str | None = None,
           metric: str = "weighted") -> pd.DataFrame:
    """Assemble a comparison table, optionally with a delta against a baseline.

    Every ablation table in 06-09 was hand-built as `pd.DataFrame([...],
    index=[...])` followed by a manual delta column. This does both, with the sign
    convention the notebooks use: NEGATIVE delta means the row beats the baseline
    (all metrics here are errors, so lower is better).
    """
    frame = pd.DataFrame(list(rows.values()), index=list(rows.keys()))
    if baseline is not None:
        if baseline not in frame.index:
            raise KeyError(f"baseline {baseline!r} not among {list(frame.index)}")
        frame[f"delta_vs_{'floor' if 'floor' in baseline else 'baseline'}"] = (
            frame[metric] - frame.loc[baseline, metric])
    return frame
