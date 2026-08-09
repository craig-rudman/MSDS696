# Weekly Status Report

| Name | | Week / Date | |
| --- | --- | --- | --- |
|  Craig Rudman |  |  Week 6 / 2026-08-09 |  |

## Project title
Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation

## Project summary

This project helps a state or regional fire planner match prevention and mitigation effort to the pattern that actually drives burned acres, instead of spreading it uniformly. The data is the Fire Program Analysis Fire-Occurrence Database (FPA-FOD), about 2.3M U.S. wildfires from 1992 to 2020, grouped by cause, EPA Level III ecoregion, and meteorological season.

The model works in two steps. First it splits a region-season's burned acres across three classes — Human, Natural, and Unknown, where Unknown means no cause was ever recorded. Then each class gets its own follow-on model, because each raises a different question.

The predictive deliverable comes from the first step plus the Human class, the only class with a composition of causes to rank. For a region and upcoming season it ranks causes by acres likely to burn rather than by fires started, so effort goes where the acres are. The ranking is the reliable part: the cause mix is stable and predictable from history, while the season's total burn is not, so the acre figures carry much wider error than the order does.

Natural is the largest first-step class at 58.9% of acres, and its branch changed this week. It previously asked where lightning-driven acres would concentrate; it now asks where within a region fires are most likely to start, on a fine hexagonal grid rather than the whole ecoregion — because fuel treatment, defensible space and pre-positioned crews are all sited works, and whether they pay off depends on whether fire arrives there. The two views disagree usefully: ignitions cluster near roads and settlement while acres accumulate in remote continuous fuel, so a cell can run high-ignition/low-acre (starts caught early) or low-ignition/high-acre (rare starts that run far), and those call for different treatments.

Unknown is not a forecast but a data-quality signal: where a region's causes go unrecorded, the record itself is the weak link. The branch ranks the regions and reporting streams where better cause data would most improve everything above it.

## The research questions

The rest of this report refers back to these:

- RQ1 (descriptive): Across a set of contrasting U.S. region-seasons, which wildfire causes (natural and human) drive the most burned area, and do those patterns differ enough to demand different prevention and mitigation strategies?
- RQ2 (predictive): Can a next-season cause-risk profile — the expected composition of causes for a region and upcoming season, ranked by the burned area each is expected to drive — be predicted well enough to pre-target that prevention effort?

## Milestones

- **Done** — Data acquisition, feasibility, and EDA: FPA-FOD 1992–2020 loaded and validated; cause composition, size distributions, and the differential missing-cause problem characterized.
- **Done** — Cleaning: documented exclusions; EPA Level III spatial join (CONUS and Alaska); meteorological season and season-year index derived.
- **Done** — Method design: hierarchical structure settled over a flat classifier, with the estimator choice defended against the alternative.
- **Done** — Perimeter correction and hex grid (W5): MTBS perimeters joined, acres distributed across res-5 hexes, conservation verified at 99.61% on-grid.
- **Done** — Feature engineering: trailing cause and burn history; pre-season climate at both region and hex grain; prior-burn state per hex-season; MODIS vegetation density, which cleared the credential blocker carried since W5. All external features lagged to pre-season availability.
- **Done** — Level III modeling: persistence baselines for all three branches, forward-chaining splits, and learned rungs on Tier 1 and Human. The k=7 trailing mean stands as the model to beat.
- **Done** — Hex-grain modeling (W6): ignition and burned-area targets for the Natural and Human branches, with shuffled-control tests and covariate ablation ladders.
- **In progress** — Findings and recommendations: rank causes by predicted burn impact, translate contrasting archetypes into matched prevention and mitigation strategies, and carry the result into the final deck.

## Last week's "To Do"

- Source the pre-season fuel-condition and climate layers. **Done** — climate at hex grain (`src/hex_climate.py`), and MODIS vegetation density (`src/hex_ndvi.py`), 55,923 hex-seasons across six forest ecoregions.
- Add a learned rung to the Human branch. **Done, and it lost** — acre-weighted TVD 0.489 → 0.588, top-1 54% → 36%, against the k=7 persistence floor.
- Enforce the leakage rule as the imagery features are built. **Done** — every covariate ends strictly before the target season opens, with anomalies normalized on training years only.

## This week's progress

### BLUF — the one-sentence recommendation

> Target prevention where the region's own history says the causes are, site mitigation where it says fires start, and fix the record where it can't say either.

### Storyboard — assertion headlines in order

Each headline is a full-sentence assertion, and the sequence is meant to carry the argument with the
slides removed. The evidence column names what the slide would show, not what it would say.

