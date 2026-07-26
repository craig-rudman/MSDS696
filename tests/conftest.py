"""Shared fixtures and markers for the pipeline regression suite.

Three tiers of test, selected by marker (see pytest.ini for the registrations):

  (unmarked)      Tier 1 -- synthetic unit tests. Hand-built frames of 5-20 rows,
                  no file I/O. These are where the edge cases live (the December
                  rule, the 100%-missing orphan cell, a year gap in a trailing
                  window), because a 2.3M-row assertion can only average over
                  them. Fast enough to run constantly.
  requires_data   Tier 2 -- artifact regression. Session-scoped reads of the
                  generated parquets, verifying schema, invariants, and content
                  fingerprints. Seconds, but needs the pipeline to have been run.
  slow            Tier 3 -- metric pins. Re-derives headline metrics (some fit
                  gradient-boosted models) and compares them to the values
                  captured from the pre-refactor notebook outputs.
  requires_raw    Needs the 918MB source SQLite or the EPA shapefiles. Excluded
                  by default; these are the checks that cannot be expressed
                  against the generated artifacts alone.

Default run (fast, no data dependency):
    pytest -m "not requires_data and not slow and not requires_raw"

Everything the artifacts can prove:
    pytest -m "not requires_raw"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from config import ProjectConfig  # noqa: E402  (needs the sys.path insert above)


# --------------------------------------------------------------------------
# Config / paths
# --------------------------------------------------------------------------
@pytest.fixture(scope="session")
def cfg() -> ProjectConfig:
    return ProjectConfig()


# --------------------------------------------------------------------------
# Captured baseline (Phase 0)
# --------------------------------------------------------------------------
@pytest.fixture(scope="session")
def fingerprints() -> dict:
    """Content fingerprints of the artifacts as they stood pre-refactor."""
    path = Path(__file__).parent / "fingerprints.json"
    if not path.exists():
        pytest.skip("fingerprints.json missing -- run tests/capture_baseline.py")
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def golden() -> dict:
    """Headline metrics scraped from the pre-refactor notebook outputs."""
    path = Path(__file__).parent / "golden_metrics.json"
    if not path.exists():
        pytest.skip("golden_metrics.json missing -- run tests/capture_baseline.py")
    return json.loads(path.read_text())


# --------------------------------------------------------------------------
# Artifacts. Session-scoped: fires_clean is 2.3M rows / 110MB, so it must be
# read at most once per run.
# --------------------------------------------------------------------------
def _read_or_skip(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        pytest.skip(f"{label} not found at {path} -- run the pipeline notebooks first")
    return pd.read_parquet(path)


@pytest.fixture(scope="session")
def fires(cfg) -> pd.DataFrame:
    """Fire-level artifact: one row per fire, derived keys attached."""
    return _read_or_skip(cfg.fires_clean, "fires_clean.parquet")


@pytest.fixture(scope="session")
def agg(cfg) -> pd.DataFrame:
    """The analysis grain: region x season_year x season x cause."""
    return _read_or_skip(cfg.region_season_cause, "region_season_cause.parquet")


@pytest.fixture(scope="session")
def features(cfg) -> pd.DataFrame:
    """Trailing fingerprint features + Tier-1 targets, one row per cell."""
    return _read_or_skip(cfg.region_season_features, "region_season_features.parquet")


@pytest.fixture(scope="session")
def agg_cells(agg, cfg) -> pd.DataFrame:
    """`agg` reduced to one row per region-season cell, boundary rule applied.

    The per-cell columns (`cell_acres`, `missing_acres`, ...) are constant across
    a cell's 12 cause rows, so deduplicating is the correct reduction -- summing
    them would inflate by 12x. That trap is the subject of its own test.
    """
    keys = list(cfg.cell_keys)
    cells = agg.drop_duplicates(keys)[
        keys + ["cell_acres", "missing_acres", "missing_fires", "missing_acre_frac"]
    ]
    return cells[~cells["season_idx"].isin(cfg.partial_winters)].reset_index(drop=True)
