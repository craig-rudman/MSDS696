# Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation

MSDS696 Practicum II — a two-tier model of U.S. wildfire cause and ignition, built on the Fire Program Analysis Fire-Occurrence Database (FPA-FOD, 6th Edition), 1992–2020.

Prevention and mitigation resources are limited, and wildfires don't start — or burn — the same way everywhere. This project identifies regional and seasonal patterns in wildfire cause so that a state or regional fire-agency planner can match the intervention to the pattern instead of spreading effort uniformly.

**Research questions**

1. *(Descriptive)* Across a set of contrasting U.S. region-seasons, which wildfire causes drive the most burned area, and do those patterns differ enough to demand different prevention and mitigation strategies?
2. *(Predictive)* Can a next-season cause-risk profile — the expected composition of causes for a region and upcoming season, ranked by the burned area each is expected to drive — be predicted well enough to pre-target that prevention effort?

**Stakeholder** — a state or regional fire-agency planner deciding where to concentrate limited pre-season prevention and mitigation effort.

**What the planner gets.** A next-season cause-risk profile: for a given region and upcoming season, the expected composition of ignition causes, ranked for impact by the burn size each is expected to drive rather than by ignition counts, so effort concentrates on what will burn most. Each cell carries a confidence rank derived from its own pre-season history.

> Project requirements, working agreements, and the settled-question record live in [CLAUDE.md](CLAUDE.md), which is the single source of truth. This README is the outward-facing summary: architecture, results, limitations, and how to rebuild the whole thing from source.

**Reading this as a submitted document?** It is written to stand alone — every number is quoted with the population it describes, and no conclusion requires opening a linked file. Links point into the repository for a reader who wants to verify.

---

## Table of contents

