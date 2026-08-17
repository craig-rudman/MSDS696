# MSDS696 Practicum II

You are an agent tasked with helping the student complete each weekly assignment. Your role is to ensure the student follows the instructions and that their work satisfies the requirements.

**This file is the single source of project requirements.** Everything an agent needs to act correctly on this project is here: working agreements, the project definition, the architecture, the two-grain rule, what is built, and what is open. If a fact belongs in more than one place, it belongs here and is *referenced* elsewhere — duplicating it across files is what produced the doc drift cleaned up in W6 (collaboration log Entry 6.7). Keep it that way.

## Working agreements

- **Defer to the student's judgment.** Support the research; do not lead the inquiry or suggest solutions except when asked. Be concise and responsive to direction.
- **The student runs notebooks manually.** Edit cells when asked, but never execute a notebook.
- **Never assert current fire policy or practice.** This project observes what the data shows. Do not claim what agencies currently do, fund, or prioritize — ground every claim in observation.
- **Write collaboration-log entries as you go**, in small iterations alongside the work, not batched at the end of a session.
- **Verify before recommending.** Facts here reflect when they were written; if this file names a file, function, or column, confirm it still exists before building on it.

### Collaboration log

The student logs interactions that contribute significantly to project outcomes, at [coursework/collaboration_log.md](coursework/collaboration_log.md), following this convention:

- **Date:**
- **What was going on:** (one line of context)
- **The exchange:** (paste or link the actual conversation)
- **What the student kept, and why:**
- **What the student rejected or overrode, and why:**

The log is written contemporaneously with decisions, which makes it **the authority when documents disagree.** Reconcile toward it.

### Repository layout

- `coursework/W1`–`W8` — weekly assignments and work products. Each week's requirements are in that week's `assignment.md`. There is no central rubric or template directory: **the report template is the most recent status report** — copy its structure forward.
- `notebook/` — analysis notebooks, numbered in pipeline order (`01_feasibility.ipynb` … `11_w5_visuals.ipynb`).
- `src/` — extracted modules. `literature/` — literature review, with its own scoped instructions for citation and sourcing rules.
- `archive/` — superseded documents kept for history. **Do not treat anything in `archive/` as current**; its live content has been absorbed here.

## The Project

**Title:** Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation

### Problem statement

Prevention and mitigation resources are limited, and wildfires don't start — or burn — the same way everywhere. Identifying regional and seasonal patterns in wildfire cause could help fire planners target both prevention and mitigation resources more effectively.

### Research questions

1. **(Descriptive)** Across a set of contrasting U.S. region-seasons, which wildfire causes (natural and human) drive the most burned area, and do those patterns differ enough to demand different prevention and mitigation strategies?
2. **(Predictive)** Can a next-season cause-risk profile — the expected composition of causes for a region and upcoming season, ranked by the burned area each is expected to drive — be predicted well enough to pre-target that prevention effort?

### Stakeholder

A state or regional fire-agency planner deciding where to concentrate limited pre-season prevention and mitigation effort.

### The outcome

The planner can match the intervention to the pattern instead of spreading effort uniformly. The concrete product is a **next-season cause-risk profile**: for a given region and upcoming season, the expected composition of ignition causes, ranked for impact by the predicted burn size they drive (not merely ignition counts), so effort concentrates on what will burn most.

### Data and grain

**Fire Program Analysis Fire-Occurrence Database (FPA-FOD), 6th Edition** (Short 2022) — ~2.3M U.S. wildfires, 1992–2020, SQLite.

- **Region** = EPA Level III ecoregion, via two separate spatial joins (CONUS *and* Alaska layers).
- **Season** = meteorological season, plus a **sequential season-year index** as the temporal spine: `(FIRE_YEAR - 1992) * 4 + season_ordinal`, range 0–115 (winter 1992 → fall 2020), ordinal matching `to_season` (winter=0, spring=1, summer=2, fall=3). The meteorological winter boundary — **December belongs to the *next* winter** — must be handled deliberately so lags line up. Keep the season **label** alongside the index: the index is the ordinal spine, the label carries the period-4 seasonal signal.
- **Preserve `FIRE_YEAR`** in the aggregation grain (ecoregion × season × year). Guardrail: dropping the year early silently locks in a static target and forecloses the static-vs-dynamic question.
- **Cleaning exclusion:** drop PR, HI, and IA (32,223 rows) in `04_cleaning.ipynb` → `data/fires_clean.parquet`. EDA and missingness notebooks stay on the raw table.

### Known constraint — differential missing cause

