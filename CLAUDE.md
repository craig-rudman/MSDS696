# MSDS696 Practicum II
You are an agent tasked with helping the student complete each weekly assignment. Your role will be to ensure that the student follows the instructions and that the student's work satisfies the requirements.

Instructions, rubrics, and templates are found in `coursework/Resources`. Specific assignments for each week are in subfolders `coursework/W1` through `coursework/W8`.

The student is to log interactions with the agent that contribute significantly to project outcomes. Log entries are to follow this convention:

- **Date:**
- **What was going on:**  (one line of context)
- **The exchange:** (paste or link the actual conversation)
- **What the student kept, and why:**
- **What the student rejected or overrode, and why:**

The collaboration log is found at /coursework/collaboration_log.md

You will support the students research and defer to the student's judgement. Be concise and responsive to the student's direction. Do not try to lead the inquiry or suggest solutions, except when asked.

## The Project

**Title:** Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation

### Problem Statement
Prevention and mitigation resources are limited, and wildfires don't start — or burn — the same way everywhere. Identifying regional and seasonal patterns in wildfire cause could help fire planners target both prevention and mitigation resources more effectively.

### Research Question
1. **(Descriptive)** Across a set of contrasting U.S. region-seasons, which wildfire causes (natural and human) drive the most burned area, and do those patterns differ enough to demand different prevention and mitigation strategies?
2. **(Predictive)** Can a next-season cause-risk profile — the expected composition of causes for a region and upcoming season, ranked by the burned area each is expected to drive — be predicted well enough to pre-target that prevention effort?

### Stakeholder
A state or regional fire-agency planner deciding where to concentrate limited pre-season prevention and mitigation effort.

### The Outcome
The planner can match the intervention to the pattern instead of spreading effort uniformly. The concrete product is a **next-season cause-risk profile**: for a given region and upcoming season, the expected composition of ignition causes, with causes ranked for impact by the predicted burn size they drive (not merely ignition counts) so effort concentrates on what will burn most.

### Approach (as of W2)
- **Two-part question: descriptive comparison + inferential product.** RQ1 compares cause composition (weighted by burned area) across region-seasons; RQ2 makes the forward-looking deliverable explicit — an inferential model trained on historical patterns to predict the next-season cause-risk profile. Start from a **persistence baseline** and justify added complexity against it via an ablation ladder; use a **forward-chaining temporal split** (no leakage).
- **Data:** Fire Program Analysis Fire-Occurrence Database (FPA-FOD), 6th Edition (Short 2022) — ~2.3M U.S. wildfires, 1992–2020, SQLite. Region = **EPA Level III ecoregion** (CONUS *and* Alaska, each via its own ecoregion-layer spatial join; HI dropped per the cleaning exclusion). Season = **meteorological season**, plus a **sequential season-year index** as the temporal spine; **preserve `FIRE_YEAR`** so the static-vs-dynamic-target question stays open.
- **Known constraint — differential missing cause.** ~26% of records have Missing/undetermined cause. Missingness is roughly flat across seasons but **differential across regions** — and the direction was measured directly in W4 (`09_unknown_dataquality.ipynb`): missing-share correlates **negatively** with Natural share across ecoregions (Pearson ≈ −0.64), i.e. it concentrates in **low-Natural, human-dominated** regions, *not* the high-Natural West. (`03_missingness.ipynb` characterizes it by agency/state/size/time.) Therefore report cause as **shares, not counts**; treat the seasonal signal as clean and the regional signal as directionally reliable but magnitude-caveated.
- **Open questions (deferred by design):** whether to augment FPA-FOD with climate/fuels layers for predictive lift (deferred until EDA shows what the base data can do, to avoid premature complexity/leakage); and whether the product needs a higher-level allocation layer that ranks region-seasons against each other, not just causes within one.

### Architecture (refined W4)
The model is **hierarchical**, not a flat 12-cause classifier. See `coursework/W4/design_refinement.md` for the full rationale. Agentic behavior must assume this structure.

- **Tier 1 — coarse allocator.** For a region-season, predict burned-area composition across **three classes: Human / Natural / Unknown**, on a *total-acres* denominator (resolved + missing) so the three shares sum to 1. Class shares by burned area over the full record: **Natural 58.9%, Human 22.7%, Unknown 18.5%** (179.3M acres total). "Unknown" is a **predicted class** in its own right — it holds the missing-cause mass (`missing_acres`), and its share is a regional **attribution-quality** signal.
- **Tier 2 — three heterogeneous branch deliverables**, each a *different* question and target:
  - **Natural → location.** ~one cause (lightning), so no cause deep-dive; predict **burned-area concentration** (spatial) to site *mitigation*. Grain may need to go finer than Level III — deferred, not assumed.
  - **Human → cause.** The composition problem, conditioned on Human; the sub-causes drive *prevention* targeting. This is where the 12-cause structure and the existing `cause_share` (attributed-only) apply.
  - **Unknown → data quality.** Deliverable is an *operational recommendation* (where to invest in cause reporting), not a fire forecast.
- **Cause→class mapping:** Natural = `Natural`; Human = all other resolved causes **including `Other causes`**; Unknown = the `missing_acres` mass (not a cause row). Reconstruct per-cell total as `cell_acres + missing_acres`; no cleaning re-run needed.
- **Scope of "prediction" (RQ2):** the next-season cause-risk profile is carried by **Tier 1 + the Human branch**. Natural (location) and Unknown (data quality) are related but methodologically distinct sub-projects.
- **Caveat (resolved W4):** the resolved **Human 22.7% is plausibly a floor**. Tier 1 predicts the Unknown share directly rather than distributing it onto Human/Natural, so the floor stays visible in the output. The mechanism was corrected in W4: an earlier draft attributed the floor to missingness leaning to the high-Natural West, but `09_unknown_dataquality.ipynb` measured the Natural-share × missing-share correlation directly and found it **negative** — Unknown concentrates in **human-dominated** regions, so the true Human share is if anything *higher* than 22.7% (floor holds, corrected reason).

Weekly work products live under `coursework/W#`; analysis notebooks under `notebook/`, numbered in pipeline order (e.g. `notebook/01_feasibility.ipynb`).