- [Architecture](#architecture) · [Method commitments](#method-commitments) · [Inputs](#inputs)
- [Results](#results) · [Limitations and known defects](#limitations-and-known-defects)
- [Reproducibility](#reproducibility) · [Repository layout](#repository-layout) · [Project history](#project-history-by-week)

---

## Architecture

The model is **hierarchical**, not a flat 12-cause classifier.

### Tier 1 — coarse allocator

For a region-season, predict burned-area composition across three classes — **Human / Natural / Unknown** — on a *total-acres* denominator (resolved + missing) so the three shares sum to 1.

| class | share of record |
|---|---|
| Natural | 58.9% |
| Human | 22.7% |
| Unknown | 18.5% |

Across 179.3M acres. **Unknown is a predicted class in its own right**: it holds the `missing_acres` mass, and its share doubles as a regional attribution-quality signal.

Cause→class mapping: Natural = `Natural`; Human = all other resolved causes, including `Other causes`; Unknown = the `missing_acres` mass.

**The Human 22.7% is a floor.** Tier 1 predicts the Unknown share directly rather than distributing it onto Human and Natural, so the floor stays visible in the output. Because Unknown concentrates in human-dominated regions (see [Limitations](#limitations-and-known-defects)), the true Human share is if anything *higher*.

### Tier 2 — three branches

Each branch is a different question, target, and grain.

| branch | question | target | grain | notebook |
|---|---|---|---|---|
| **Ignition likelihood** | Where are fires most likely to start? | ignition counts | res-5 hex-season | [12](notebook/12_hex_ignition_baselines.ipynb), [14](notebook/14_hex_human_branch.ipynb) |
| **Human → cause** | What starts them? | sub-cause composition | Level III region-season | [08](notebook/08_human_cause.ipynb) |
| **Unknown → data quality** | Where is the record weak? | operational recommendation | Level III region-season | [09](notebook/09_unknown_dataquality.ipynb) |

RQ2's cause-risk profile is carried by **Tier 1 plus the Human branch**, both at Level III grain. The hex-grain ignition surface and the Unknown branch are methodologically distinct sub-projects — different grain, different target, different unit. The ignition surface is not an acres model.

### Two grains — never mixed

| | Level III region-season | res-5 H3 hex-season |
|---|---|---|
| unit | 105 ecoregions × season-year | 36,234 hexes × season-year |
| cell size | variable | ~62,494 acres |
| targets | Tier 1 allocator; Human sub-cause | ignition likelihood |

**Geometry follows the target, not preference.** FPA-FOD stores a *pinpoint* `LATITUDE`/`LONGITUDE`, but `FIRE_SIZE` describes an *area*. That mismatch decides which geometry each target may use:

- **Counts → raw points.** All ~2.27M fires, no MTBS join — an ignition location is exactly what the record stores correctly. Distributing a perimeter would corrupt a count by smearing one ignition across ~26 hexes.
- **Acres at hex grain → MTBS perimeters**, via [`src/hex_burn.py`](src/hex_burn.py), with per-fire weights summing to 1.0 so acres are conserved by construction. A fire larger than 62,494 acres provably cannot fit in its assigned cell. MTBS-linked fires are 0.6% of rows but **81.6% of acres**; point-only fires average 14 acres, where point attribution is fine — but that average hides a tail, and the tail is a [known defect](#3-point-attribution-of-large-unperimetered-fires).

### Prevention vs. mitigation, partitioned by lever

Fuel treatment, defensible space, and suppression pre-positioning are all **sited works** — whether they pay off depends on whether fire arrives there. That makes ignition likelihood a **mitigation-siting question regardless of cause**. Lightning is not "mitigation because it can't be prevented"; the lever is siting because mitigation is about where fuel and exposure sit, not what started the fire.

The operative distinction is between **regimes**: a hex can be high-ignition/low-acre (starts caught small — siting arguably already working) or low-ignition/high-acre (rare starts that run, where one ignition is expensive). Both are siting-relevant and call for different treatments.

---

## Method commitments

- **Persistence baseline first** — "region-season = its own last occurrence." Any model must beat it; added complexity is justified against it via an **ablation ladder**.
- **Forward-chaining temporal split**, held across five split years. Train 1992–2009, grade 2010–2020. No leakage.
- **Every external feature lagged to pre-season availability** — aggregated over `preseason_months()`, ending strictly *before* the target season opens. A window overlapping the season reads the burn scar itself and produces a spectacular, circular result. Neighbor features are built from already-lagged values.
- **Missing external data surfaces as NaN, never imputed to zero** — a zero anomaly reads as "average fuel," a fabricated observation.
- **Shuffled controls on every claimed gain**, reported in SD above the control distribution.
- **Cause reported as shares, not counts** — see the missing-cause constraint under [Limitations](#limitations-and-known-defects).
- **A null is publishable.** If a covariate does not beat the cheaper rung below it, that is the finding. Most of this project's results are nulls.

Shared machinery lives in [`src/hex_panel.py`](src/hex_panel.py): one panel assembly, one persistence baseline, one scorer, so no branch can score itself on a private definition.

---

## Inputs

**Spine** — FPA-FOD 6th Edition (Short 2022), ~2.3M U.S. wildfires, 1992–2020, SQLite. Cleaned in [04_cleaning.ipynb](notebook/04_cleaning.ipynb) → `data/fires_clean.parquet` (2,271,343 rows after exclusions).

- **Region** = EPA Level III ecoregion, via two separate spatial joins (CONUS *and* Alaska, which ship as different layers in different projections).
- **Season** = meteorological season, with a sequential season-year index as the temporal spine: `(FIRE_YEAR - 1992) * 4 + season_ordinal`, range 0–115 (winter 1992 → fall 2020). December belongs to the *next* winter, handled deliberately so lags line up. The season label is kept alongside the index — the index is the ordinal spine, the label carries the period-4 seasonal signal.
- `FIRE_YEAR` is preserved in the aggregation grain (ecoregion × season × year). Dropping it early would silently lock in a static target and foreclose the static-vs-dynamic question.
- **Exclusions:** PR, HI, and IA (32,223 rows) dropped in cleaning. EDA and missingness notebooks stay on the raw table.

**Covariate layers**

| module | layer | output |
|---|---|---|
| [`src/terraclimate.py`](src/terraclimate.py) | TerraClimate PDSI / soil moisture / deficit / VPD, area-weighted to Level III | `data/region_season_climate.parquet` |
| [`src/hex_climate.py`](src/hex_climate.py) | the same covariates re-fetched at hex grain | `data/hex_season_climate.parquet` |
| [`src/burn_history.py`](src/burn_history.py) | prior-burn state per hex-season, 4,239,378 cells | `data/hex_burn_history.parquet` |
| [`src/hex_ndvi.py`](src/hex_ndvi.py) | MODIS vegetation density (fuel load) via the Planetary Computer STAC API | `data/hex_season_ndvi.parquet` |

`hex_climate.py` imports `preseason_months` / `season_start` from `terraclimate.py`, so the December-boundary rule keeps exactly one definition in the project. The hex cache could not reuse the region-grain one — its checkpoints hold values already reduced to region means, and a region mean cannot be disaggregated back to hexes.

Prior burn is a **state, not a forecast** — known with certainty before the season opens. Point-only fires are excluded from it on semantic, not quality, grounds: 14 acres against a 62,494-acre hex (0.02%) would make the feature encode *where small fires get reported*, which near-leaks the ignition target.

**Grid artifacts** — `data/hex_grid_res5.parquet`, `data/hex_acres_res5.parquet`, `data/mtbs_perimeters/`. National coverage: 36,234 hexes, 105 ecoregions, **99.61% of acres on-grid** (loss is coastal). Two thirds of perimeter-backed fires span more than one hex.

LANDFIRE was evaluated and pre-rejected for this panel: a circa-2001 base map with discrete vintages, and Alaska only from the 2016 Remap, leaves almost no interannual variance to exploit.

---

## Results

### What the modeling established

**Persistence is the model to beat, everywhere.** Ignition Spearman: Human **+0.526** all-season (+0.593 MAM), Natural **+0.344** (+0.411 JJA). Shuffled controls fall within ±0.003 of zero on ignition and ±0.007 on acres, so the skill is spatial, not statistical luck.

**Where fires start is a property of the place, not the year.** Five consecutive covariate nulls on ignition targets — drought, prior burn, NDVI, and combinations, on both branches. The measured reason: these covariates identify dry *places*, not dry *years*. Under a within-hex anomaly, pdsi goes −0.137 → −0.073 and NDVI +0.228 → +0.098. Place is what history already knows.

**One verified covariate gain, on burned area only — and it is not useful.** Climate + NDVI together, **+0.0493**, **26.6 SD** above a shuffled control, holding across five split years. Both parts are jointly necessary: fuel load and fuel dryness, neither alone. But the gain lands in deciles 6–8 (1–20 acre fires), and the top decile goes 855× → 868×. A real effect in the wrong place is still a null for the planner.

**Ignition is a gate, not a dial.** A hex-season that ignites at all is **22.8×** more likely to produce a ≥1,000-acre burn (6.7% vs 0.29%), but escape probability *per ignition* falls with count, and 49% of large fires came from hexes with exactly one natural ignition. The rule is binary — *does this place ignite* — not graded.

**The two branches' tails differ by more than an order of magnitude**, which licenses different products. Quote the population with the number — the two natural figures are not interchangeable:

| population | top-decile under-prediction | median cell |
|---|---|---|
| Human, all seasons, all regions | 12.3× | 135 acres |
| Natural, all JJA burning cells | 269.8× | 2,970 acres |
| Natural, six forest ecoregions (covariate ladder) | 854.9× | 5,073 acres |

The like-for-like comparison against Human is **269.8×**, not 855×. Human can therefore be ranked by expected acres; Natural is delivered as a siting surface instead.

**A human sub-cause fingerprint at Level III is closed, not open.** Three learned rungs across two model families all lost to the k=7 trailing-mean floor (0.489 TVD / 54.1% top-1). Gradient boosting with history scores 0.554 / 47.5%; ridge with history scores **0.537 TVD / 52.2% top-1** — better than the booster, still short of simply taking the feature's mean. The `alpha` sweep is flat across four orders of magnitude, which is an information ceiling rather than an under-tuned model.

### Per-cell confidence, from pre-season dispersion

The planner needs the reliability flag *before* the season opens, so realized error — knowable only afterward — is the wrong quantity. `TrailingMean(k=7, how="std")` uses the **same window, same `shift(1)`, same `(region, season)` grouping** as the prediction itself, so it is strictly pre-season information, and it predicts the error of the trailing mean.

| | Tier 1 | Human |
|---|---|---|
| Spearman(dispersion, realized TVD) | **+0.484** | **+0.577** |
| SD above a 200-run shuffled control | 33 | 35 |
| accuracy, steadiest → most volatile quartile | **83.1% → 61.9%** | **72.5% → 39.4%** |
| series with n≥20 positive *within* a region | 74 / 93 | 80 / 92 |

**It is per-cell, not geography** — it holds *inside* individual regions, so it is about this cell in this year, not "some regions are stable places." **Each season carries its own level of trust**: Klamath sits at dispersion 0.121 / 75.8% accuracy in winter and 0.293 / 57.3% in summer. The spread is widest on the Human branch, the weaker product, which is the useful direction — its failures are anticipated rather than random.

**It ranks confidence; it does not calibrate it.** The honest phrasing is "this cell is in the steadiest quartile, which historically scored 83%," never "83% likely to be right." See the caveat under [Limitations](#4-confidence-is-ranked-not-calibrated).

---

## Limitations and known defects

Every substantive limitation found during the project is recorded here. Several of them cut against results stated above, and are reported at the same prominence.

### 1. Differential missing cause — the constraint that shapes the whole design

**~26% of records carry a Missing/undetermined cause.** Missingness is roughly flat across seasons but **differential across regions**: measured directly, missing-share correlates **negatively** with Natural share across ecoregions (Pearson ≈ **−0.64**), concentrating in low-Natural, human-dominated regions rather than the high-Natural West.

Consequences, applied throughout: cause is reported as **shares, not counts**; the **seasonal signal is treated as clean**, the **regional signal as directionally reliable but magnitude-caveated**; and Unknown is modeled as its own class rather than being redistributed, so the uncertainty stays visible instead of being silently allocated.

### 2. A 0.1-acre reporting floor distorts the small end

**25.3% of all cleaned rows are recorded at exactly 0.1 acres** — a default entered for a fire too small to measure, not a measurement — and it is **not evenly distributed: 44.5% of natural fires against 19.0% of human ones**. The share of fires ≤1 acre also drifts upward over the record, 58.4% (1992–2000) to 67.0% (2011–2020).

This cuts against the error story above. Restricting the decile analysis to cells ≥1 acre drops the smallest decile's apparent error from 10.0× to 4.3×, so **the over-prediction of small cells is partly a records artifact**. Above the floor the comparison sharpens rather than disappears: natural runs 2–3× worse than human *at matched cell size*.

### 3. Point attribution of large unperimetered fires

A point-only fire puts its **entire acreage on the single hex containing its ignition point** — correct at the 14-acre average, wrong in the tail:

- **2,710 point fires exceed 1,000 acres and carry 8.9% of all acres**, each concentrated on one cell.
- **23 point rows assign more than a full hex (62,494 ac) to one cell**, including the record's maximum: **606,945 acres — 971% of a hex.**
- Across both sources, 81 hex-seasons exceed one hex of natural acres and hold 8.3% of natural acres. The 69 perimeter-sourced cases are mostly legitimate — those fires genuinely are distributed, and Alaska megafires are simply larger than a cell. The 23 point-sourced cases are the defect.

**Why the published findings still stand:** the affected results use rank statistics — median log error by decile, cumulative acre share — so redistributing a few thousand cells shifts the top percentile's median without changing shape, direction, or conclusion. No claim in this README rests on an individual cell's acreage. The fix is designed but not executed: impute a circular burn from the ignition point, reusing the weight machinery already applied to perimeters. A 606,945-acre circle has a 28 km radius against a hex's ~9.9 km circumradius, so it would spread across ~10 cells. Two caveats carry into that build — fires elongate along wind and terrain, so a circle over-assigns upwind, a directional error in a product that sites work by location; and rebuilding the acres artifact invalidates the downstream notebooks, making it a re-run rather than a patch.

### 4. Confidence is ranked, not calibrated

The dispersion signal orders cells by reliability; it does not produce probabilities. **36 of 986 steadiest-quartile cells (3.7%) still scored below 25%**, several at dispersion exactly 0.000 — a settled history can precede a regime break, and those are the confident-looking misses.

More broadly, **no calibrated uncertainty is propagated anywhere**: every prediction is a point estimate. A Dirichlet over the composition is the principled next rung — the *ranking* is scale-invariant and does not need intervals, but the *acre level* is not and does.

### 5. The end-to-end composition does not inherit Tier 1's ranking error — but the acre level does

Composing Tier 1 × Human gives top-1 **0.4619** on 3,850 joined held-out cells — **identical to Human scored alone**, because Tier 1 contributes one scalar that multiplies all 11 sub-shares and cannot move their argmax. So the ranked profile is unaffected, while predicted human acres carry a median 1.01× but run 2× low at p10 and 8× high at p90.

**Do not quote Human's 54% as an end-to-end number** — that is the Human floor on its own population.

### 6. What remains open

- **Same-day escape conditions.** The nulls above are about *pre-season* covariates. Wind, timing, and suppression availability are a different model with a different data requirement — untested, and none of the nulls here extend to them.
- **Unknown triage by reporting stream.** The missingness pattern is agency-shaped; the current triage ranks by region only.
- **Missing-cause sensitivity bound.** Does the spatial Natural-share contrast survive if all missing fires were, or were not, Natural?
- **A higher-level allocation layer** ranking region-seasons against each other, not just causes within one — deferred by design.
- **No single planner walkthrough** joins Tier 1 to the branch products end to end.

---

## Reproducibility

The repository is designed so a reader can trace **problem → data → method → result** and re-derive the numbers.

### Sources are pinned, not vendored

The four third-party sources total ~2.3 GB and three exceed GitHub's 100 MB file limit, so none are committed. Instead:

- **[`data/SOURCES.md`](data/SOURCES.md)** — for each source: citation, canonical download URL, retrieval date, the path the code expects, and the stage-by-stage rebuild order.
- **[`data/checksums.sha256`](data/checksums.sha256)** — SHA-256 for all 16 source files, verifiable with `shasum -a 256 -c data/checksums.sha256`.

For data we did not create, the checksum is the stronger claim: it proves *which vintage* was used. That matters most for MTBS, which is reissued as fires are mapped, so a later download will legitimately not match.

### Rebuild order

With the four sources in place and the environment active:

```bash
conda env create -f environment.yml
conda activate msds696
shasum -a 256 -c data/checksums.sha256      # verify sources before trusting anything downstream
```

1. **Fire-level artifact** — [`04_cleaning.ipynb`](notebook/04_cleaning.ipynb) reads the SQLite, performs both ecoregion joins, derives the season spine, applies the exclusions, writes `fires_clean.parquet`. Everything is downstream of this.
2. **Level III grain** — [`05_features.ipynb`](notebook/05_features.ipynb) writes the cause and feature tables; [`src/terraclimate.py`](src/terraclimate.py) fetches climate covariates over OPeNDAP, checkpointing per year so an interrupted run resumes.
3. **Hex grain** — [`src/hex_burn.py`](src/hex_burn.py) distributes acreage across the res-5 H3 grid using MTBS perimeters; then `hex_ignitions`, `burn_history`, `hex_climate`, and `hex_ndvi` build their layers and [`src/hex_panel.py`](src/hex_panel.py) assembles the modelling panel.
4. **Verify** — `pytest`.

### Verification is a test suite, not a claim

[`tests/`](tests/) is a regression gate built during the OO refactor so structural changes can be *proven* not to move a published number:

| marker | covers |
|---|---|
| *(unmarked)* | synthetic unit tests on hand-built frames — the December rule, the 100%-missing orphan cell, a year gap in a trailing window |
| `requires_data` | artifact invariants: schema, exclusion rule, temporal spine, region key, cross-artifact acre reconciliation, content fingerprints |
| `slow` | metric pins — re-derives the published headline numbers against `tests/golden_metrics.json` |
| `requires_raw` | the checks that can only be expressed against the source SQLite |

Fingerprints are **content** hashes — row count, schema, an order-independent value hash, grand totals — not file hashes, because parquet writes are not byte-deterministic and a file hash would false-alarm on an identical rebuild. `n_cells` is pinned exactly while metrics use `approx` at 4 decimals: a silently-changed scorable population is the likeliest way a refactor corrupts a result, and it shows up in the count before the metric.

### Two honest caveats

**The network layers are not checksummed.** TerraClimate and MODIS are fetched at build time and are only as reproducible as the upstream services. A reprocessing would be *detected* by the fingerprint tests, not prevented.

**A rebuild reproduces the pipeline, not the environment.** `environment.yml` pins dependencies, but the golden metrics were captured on the environment that produced them; model-fitting rungs may move in the last decimals across library versions. That is why the tolerance convention exists.

### Dependencies

Declared in [environment.yml](environment.yml), each with a comment explaining why it is there. External data sources are open: TerraClimate over OPeNDAP, and MODIS via the Microsoft Planetary Computer STAC API, which serves its collections anonymously — no account, no API key, no OAuth.

---

## Repository layout

```
coursework/W1–W8   weekly assignments and work products; each week's
                   requirements are in that week's assignment.md
notebook/          analysis notebooks, numbered in pipeline order (01–17)
src/               extracted modules
literature/        literature review, with its own citation and sourcing rules
data/              sources and generated artifacts (untracked; see data/SOURCES.md)
img/               figures
tests/             regression suite for the pipeline modules
```

**Pipeline order** — cleaning ([04](notebook/04_cleaning.ipynb)), EDA ([02](notebook/02_eda.ipynb), [03](notebook/03_missingness.ipynb)), features ([05](notebook/05_features.ipynb)), analysis ([06](notebook/06_analysis.ipynb)), Level III branch notebooks ([07](notebook/07_natural_location.ipynb)–[09](notebook/09_unknown_dataquality.ipynb)), hex burn distribution ([10](notebook/10_hex_burn_demo.ipynb)), W5 visuals ([11](notebook/11_w5_visuals.ipynb)), hex-grain modeling ([12](notebook/12_hex_ignition_baselines.ipynb)–[14](notebook/14_hex_human_branch.ipynb)), W6 visuals ([15](notebook/15_w6_visuals.ipynb)), W7 visuals ([16](notebook/16_w7_visuals.ipynb)), covariate builders ([17](notebook/17_covariate_builders.ipynb)).

The [collaboration log](coursework/collaboration_log.md) records decisions contemporaneously and is **the authority when documents disagree**.

---

## Project history by week

The analysis is the product of eight weeks of scoping, and several of the strongest results are reversals. Each week's deliverables are in its `coursework/` directory.

| week | what happened |
|---|---|
| **W1** | Proposal: problem, stakeholder, and the two research questions. FPA-FOD selected as the spine. |
| **W2** | Feasibility and EDA. The ~26% missing-cause rate surfaced as the central design constraint rather than a cleaning nuisance. |
| **W3** | Missingness characterized by agency, state, size, and time; established as flat across seasons but differential across regions. Cause fixed to shares, not counts. |
| **W4** | Method defense. The flat 12-cause classifier was **rejected** in favor of the hierarchical Tier 1 + branches design. TerraClimate covariates returned a **pooled null** — per-region \|ρ\| 0.086–0.529, sign-inverting in two regions — read as "the covariates are real but the grain is wrong," which motivated the hex build. |
| **W5** | The point-vs-area asymmetry identified: a pinpoint location cannot carry an area target. MTBS perimeters joined and acreage distributed across a res-5 H3 grid, 99.61% of acres on-grid. |
| **W6** | Hex-grain modeling. Five covariate nulls on ignition; the one verified gain lands where it does not help. Prevention/mitigation re-partitioned **by lever, not by cause**, correcting an earlier compression error. The point-attribution defect found while sanity-checking cell acreages. |
| **W7** | Per-cell confidence from pre-season dispersion — the one new result, and free from the baseline already in use. The model-family question closed by running a linear rung: ridge beats the booster and still loses to the trailing mean. Repository hygiene and verification. |
| **W8** | Final deck, per-slide notes, acquisition manifest, and this README. |

---

## Sources

**FPA-FOD, 6th edition** — the spine: 2.27M fires, 1992–2020, with date, location, size and cause.
Short (2022) · Forest Service Research Data Archive · `doi.org/10.2737/RDS-2013-0009.6`

Joined onto it:

**EPA Level III ecoregions** — the regional unit: 105 regions, drawn from terrain, vegetation and climate.
U.S. EPA (2025) · Omernik & Griffith (2014) · `epa.gov/eco-research/ecoregions`

**MTBS burned-area perimeters** — fire as an area, not a point: 81.6% of acres, spread across cells.
Eidenshink et al. (2007) · USGS · `doi.org/10.5066/P9IED7RZ`

**TerraClimate** — drought before the season: PDSI, soil moisture, deficit, VPD.
Abatzoglou et al. (2018) · Climatology Lab · `climatologylab.org/terraclimate`

**MODIS MOD13A1 v6.1** — fuel load: 500 m vegetation index, via Microsoft Planetary Computer.
Didan (2021) · NASA LP DAAC · `doi.org/10.5067/MODIS/MOD13A1.061`

Access dates, file names and per-file checksums are in [`data/SOURCES.md`](data/SOURCES.md).
