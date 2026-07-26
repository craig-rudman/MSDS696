"""Capture the pre-refactor baseline: golden metrics + artifact fingerprints.

Phase 0 of the OO refactor. This script is the mechanism that breaks the
dependency inversion in the refactor plan: the pytest regression suite needs
golden metric values, but those values are produced by the very notebooks being
refactored. Re-running the notebooks to get them would be both expensive (04 is
a full 2.3M-row load plus two spatial joins) and circular.

The resolution: the committed `.ipynb` files already contain their executed
outputs. This script reads those stored outputs as the golden record, so the
baseline is captured with zero notebook executions. The student's later manual
re-run then *confirms* the pin rather than producing it.

Two outputs, both written to `tests/`:

  golden_metrics.json   -- headline numbers scraped from notebook cell outputs,
                           plus the raw output text per cell so a human can audit
                           what was captured and add pins later without re-running.
  fingerprints.json     -- content fingerprints of the pipeline parquets. NOT file
                           hashes: parquet writes are not byte-deterministic across
                           pyarrow versions or row-group boundaries, so a file hash
                           would produce false alarms. Instead we pin row count,
                           schema, a pandas content hash, and grand totals.

Run from the repo root:  python tests/capture_baseline.py
Idempotent and read-only with respect to the pipeline; safe to re-run.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_DIR = ROOT / "notebook"
DATA = ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent


# --------------------------------------------------------------------------
# Notebook output extraction
# --------------------------------------------------------------------------
def cell_outputs(nb_path: Path) -> list[dict]:
    """Return [{cell_index, text}] for every code cell that produced text output.

    Both stream output (`text`) and execute_result/display_data
    (`data["text/plain"]`) are captured; figures and other MIME types are skipped.
    """
    nb = json.loads(nb_path.read_text())
    out = []
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        chunks = []
        for o in cell.get("outputs", []):
            if "text" in o:
                chunks.append("".join(o["text"]))
            elif "data" in o and "text/plain" in o["data"]:
                chunks.append("".join(o["data"]["text/plain"]))
        text = "".join(chunks).strip()
        if text:
            out.append({"cell_index": i, "text": text})
    return out


def find_number(text: str, pattern: str, cast=float):
    """First regex group-1 match in `text`, cast; None if the pattern is absent."""
    m = re.search(pattern, text)
    return cast(m.group(1).replace(",", "")) if m else None


def parse_keyvalue_block(text: str) -> dict[str, float]:
    """Parse an indented `name    value` metric block.

    08's floor cell prints its metrics with a per-key loop rather than
    `DataFrame.to_string()`, so `parse_metric_table` does not see it. Those five
    numbers are the Human branch's headline floor, so they get their own parser.
    Only lines of the form `<indent><identifier><spaces><number>` are taken.
    """
    out: dict[str, float] = {}
    for ln in text.splitlines():
        m = re.match(r"^\s{2,}([A-Za-z][\w]*)\s{2,}([\d,]+\.?\d*)\s*$", ln)
        if m:
            out[m.group(1)] = float(m.group(2).replace(",", ""))
    return out


def parse_metric_table(text: str) -> dict[str, dict[str, float]]:
    """Parse a printed pandas frame whose first token per line is a row label.

    Handles the metric tables in 06-09 (`ksweep`, `scores`, `ladder`, ...), which
    are emitted via `DataFrame.to_string()`. Returns {row_label: {col: value}}.
    Lines that do not parse as label-plus-all-numerics are skipped, so surrounding
    prose in the same output blob is ignored.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    header: list[str] | None = None
    rows: dict[str, dict[str, float]] = {}
    for ln in lines:
        tokens = ln.split()
        # A header line is all-non-numeric tokens that look like metric names.
        if header is None:
            if tokens and all(re.match(r"^[A-Za-z_][\w%]*$", t) for t in tokens) and any(
                "TVD" in t or "MAE" in t or "n_cells" in t or "hit" in t or "x_off" in t
                or "RMSE" in t or "share" in t or "HHI" in t for t in tokens
            ):
                header = tokens
            continue
        # Data line: trailing tokens must all be numeric; the rest is the label.
        numeric_tail: list[float] = []
        idx = len(tokens)
        while idx > 0:
            try:
                numeric_tail.insert(0, float(tokens[idx - 1].replace(",", "").rstrip("%")))
                idx -= 1
            except ValueError:
                break
        if numeric_tail and idx > 0 and len(numeric_tail) == len(header):
            rows[" ".join(tokens[:idx])] = dict(zip(header, numeric_tail))
    return rows