~26% of records have a Missing/undetermined cause. Missingness is roughly flat across seasons but **differential across regions**. The direction was measured directly in W4 (`09_unknown_dataquality.ipynb`): missing-share correlates **negatively** with Natural share across ecoregions (Pearson ≈ −0.64) — it concentrates in **low-Natural, human-dominated** regions, *not* the high-Natural West. (`03_missingness.ipynb` characterizes it by agency, state, size, and time.)

Therefore: report cause as **shares, not counts**; treat the seasonal signal as clean and the regional signal as directionally reliable but magnitude-caveated. This question is **settled — do not reopen it.**

## Architecture

The model is **hierarchical**, not a flat 12-cause classifier. Agentic behavior must assume this structure. (Full W4 rationale: `archive/design_refinement.md`, superseded on the Natural branch by the W6 redefinition below.)

**Tier 1 — coarse allocator.** For a region-season, predict burned-area composition across three classes: **Human / Natural / Unknown**, on a *total-acres* denominator (resolved + missing) so the three shares sum to 1. Class shares over the full record: **Natural 58.9%, Human 22.7%, Unknown 18.5%** (179.3M acres). "Unknown" is a **predicted class in its own right** — it holds the missing-cause mass (`missing_acres`) and its share is a regional attribution-quality signal.

**Tier 2 — three heterogeneous branches**, each a different question, target, and grain:

| branch | question | target | grain |
|---|---|---|---|
| **Ignition likelihood** (former Natural→location, redefined W6) | Where are fires most likely to start? | ignition counts | res-5 hex-season |
| **Human → cause** | What starts them? | sub-cause composition | Level III region-season |
| **Unknown → data quality** | Where is the record weak? | operational recommendation, not a forecast | Level III region-season |

- **Cause→class mapping:** Natural = `Natural`; Human = all other resolved causes **including `Other causes`**; Unknown = the `missing_acres` mass (not a cause row). Reconstruct per-cell total as `cell_acres + missing_acres`; no cleaning re-run needed.
- **Scope of "prediction" (RQ2):** the next-season cause-risk profile is carried by **Tier 1 + the Human branch**, at Level III grain. The hex-grain ignition surface and the Unknown branch are methodologically distinct sub-projects — different grain, different target, different unit. Do not conflate them; in particular **the ignition surface is not an acres model.**
- **The Human 22.7% is a floor.** Tier 1 predicts the Unknown share directly rather than distributing it onto Human/Natural, so the floor stays visible in the output. Because Unknown concentrates in human-dominated regions (above), the true Human share is if anything *higher* than 22.7%.

### Prevention vs. mitigation partition by LEVER, not by cause

Settled W6 (Entry 6.3). Fuel treatment, defensible space and suppression pre-positioning are all **sited works** — whether they pay off depends on whether fire arrives there. That makes ignition likelihood a **mitigation-siting question regardless of cause.**

Do not reintroduce the framing that lightning "cannot be prevented, only planned around" as though it assigned Natural to mitigation and Human to prevention. That was a *compression error* in an earlier version of this file, not the W4 reasoning, which had it right: "the only lever is mitigation, and mitigation is about where fuel and exposure sit, not what started the fire."

The useful distinction is between **regimes**, not causes. A hex can be **high-ignition/low-acre** (starts caught small — siting arguably already working) or **low-ignition/high-acre** (rare starts that run, where one ignition is expensive). Both are siting-relevant and call for different treatments.

## Two grains — never mix them

| | Level III region-season | res-5 H3 hex-season |
|---|---|---|
| targets | Tier 1 allocator; Human sub-cause composition | ignition likelihood |
| unit | 105 ecoregions × season-year | 36,234 hexes × season-year |
| cell size | variable | ~62,494 acres |

**The point-vs-area asymmetry (W6 Entry 6.2 — load-bearing).** FPA-FOD stores a *pinpoint* `LATITUDE`/`LONGITUDE`, but `FIRE_SIZE` describes an *area*. That mismatch is what made an acres target expensive at hex grain and forced the MTBS perimeter build in W5. The same defect makes the **starts** target cheap: an ignition location is exactly what the record stores correctly. **Which geometry to use follows from the target, not from preference:**

- **Ignition counts → raw points**, all ~2.27M fires, no MTBS join. Perimeter distribution would corrupt a count by smearing one ignition across ~26 hexes.
- **Any acres quantity at hex grain → MTBS perimeters**, via `src/hex_burn.py`. A fire larger than 62,494 acres provably cannot fit in its assigned cell. MTBS-linked fires are 0.6% of rows but **81.6% of acres**; point-only fires average 14 acres, where point attribution is fine — **but the average hides a tail, and that tail is a known defect** (see *Point attribution of large unperimetered fires*, below).

