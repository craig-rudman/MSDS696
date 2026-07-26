# Weekly Status Report

| Name | | Week / Date | |
| --- | --- | --- | --- |
|  Craig Rudman |  |  Week 4 / 2026-07-25 |  |

## Project title
Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation

## Project summary

This project asks two linked questions. The first is descriptive: across contrasting U.S. region-seasons, which wildfire causes burn the most acres, and do those patterns differ enough to call for different prevention or mitigation strategies? The second is predictive: can I forecast next season's mix of causes for a region well enough to target that effort before the season starts? The goal is to let a state or regional fire planner match the response to the pattern.

The data is the Fire Program Analysis Fire-Occurrence Database (FPA-FOD), about 2.3M U.S. wildfires from 1992 to 2020. I group the fires by cause, EPA Level III ecoregion, and meteorological season, then train a model on those historical patterns.

The model works in two steps. First it splits a region-season's burned acres across three broad classes: Human, Natural, and Unknown, where Unknown means the record never recorded a cause. Then each class gets its own follow-on model, because each one raises a different question.

The forecast that answers the predictive question comes from the first step plus the Human class. For a given region and upcoming season, it gives the expected mix of ignition causes, ranked by how many acres each is likely to burn rather than by how many fires it starts. That lets a planner put prevention effort where the acres are. The Natural class asks a different question — where the acres will concentrate — because lightning cannot be prevented, only planned around. The Unknown class treats unrecorded causes as a sign of weak reporting and points to the regions and data sources where better cause data would help most.

## The research questions, restated

This report refers to my two research questions, so I'll restate them here:

- RQ1 (descriptive): Across a set of contrasting U.S. region-seasons, which wildfire causes (natural and human) drive the most burned area, and do those patterns differ enough to demand different prevention and mitigation strategies?
- RQ2 (predictive): Can a next-season cause-risk profile — the expected composition of causes for a region and upcoming season, ranked by the burned area each is expected to drive — be predicted well enough to pre-target that prevention effort?

## Milestones

- Data acquisition: load FPA-FOD 2.3M edition (1992–2020), confirm schema and record count
- Feasibility assessment: sample-scale approach validation, missing-cause and regional-contrast checks
- EDA: cause × year composition; Natural-cause size distribution; human-cause composition; missing-cause characterization
- Cleaning: documented exclusion; EPA Level III ecoregion spatial join (CONUS and Alaska layers); derive meteorological season + sequential season-year index; preserve FIRE_YEAR; write the fire-level and region-season-cause artifacts
- Method design & justification: settle the model structure (flat vs. hierarchical) and defend the estimator choice against the alternative
- Feature engineering: lagged burn/cause history (t-1, t-4), log fire size, per-region dominant-cause share, per-cell missing rate as a data-quality weight; optional climate/fuels integrations as predictive-lift hypotheses (lagged to pre-season, no leakage)
- Modeling: persistence baseline first; predict region-season cause composition; predict expected burn size per cause to weight impact; forward-chaining temporal split; ablation ladder vs. baseline
- Findings & prevention strategies: rank causes within each region-season by predicted burn impact; translate contrasting archetypes into matched prevention recommendations; write up

## Last week's "To Do"

- Extend the descriptive comparison to the region dimension on `region_season_cause.parquet`: cause × ecoregion × season composition, and identify the contrasting region-season archetypes RQ1 compares.
- Build the persistence baseline ("region-season = its own last occurrence") via `season_idx.shift(1)`, and settle the scoring metric for a predicted cause composition.
- Set up the forward-chaining temporal split on `season_idx`.
- Decide Alaska's modeling treatment — in-grain with everything else, or flagged as an edge case.

All four are addressed below. The region-composition work changed the model's structure, and Alaska's treatment was resolved as a consequence.

## This week's progress

