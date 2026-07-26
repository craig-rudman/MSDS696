# Test suite

Regression gate for the wildfire cause-composition pipeline. Built during the OO
refactor so that structural changes to the pipeline can be proven not to move any
published number.

## Running

```bash
conda activate msds696

pytest                        # default: unit tests + artifact invariants (~15s)
pytest -m slow                # metric pins (fits gradient-boosted models)
pytest -m "not requires_raw"  # everything the generated artifacts can prove
pytest -o addopts="" -m ""    # literally everything, including the SQLite check
```

## The three tiers

| Marker | What it covers | Needs |
| --- | --- | --- |
| *(unmarked)* | Synthetic unit tests on hand-built 5–20 row frames. The edge cases live here — the December rule, the 100%-missing orphan cell, a year gap in a trailing window, the sort-invariant assertion firing — because a 2.3M-row assertion can only average over them. | nothing |
| `requires_data` | Artifact invariants: schema, exclusion rule, temporal spine, region key, aggregate grain, cross-artifact acre reconciliation, and content fingerprints. Ported from `04_cleaning.ipynb`'s validation cell. | the generated parquets |
| `slow` | Metric pins: re-derives the published headline numbers and compares them to the values captured from the pre-refactor notebook outputs. | parquets + sklearn |
| `requires_raw` | The three checks that cannot be expressed against the artifacts alone, because they closed over in-memory state from the SQLite load. | the 918 MB source DB |

## Baseline capture

`capture_baseline.py` produced two files, both committed:

- **`golden_metrics.json`** — headline scalars, parsed metric tables, and the raw
  per-cell output text scraped from the *already-executed* notebooks. Capturing
  from stored outputs rather than a fresh run is deliberate: it breaks the
  circularity of needing golden values from the notebooks being refactored, and it
  costs zero notebook executions.
- **`fingerprints.json`** — content fingerprints of the three pipeline parquets:
  row count, schema, an order-independent `hash_pandas_object` sum, and grand
  totals. **Not** file hashes — parquet writes are not byte-deterministic, so a
  file hash would false-alarm on an identical rebuild.

Re-run it only to establish a *new* baseline, deliberately:

```bash
python tests/capture_baseline.py
```

## Two conventions worth knowing

**`n_cells` is pinned exactly; metrics use `approx` at 4 decimals.** Float
accumulation order can shift a sum at ~1e-15 and that is not a finding. But a
silently-changed scorable-cell population is the likeliest way a refactor
corrupts a result, and it shows up in the count before it shows up in the metric.
The count is the canary.

**The notebook validation cell was kept, not replaced.** `04_cleaning.ipynb` still
prints its PASS/FAIL roster — that is graded evidence for a human reader.
`test_artifacts.py` is the machine-checkable gate over the same assertions. The
duplication is intentional; the two must agree.