## Method commitments

- **Persistence baseline first** ("region-season = its own last occurrence"). Any model must beat it; added complexity is justified against it via an **ablation ladder.**
- **Forward-chaining temporal split.** No leakage.
- **Every external feature is lagged to pre-season availability.** Aggregate over `preseason_months()`, ending strictly *before* the target season opens. A window overlapping the season reads the burn scar itself and produces a spectacular, circular result. Neighbor features must be built from already-lagged values.
- **Missing external data surfaces as NaN, never imputed to zero** — a zero anomaly reads as "average fuel," a fabricated observation.
- **A null is publishable.** If a covariate does not beat the cheaper rung below it, that is the finding.

## What is built

**Pipeline** — cleaning (`04`), EDA (`02`, `03`), features (`05`), analysis (`06`), Level III branch notebooks (`07`–`09`), hex burn distribution (`10`), W5 visuals (`11`), hex-grain modeling (`12`–`14`), W6 visuals (`15`).

**Perimeter correction and hex grid (W5)** — `src/hex_burn.py`, `notebook/10_hex_burn_demo.ipynb`. MTBS perimeters joined via the `MTBS_ID` foreign key in the `Fires` table; acres distributed across res-5 hexes with weights summing to 1.0 per fire, so acres are conserved by construction. National: 36,234 hexes, 105 ecoregions, **99.61% of acres on-grid** (loss is coastal). Two thirds of perimeter-backed fires span more than one hex. Artifacts: `data/hex_grid_res5.parquet`, `data/hex_acres_res5.parquet`, `data/mtbs_perimeters/`.

**Covariate layers — do not re-source these.**

- **`src/terraclimate.py`** — TerraClimate PDSI / soil moisture / deficit / VPD, area-weighted to Level III ecoregions, run 2026-07-26 → `data/region_season_climate.parquet`. The DJF leakage trap is unit-checked here. **W4 result: a pooled null** at this grain — per-region Spearman |ρ| ran 0.086–0.529 and *inverted sign* in two regions, so pooling across 105 regions averaged a real signal to zero. The reading is "the covariates are real but the grain of the model is wrong."
- **`src/hex_climate.py`** — the hex-grain re-fetch testing exactly that grain hypothesis. The old cache **cannot be reused**: its checkpoints hold values already reduced to region means, and a region mean cannot be disaggregated back to hexes. Imports `preseason_months`/`season_start` from `terraclimate.py` — **the DJF rule keeps exactly one definition in this project.**
- **`src/burn_history.py`** — prior-burn state per hex-season (4,239,378 cells; `any_burn` at 1/3/5-season windows, `seasons_since_burn`). Prior burn is a **state, not a forecast** — known with certainty before the season opens. **Point-only fires are excluded on semantic, not quality, grounds:** 14 acres against a 62,494-acre hex (0.02%) would make the feature encode *where small fires get reported*, which near-leaks the ignition target. Prevalence is low — 2.01% of hex-years carry a perimeter burn vs. 37.4% carrying any burn. **Clamp caveat:** burned fraction is clamped at 1.0, so genuine full burns and boundary-clipped partial hexes (0.759% of perimeter hex-years) are indistinguishable afterward.
- **`src/hex_ndvi.py`** — MODIS vegetation density (fuel load) per hex-season, via the **Planetary Computer STAC API, which needs no credentials.** That cleared the Earthdata/GEE blocker carried since W5: 55,923 hex-seasons across six forest ecoregions, 126/126 units, zero failures. Regional ordering is physically right (Klamath coastal forest 0.649; Idaho Batholith and Great Plains ~0.27). **Nothing is blocked now** — do not report climate *or* fuels imagery as pending. LANDFIRE stays pre-rejected for this panel (circa-2001 base map, discrete vintages, Alaska only from the 2016 Remap → almost no interannual variance).

**Hex-grain modeling (W6)** — `src/hex_ignitions.py` (ignition counts, all 2.27M fires on raw points), `src/hex_acres.py` (burned area, hurdle split), `src/hex_panel.py` (one panel assembly, one persistence baseline, one scorer). Notebooks `12` (Natural ignition), `13` (Natural acres), `14` (Human, both targets, scored **per season** — human fire runs in all four where **78.1%** of natural ignition falls in JJA).

**Settled by the W6 modeling — do not re-litigate.**