Week 4's assigned focus is to choose and justify the method. I extended the descriptive comparison to the region axis, and the result changed the model's structure: I replaced the flat 12-cause model with a two-tier hierarchy. The full rationale is in `coursework/W4/design_refinement.md` and the Defend-Your-Method write-up; in brief, burned area over the full post-cleaning record (1992–2021) splits 58.9% Natural, 22.7% Human, and 18.5% Unknown, and those three need different treatment. Natural is effectively one cause and can only be mitigated, not prevented. Unknown is nearly as large as Human and varies by region, so it is a data-quality signal rather than a cause. The research questions and the deliverable did not change.

This also settled last week's open Alaska decision. Alaska stays in-grain at Level III; the Tier-1 allocator routes its lightning dominance into the Natural branch, and last week's `AK|Summer` missingness number (r ≈ −0.61) lands in the Unknown branch as an attribution-quality signal.

### Built this week

Tier 1 is in `notebook/06_analysis.ipynb`. I opened the second tier as three notebooks, one per branch: `07_natural_location.ipynb`, `08_human_cause.ipynb`, and `09_unknown_dataquality.ipynb`. Each now holds a first working pass, so all four models have an early efficacy read.

All four share the same discipline: a forward-chaining temporal split (train on season-years < 2010, score ≥ 2010), a persistence floor built before any learned model, and acre-weighted scoring. The scoring metric is locked: total-variation distance (TVD) for compositions, log-MAE for burn size. Pipeline notebooks are renumbered `01_`–`09_`. (Numbers below are from validation runs pending my own manual notebook execution.)

- Tier 1 (coarse allocator). Persistence floor: acre-weighted TVD ≈ 0.27 on the cause mix, but the burn-size level is ~9× off. A learned rung (gradient boosting on trailing "fingerprint" features) beat the floor on size (~6× vs ~9× off) but not on mix. From history alone, cause mix is predictable and size is not.
- Human branch (→ prevention). The forecast partner for RQ2. The human sub-cause mix is region-season structured: a persistence floor scores TVD ≈ 0.49 with a 54% top-cause hit-rate, versus a global-mix baseline at 0.64 / 16%. Knowing the region-season tells you which human cause to prevent.
- Natural branch (→ mitigation). On the megafire cells that carry the acres, a region's own history under-predicts every record year by 1–1.7 orders of magnitude, so persistence scores worse than a global constant (~14× vs ~3× off). This is the clearest case for adding external pre-season drought/fuels data, which I wired as a documented, not-yet-sourced stub.
- Unknown branch (→ data quality). Produces an operational targeting list of where attribution is weak and material, and `missing_acre_frac` is modestly forecastable (persistence beats the global mean).

Each branch behaves differently under the same scoring, which is what the split was for.

## Next week's "To Do"

- Source the drought/fuels data for the Natural branch and populate the wired external-covariate stub — the megafire result makes this the clearest path to predictive lift. Pre-season values only, so no leakage risk.
- Add a learned rung to the Human branch (and a per-branch `k`-sweep), to test whether its region-structured sub-cause mix is predictable beyond persistence — the Tier-1 pattern applied to the RQ2 partner.

## Resources (optional)

- Design refinement: `coursework/W4/design_refinement.md`; W4 plan snapshot: `coursework/W4/w4_plan_snapshot.md`
- Pipeline notebooks (renumbered `01_`–`09_`): exploration (`01_feasibility`, `02_eda`, `03_missingness`) → `04_cleaning` → `05_features` → Tier 1 `06_analysis`
- Tier-2 branches: `notebook/07_natural_location.ipynb`, `notebook/08_human_cause.ipynb`, `notebook/09_unknown_dataquality.ipynb`
- `04_cleaning.ipynb` → `data/fires_clean.parquet`, `data/region_season_cause.parquet`; `05_features.ipynb` → `data/region_season_features.parquet`
- Short, K. C. (2022). *Spatial wildfire occurrence data for the United States, 1992–2020* (6th ed.). USDA Forest Service Research Data Archive. https://doi.org/10.2737/RDS-2013-0009.6
- U.S. EPA. *Level III Ecoregions of the Conterminous United States*; *Level III Ecoregions of Alaska*.