# W4 — Design Refinement: A Hierarchical Three-Branch Architecture

**Craig Rudman · Week 4 / 2026-07-21**

I have decided to replace the flat 12-cause composition model with a first-pass allocator over three classes — Human / Natural / Unknown — followed by a separate, purpose-built deep-dive for each branch. The three branches answer different questions; each has a different prediction target for a different intervention.

I made this change based on what the cleaned region-season-cause data showed. My research questions and deliverable stay the same. What changes is the structure of the model that produces them and, more significantly, what I do about the 18.5% of burned area with no attributed cause. That was my largest known liability. It now becomes its own branch of the model, with its own deliverable.

## The research questions, restated

This document refers to my two research questions throughout, so I state them here:

- **RQ1 (descriptive):** Across a set of contrasting U.S. region-seasons, which wildfire causes (natural and human) drive the most burned area, and do those patterns differ enough to demand different prevention and mitigation strategies?
- **RQ2 (predictive):** Can a next-season cause-risk profile — the expected composition of causes for a region and upcoming season, ranked by the burned area each is expected to drive — be predicted well enough to pre-target that prevention effort?

## Why the split

The move follows directly from a snapshot of burned area across the three coarse classes, taken over the full record (1992–2021, post-cleaning):

| Coarse class | Burned acres | Share of total |
| --- | --- | --- |
| Natural | 105.5M | 58.9% |
| Human | 40.6M | 22.7% |
| Unknown | 33.1M | 18.5% |
| **Total** | **179.3M** | **100%** |

Two facts in this table inform the updated design:

1. Most acres burn from a cause the planner cannot prevent. Natural causes account for 58.9% of burned area. Prevention has no lever here; the only lever is mitigation, and mitigation is about where fuel and exposure sit, not what started the fire. A cause-composition model is the wrong tool for this branch. The Natural branch is effectively a single cause, so its deep dive is spatial, not compositional.

2. The Unknown branch is too large to ignore. At 18.5% it is nearly as large as the entire Human branch. Prior work (`notebook/03_missingness.ipynb`) established that this missingness is not uniform. It varies by reporting agency, state, fire size, and over time. That means the Unknown share is not neutral noise distributed evenly across the map — it is a regional data-quality signal. Predicting the Unknown share directly is more defensible than imputing causes the record does not contain.
   
The flat 12-cause model would have forced all three of these into one composition vector, letting the Unknown set contaminate every other share. The hierarchy quarantines the problem where it lives.

## The architecture

**Tier 1 — coarse allocator.** For a region-season, predict the composition across Human / Natural / Unknown by burned-area share. The denominator is total burned acres, so the three shares sum to 1. 

**Tier 2 — three heterogeneous branch deliverables.**

| Branch | Question | Prediction target | Grain | Planner's intervention |
| --- | --- | --- | --- | --- |
| **Natural** | Where  will it burn? | burned-area concentration | region-season (spatial) | mitigation siting (e.g fuel treatment, defensible space, suppression pre-positioning) |
| **Human** | What starts it? | cause composition (sub-causes) | region-season × sub-cause | prevention targeting matched to the dominant human cause |
| **Unknown** | Where is the record weak? | attribution-quality | region-season | data-quality improvement, investing in cause reporting where the record can't support a decision |

The Human branch is where the original 12-cause structure earns its keep, now conditioned on Human: arson, debris/open burning, equipment/vehicle, powerlines, recreation each imply a different prevention intervention and are regionally structured. The existing `cause_share` column (computed within attributed fires) is already close to the right quantity for this branch.

## Scope note — what "prediction" means per branch

Only **Tier 1 and the Human branch** are prediction in the RQ2 sense — forecasting a next-season composition. The RQ2 deliverable, next-season cause-risk profile, is carried by those two. The Natural and Unknown branches are methodologically distinct sub-projects:

- **Natural-as-location** is a spatial-concentration question that may need a finer grain than the Level III ecoregion.
- **Unknown-as-data-quality** produces an operational recommendation, not a fire forecast. It addresses which region-seasons have attribution weak enough that the planner's own inputs are unreliable.