- **Persistence is the model to beat, everywhere.** Ignition Spearman: Human **+0.526** all-season (+0.593 MAM), Natural **+0.344** (+0.411 JJA); shuffled controls within ±0.003 of zero on ignition and ±0.007 on acres, so the skill is spatial, not statistical luck.
- **Five consecutive covariate nulls on ignition targets** (drought, prior burn, NDVI, and combinations, on both branches). The measured reason: these covariates identify dry *places*, not dry *years* — raw vs. within-hex anomaly, pdsi −0.137 → −0.073, NDVI +0.228 → +0.098 — and place is what history already knows. **Where fires start is a property of the place, not of the year.**
- **One verified covariate gain, on burned area only:** climate + NDVI together **+0.0493**, **26.6 SD** above a shuffled control, holding across five split years. Neither part works alone — fuel load and fuel dryness are jointly necessary. **But it is not useful:** the gain lands in deciles 6–8 (1–20 acre fires) and the top decile goes 855× → 868×.
- **A 0.1-acre reporting floor distorts the small end of any acres analysis.** 25.3% of all cleaned FPA-FOD rows are recorded at exactly 0.1 acres — **44.5% of natural fires against 19.0% of human ones** — a default entered for a fire too small to measure, not a measurement. The share of fires ≤1 acre also drifts up over the record (58.4% in 1992–2000 to 67.0% in 2011–2020). Restricting the decile analysis to cells ≥1 acre cuts the smallest decile's apparent error from 10.0x to 4.3x, so **the over-prediction of small cells is partly a records artifact.** Above the floor the picture sharpens: natural runs 2–3x worse than human *at matched cell size*, reaching 687x on a median 8,061-acre cell against human's 19x on 240.
- **The two branches' tails differ by more than an order of magnitude.** **Quote the population with the number — the two natural figures are not interchangeable:** across all JJA natural burning cells the top decile is **269.8×** under-predicted on a median cell of 2,970 acres; restricted to the six forest ecoregions used for the covariate ladder it is **854.9×** on a median of 5,073. Human is **12.3×** on 135 acres, all seasons, all regions. The like-for-like comparison against Human is therefore **269.8×**, not 855×. This still licenses *different products*: Human can be ranked by expected acres, Natural cannot.
- **Ignition is a gate, not a dial.** A hex-season that ignites at all is **22.8×** more likely to produce a ≥1,000-acre burn (6.7% vs 0.29%), but escape probability *per ignition* falls with count, and 49% of large fires came from hexes with exactly one natural ignition. The rule is binary — *does this place ignite* — not graded.

### Per-cell confidence from trailing dispersion (W7)

Settled in `06_analysis.ipynb`. `TrailingMean(k=7, how="std")` — the **same window, same `shift(1)`, same `(region, season)` grouping** as the prediction itself, so it is strictly pre-season information — predicts the error of the trailing mean.

- **Spearman(dispersion, realized TVD): +0.484 Tier 1, +0.577 Human**, at **33 and 35 SD** above a 200-run shuffled control.
- **Per-cell, not geography.** Holds *within* individual regions: 74/93 (Tier 1) and 80/92 (Human) of series with n≥20 are positive, median rho +0.175 / +0.267.
- **Quartiles of pre-season dispersion,** steadiest → most volatile: Tier 1 **83.1% → 61.9%** accuracy, Human **72.5% → 39.4%**. The spread is widest on the Human branch, which is the weaker product — its failures are anticipated rather than random.
- **Each season is its own series and carries its own confidence.** Klamath: DJF dispersion 0.121 at 75.8%, JJA 0.293 at 57.3%. One region, four different levels of trust.
- **It ranks confidence; it does not calibrate it.** Say "this cell is in the steadiest quartile, which historically scored 83%," never "83% likely to be right." **36 of 986 steadiest-quartile cells (3.7%) still scored below 25%**, several at dispersion exactly 0.000 — a settled history can precede a regime break, and those are the confident-looking misses.

### Known defect — point attribution of large unperimetered fires

Found W6 while sanity-checking cell acreages against hex area. **A point-only fire puts its entire acreage on the single hex containing its ignition point**, which is correct at the 14-acre average and wrong in the tail:

- **2,710 point fires exceed 1,000 acres and carry 8.9% of all acres**, each concentrated on one cell.
- **23 point rows assign more than a full hex (62,494 ac) to one cell**, including the record's maximum: **606,945 acres — 971% of a hex.**
- Across both sources, 81 hex-seasons exceed one hex of natural acres and hold **8.3% of natural acres**. The 69 perimeter-sourced cases are mostly legitimate — those fires *are* distributed (median 10 hexes, weights 0.10–1.0) and Alaska megafires are simply larger than a cell. The 23 point-sourced cases are the defect.

