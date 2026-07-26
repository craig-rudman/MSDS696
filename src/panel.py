"""The region-season panel and the four branch targets built from it.

`region_season_cause.parquet` is long: one row per (region, season-year, season,
cause). Every modeling notebook begins by reshaping it to one row per
region-season **cell** and deriving its own target. Before this module each did
that inline, which meant the same three subtleties were re-implemented four times:

* **the coarse mapping** — Natural is the single `Natural` cause; Human is every
  other *resolved* cause including `Other causes`; Unknown is the `missing_acres`
  mass, which is not a cause row at all;
* **the dedup-don't-sum rule** — `missing_acres` and `missing_fires` are per-cell
  quantities repeated across the cell's 12 cause rows. Summing them inflates the
  Unknown mass 12x (measured: 397.5M acres instead of the correct 33.1M);
* **the boundary rule** — drop the two structurally-truncated DJF seasons.

Each is now written once. The dedup rule is additionally *asserted*, because a
mistake there would silently corrupt Tier 1, the feature table and the Unknown
branch at the same time.

What this module deliberately does NOT do
-----------------------------------------
The four target builders return frames of **different sizes**, and that is
correct, not an inconsistency to paper over. Each branch conditions on a
different population:

    tier1_composition()      total_ac > 0        ~10,135 cells
    human_subcause_shares()  human acres > 0     ~9,924 cells
    natural_acres()          all cells (caller filters nat_ac > 0)
    attribution_quality()    total_ac > 0        ~10,135 cells

`07_natural_location.ipynb` computes its `train`/`in_test` masks on the
Natural-positive subset specifically, so unifying these populations would change
its numbers. The differing row counts are pinned in tests.

There is also no `Branch` base class with a shared `ablation_ladder`. The four
branches do not share a control flow: 07's headline finding *is* a disagreement
between two metrics plus six diagnostic cells, 09 runs a cross-ecoregion
correlation study that is not a prediction at all, and 08 has a rung that feeds
its own floor back in as features. A common driver would need hooks for all of
that and would hide the very sequence the analysis is judged on. The notebooks
keep their narrative; this module just stops them retyping the plumbing.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import ProjectConfig

# The single 'Natural' cause label in FPA-FOD's NWCG general-cause vocabulary.
NATURAL = "Natural"


class RegionSeasonPanel:
    """One region-season panel, loaded once, with the branch targets on tap.

    Construct via `RegionSeasonPanel.load(cfg)`. The boundary rule is applied at
    construction, so every target inherits the identical cell set, and the frame
    is sorted by (region, season, season_idx) so `src.trailing` predictors can be
    handed any of these targets directly.
    """

    def __init__(self, rsc: pd.DataFrame, cfg: ProjectConfig, *, apply_boundary_rule: bool = True):
        self.cfg = cfg
        self.keys = list(cfg.cell_keys)

        # The frame as loaded, before the boundary rule. Kept because 06_analysis
        # reports the raw grain first and the boundary rule second -- the drop is part
        # of that notebook's narrative, so both states have to be inspectable.
        self.raw = rsc

        frame = rsc.copy()
        if apply_boundary_rule:
            before = frame.drop_duplicates(["region", "season_idx"]).shape[0]
            frame = frame[~frame["season_idx"].isin(cfg.partial_winters)].copy()
            after = frame.drop_duplicates(["region", "season_idx"]).shape[0]
            self.cells_dropped = before - after
            self.cells_before = before
            self.cells_after = after
        else:
            self.cells_dropped = 0
            self.cells_before = self.cells_after = frame.drop_duplicates(
                ["region", "season_idx"]).shape[0]

        # Coarse class per cause row. Natural is one cause; everything else that is
        # resolved counts as Human (including 'Other causes', which is a resolved
        # determination that happens to be miscellaneous). Unknown lives in
        # missing_acres and is deliberately not a value here.
        frame["coarse"] = np.where(frame["cause"] == NATURAL, "Natural", "Human")

        self.rsc = frame.sort_values(self.keys + ["cause"]).reset_index(drop=True)
        self._assert_per_cell_columns_constant()

    @classmethod
    def load(cls, cfg: ProjectConfig | None = None, **kwargs) -> "RegionSeasonPanel":
        cfg = cfg or ProjectConfig()
        return cls(pd.read_parquet(cfg.region_season_cause), cfg, **kwargs)

    def __repr__(self) -> str:
        return (f"RegionSeasonPanel({len(self.rsc):,} rows, "
                f"{self.rsc['region'].nunique()} regions, "
                f"{self.cells_after:,} cells)")

    # ----------------------------------------------------------------------
    # Invariants
    # ----------------------------------------------------------------------
    def _assert_per_cell_columns_constant(self) -> None:
        """`missing_*` must be constant within a cell, which is what makes the
        deduplication in `_per_cell()` correct rather than arbitrary."""
        cols = [c for c in ("missing_acres", "missing_fires", "missing_acre_frac")
                if c in self.rsc.columns]
        if not cols:
            return
        nuniq = self.rsc.groupby(self.keys, observed=True)[cols].nunique()
        bad = nuniq[(nuniq > 1).any(axis=1)]
        if len(bad):
            raise AssertionError(
                f"{len(bad)} cells have non-constant {cols} -- deduplication would be "
                "arbitrary and summing would be wrong. Check the aggregate build."
            )

    # ----------------------------------------------------------------------
    # Shared building blocks
    # ----------------------------------------------------------------------
    def _resolved_by_class(self) -> pd.DataFrame:
        """Resolved acres pivoted to one row per cell: `human_ac` / `natural_ac`."""
        out = (
            self.rsc.groupby(
                ["region", "season", "season_idx", "season_year", "coarse"], observed=True
            )["acres"].sum()
            .unstack("coarse", fill_value=0.0)
            .rename(columns={"Human": "human_ac", "Natural": "natural_ac"})
            .reset_index()
        )
        # A panel with no Natural (or no Human) rows at all would drop the column.
        for col in ("human_ac", "natural_ac"):
            if col not in out.columns:
                out[col] = 0.0
        return out

    def _per_cell(self, cols) -> pd.DataFrame:
        """Per-cell columns, DEDUPLICATED not summed.

        Keyed on (region, season_idx) -- season_idx determines both season and
        season_year, so this is equivalent to keying on all four cell keys, and
        it is the key the notebooks used. Tests pin the row count either way.
        """
        return self.rsc.drop_duplicates(["region", "season_idx"])[
            ["region", "season_idx"] + list(cols)]

    def _sorted(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Impose the order `src.trailing` requires, so targets are ready to use."""
        return frame.sort_values(list(self.cfg.sort_keys)).reset_index(drop=True)

    # ----------------------------------------------------------------------
    # Tier 1 -- the coarse allocator
    # ----------------------------------------------------------------------
    def tier1_composition(self, *, with_counts: bool = False) -> pd.DataFrame:
        """Human / Natural / Unknown shares on a TOTAL-acres denominator.

        Total = resolved (Human + Natural) + Unknown (`missing_acres`), so the
        three shares sum to 1 -- unlike `cause_share`, which conditions on
        attribution and therefore cannot represent the Unknown mass at all.

        `with_counts=True` additionally returns the fire counts and
        `mean_fire_size` that the feature table's regime-shape features need.
        """
        classes = list(self.cfg.tier1_classes)
        cell = self._resolved_by_class()

        per_cell_cols = ["missing_acres"] + (["missing_fires"] if with_counts else [])
        cell = cell.merge(self._per_cell(per_cell_cols), on=["region", "season_idx"], how="left")
        cell = cell.rename(columns={"missing_acres": "unknown_ac",
                                    "missing_fires": "unknown_fires"})

        if with_counts:
            cell["unknown_fires"] = cell["unknown_fires"].fillna(0.0)
            resolved_fires = (self.rsc.groupby(["region", "season_idx"], observed=True)["fires"]
                              .sum().rename("resolved_fires"))
            cell = cell.merge(resolved_fires, on=["region", "season_idx"], how="left")

        cell["total_ac"] = cell[["human_ac", "natural_ac", "unknown_ac"]].sum(axis=1)
        if with_counts:
            cell["total_fires"] = cell["resolved_fires"] + cell["unknown_fires"]

        cell = cell[cell["total_ac"] > 0].copy()      # a composition needs some burned area

        for name, acres in zip(classes, ["human_ac", "natural_ac", "unknown_ac"]):
            cell[name] = cell[acres] / cell["total_ac"]
        cell["log_total"] = np.log10(cell["total_ac"])
        if with_counts:
            cell["mean_fire_size"] = cell["total_ac"] / cell["total_fires"].clip(lower=1)

        cell = self._sorted(cell)
        assert np.allclose(cell[classes].sum(axis=1), 1.0), "compositions must sum to 1"
        return cell

    # ----------------------------------------------------------------------
    # Tier 2 -- Human: the sub-cause composition
    # ----------------------------------------------------------------------
    def human_subcause_shares(self) -> tuple[pd.DataFrame, list[str]]:
        """Shares across the resolved human sub-causes, on a HUMAN-only denominator.

        Returns `(frame, share_columns)`. Conditioning on Human means
        re-normalizing within the human sub-causes alone -- the existing
        `cause_share` column divides by all attributed acres, so its denominator
        carries the lightning mass. The Unknown mass is excluded entirely here.
        """
        human = self.rsc[self.rsc["cause"] != NATURAL]
        subcauses = sorted(human["cause"].unique())

        wide = (human.groupby(self.keys + ["cause"], observed=True)["acres"].sum()
                .unstack("cause", fill_value=0.0).reset_index())
        wide["human_total_ac"] = wide[subcauses].sum(axis=1)
        wide = wide[wide["human_total_ac"] > 0].copy()   # a composition needs some human burn

        shares = wide[subcauses].div(wide["human_total_ac"], axis=0)
        shares.columns = [f"sh_{c}" for c in subcauses]
        out = pd.concat([wide[self.keys + ["human_total_ac"]], shares], axis=1)
        out = self._sorted(out)

        share_cols = list(shares.columns)
        assert np.allclose(out[share_cols].sum(axis=1), 1.0), "human shares must sum to 1"
        return out, share_cols

    # ----------------------------------------------------------------------
    # Tier 2 -- Natural: the location target
    # ----------------------------------------------------------------------
    def natural_acres(self) -> pd.DataFrame:
        """Natural burned acres per cell, as `nat_ac`.

        Returns every cell, including zeros. The caller filters to `nat_ac > 0`
        before taking logs -- that positive subset is a genuinely different cell
        population, and 07 computes its split masks on it, so the filter is left
        to the caller rather than applied here.
        """
        nat = (self.rsc[self.rsc["cause"] == NATURAL]
               .groupby(self.keys, observed=True)["acres"].sum()
               .rename("nat_ac").reset_index())
        return self._sorted(nat)

    # ----------------------------------------------------------------------
    # Tier 2 -- Unknown: the attribution-quality target
    # ----------------------------------------------------------------------
    def attribution_quality(self) -> pd.DataFrame:
        """Per-cell missing-cause fraction plus the coarse acres it sits beside.

        `missing_acre_frac` is the branch's target; `Human`/`Natural`/`nat_share`
        support the cross-ecoregion correlation that settles whether the Unknown
        mass tracks Natural burn (it does not -- it concentrates in low-Natural,
        human-dominated regions).
        """
        res = (self.rsc.groupby(self.keys + ["coarse"], observed=True)["acres"].sum()
               .unstack("coarse", fill_value=0.0).reset_index())
        for col in ("Human", "Natural"):
            if col not in res.columns:
                res[col] = 0.0

        cell = res.merge(self._per_cell(["missing_acres", "missing_acre_frac"]),
                         on=["region", "season_idx"], how="left")
        cell["total_ac"] = cell["Human"] + cell["Natural"] + cell["missing_acres"]
        cell = cell[cell["total_ac"] > 0].copy()
        cell["nat_share"] = cell["Natural"] / cell["total_ac"]
        return self._sorted(cell)

    # ----------------------------------------------------------------------
    # Descriptive
    # ----------------------------------------------------------------------
    def class_acre_snapshot(self) -> pd.DataFrame:
        """Total acres and share for Human / Natural / Unknown over the panel.

        The table behind the design's 58.9% / 22.6% / 18.5% split. Unknown is
        deduplicated per cell, not summed -- summing gives 397.5M instead of 33.1M.
        """
        hn = self.rsc.groupby("coarse")["acres"].sum()
        unknown = self._per_cell(["missing_acres"])["missing_acres"].sum()
        snapshot = pd.DataFrame(
            {"acres": [hn.get("Human", 0.0), hn.get("Natural", 0.0), unknown]},
            index=["Human", "Natural", "Unknown"],
        )
        snapshot["Macres"] = snapshot["acres"] / 1e6
        snapshot["share"] = snapshot["acres"] / snapshot["acres"].sum()
        return snapshot
