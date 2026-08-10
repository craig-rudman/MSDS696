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

Natural is the largest first-step class at 58.9% of acres, and its branch changed this week. It previously asked where lightning-driven acres would concentrate; it now asks where within a region fires are most likely to start, on a fine hexagonal grid rather than the whole ecoregion — because fuel treatment, defensible space and pre-positioned crews are all sited works, and whether they pay off depends on whether fire arrives there. The two views disagree usefully: ignitions and acres concentrate in different places, so a cell can run high-ignition/low-acre (starts caught early) or low-ignition/high-acre (rare starts that run far), and those call for different treatments. The pattern is consistent with ignitions clustering near roads and settlement while acres accumulate in remote continuous fuel, though no road or settlement layer was built to test that.

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
| 1 | Wildfires are seasonal. | `img/w6_seasonality.png` — starts and acres on one calendar, no axes and no magnitudes: most fires start in spring, most acres burn in summer. MAM and JJA start nearly the same number of fires and differ 3.9x in acres. |
| 2 | Cause is regional, not national. | `img/w6_cause_map.png` — all 105 Level III ecoregions shaded by natural share of attributed acres. A West/East split at roughly the 100th meridian, Alaska almost entirely natural. The distribution is bimodal: 50 regions below 20% natural, 28 above 80%, only 27 in between. |
| 3 | A region's cause mix is stable enough to forecast. | `img/w6_tier1_tiles.png` — three tiles worst to best, share of a region-season's burned-acre composition placed on the right cause: the national average mix 42%, an even split 52%, the region's own history **73%**. Acre-weighted TVD 0.580 / 0.485 / 0.266, forward-chained on 2010+, 3,949 held-out region-seasons. |
| 4 | A few years of rolling average is enough. | `img/w6_k_sweep.png` — error in the predicted cause mix against window length. Acre-weighted TVD falls 0.331 → 0.278 from one prior season to three, then flattens; every window from three up sits within 1.4 points of the best. Cause composition is a standing property, not a yearly swing, and the window length is not a decision worth agonizing over. |
| 5 | Within Human, history names the lead cause more often than not. | `img/w6_human_tiles.png` — the same three tiles as beat 3, one level deeper: how often the predicted leading human sub-cause is the right one out of 11. An even split 9%, the national human mix 16%, the region's own history **54%**. Acre-weighted TVD 0.489 against the national mix's 0.643, forward-chained on 2010+, 3,850 held-out region-seasons. |
| 6 | A learned model made it worse. | `img/w6_human_ladder.png` — three rungs against the floor line. The region's own history names the leading human cause **54%** of the time; gradient boosting on region character 36%; the same model *given that history as a feature* 47%. Acre-weighted TVD 0.489 / 0.588 / 0.554. Even handed the winning quantity, the model cannot beat taking its mean. |
| 7 | Where fires start is predictable, but not at ecoregion scale. | `img/w6_siting_glance.png` — Klamath hexes in two bands, labelled on the map with no legend: the deep band is **6% of the region catching 32% of next season's starts** (5.2x), the light band **29% for 60%** (2.1x). The bands are the map's version of the capture curve's first two marks, so the geography of the diminishing return is visible. Held-out Spearman: Human +0.53, Natural +0.34. Companion for Q&A — `img/w6_capture_curve.png`, which carries the decay out to 1.16x at 90%. **This headline also carries the deck's one grain change** — the ecoregion of beats 3–6 becomes a 62,494-acre hex, and the map is the first thing the audience sees at that scale. |
| 8 | That skill is spatial, not statistical luck. | `img/w6_shuffled_control.png` — one panel, two lines labelled **forecast** and **shuffled**: mean observed starts against mean predicted for 20 equal-count strata. The forecast climbs the diagonal (top stratum predicted 4.7, observed 3.7); the same predictions dealt to the wrong hexes go flat at ~0.4 whatever the prediction. Spearman **+0.526 → +0.0002**, MAE 0.43 → 0.77 (worse than the uniform baseline's 0.70), on 1.59M held-out hex-seasons. |
| 9 | Human fire is predictable year-round; lightning only in summer. | `img/w6_season_skill.png` — held-out Spearman by season, each branch scored separately in all **11 held-out years**, with the band spanning the observed year-to-year range. Human runs flat and high (median +0.47 to +0.61, peaking in spring); natural is a summer surface (+0.42 JJA, +0.07 DJF). **Human beats natural in all 44 season-years without exception.** The deck's only figure showing a distribution rather than a point estimate. |
| 10 | Almost all the acres are in almost none of the cells. | `img/w6_acres_concentration.png` — cumulative share of natural acres, cells ordered by acres burned, **least to most**. The curve hugs the floor and spikes at the right edge: the worst-burning 10% of cells hold **98%** of the acres, the worst-burning 1% hold **55%**. On its own this is a fact about how fire is distributed; it sets the stakes for the next slide by naming, before any error is shown, which cells a forecast has to get right. |
| 11 | Up to a point, both are predictable. Past that point, natural fire is harder. | `img/w6_branch_deciles.png` — typical forecast error against how much a cell burned, both branches on one axis, **the same axis and the same direction as beat 10**, so the right edge means "the big burns" on both slides. They track each other through the smallest third and separate steadily after: natural runs 2–3x worse than human **at the same cell size**, reaching 687x on a median 8,061-acre cell against human's 19x on 240. The separation lands exactly on the right edge beat 10 just marked. Cells under 1 acre are excluded — 25.3% of FPA-FOD rows sit at exactly 0.1 acres (44.5% of natural fires), a reporting default rather than a measurement. |
| 12 | We tried to fix it with drought and fuel, but where fires start is a property of the place, not of the year. | `img/w6_ignition_ladder.png` — two flat lines, one per branch, across the rungs added to improve them: the region's own history, + drought, + fuel load, + both. **Nothing moves.** Best gain on either branch is **+0.0045**; the y-axis runs from zero so a real effect would have been visible. Both branches on the same 29,293 held-out cells (JJA, the six forest ecoregions NDVI was fetched for), so the two lines are directly comparable. **The opening of the repair attempt, and it has to be said as one** — beat 11 leaves a failure on the table; beats 12–14 are what was done about it, not a new topic. The measured reason is spoken, not drawn: these layers identify dry *places*, not dry *years* (raw vs. within-hex anomaly, pdsi −0.137 → −0.073, NDVI +0.228 → +0.098), and place is what history already knows. Held for Q&A — `img/w6_ndvi_variance.png`, the place-vs-year split at 2.8x, which is the mechanism behind the flat line. |
| 13 | The same data does predict how much burns. | `img/w6_acres_ladder.png` — **deliberately the same figure as beat 12**: same rungs, same axis, same zero-based scale, one line instead of two. The shape is the argument. Three rungs sit on the baseline rule and the fourth leaves it: climate + NDVI together **+0.049**, **26.6 SD** above a covariate-shuffled control, holding across five forward-chaining split years (+0.012 to +0.066). Neither half works alone — drought alone **−0.008**, fuel alone **+0.001** — and the figure's one callout is the size of the step, **+0.049**, since the `+ both` tick already names the conjunction: wet heavy fuel will not carry fire, dry bare ground has nothing to burn. Different target and population from beat 12 (7,799 burning JJA cells, burn-conditional baseline), so the two are comparable in **shape, not cell for cell**. |
| 14 | But the gain lands on the fires nobody needed predicted. | `img/w6_gain_landing.png` — **beat 11's axis again**, cells ordered by acres burned least to most, with the covariate model laid over the baseline. The shaded lens is the trade: it opens in deciles 6–9 (1–200 acre cells), and it closes at the right edge where the two lines finish together, **855x → 868x** on a median 5,073-acre cell. Deciles 1–5 get materially *worse* — decile 1 nearly doubles, 18.8x → 35.9x — so the model buys middling cells by giving up small ones and gains nothing where it counts. **Beat 10 is what makes this fatal rather than disappointing**: the improvement misses the cells holding 98% of the acres. Third beat to land the eye on the same right edge, which is the argument for reframing rather than tuning. 780 held-out cells per decile. |
| 15 | Siting needed a finer place. Size needs a finer moment. | `img/w6_grain_parallel.png` — **the deck's only figure that plots no data, and its only one about the method rather than the fire.** Every number this beat could show has already been shown (the tail is beat 11, the concentration beat 10, the nulls 12–14), and re-plotting any of them invites the audience to re-audit numbers at the moment the talk needs them accepting a conclusion. What it draws instead is a parallel: beat 7 fixed a forecast by dropping grain in *space* — the region was too coarse to site anything, so the map broke into hexes — and the tail failure is the same defect on the *time* axis, where a season is too coarse to say how big a fire gets. The solved row is closed and the untested row dashed, because one drop is a result and the other a hypothesis. **This is the fourth time the project has met the same lesson** (W4's pooled climate null, beat 12's places-not-years, beat 7's grain drop, now this) and the first time it is named as one. Megafire size remains not forecastable *before the season* — the bounded claim — but the reason is now stated as a grain mismatch rather than a dead end, which is what lets beat 16 move upstream instead of consoling. |
| 16 | Every megafire was an ignition first. | `img/w6_ignition_gate.png` — two bars in a common frame, no axis: a hex-season that ignites at all produces a ≥1,000-acre burn **6.7%** of the time against **0.29%** for one that does not, a **22.8x** gate. JJA natural, held-out years. The deck's only ratio-between-two-probabilities, so it uses the plainest encoding available rather than reusing a learned axis; the percentages are printed because at true scale the 0.29% bar is nearly invisible — which is itself the finding. This is the door beat 15 left open: size is not forecastable, but the event upstream of it is, and beat 7 already showed that ignition location is the most predictable surface in the project. |
| 17 | One ignition is enough. | `img/w6_one_is_enough.png` — one stacked bar over all **2,724** large-fire cells in the held-out years, split by how many times their hex ignited that season: **49% had exactly one**, 21% two, 30% three or more. Only the first segment carries colour, because it is the ground a planner would deprioritise by ranking on ignition count. Held for Q&A — the rate curves showing escape probability *per ignition* falling 0.054 → 0.014 as count rises, which answers "but doesn't more ignitions mean more risk?" without putting a rate-versus-total subtlety on the slide. The rule is binary: does this place ignite, not how often. |
| 18 | Nearly a fifth of burned acres have no specific cause — and that gap is itself forecastable. | `img/w6_unknown_triage.png` — the ranked triage list, headed by Southwestern Tablelands MAM at **1.17M** predicted unattributed acres. Ranked by acres rather than by rate: Central Great Plains has the worse attribution rate (66%) but a fifth of the burn. Unknown-branch persistence: acre-weighted MAE **0.167** against the global mean's 0.240, so a planner can be told a season ahead where next year's record will fail. This is the third leg of the recommendation, delivered where it is actionable rather than as a finding in its own right. |
| 19 | Target causes by region. Site the work by ignition. Fix the record where it says neither. | One walkthrough: profile → ranked hexes → triage list, the three products of the three Tier-1 classes. `img/w6_siting_glance.png` with the capture table: 32% of starts under 6.1% of ground (5.23x), 90% needing 77.8% (1.16x). |

