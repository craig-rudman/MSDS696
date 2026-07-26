"""Project-wide constants and paths — the single source of truth.

Phase A of the OO refactor. Before this module, the constants below were
re-declared literal-by-literal in each notebook: `PARTIAL_WINTERS` in five
notebooks, `TEST_START` in four, the `MISSING` sentinel in four notebooks plus
two `src/` modules, and the season ordinal in both `04_cleaning.ipynb` (as
`SEASON_ORDER`) and `src/terraclimate.py` (as `SEASON_OFFSET`). Five independent
copies of a rule cannot be changed once; they can only drift.

Usage from a notebook (the import seam, following the precedent in
`07_natural_location.ipynb`):

    import sys; sys.path.insert(0, "../src")
    from config import ProjectConfig
    cfg = ProjectConfig()

Everything here is a constant of the *record* or a *locked analysis decision*.
Values that are tuned per-target deliberately do NOT live here — see the note on
`SHARES_K` below.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

ROOT = Path(__file__).resolve().parent.parent

# The single sentinel category FPA-FOD uses for unattributed cause. Cause is never
# null in this record — the gap lives in this category, which is why every
# missingness measure keys off equality with this string rather than `isna()`.
MISSING = "Missing data/not specified/undetermined"

# Meteorological season ordinal within a season-year. Used to build the monotonic
# `season_idx` spine. `src/terraclimate.py` calls this SEASON_OFFSET and
# `04_cleaning.ipynb` calls it SEASON_ORDER; both now source it here.
SEASON_ORDER: Mapping[str, int] = MappingProxyType({"DJF": 0, "MAM": 1, "JJA": 2, "SON": 3})

# Canonical season labels in chronological order within a season-year.
SEASONS: tuple[str, ...] = ("DJF", "MAM", "JJA", "SON")

# Coarse Tier-1 classes, in the fixed column order used by every share table.
TIER1_CLASSES: tuple[str, ...] = ("human", "natural", "unknown")

# The cell key. Region x season on a season-year spine; `season_idx` is the
# monotonic version of (season_year, season) and is what lag arithmetic uses.
CELL_KEYS: tuple[str, ...] = ("region", "season", "season_idx", "season_year")

# The sort order that the forward-chaining trailing-window idiom depends on.
# See src/trailing.py: the shift-then-roll pattern silently attaches one region's
# history to another region's rows if the frame is not in this order.
SORT_KEYS: tuple[str, ...] = ("region", "season", "season_idx")


@dataclass(frozen=True)
class ProjectConfig:
    """Immutable configuration for the wildfire cause-composition pipeline."""

    # --- paths ---------------------------------------------------------------
    root: Path = ROOT
    data: Path = ROOT / "data"
    img: Path = ROOT / "img"

    # --- record constants ---------------------------------------------------
    # First season-year in FPA-FOD 6th edition; the origin of the season_idx spine.
    base_year: int = 1992
    missing: str = MISSING

    # --- locked analysis decisions ------------------------------------------
    # Forward-chaining split: train strictly before this season_year, score from
    # it onward. This is the integrity claim of the predictive result.
    test_start: int = 2010

    # The two structurally-truncated DJF seasons at the ends of the record.
    # season_idx 0 is the winter cut short by the 1992-01-01 record start (it has
    # no December); 116 is the winter cut short by the 2020-12-31 end (December
    # only). Both are partial by construction, not by data quality, so they are
    # dropped rather than modeled.
    partial_winters: tuple[int, ...] = (0, 116)

    # The trailing window locked for the Tier-1 SHARES baseline. This is a
    # *result*, not a default: it is the acre-weighted argmin of the k-sweep in
    # 06_analysis.ipynb. It is named for its target on purpose — the level
    # baseline re-sweeps independently and lands elsewhere (k=6), and the Human
    # branch sweeps a different grid entirely. There is deliberately no generic
    # `default_k` here, because a generic name would erase the finding that k was
    # tuned per target. Each notebook keeps its own k-grid local.
    shares_k: int = 7

    # --- derived / structural ------------------------------------------------
    seasons: tuple[str, ...] = SEASONS
    # default_factory, not default: dataclasses reject a mappingproxy as a plain
    # default (it is not hashable-immutable in the way tuples are). The factory
    # hands back the same read-only proxy, so it still cannot be mutated.
    season_order: Mapping[str, int] = field(default_factory=lambda: SEASON_ORDER)
    tier1_classes: tuple[str, ...] = TIER1_CLASSES
    cell_keys: tuple[str, ...] = CELL_KEYS
    sort_keys: tuple[str, ...] = SORT_KEYS

    # --- artifact paths ------------------------------------------------------
    @property
    def fires_db(self) -> Path:
        """Raw FPA-FOD SQLite (6th edition, Short 2022)."""
        return self.data / "FPA_FOD_20221014.sqlite"

    @property
    def fires_clean(self) -> Path:
        """Fire-level artifact with the derived region/season keys attached."""
        return self.data / "fires_clean.parquet"

    @property
    def region_season_cause(self) -> Path:
        """The analysis grain: region x season_year x season x cause."""
        return self.data / "region_season_cause.parquet"

    @property
    def region_season_features(self) -> Path:
        """Trailing cross-sectional fingerprint features + Tier-1 targets."""
        return self.data / "region_season_features.parquet"

    @property
    def region_season_climate(self) -> Path:
        """TerraClimate pre-season covariates (built by src/terraclimate.py)."""
        return self.data / "region_season_climate.parquet"

    @property
    def conus_ecoregions(self) -> Path:
        """EPA Level III ecoregions, conterminous US."""
        return self.data / "us_eco_l3_state_boundaries" / "us_eco_l3_state_boundaries.shp"

    @property
    def ak_ecoregions(self) -> Path:
        """EPA Level III ecoregions, Alaska (a separate layer, its own CRS)."""
        return self.data / "ak_eco_l3" / "ak_eco_l3.shp"

    # --- helpers -------------------------------------------------------------
    def season_index(self, season: str, season_year: int) -> int:
        """Project-standard sequential season index.

        The monotonic spine: 4 seasons per season-year, ordered within the year,
        so `+1` is the next season and `+4` is the same season next year. Note
        the meteorological convention baked into `season_year` upstream — DJF of
        year Y spans December of Y-1 plus Jan/Feb of Y.
        """
        return (season_year - self.base_year) * 4 + self.season_order[season]

    def is_partial_winter(self, season_idx: int) -> bool:
        """Whether a season_idx is one of the truncated boundary winters."""
        return season_idx in self.partial_winters