| # | Assertion headline | Evidence on the slide |
| --- | --- | --- |
| 1 | Prevention is a pre-season decision; it needs a pre-season forecast. | The stakeholder decision, stated plainly: a map and a budget, with the two questions labelled. |
| 2 | Cause is regional, not national. | National class split (Natural 58.9%, Human 22.7%) beside two ecoregion profiles where the ratio inverts. |
| 3 | A region's cause mix is stable enough to forecast. | Cause shares by year for contrasting region-seasons — flat lines, not swings. Tier 1 baseline: acre-weighted TVD 0.266, top-1 73%, forward-chained on 2010+. |
| 4 | More history is better. | The k-sweep: TVD falling monotonically to k=7, with `t-4` losing by ~5 points. Cause composition is a standing property, not a yearly swing. |
| 5 | Within Human, history names the lead cause more often than not. | Human-branch floor: acre-weighted TVD 0.489, top-1 54% against an 11-way simplex. |
| 6 | A learned model made it worse. | The head-to-head: TVD 0.489 → 0.588, top-1 54% → 36%. A region's coarse character does not recover its within-Human mix. |
| 7 | A quarter of burned acres have no recorded cause; that gap is predictable. | Unknown-branch persistence: acre-weighted MAE 0.167 against the global mean's 0.240. The ranked triage list, headed by Southwestern Tablelands MAM at 1.17M unattributed acres. |
| 8 | Where fires start is predictable. | `img/w6_siting_glance.png` — Klamath hexes in triage tiers. Held-out Spearman: Human +0.53, Natural +0.34. |
| 9 | That skill is spatial, not statistical luck. | Real ranking against shuffled: same values, wrong hexes, and it collapses to within ±0.003 of zero. Persistence MAE 0.43 against the shuffle's 0.77. |
| 10 | People start fires where the roads are. | Human ignition is the most predictable surface in the project: per-season Spearman, MAM peak at +0.59; the four-season human profile against natural's 78.1% concentration in JJA. |
| 11 | The two branches' tails are not comparable. | The decile tables side by side: Human top decile 12.3x under on a median 135-acre cell, Natural 270x on 2,970. |
| 12 | A tenth of the burning cells carry nearly all the acres. | Concentration curve — top 10% of burning cells hold 98% of burned acres, top 1% hold 55%. |
| 13 | Fuel state says nothing about where a fire starts. | Ablation ladders: no gain exceeds +0.005, and the larger moves are negative. `img/w6_ndvi_variance.png` — between-place spread is 2.8x the within-hex year-to-year spread. |
| 14 | The same data does predict how much burns. | Climate + NDVI together +0.049, 26.6 SD above a shuffled control, holding across five split years. Neither half works alone: wet heavy fuel will not carry fire, dry bare ground has nothing to burn. |
| 15 | But the gain lands on the fires nobody needed predicted. | Gain by decile: deciles 6–8 (1–20 acre cells) improve, 1–5 get worse, and the top decile goes 855x → 868x. |
| 16 | Megafire size is not forecastable before the season. Stop targeting it. | The tail failure as a bounded, reportable null — with the same-day question (wind, timing, suppression) named as what remains untested. |
| 17 | Every megafire was an ignition first. | A hex-season that ignites at all is 22.8x more likely to produce a ≥1,000-acre burn: 6.7% against 0.29%. |
| 18 | One ignition is enough. | The rule is binary — does this place ignite, not how often. Escape probability *per ignition* falls with count, 0.054 → 0.014, and 49% of large fires came from hexes with exactly one natural ignition. |
| 19 | Target causes by region. Site the work by ignition. Fix the record where it says neither. | One walkthrough: profile → ranked hexes → triage list. `img/w6_siting_glance.png` with the capture table: 30% of starts under 6.1% of ground (4.95x), 90% needing 77.8% (1.16x). |

### The five-minute cut, for the W6 practice recording

The final is 15 minutes — about 10 to present, 5 for questions — which is what the nineteen beats
above are sized for, at roughly 30 seconds each. The W6 practice talk is 5 minutes, so it is a
**subset of the same storyboard rather than a second one**: beats **1, 2, 3, 8, 12, 16, 17, 18, 19**.

That keeps the spine intact — the decision, why cause differs regionally, what is predictable, where
to site, where the tail fails, the concession, the gate, the binary rule, the recommendation. What it
drops is every beat whose job is to *defend* a result rather than state one: the k-sweep (4), the
losing learned rung (6), the shuffled controls (9), the four-season human profile (10), the
two-branch tail split (11), and the whole covariate arc (13–15). Those are the beats most likely to
draw questions, which is exactly why they stay in the final and come out of the rehearsal.

Beat 7 (Unknown) also drops. It is a third of the recommendation and it survives in beat 19, but at
five minutes a track that appears once cannot carry its own slide.

### Headline-only test

Read as a sequence with the slides removed, the nineteen assertions carry the argument: the decision
and its two halves (1–2), what to target and why history suffices (3–6), where the record itself is
the weak link (7), where to site and why the skill is real (8–10), where the two branches diverge
(11–12), what fuel data can and cannot buy (13–15), the concession (16), and the reframe that turns
the concession into a recommendation (17–19).