### The five-minute cut, for the W6 practice recording

The final is 15 minutes — about 10 to present, 5 for questions — which is what the nineteen beats
above are sized for, at roughly 30 seconds each. The W6 practice talk is 5 minutes, so it is a
**subset of the same storyboard rather than a second one**: beats **1, 2, 3, 7, 10, 15, 16, 17, 19**.

That keeps the spine intact — the decision, why cause differs regionally, what is predictable, where
to site, where the tail fails, the concession, the gate, the binary rule, the recommendation. What it
drops is every beat whose job is to *defend* a result rather than state one: the k-sweep (4), the
losing learned rung (6), the shuffled controls (8), the four-season human profile (9), the
two-branch tail split (11), and the whole covariate arc (12–14). Those are the beats most likely to
draw questions, which is exactly why they stay in the final and come out of the rehearsal.

Beat 18 (Unknown) also drops. It is a third of the recommendation and it survives as a clause in beat
19, but at five minutes a track that appears once cannot carry its own slide.

### Headline-only test

Read as a sequence with the slides removed, the nineteen assertions carry the argument: fire is
seasonal and cause is regional (1–2), what to target and why history suffices (3–6), where to site and
why the skill is real (7–9), where the acres actually sit and where the branches diverge (10–11),
what fuel data can and cannot buy (12–14), the concession (15), the reframe that turns the concession
into a recommendation
(16–17), where the record itself is the weak link (18), and the three-part recommendation (19).

