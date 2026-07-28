# MSDS696 Practicum II — Project TODO

Durable task list for the wildfire cause × region × season project.
Week 2 feasibility verdict is essentially complete; items below are the
pipeline build and open questions that follow from it.

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
- [ ] **Feature engineering** — lagged burn/cause history (`t-1`, `t-4`), log fire
      size, per-region dominant-cause share; optional climate (drought/lightning)
      and fuel (LANDFIRE/satellite) integrations as predictive-lift hypotheses,
      tested by ablation (climate before fuels; all external features lagged to
      pre-season availability — no leakage).
- [ ] **Modeling (HIERARCHICAL — refined W4; see `W4/design_refinement.md`).**
      Tier 1: coarse Human/Natural/Unknown burned-area allocator (total-acres
      denominator). Tier 2 branch deep-dives: Natural→spatial burn-concentration,
      Human→sub-cause composition, Unknown→data-quality recommendation. Build
      Tier 1 first (all branches hang off it). Throughout: forward-chaining
      temporal split; ablation ladder vs. persistence baseline.
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