**The buried lead, and where it moved.** The first ordering was chronological — build the hex grid,
fetch the covariates, run the ablations, discover the tail failure, then notice the ignition gate —
which buried the lead at position 11 of 12. That draft also had a second, larger problem: it opened
on the hex natural surface, which is *one of three tracks* in a two-tier architecture, and presented
it as though it were the whole product. RQ2's actual deliverable, the region-season cause profile,
appeared nowhere. The rewrite restores the hierarchy: Tier 1 establishes **what**, hex grain answers
**where**, and the recommendation joins them.

**The gap the test exposed.** Between "megafire size is not forecastable" (16) and "ignition is a
gate" (17), a reader has no reason to believe the second follows from the first — they read as a
failure followed by an unrelated consolation. Beat 16 is phrased to make the null *force* the reframe
rather than sit beside it. The same test caught beat 11 doing double duty: splitting the two
branches' tails apart is what licenses two *different* products in beat 19, so it cannot be
compressed away.

**The covariate arc had to be split, not compressed.** Beats 13–15 were one headline reporting a
null. That hid the actual shape of the result: the same fuel data that says nothing about *where a
fire starts* does add real signal about *how much burns* (+0.049, 26.6 SD above a shuffled control) —
and then lands on 1–20 acre fires while the tail goes 855x to 868x. Told as a single null it is a
disappointment; told as three beats it is a contrast that explains why the recommendation sites
against starts rather than against predicted burn size.

**What still needs pod feedback.** Whether the deck reads as one argument or as two stapled together
— the Level III *what* and the hex-grain *where* — is the question I most want a podmate to answer.
The compression candidates if it runs long are beats 4 and 6, both variations on "the simple thing
won and nothing beat it."

### Built this week

- `src/hex_ignitions.py` — ignition-count target per hex-season, 4,166,910 cells, all 2.27M fires on
  raw points (no perimeter join: an ignition is exactly what the record stores correctly).
- `src/hex_acres.py` — burned-area target with a hurdle split (does it burn / how much), plus the
  burn-conditional baseline that corrected a reversed finding.
- `src/hex_panel.py` — one panel assembly, one persistence baseline, one scorer. Calls
  `trailing.TrailingMean` rather than reimplementing it; results are cached so the floor is quoted
  rather than recomputed.
- `src/hex_climate.py`, `src/hex_ndvi.py` — pre-season covariates at hex grain. The MODIS probe
  reaches the Planetary Computer STAC API anonymously, which cleared the Earthdata/GEE credential
  blocker carried since W5.
- `notebook/12_hex_ignition_baselines.ipynb`, `notebook/13_hex_acres_baselines.ipynb` — the two
  natural-branch targets, their baselines, the shuffled-control tests, and the ablations.
- `notebook/14_hex_human_branch.ipynb` — the Human branch at hex grain. No new data was needed; the
  targets were already in the cached panels. Scored per season, because human fire runs in all four
  where natural ignition concentrates 78.1% in summer.
- `src/w6_visuals.py`, `notebook/15_w6_visuals.ipynb` — the deck's figures. The siting triage map
  (tiers cut by starts captured, not by an assumed ground budget) and its held-out scoring; the NDVI
  variance decomposition that explains the covariate nulls in one picture — between-place spread is
  2.8x the within-hex year-to-year spread.

## Next week's "To Do"

- Build the final deck against this storyboard, one slide per assertion, and compress beats 4, 6 and
  12 to whatever survives pod feedback.
- Produce the two figures still missing: the two-branch decile comparison (beat 11) and the acres
  concentration curve (beat 12). The siting map and the covariate-null figure are built
  (`notebook/15_w6_visuals.ipynb`).
- Test whether same-day conditions — wind, timing, suppression availability — predict which igniting
  natural hexes escape. This is the open question beat 13 concedes, and it is a different model with
  a different data requirement.
- Resolved from the W5 carry-over: the learned rung on the Human branch at Level III grain **is
  built** (`08_human_cause.ipynb`) and loses to the k=7 persistence floor — TVD 0.489 → 0.588, top-1
  54% → 36%. The W5 to-do described it as unbuilt; that was wrong. The remaining version worth
  trying is a fingerprint built from the cell's own *human sub-cause* history rather than the coarse
  Tier-1 summaries that failed here.

## Resources (optional)

- W6 assignment: `coursework/W6/assignment.md`
- W5 status report: `coursework/W5/MSDS696_W5_Status_Report.md`
- Short, K. C. (2022). *Spatial wildfire occurrence data for the United States,
  1992–2020* (6th ed.). USDA Forest Service Research Data Archive.
  https://doi.org/10.2737/RDS-2013-0009.6
- Eidenshink, J., Schwind, B., Brewer, K., Zhu, Z., Quayle, B., & Howard, S. (2007).
  A project for monitoring trends in burn severity. *Fire Ecology*, 3(1), 3–21.
  (MTBS burn perimeters.)
- U.S. EPA. *Level III Ecoregions of the Conterminous United States*; *Level III
  Ecoregions of Alaska*.