**The seam between the two grains, and where it is announced.** Beats 3–6 and beats 7–9 are
different sub-projects: the grain changes from 105 ecoregions to 36,234 hexes, the target from acre
composition to ignition counts, and the unit from shares to counts. The first draft changed all
three without saying so, and a listener had no reason to expect it. Beat 7's headline now carries
the grain change — *"but not at ecoregion scale"* names what is being left behind rather than
just what is arriving. The target change is not something a headline can hold, so it is a spoken
line in `talk_notes.md`: this beat predicts **where fires start**, not how much burns, and the two
are not the same model.

**The second seam, at 11→12.** The same defect as 7, in a different form. Beat 11 ends on a failure;
beat 12 opened on drought and vegetation indices with nothing connecting them, so the covariate arc
read as a change of subject when it is actually the *response* to the failure just shown. Nobody
sourced climate and NDVI out of curiosity — they were sourced to fix exactly what beat 11 exposes.
Beat 12's headline now says so outright ("we tried to fix it with drought and fuel, but..."), which makes
12–14 a repair attempt with a verdict rather than three unexplained slides of covariate results. It
also changes what the null *means*: a covariate that fails after being introduced as a fix is
evidence about the problem, where the same covariate failing in a vacuum is just a dead end.

**Where the Unknown branch sits, and why it moved.** It was beat 7, between the Human arc and the hex
arc. Unknown is not a finding in the sense the other beats are — it is a recommendation about the
record, and the deck's only Unknown slide was interrupting the Human thread to deliver it fifteen
beats before it could be acted on. Moving it to 18 puts it against the recommendation it belongs to,
so beat 19 shows three products for the three Tier-1 classes with all three on screen. The cost is
that Tier 1 introduces a class at beat 3 that is not exercised until 18; beat 19 has to reintroduce
it, which is one sentence rather than a slide.

