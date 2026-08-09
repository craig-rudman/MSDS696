# MSDS696 Practicum II — Project TODO

Durable task list for the wildfire cause × region × season project.
Reconciled against the collaboration log through **W6 (2026-08-04)**.

**Two grains, do not mix them.** Tier 1 and the Human sub-cause branch work at
**EPA Level III region-season**. The ignition-likelihood surface works at
**res-5 H3 hex-season**. Which fire geometry to use follows from the target, not
from preference: *ignition counts use raw points* (the record stores ignition
location exactly right), *any acres quantity at hex grain uses MTBS perimeters*
(a point cannot carry an area, and a res-5 hex is ~62,494 acres).

## Pipeline design decisions (implement at the cleaning / feature-engineering stage)

- [ ] **Sequential season-year index.** Add `(FIRE_YEAR - 1992) * 4 + season_ordinal`
      (range 0–115, winter 1992 → fall 2020), season ordinal matching `to_season`
      (winter=0, spring=1, summer=2, fall=3). Handle the meteorological winter
      boundary (Dec belongs to the next winter) deliberately so lags line up.
      Keep the **season label** alongside the index — the index is the ordinal
      spine; the label carries the period-4 seasonal signal.
- [ ] **Preserve `FIRE_YEAR`** in the aggregation grain (ecoregion × season × year).
      Guardrail: dropping the year early silently locks in the static target.

## Open questions (settle in EDA)

- [ ] **Static vs. dynamic target.** Plot cause shares by year for the contrasting
      region-seasons. Stable mix → static/persistence honest; shifting mix →
      dynamic year-indexed target earns its keep. This EDA check makes the call.
- [ ] **Build the persistence baseline early** ("region-season = its own last
      occurrence"). The predictive model must beat it.

## Deferred analysis

- [ ] **Missing-cause sensitivity bound.** Cheap worst-case version in the
      feasibility notebook (does the spatial Natural-share contrast survive if all
      missing fires were / were not Natural?). Reportable version recomputed on
      full data in EDA.

## Pipeline stages (approach proven on the sample; run at scale)

- [ ] **Cleaning** — full 2.3M load; drop/flag Missing; ecoregion spatial join
      (CONUS *and* Alaska layers, both at EPA Level III; HI dropped per the
      exclusion rule); season + sequential index derivation.
- [ ] **EDA** — cause × region × season composition; year-over-year variability
      check; reportable sensitivity bound.
- [x] **Perimeter correction + hex grid (W5)** — `src/hex_burn.py`,
      `notebook/10_hex_burn_demo.ipynb`. MTBS perimeters joined via the `MTBS_ID`
      foreign key in the `Fires` table; burned acres distributed across res-5 hexes
      with weights summing to 1.0 per fire, so acres are conserved by construction.
      National: 36,234 hexes, 105 ecoregions, **99.61% of acres on-grid** (loss is
      coastal). MTBS-linked fires are 0.6% of rows but **81.6% of acres**; two thirds
      of perimeter-backed fires span more than one hex. Artifacts:
      `data/hex_grid_res5.parquet`, `data/hex_acres_res5.parquet`,
      `data/mtbs_perimeters/`.
- [ ] **Feature engineering** — lagged burn/cause history (`t-1`, `t-4`), log fire
      size, per-region dominant-cause share. External layers, tested by ablation;
      all lagged to pre-season availability — no leakage:
    - [x] **Climate at Level III** (`src/terraclimate.py`, run 2026-07-26 →
          `data/region_season_climate.parquet`). TerraClimate PDSI / soil moisture /
          deficit / VPD. **Result: a pooled null** in `07_natural_location.ipynb` —
          per-region Spearman |rho| 0.086–0.529 and sign-inverting, so pooling across
          105 regions averaged a real signal to zero. Reading: covariates are real,
          model grain is wrong.
    - [x] **Climate at hex grain** (`src/hex_climate.py`) — the re-fetch that tests
          that grain hypothesis. Old cache is unusable (holds region means; cannot
          disaggregate). Imports `preseason_months`/`season_start` rather than
          reimplementing them, so the DJF rule keeps one definition.
    - [x] **Prior-burn state per hex-season** (`src/burn_history.py`) — `any_burn` at
          1/3/5-season windows, `seasons_since_burn`, 4,239,378 cells. Perimeter rows
          only; point-only fires excluded on **semantic** grounds (14 ac vs a
          62,494-ac hex would encode *where small fires get reported*, near-leaking
          the ignition target). Prevalence 2.01% of hex-years. **Clamp caveat:**
          burned fraction clamped at 1.0, so genuine full burns and boundary-clipped
          partial hexes (0.759%) are indistinguishable afterward.
    - [ ] **Fuels imagery — still blocked.** Needs Earthdata / Google Earth Engine
          credentials. LANDFIRE pre-rejected for this panel (circa-2001 base map,
          discrete vintages, AK only from 2016 Remap → almost no interannual
          variance). *Note: climate is NOT blocked — W5's "blocked" line referred to
          fuels imagery only.*
- [ ] **Modeling (HIERARCHICAL — refined W4; see `W4/design_refinement.md`).**
      Tier 1: coarse Human/Natural/Unknown burned-area allocator (total-acres
      denominator). Tier 2 branch deep-dives: Human→sub-cause composition,
      Unknown→data-quality recommendation, and the former Natural branch
      **redefined W6** (below). Build Tier 1 first. Throughout: forward-chaining
      temporal split; ablation ladder vs. persistence baseline.
    - [ ] **Hex-grain ignition likelihood — replaces the Natural→location branch.**
          Target is *where fires are most likely to start*, at res-5 H3 (~62,494 ac),
          not burned-area concentration at Level III. Uses **raw ignition points, all
          ~2.27M fires, no MTBS join** — perimeter distribution would smear one
          ignition across ~26 hexes and corrupt the count. Rationale: prevention and
          mitigation partition by **lever** (sited works), not by cause, so ignition
          likelihood is a siting question regardless of what starts the fire.
          Watch for the two regimes: high-ignition/low-acre vs. low-ignition/high-acre.
          **Two design questions still open:** cause scope, and the exposure denominator.
    - [ ] **Test burn history against ignitions.** Deferred in W6 in favor of running
          the climate fetch first; costs nothing and is the cheapest read on whether
          the prior-burn feature earns its place.
    - [x] Measure the Natural-share × missing-share relationship directly
          (decides whether the Human-22.7%-is-a-floor caveat is live).
          RESOLVED W4 in `09_unknown_dataquality.ipynb`: the correlation is
          **negative** (Pearson ≈ −0.64) — Unknown concentrates in low-Natural,
          human-dominated regions, NOT the high-Natural West. The floor caveat
          is live, for the opposite reason: if unattributed acres are
          disproportionately human, true Human share is *higher* than 22.7%.

## Homework (not agent tasks)

- [ ] Verify the cited papers (Syphard et al. 2025; Chen & Jin 2022) use EPA
      Level III ecoregions specifically — read the PDFs.
- [ ] Confirm the Kaggle page states which FPA-FOD edition it mirrors.
