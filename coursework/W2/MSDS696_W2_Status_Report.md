# Weekly Status Report

| Name | | Week / Date | |
| --- | --- | --- | --- |
|  Craig Rudman |  |  Week 2 / 2026-07-12 |  |

## Project title
Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation

## Project summary

This project asks two linked questions. First, descriptively: across contrasting U.S. region-seasons, which wildfire causes **drive the most burned area**, and do those patterns differ enough to demand distinct prevention and/or mitigation strategies? Second, predictively: can a **next-season cause-risk profile** — the expected mix of causes for a region and upcoming season, ranked by the burn each is expected to drive — be predicted well enough to pre-target that effort? The goal is to let a state or regional fire planner match the intervention to the pattern. The data is the Fire Program Analysis Fire-Occurrence Database (FPA-FOD): around 2.3M U.S. wildfires from 1992 to 2020. Fires are grouped by cause, EPA Level III ecoregion, and meteorological season. These historical patterns train an inferential model whose product is a **next-season cause-risk profile**. For a given region and upcoming season, that profile gives the expected composition of ignition causes. A planner can then pre-position prevention and mitigation effort against the causes most likely to dominate. Within each region-season, causes are ranked for impact by the predicted size of the fires they produce, so effort concentrates on the causes expected to drive the most burn — not merely the most ignitions. An exploratory goal is to layer in additional evidence — emergent risk factors beyond historical composition — to strengthen that inference.

## Milestones

- Data acquisition: load FPA-FOD 2.3M edition (1992–2020), confirm schema and record count
- Feasibility assessment: sample-scale approach validation, missing-cause and regional-contrast checks
- Cleaning: full 2.3M load; drop/flag Missing causes; CONUS ecoregion spatial join (AK/HI at state grain); derive meteorological season + sequential season-year index; preserve FIRE_YEAR
- EDA: cause × region × season composition; year-over-year variability check (static vs. dynamic target); reportable missing-cause sensitivity bound
- Feature engineering: lagged burn/cause history (t-1, t-4), log fire size, per-region dominant-cause share; optional climate/fuels integrations as predictive-lift hypotheses (lagged to pre-season, no leakage)
- Modeling: persistence baseline first; predict region-season cause composition; predict expected burn size per cause to weight impact; forward-chaining temporal split; ablation ladder vs. baseline
- Findings & prevention strategies: rank causes within each region-season by predicted burn impact; translate contrasting archetypes into matched prevention recommendations; write up

## Last week's "To Do"

Week 1 had no explicit to-do list. Its deliverable was the project proposal (problem statement, research question, stakeholder, and dataset selection). Week 2 begins execution, and the implicit carry-over was the Week 2 goal itself: **determine whether the available data can actually answer the research question.**

## This week's progress

Milestones addressed: **Data acquisition** and **Feasibility assessment** (`notebook/feasibility.ipynb`).

- **Acquired and documented the data.** Loaded the FPA-FOD 6th Edition SQLite database (Short 2022), confirmed **2,303,566 records** spanning **1992–2020** with the columns the question depends on (cause, lat/lon, state, discovery date, size). Documented provenance, terms, and known biases in-notebook; also retrieved the EPA Level III ecoregion boundary layer for the spatial join.
- **Confirmed the question is answerable — cause varies by both region and season.** On a 400,000-fire seeded random sample (non-Missing causes; pooled across all years 1992–2020):
  - **Season:** cause mix shifts sharply across seasons — Natural ignitions swing **1% (Winter) → 44% (Summer)** (a 43-pt spread), while Debris/open burning runs the opposite direction (49% → 14%). The seasonal half of the question has real signal.
  - **Region:** across **84 ecoregions** with adequate sample, dominant cause differs region to region (4 distinct dominant causes). Natural share ranges from **~0.7%** in human-ignition regions (Central Appalachians, Lake Agassiz Plain) to **~84%** in lightning-driven ones (Idaho Batholith, Colorado Plateaus). The spatial half holds.
  - **Cell density is adequate** to contrast region-seasons (state × season × cause yields 1,971 non-empty cells; 99.2% of fire points spatially matched to a CONUS ecoregion).