**The buried lead, and where it moved.** The first ordering was chronological — build the hex grid,
fetch the covariates, run the ablations, discover the tail failure, then notice the ignition gate —
which buried the lead at position 11 of 12. That draft also had a second, larger problem: it opened
on the hex natural surface, which is *one of three tracks* in a two-tier architecture, and presented
it as though it were the whole product. RQ2's actual deliverable, the region-season cause profile,
appeared nowhere. The rewrite restores the hierarchy: Tier 1 establishes **what**, hex grain answers
**where**, and the recommendation joins them.

**The gap the test exposed.** Between "megafire size is not forecastable" (15) and "ignition is a
gate" (16), a reader has no reason to believe the second follows from the first — they read as a
failure followed by an unrelated consolation. Beat 15 is phrased to make the null *force* the reframe
rather than sit beside it. The same test caught beat 11 doing double duty: showing that only
lightning fire has a runaway tail is what licenses two *different* products in beat 19, so it cannot
be compressed away.

**The covariate arc had to be split, not compressed.** Beats 12–14 were one headline reporting a
null. That hid the actual shape of the result: the same fuel data that says nothing about *where a
fire starts* does add real signal about *how much burns* (+0.049, 26.6 SD above a shuffled control) —
and then lands on 1–20 acre fires while the tail goes 855x to 868x. Told as a single null it is a
disappointment; told as three beats it is a contrast that explains why the recommendation sites
against starts rather than against predicted burn size.