# Headline scalars worth pinning explicitly, as (notebook, key, regex) triples.
# Everything else stays available in the raw per-cell text for later pinning.
SCALAR_PINS = [
    ("06_analysis", "agg_rows", r"([\d,]+) rows\s+\|\s+\d+ regions"),
    ("06_analysis", "cells_after_boundary_rule", r"->\s+([\d,]+)\)"),
    ("06_analysis", "tier1_cells", r"([\d,]+) region-season cells \| season_years"),
    ("06_analysis", "shares_test_cells", r"head-to-head on ([\d,]+) held-out cells"),
    ("06_analysis", "top1_unweighted_pct", r"unweighted\s+([\d.]+)%"),
    ("06_analysis", "top1_acre_wtd_pct", r"acre-weighted ([\d.]+)%"),
    ("07_natural_location", "natural_cells_positive", r"\|\s+([\d,]+) with Natural burn > 0"),
    ("07_natural_location", "global_prior_log_acres", r"global prior = ([\d.]+) log-acres"),
    ("08_human_cause", "human_rows", r"([\d,]+) rows \| \d+ human sub-causes"),
    ("08_human_cause", "human_cells", r"([\d,]+) region-season cells with human burn"),
    ("09_unknown_dataquality", "unknown_cells", r"([\d,]+) region-season cells"),
]


def capture_golden_metrics() -> dict:
    """Scrape stored outputs from the modeling notebooks into a golden manifest."""
    notebooks = [
        "04_cleaning", "05_features", "06_analysis",
        "07_natural_location", "08_human_cause", "09_unknown_dataquality",
    ]
    manifest: dict = {
        "_provenance": (
            "Scraped from committed notebook outputs at refactor Phase 0 "
            "(no notebooks were executed). Values are the pre-refactor golden "
            "record the refactor must reproduce."
        ),
        "notebooks": {},
    }

    for name in notebooks:
        path = NOTEBOOK_DIR / f"{name}.ipynb"
        if not path.exists():
            continue
        outs = cell_outputs(path)
        blob = "\n".join(o["text"] for o in outs)

        scalars = {}
        for nb_name, key, pattern in SCALAR_PINS:
            if nb_name != name:
                continue
            val = find_number(blob, pattern)
            if val is not None:
                scalars[key] = val

        tables = {}
        blocks = {}
        for o in outs:
            parsed = parse_metric_table(o["text"])
            if parsed:
                tables[f"cell_{o['cell_index']}"] = parsed
            kv = parse_keyvalue_block(o["text"])
            if kv:
                blocks[f"cell_{o['cell_index']}"] = kv

        manifest["notebooks"][name] = {
            "scalars": scalars,
            "metric_tables": tables,
            "keyvalue_blocks": blocks,
            "raw_outputs": outs,
        }
    return manifest


# --------------------------------------------------------------------------
# Artifact fingerprints
# --------------------------------------------------------------------------
# Grand totals worth pinning per artifact, beyond shape and schema. Only columns
# that exist are used, so one spec serves both artifacts.
SUM_COLS = ["FIRE_SIZE", "acres", "fires", "cell_acres", "missing_acres", "missing_fires"]
NUNIQUE_COLS = ["region", "na_l2name", "season", "season_year", "season_idx", "cause", "STATE"]


def fingerprint(path: Path) -> dict:
    """Content fingerprint of a parquet artifact.

    Deliberately not a file hash -- parquet writes are not byte-deterministic, so
    a file hash yields false alarms on an unchanged rebuild. These fields are
    invariant under re-serialization but sensitive to any change in the data.
    """
    df = pd.read_parquet(path)
    fp: dict = {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "columns": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        # Order-independent content hash: sum of per-row hashes. Catches any changed
        # value while tolerating a different row ordering on rebuild.
        "content_hash": int(pd.util.hash_pandas_object(df, index=False).sum()),
    }
    fp["sums"] = {
        c: float(df[c].sum()) for c in SUM_COLS if c in df.columns
    }
    fp["nunique"] = {
        c: int(df[c].nunique()) for c in NUNIQUE_COLS if c in df.columns
    }
    return fp


def capture_fingerprints() -> dict:
    artifacts = {
        "fires_clean": DATA / "fires_clean.parquet",
        "region_season_cause": DATA / "region_season_cause.parquet",
        "region_season_features": DATA / "region_season_features.parquet",
    }
    out = {
        "_provenance": (
            "Content fingerprints of the pre-refactor pipeline artifacts. Pinned so "
            "a post-refactor rebuild can be proven content-identical without a byte "
            "comparison (parquet writes are not byte-deterministic)."
        ),
    }
    for name, path in artifacts.items():
        if path.exists():
            out[name] = fingerprint(path)
            print(f"  fingerprinted {name}: {out[name]['n_rows']:,} rows x {out[name]['n_cols']} cols")
        else:
            print(f"  SKIP {name}: {path} not found")
    return out


def main() -> None:
    print("Capturing golden metrics from notebook outputs (no execution)...")
    metrics = capture_golden_metrics()
    (OUT_DIR / "golden_metrics.json").write_text(json.dumps(metrics, indent=2))
    for nb, payload in metrics["notebooks"].items():
        print(f"  {nb}: {len(payload['scalars'])} scalars, "
              f"{len(payload['metric_tables'])} metric tables, "
              f"{len(payload['raw_outputs'])} output cells")

    print("\nFingerprinting artifacts...")
    fps = capture_fingerprints()
    (OUT_DIR / "fingerprints.json").write_text(json.dumps(fps, indent=2))

    print(f"\nWrote {OUT_DIR / 'golden_metrics.json'}")
    print(f"Wrote {OUT_DIR / 'fingerprints.json'}")


if __name__ == "__main__":
    main()