- **Quantified the central data risk (differential missing cause).** ~26% of records have Missing/undetermined cause. A diagnostic shows missingness is **flat across seasons** (23.5%–26.0%, 2.5-pt spread) but **strongly differential across ecoregions** (3.7%–66.4%, 62.6-pt spread) — and the low-missing regions are exactly the high-Natural federal West. Conclusion baked into the analysis plan: report cause as **shares, not counts**; treat the seasonal signal as clean, and the regional signal as directionally reliable but magnitude-caveated.

**Bottom line: the data addresses the research question.** Cause composition varies meaningfully across both region and season, and the one bias that could distort that result — uneven missing-cause reporting across regions — has been measured, so cause is reported as shares and the regional signal is flagged as directional. (A numerical sensitivity bound on how far that missingness could shift the regional contrast is next week's work.)

## Issues & discussion

No blocking issues. Two open questions I'll resolve after preliminary analysis:

- Whether to **augment FPA-FOD with additional sources** (e.g., climate/fuels layers) to improve predictive power. I'm deliberately deferring that decision until the EDA demonstrates what the existing dataset can and can't do on its own — I don't want to add complexity or leakage risk before the baseline is understood.
- Whether the product needs **systemic triage across region-seasons**, not just ranking of causes within each one. The current scope ranks causes inside a given region-season by predicted burn impact; whether to also rank the region-seasons themselves against each other — a higher-level allocation layer — is open, and depends on how the stakeholder actually apportions effort.

Flagging both for visibility; no action needed yet.

## Next week's "To Do"

- Move from the 400K seeded sample to the **full 2.3M-record load**; drop/flag Missing causes; run the CONUS ecoregion spatial join at full scale (AK/HI handled at state grain).
- Derive **meteorological season** and the **sequential season-year index**; preserve `FIRE_YEAR`.
- Begin **EDA proper**: full-scale cause × region × season composition and a year-over-year variability check (to settle whether the target is static or dynamic).
- Produce a reportable **missing-cause sensitivity bound** on the full data.

## Resources (optional)

- Feasibility notebook: `notebook/feasibility.ipynb`
- Short, K. C. (2022). *Spatial wildfire occurrence data for the United States, 1992–2020* (6th ed.). USDA Forest Service Research Data Archive. https://doi.org/10.2737/RDS-2013-0009.6
- EPA Level III Ecoregions of the Continental United States. https://www.epa.gov/eco-research/level-iii-and-iv-ecoregions-continental-united-states

**Literature (informing and validating the method):**

- Edgeley, C. M., Evans, A. M., Devenport, S. E., Kohler, G., Zamudio, Z. M., & DeGrandpre, W. D. (2025). Preventing human-caused wildfire ignitions on public lands: A review of best practices. *Forest Science, 71*(6), 493–521. https://doi.org/10.1007/s44391-025-00025-9
- Prestemon, J. P., Hawbaker, T. J., Bowden, M., Carpenter, J., Brooks, M. T., Abt, K. L., Sutphen, R., & Scranton, S. (2013). *Wildfire ignitions: A review of the science and recommendations for empirical modeling* (General Technical Report SRS-171). U.S. Department of Agriculture, Forest Service, Southern Research Station. https://www.srs.fs.usda.gov/pubs/gtr/gtr_srs171.pdf
- Davis, K. T., Peeler, J., Fargione, J., Haugo, R. D., Metlen, K. L., Robles, M. D., & Woolley, T. (2024). Tamm review: A meta-analysis of thinning, prescribed fire, and wildfire effects on subsequent wildfire severity in conifer dominated forests of the Western US. *Forest Ecology and Management, 561*, 121885. https://doi.org/10.1016/j.foreco.2024.121885
