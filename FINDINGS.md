# Findings surfaced by the refactor

Things the refactor exposed that are **properties of the data or the original code**, not
consequences of restructuring. Recorded here so a future reader (or a future re-run) does
not mistake them for regressions.

---

## 1. Ecoregion boundary fires are geodetically unstable (14 fires, 830 acres)

**What happens.** Re-running the two-layer ecoregion join in the current environment assigns
a different `region` to 14 fires than the value stored in `data/fires_clean.parquet`. One
fire that previously matched no region now matches one; one that matched now does not.

**Why it is not a refactor bug.** I ran the *original* `join_ecoregion` function — copied
verbatim from the pre-refactor notebook — on the disputed points. It produces exactly what
the refactored `EcoregionJoiner` produces, and both disagree with the stored artifact. The
extracted code is faithful; the environment moved.

**Root cause.** All 14 fires sit within **centimetres** of an ecoregion seam:

| FOD_ID | stored region | distance to the adjacent polygon |
| --- | --- | --- |
| 236919 | Cascades | 0.31 m |
| 201770710 | Arizona/New Mexico Mountains | 0.06 m |
| 1443345 | Middle Atlantic Coastal Plain | 0.13 m |

The CONUS layer ships **1,631 polygons for only 85 distinct Level III names** — the EPA
splits them by state — so these points lie on shared edges between two records. Which side
they fall on is decided by the WGS84 → Albers reprojection at sub-metre precision, and that
decision differs between PROJ/GEOS versions. Current environment: geopandas 1.1.4,
pyproj 3.7.2, PROJ 9.7.1. The join is fully deterministic *within* this environment (three
repeat runs agree); it simply is not portable across PROJ releases at this precision.

**Scale.**

- 14 of 2,271,343 fires — **0.0006%** of rows
- 830 of 179,405,808 acres — **0.000463%** of burned area
- touches 11 of 10,276 region-season cells — **0.107%**
- 12 of the 14 are under 5 acres

**Net effect is a small improvement.** The largest affected fire (FOD_ID 400084304, 800
acres, Alabama) previously matched *no* ecoregion and was dropped from the aggregate; it now
correctly joins to Southern Coastal Plain. So the refactored join loses slightly less data
than the original.

**Consequence for the artifacts.** A 04 re-run in this environment will produce parquets that
differ from the Phase-0 fingerprints in these 14 rows and 11 cells. That is expected. The
fingerprints must be **deliberately re-captured** after the re-run, not treated as a failure.

**What is pinned instead.** `tests/test_cleaning.py::test_boundary_fires_are_a_negligible_share_of_acres`
asserts these fires can never carry enough acreage to move a published result (<1e-5 of
burned area). Pinning *which* region they get would be pinning a PROJ version, which is not
a property of the analysis.

**Not worth fixing.** A nearest-polygon fallback or a snap-to-grid tolerance would make the
join reproducible across environments, but it would add machinery for 0.0006% of rows and
0.0005% of acres — and it would change the region assignment of fires that are genuinely
ambiguous. The honest position is that region assignment is undefined at sub-metre distances
from a seam, and that this cannot affect any acre-weighted conclusion.

---

## 2. `f_log_total_std` uses a different `min_periods` than every other feature

**What happens.** In `05_features.ipynb`, `f_log_total_std` is built with `min_periods=2`
(a spread needs two observations) while every other trailing feature uses `min_periods=1`.
So it is NaN on 795 rows where the others are NaN on 402.

**Consequence.** `06_analysis.ipynb` gates its learned rung on
`feats[FEATCOLS].notna().all(axis=1)`, which is driven by the strictest column — giving
**3,941** test cells. The standalone persistence baselines earlier in the same notebook use
their own NaN mask and score **3,949**. Both numbers are correct for what they measure, and
the floor-vs-learned head-to-head is still fair because it is key-aligned onto the same rows.
But the floor's TVD appears twice in the notebook with slightly different values (0.2663 in
the k-sweep, 0.2659 in the head-to-head) because the populations differ by 8 cells.

**Decision: preserved deliberately.** A unified panel would naturally converge these masks
and silently change a published number. The refactor keeps the scorable mask a per-comparison
concern rather than a property of the panel, so both numbers stay exactly as reported. Fixing
it is a legitimate future choice, but it is an analysis decision, not a refactor cleanup.

---

## 3. The trailing idiom was silently order-dependent (fixed)

**What happened.** The `groupby.shift(1)` → `.rolling(k)` → `reset_index(drop=True)` pattern
re-attached its result **positionally**, which is correct only if the frame is already sorted
group-major. On a frame ordered by region B before region A it returns
`[nan, 1.0, 1.5, nan, 10.0, 15.0]` where the correct per-row answer is
`[nan, 10, 15, nan, 1, 1.5]` — one region's history attached to another region's rows, with
no NaN, no exception, shares still summing to 1, and TVD still computing to a plausible
number.

Every notebook happened to call `sort_values(["region","season","season_idx"])` immediately
beforehand, so **no published result was ever wrong**. But the safety lived in a line with no
visible connection to what it protected, and this pattern was retyped ~8 times.

**Fixed in Phase C.** `src/trailing.py` asserts the sort invariant on entry and returns
index-aligned output rather than a positional re-attachment. Verified on the real feature
table: the corrupted and correct versions share the same *mean*, so no summary statistic
could have caught it — the guard is the only defence.