**What still needs pod feedback.** Whether the deck reads as one argument or as two stapled together
— the Level III *what* and the hex-grain *where* — is the question I most want a podmate to answer.
The compression candidate if it runs long is beat 4 — it tunes a parameter of the beat-3 baseline
rather than adding a claim, and its finding is that the parameter barely matters. Beat 6 (the
learned rung losing) reads as the same "the simple thing won" note but earns its place: it is the
only beat that concedes a model was tried and lost, which is what keeps the null credible.

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
  2.8x the within-hex year-to-year spread; the two figures that establish why the product ranks
  starts rather than acres — the acres concentration curve and the two-branch decile comparison,
  both computed from the cached acres panel so a figure cannot drift from the notebook that
  reported the number; and the opening seasonality figure, which puts the project's premise on one
  calendar axis — the season that starts the most fires is not the season that burns. That figure
  carries no axes and no magnitudes, because each plotted point is a 29-year mean per week-of-year
  slot and weekly acres are heavy-tailed enough that the mean is not a typical value (peak-week mean
  526k against a median of 237k, a gap produced by 2015 alone). It claims when, not how much; the
  derivation and the caveat are recorded in `notebook/15_w6_visuals.ipynb`. Its spatial counterpart,
  the cause map, shades all 105 ecoregions by natural share of attributed acres — Unknown is kept
  out of the denominator so the map is not partly a picture of attribution quality — and shows the
  regional distribution to be bimodal rather than centred on the national average.

## Next week's "To Do"

- **Fix the point attribution of large unperimetered fires.** Found this week: a point-only fire puts
  its whole acreage on the single hex holding its ignition, which is right at the 14-acre average and
  wrong in the tail — **2,710 point fires over 1,000 acres carry 8.9% of all acres**, and 23 assign
  more than a full hex to one cell, including the record's 606,945-acre maximum at 971% of a hex. The
  fix is to impute a circular burn of the correct area from the ignition point and distribute it with
  the same weight machinery `hex_burn` applies to perimeters; a 606,945-acre circle has a 28 km radius
  against a hex's 9.9 km, so it spreads across ~10 cells. Two things to carry into the build: fires
  elongate along wind and terrain, so a circle errs directionally in a product that sites work by
  location, and rebuilding `hex_acres_res5.parquet` invalidates notebooks 13–15 and every acres figure
  in the deck. Rank statistics mean the W6 findings do not move, which is why this is W7 work rather
  than a W6 correction.
- Build the final deck against this storyboard, one slide per assertion. Beat 4 is the compression
  candidate if it runs long; beats 10 and 11 are a matched pair — 10 sets the stakes, 11 is the
  finding that lands on them — and neither survives alone.
- Every storyboard beat that names a figure now has one, all rendered from
  `notebook/15_w6_visuals.ipynb`; what remains is laying them into slides.
- Test whether same-day conditions — wind, timing, suppression availability — predict which igniting
  natural hexes escape. This is the open question beat 15 concedes, and it is a different model with
  a different data requirement.
- Optionally, a hyperparameter search on the Human branch's learned rungs. Both rungs are built and
  both lost (`08_human_cause.ipynb`): the coarse fingerprint scores 0.588 TVD / 35.7% top-1 and the
  history-aware rung 0.554 / 47.5%, against the k=7 floor's 0.489 / 54.1%. Neither was tuned, so a
  search is the one genuinely untried thing left on that branch.

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
