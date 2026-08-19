"""Forward-chaining predictors over the region-season panel.

This module exists because of one specific hazard. Across `05_features` through
`09_unknown_dataquality` the same idiom was written from scratch roughly eight
times:

    shifted = frame.groupby(["region", "season"])[cols].shift(1)
    sg = shifted.groupby([frame["region"], frame["season"]])
    pred = sg.rolling(k, min_periods=1).mean().reset_index(drop=True)

That is the leakage rule of the entire predictive result — for a target cell,
use only same-region/same-season occurrences at strictly earlier `season_idx` —
and it is subtly unsafe.

The hazard, demonstrated
------------------------
`groupby(...).rolling(...)` returns a frame indexed by
`(region, season, original_position)`, ordered **group-major**. The trailing
`reset_index(drop=True)` then re-attaches those values to the caller's frame
**positionally**. That is correct only if the caller's row order already equals
group-major order.

On an unsorted frame the idiom attaches one region's history to another
region's rows. Verified on a two-region frame ordered B-then-A: it returns
`[nan, 1.0, 1.5, nan, 10.0, 15.0]` when the correct per-row answer is
`[nan, 10, 15, nan, 1, 1.5]`. There is no NaN, no exception, the shares still
sum to 1, and TVD still computes to a plausible number. Nothing downstream can
detect it.

Every notebook happens to call `sort_values(["region","season","season_idx"])`
immediately beforehand, so the existing results are correct. But that safety
lives in a line of code with no visible connection to the thing it protects, and
an extracted helper will eventually be handed a filtered or re-ordered frame.

So this module does two things the inline idiom did not:

1. **Asserts the sort invariant on entry.** Wrong order raises rather than
   silently mis-attributing history.
2. **Returns index-aligned output**, never a positional re-attachment. Results
   are joined back by index, so they stay correct even on a non-default index
   (e.g. a frame that has been filtered without resetting).

Both are strict improvements; neither changes any number on correctly-sorted
input, which `tests/test_trailing.py` proves against the on-disk artifacts.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

# The panel's series identity: a prediction for a cell may only draw on earlier
# cells sharing these keys. `season_idx` (the third sort key) orders within a series.
GROUP_KEYS: tuple[str, ...] = ("region", "season")


class SortInvariantError(AssertionError):
    """Raised when a frame is not in the order the trailing idiom requires."""


def assert_sorted(frame: pd.DataFrame, *, group_keys: Sequence[str] = GROUP_KEYS) -> None:
    """Verify `frame` is ordered by (group keys..., season_idx), ascending.

    This is the guard described in the module docstring. It is cheap (one
    comparison against a re-sorted copy of the key columns) relative to the class
    of bug it prevents, so it runs on every call rather than behind a flag.
    """
    keys = list(group_keys) + ["season_idx"]
    missing = [k for k in keys if k not in frame.columns]
    if missing:
        raise SortInvariantError(f"frame is missing required key columns: {missing}")

    actual = frame[keys].reset_index(drop=True)
    expected = frame[keys].sort_values(keys, kind="mergesort").reset_index(drop=True)
    if not actual.equals(expected):
        raise SortInvariantError(
            "frame must be sorted by "
            f"{keys} before a trailing window is computed.\n"
            "The shift-then-roll idiom re-attaches its result group-major; on an "
            "unsorted frame it silently attaches one region's history to another "
            "region's rows (no NaN, no error, shares still sum to 1).\n"
            f"Fix: frame = frame.sort_values({keys}).reset_index(drop=True)"
        )


def _as_columns(cols: str | Sequence[str]) -> list[str]:
    return [cols] if isinstance(cols, str) else list(cols)


class TrailingMean:
    """Mean over the last `k` strictly-prior same-series values.

    The forward-chaining floor used throughout the project. `shift(1)` drops the
    target row, then a rolling mean covers at most `k` earlier rows of the same
    (region, season) series. With `min_periods=1` a prediction is available as
    soon as any history exists; a series' first occurrence is NaN, which is
    exactly the set of cells the baselines leave unscored.

    Parameters
    ----------
    k
        Window length. `None` means expanding (all prior values) — matching the
        `score_trailing(None)` convention in `06_analysis.ipynb`.
    min_periods
        Minimum prior observations required. The one place this is not 1 is
        `f_log_total_std` in the feature table, which needs 2 to have a spread.
    how
        Aggregation to apply: "mean" or "std" (the two the project uses).
    """

    def __init__(self, k: int | None = None, *, min_periods: int = 1, how: str = "mean"):
        if k is not None and k < 1:
            raise ValueError(f"k must be >= 1 or None (expanding), got {k}")
        if how not in {"mean", "std"}:
            raise ValueError(f"unsupported aggregation {how!r}; use 'mean' or 'std'")
        self.k = k
        self.min_periods = min_periods
        self.how = how

    def __repr__(self) -> str:
        window = "expanding" if self.k is None else f"k={self.k}"
        return f"TrailingMean({window}, how={self.how!r}, min_periods={self.min_periods})"

    def predict(
        self,
        frame: pd.DataFrame,
        cols: str | Sequence[str],
        *,
        group_keys: Sequence[str] = GROUP_KEYS,
    ) -> pd.DataFrame:
        """Trailing aggregate of `cols`, index-aligned to `frame`.

        Returns a DataFrame with the same index and column names as
        `frame[cols]`, so callers may assign it straight back or compare it
        column-by-column without worrying about row order.
        """
        assert_sorted(frame, group_keys=group_keys)
        columns = _as_columns(cols)
        gk = list(group_keys)

        # shift(1) within the series: the target row never sees itself.
        shifted = frame.groupby(gk, observed=True)[columns].shift(1)

        # Re-group the shifted values and roll. The result carries a
        # (group..., original-index) MultiIndex ordered group-major.
        regrouped = shifted.groupby([frame[k] for k in gk], observed=True)
        window = (
            regrouped.expanding(min_periods=self.min_periods)
            if self.k is None
            else regrouped.rolling(window=self.k, min_periods=self.min_periods)
        )
        out = getattr(window, self.how)()

        # Drop the group levels and realign BY INDEX -- never positionally.
        # This is what makes the result correct on a non-default index and
        # removes the hidden dependency on row order matching group order.
        out = out.reset_index(level=list(range(len(gk))), drop=True)
        return out.reindex(frame.index)[columns]


class T4Predictor:
    """Same season last year, requiring a true one-year step (no gap).

    Deliberately distinct from `TrailingMean(k=1)`. Both take the immediately
    prior same-season occurrence, but this one additionally requires that
    occurrence to be exactly four season-steps back (`season_idx - 4`), i.e. the
    previous season-year is actually present. Where a series has a gap, this
    yields NaN and the cell goes unscored.

    `06_analysis.ipynb` reports both and its narrative turns on the difference:
    `t4` is scored on fewer, gap-free cells (3,803) than `k=1` (3,949). Merging
    them would erase that distinction, so they stay separate classes.
    """

    STEP = 4  # four seasons per season-year on the project's monotonic spine

    def __repr__(self) -> str:
        return "T4Predictor(step=4)"

    def predict(
        self,
        frame: pd.DataFrame,
        cols: str | Sequence[str],
        *,
        group_keys: Sequence[str] = GROUP_KEYS,
    ) -> pd.DataFrame:
        assert_sorted(frame, group_keys=group_keys)
        columns = _as_columns(cols)
        gk = list(group_keys)

        grouped = frame.groupby(gk, observed=True)
        prev_idx = grouped["season_idx"].shift(1)
        is_true_t4 = (frame["season_idx"] - prev_idx) == self.STEP
        prior = grouped[columns].shift(1)
        return prior.where(is_true_t4, other=np.nan)


class GlobalPrior:
    """One constant for every cell: the weighted mean over training rows only.

    The deliberately uninformed reference used in the Natural, Human and Unknown
    branches — it knows nothing about which region-season it is predicting. Fit
    strictly on rows before `test_start` so it cannot see the held-out tail.

    In the Natural branch this predictor *beats* persistence on the acre-weighted
    metric, which is that branch's headline finding: on megafire cells a region's
    own calm-year history under-predicts badly, while a high global constant
    lands closer.
    """

    def __init__(self, *, weighted: bool = True):
        self.weighted = weighted
        self.value_: np.ndarray | None = None
        self.columns_: list[str] | None = None

    def __repr__(self) -> str:
        fitted = "unfitted" if self.value_ is None else f"value={np.round(self.value_, 4)}"
        return f"GlobalPrior(weighted={self.weighted}, {fitted})"

    def fit(
        self,
        frame: pd.DataFrame,
        cols: str | Sequence[str],
        *,
        train_mask: np.ndarray,
        weight_col: str | None = None,
    ) -> "GlobalPrior":
        columns = _as_columns(cols)
        self.columns_ = columns
        train = frame.loc[train_mask]
        values = train[columns].to_numpy(dtype=float)
        if self.weighted:
            if weight_col is None:
                raise ValueError("weighted=True requires weight_col")
            w = train[weight_col].to_numpy(dtype=float)
            self.value_ = np.average(values, axis=0, weights=w)
        else:
            self.value_ = values.mean(axis=0)
        return self

    def predict(self, frame: pd.DataFrame, cols=None, **_) -> pd.DataFrame:
        """Broadcast the fitted constant across every row of `frame`."""
        if self.value_ is None or self.columns_ is None:
            raise RuntimeError("GlobalPrior must be fit before predict")
        data = np.tile(self.value_, (len(frame), 1))
        return pd.DataFrame(data, index=frame.index, columns=self.columns_)


def sweep(
    frame: pd.DataFrame,
    cols: str | Sequence[str],
    windows: Sequence[int | None],
    score_fn,
    *,
    min_periods: int = 1,
    group_keys: Sequence[str] = GROUP_KEYS,
) -> pd.DataFrame:
    """Score a `TrailingMean` at each window in `windows`.

    `score_fn(predictions_ndarray) -> dict` supplies the metrics, so the same
    driver serves TVD (Tier 1, Human), log-MAE (Natural, Tier-1 level) and MAE
    (Unknown) without this module knowing anything about them. Index labels
    follow the notebooks' convention: "k=3", or "expanding" for `None`.
    """
    rows, labels = [], []
    for k in windows:
        pred = TrailingMean(k, min_periods=min_periods).predict(
            frame, cols, group_keys=group_keys)
        rows.append(score_fn(pred.to_numpy()))
        labels.append("expanding" if k is None else f"k={k}")
    return pd.DataFrame(rows, index=labels)