**Why it does not move the W6 findings.** Beats 11 and 12 use rank statistics — median log error by decile, cumulative acre share — so redistributing a few thousand cells shifts the top percentile's median without changing shape, direction, or conclusion. No claim in the deck rests on an individual cell's acreage.

**The W7 fix: impute a circular burn from the ignition point.** For a point-only fire, place a circle of the correct area centered on the ignition and distribute across the hexes it covers, reusing the weight machinery `hex_burn` already applies to perimeters. The geometry is favorable — a 606,945-acre circle has a **28 km radius against a hex's ~9.9 km circumradius**, so it spreads across ~10 cells instead of one. Two caveats to carry into the build: fires elongate along wind and terrain, so a circle over-assigns upwind and under-assigns downwind — a directional error in a product that sites work by location; and rebuilding `data/hex_acres_res5.parquet` invalidates notebooks 13–15 and every acres figure in the deck, so it is a re-run, not a patch.

## What is open

- **Same-day escape conditions.** The one question the W6 nulls leave genuinely open: **pre-season** covariates do not predict which igniting hexes escape, which is narrower than "nothing does." Wind, timing, and suppression availability are a different model with a different data requirement — untested.
- **A human sub-cause fingerprint at Level III — closed, not open.** Three learned rungs across two model families were tried and all lost to the k=7 floor (0.489 TVD / 54.1% top-1). The coarse Tier-1 fingerprint scores 0.588 / 35.7%: a region's coarse character does not recover its within-Human mix. **The history-aware rung was also built** (`08_human_cause.ipynb`, cell 21) — the same model handed the 11 trailing human-mix columns as features, i.e. the exact quantity the floor averages — and scores 0.554 / 47.5%, still 7 points short of taking that feature's mean. An earlier version of this file described that rung as "the remaining untried rung"; it is not.

  **The model-family question is also closed (W7).** Both plotted rungs are `SimplexRegressor` — `HistGradientBoostingRegressor` at stock settings — so "was the learner at fault?" was open until a linear rung was run in `08_human_cause.ipynb` (final section): ridge per sub-cause, everything else held identical. **Ridge with history scores 0.5366 TVD / 52.2% top-1, beating gradient boosting's 0.5536 / 47.5% and still losing to the floor's 0.4887 / 54.1%.** The booster was paying a variance cost on a small wide panel (~5,300 training cells, 23 features, 11 correlated targets); correcting it recovers ~5 points of top-1 and does not reach the trailing mean. **The `alpha` sweep is flat across four orders of magnitude** — top-1 identical to six decimals from 0.1 to 1000 — which is an information ceiling, not an under-tuned model. Ridge is not merely rediscovering the floor: 0.283 TVD units away per cell, 75.2% argmax agreement. What remains genuinely untried is a hyperparameter search over the booster, which the flat sweep makes unpromising.
- **Unknown triage by agency.** `09_unknown_dataquality.ipynb` ranks by region but not by reporting stream, and the missingness pattern is agency-shaped.
- **Missing-cause sensitivity bound.** Reportable worst-case: does the spatial Natural-share contrast survive if all missing fires were, or were not, Natural?
- **A higher-level allocation layer** that ranks region-seasons against each other, not just causes within one — deferred by design.
- **No single planner walkthrough** joins Tier 1 to the branch products end to end. *Partly measured W6:* composing Tier 1 × Human gives top-1 **0.4619** on 3,850 joined held-out cells — **identical to Human scored alone**, because Tier 1 contributes one scalar that multiplies all 11 sub-shares and cannot move their argmax. **The ranked profile therefore does not inherit Tier 1's error; the acre level does** (predicted human acres: median 1.01×, but 2× low at p10 and 8× high at p90). Do not quote Human's 54% as an end-to-end number — that is the Human floor on its own population.
- **No *calibrated* uncertainty is propagated anywhere.** Every prediction is still a point estimate, and a Dirichlet over the composition remains the principled next rung — the ranking is scale-invariant and does not need intervals, the acre level is not and does. **But a per-cell confidence *ranking* now exists** (W7, `06_analysis.ipynb`, final section) and is free from the baseline already in use.

**Closed in W6 — do not reopen.** Hex-grain cause scope and the exposure denominator (settled: counts on raw points, per-hex, no denominator). Burn history against ignitions (tested; null). Static vs. dynamic target (settled static: averaging beats `t-4`, and wider windows keep helping to k=7).

### Student homework (not agent tasks)

- Verify that Syphard et al. (2025) and Chen & Jin (2022) use EPA Level III ecoregions specifically — read the PDFs.
- Confirm which FPA-FOD edition the Kaggle page mirrors.
