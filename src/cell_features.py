"""Per-cell modeling features: cause-composition target + missingness weight.

The predictive product is a region-season *cause-risk profile* — for each cell
(region x season, on a season-year spine) the composition of ignition causes,
ranked by the burned area each drives. This module builds that target and the
data-quality weight that goes with it, from a single pass over the fire record,
at whatever cell grain the caller specifies.

Why this lives in one place. The missingness section of `03_missingness.ipynb`
established (three independent probes: compositional stability over time, a
within-region-season correlation, and the cause-mix-by-size check) that the
`Missing/undetermined` bucket is *not* the mirror of any one cause — Natural
included — and that the residual non-randomness it does carry (it under-samples
small, human, Debris-heavy fires) lands on the *count*-weighted composition, not
the *acre*-weighted one the product ranks by. The operating conclusion was:
build the model on the cause-attributed record, treat Missing as "not a label,"
and carry each cell's missing rate as a data-quality covariate/weight so the
cells whose attributed target rests on a thin sample (disproportionately recent
western region-seasons — exactly the ones a next-season forecast leans on) are
flagged or down-weighted rather than silently trusted.

That weight is a pure function of the record (`mean(is_missing)` within a cell,
and the acre analog), so it is never stored separately — it is recomputed here
alongside the target, from the same frame, at the same grain, so the two cannot
drift out of sync. The only requirement upstream is that the cleaned artifact
*keeps* the ordinary Missing rows (flagged, not dropped); `04_cleaning.ipynb` does
exactly that — it drops only the no-signal PR/HI/IA streams.

Grain-agnostic by design. `cell_keys` is a parameter, so the same code serves
the STATE x season stand-in used in the missingness tests and the project's
actual ecoregion x season x season-year grain once that spine is finalized. The
caller is responsible for having already attached whatever key columns it names
(e.g. an ecoregion label from the spatial join, a season label, a season-year
index); this module only aggregates over them.

Honesty conventions consistent with the rest of the project:
  * cause composition is reported as SHARES within attributed fires, never raw
    counts — the stance that neutralizes the reporting biases the missingness
    section documented;
  * both a count-weighted and an acre-weighted share are returned, because the
    product ranks by burned area but the count view informs prevention targeting
    (the two-lever scope);
  * the weight is the observed missing RATE, a descriptive data-quality signal,
    not an imputation or a correction — nothing here fills in a missing cause.
"""
from __future__ import annotations

from typing import Sequence

import pandas as pd

# The single sentinel category FPA-FOD uses for unattributed cause. Matches the
# constant used across the notebooks.
MISSING = "Missing data/not specified/undetermined"


def add_missing_flag(df: pd.DataFrame, cause_col: str = "NWCG_GENERAL_CAUSE") -> pd.DataFrame:
    """Return a copy of `df` with a boolean `is_missing` column.

    `is_missing` marks the `Missing/undetermined` cause category (never a null —
    cause is always populated; the gap lives in the category). Idempotent: if the
    column already exists it is recomputed, so callers need not guard.
    """
    out = df.copy()
    out["is_missing"] = out[cause_col] == MISSING
    return out


def build_cell_targets(
    df: pd.DataFrame,
    cell_keys: Sequence[str],
    *,
    cause_col: str = "NWCG_GENERAL_CAUSE",
    size_col: str = "FIRE_SIZE",
    min_fires: int = 0,
) -> dict[str, pd.DataFrame]:
    """Build per-cell cause-composition targets and the missingness weight.

    One pass over `df` at the grain given by `cell_keys` (e.g.
    ``["US_L3NAME", "season", "season_year"]`` for the product grain, or
    ``["STATE", "season", "FIRE_YEAR"]`` for the missingness-test stand-in).
    Missing-cause rows are used ONLY to measure the weight; the composition
    targets are computed on the attributed rows, matching the "treat Missing as
    not-a-label" decision.

    Parameters
    ----------
    df
        Fire records. Must contain `cause_col`, `size_col`, and every column in
        `cell_keys`. An `is_missing` column is added if absent.
    cell_keys
        The columns that define a cell. Aggregation grain is fully caller-chosen,
        so this module never commits to region/season/spine definitions.
    cause_col, size_col
        Column names for cause label and fire size (acres).
    min_fires
        Drop cells with fewer than this many total fires (attributed + missing)
        from every returned table. Default 0 keeps all cells; the caller decides
        the stability threshold for its grain.

    Returns
    -------
    dict of DataFrames, all indexed by `cell_keys`:
      ``"weights"``      — one row per cell: `n_fires`, `n_attributed`,
                           `missing_rate` (count), `acres`, `attr_acres`,
                           `acre_missing_rate`. This is the data-quality
                           covariate/weight to carry into the model.
      ``"count_shares"`` — cause share of ATTRIBUTED fires per cell (columns are
                           causes; rows sum to 1). The count-weighted target.
      ``"acre_shares"``  — cause share of ATTRIBUTED acres per cell (columns are
                           causes; rows sum to 1). The acre-weighted target the
                           product ranks by.

    A cell with fires but zero attributed fires (all-Missing) appears in
    ``weights`` with `missing_rate == 1` and is absent from the share tables
    (no attributed base to form a composition) — an explicit, inspectable state
    rather than a silent NaN row.
    """
    df = add_missing_flag(df, cause_col=cause_col)
    keys = list(cell_keys)

    # --- weights: computed over ALL fires in the cell (missing included) ---
    def _missing_acres(s: pd.Series) -> float:
        return df.loc[s.index, size_col].where(df.loc[s.index, "is_missing"], 0.0).sum()

    weights = df.groupby(keys).agg(
        n_fires=("is_missing", "size"),
        n_attributed=("is_missing", lambda s: int((~s).sum())),
        missing_rate=("is_missing", "mean"),
        acres=(size_col, "sum"),
    )
    # missing acres via a separate grouped sum on the masked size (robust to the
    # index-alignment fragility of doing it inside .agg).
    miss_acres = (
        df.assign(_ma=df[size_col].where(df["is_missing"], 0.0))
        .groupby(keys)["_ma"].sum()
    )
    weights["attr_acres"] = weights["acres"] - miss_acres
    weights["acre_missing_rate"] = (miss_acres / weights["acres"]).where(weights["acres"] > 0)

    if min_fires > 0:
        weights = weights[weights["n_fires"] >= min_fires]

    # --- targets: computed over ATTRIBUTED fires only ---
    attr = df[~df["is_missing"]]

    count_counts = attr.groupby(keys)[cause_col].value_counts().unstack(fill_value=0)
    count_shares = count_counts.div(count_counts.sum(axis=1), axis=0)

    acre_sums = (
        attr.groupby(keys + [cause_col])[size_col].sum().unstack(fill_value=0.0)
    )
    acre_shares = acre_sums.div(acre_sums.sum(axis=1), axis=0)

    # Restrict share tables to the cells that survived the min_fires gate.
    kept = weights.index
    count_shares = count_shares.reindex(kept).dropna(how="all")
    acre_shares = acre_shares.reindex(kept).dropna(how="all")

    return {
        "weights": weights,
        "count_shares": count_shares,
        "acre_shares": acre_shares,
    }
