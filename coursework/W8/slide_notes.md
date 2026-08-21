# W8 slide notes — MSDS696_W7_Deck.pptx

Working notes, one entry per slide, 19 slides numbered 0–18 in delivery order. For each: name, figure, data and method, the question that raised it, findings. Companion to `coursework/W7/final_script.md`, which stays authoritative for delivery text; this file is about what each slide *is*, not how to say it.

**Conventions that apply throughout.** Every prediction is pre-season — features aggregate over months ending strictly before the target season opens, so nothing reads the burn it predicts; same-day conditions were never tested and no null here extends to them. Every target is acres unless the entry says otherwise; counts appear as features and, on slide 4, as a contrast, never as a target. Scoring is forward-chained: train 1992–2009, grade 2010–2020. Spearman = rank correlation on held-out cells; TVD = share of a predicted mix landing on the wrong cause; top-1 = how often the highest-ranked cause was the actual biggest.

## Sample size by figure

**There is no single n in this deck.** Three different units carry the argument, and a figure's n is only interpretable against its unit — 3,949 region-seasons and 149,949 hex-seasons are not a large and a small sample of the same thing, they are different populations at [the two grains](../../CLAUDE.md). Quote the unit with the number. Where a figure is scored, n is the *held-out* population, not the training panel.

| # | Slide | Unit | n | Status |
|---|---|---|---|---|
| 0 | Title | fires (full record) | 2,271,343 | stated |
| 1 | Wildfires are seasonal | fires, all cleaned | 2,271,343 (179.4M acres, 29 years) | stated |
| 2 | Cause is regional | Level III ecoregions | 105 | stated |
| 3 | Cause mix is forecastable | held-out region-seasons | 3,949 | stated |
| 4 | History names the lead cause | held-out region-seasons | 3,850 (volatility split 3,844) | stated |
| 5 | A learned model made it worse | held-out region-seasons | 3,846 | stated |
| 6 | Where fires start is predictable | res-5 hexes, Klamath, JJA 2020 | 198 hexes, 366 starts | stated |
| 7 | Acres are in almost no cells | burning hex-seasons | 167,768 | stated |
| 8 | Natural is harder past a point | burning hex-seasons ≥1 acre | 18,633 natural / 149,949 human | stated |
| 9 | Human year-round, natural summer | held-out hex-seasons, per season-year | 36,234 per point (398,574 per season) | stated |
| 10 | Covariates did not move ignition | held-out hex-seasons, JJA, six forest ecoregions | 29,293 | stated |
| 11 | The data does predict how much burns | burning JJA hex-seasons | 7,799 | stated |
| 12 | The gain misses where it matters | held-out hex-seasons, by decile | 7,799 (780 per decile) | stated |
| 13 | Grain parallel | — | — | plots no data |
| 14 | One ignition is enough | large-fire cells, held-out years | 2,724 | stated |
| 15 | The unattributed gap | held-out region-seasons; 8 of 393 pairs shown | 3,949 cells → 393 pairs | stated |
| 16 | Data sources | — | — | plots no data |
| 17 | Recommendation | joined held-out region-seasons | 3,850 | stated |
| 18 | Closing | — | — | plots no data |

**The four counts, pulled 2026-08-21.** All four resolved against the artifacts, not estimated.

- **Slide 1** — 2,271,343 cleaned fires, 179.4M acres, 29 years. `season_curves()` drops rows with no `DISCOVERY_DOY` and **none are dropped**, so the curves run on the full cleaned record and the slide-0 figure carries over unchanged. Both curves are divided by 29 to read as a typical year.
- **Slide 6** — **198 hexes**, one region-season (Klamath, JJA 2020), 366 actual starts. "Roughly two hundred" was accurate. Note the unit: this is a *single* held-out season shown as a map, not a pooled score — the 6%/32% and 29%/60% capture bands are one season's result, and the national +0.526/+0.344 quoted alongside them comes from a different population.
- **Slide 9** — **36,234 cells per plotted point**, 398,574 per season across the 11 held-out years.
- **Slide 15** — **3,949 held-out region-seasons**, aggregated to **393 region-season pairs**, of which the top 8 are drawn. Two denominators, and the bars are ranked out of 393, not 3,949. The 3,949 matches slide 3 exactly — same Tier-1 held-out population.

**Why n varies across slides 3, 4, 5 and 17.** These are all Level III region-seasons on the same split, but 3,949 / 3,850 / 3,846 / 3,850 differ because the denominator changes with the target: Tier 1 scores every region-season with any acres, the Human branch only those with human acres, and the ablation ladder drops cells missing a feature. None of the differences is a subsetting choice made for the result. The k=7 trailing mean is why all four are far below the 10,135 region-seasons in the full panel — the first seven same-season years of every series have no prediction.

---

## Slide 0 — Title slide

**Figure.** None. A text plate: "For pre-season planning: / Rank the ground, / not the fire." over the project title and author block. The recommendation is stated before any evidence, so the deck reads as an argument for a conclusion rather than a tour of results.

**Caption.** No figure. Source: FPA-FOD 6th ed., 2,271,343 fires, 1992–2020, 179.4M acres.

**Data and method.** Nothing computed. Names the source everything rests on: FPA-FOD 6th edition (Short 2022), 2,271,343 U.S. wildfires, 1992–2020, each with a date, a point location, a size in acres, and a cause code. Two missingness figures stated aloud from `fires_clean.parquet`: 566,210 of 2,271,343 fires have no cause recorded (24.9% by count), but only 33.2M of 179.4M acres (18.5% by acres).

**Question that raised it.** Who is this for, and what should they do differently? The stakeholder is a state or regional fire-agency planner allocating a fixed prevention and mitigation budget before a season opens.

**Findings.** For pre-season planning, rank the ground — not the fire. Where fires start is predictable; how big they get, before the season, is not. The missing-cause quarter is disclosed voluntarily here rather than defended later; slide 15 returns to it as a product.

*Note to self:* both denominators are said on purpose. A quarter of fires, nearly a fifth of acres — the missing fires are smaller than average. Stating only one makes slide 0 and slide 15 sound contradictory.

---

## Slide 1 — Wildfires are seasonal.

**Figure.** `img/w6_seasonality.png`. Two curves over a twelve-month calendar, no y-axis and no magnitudes. A dashed grey line traces when fires start, peaking broadly across March–April; a solid orange filled curve traces how much area burns, peaking sharply in July–August. Annotations: "most fires start in spring," "most acres burn in summer." A narrow spike interrupts the dashed curve in early July.

**Caption.** 2,271,343 cleaned fires, 179.4M acres, 29 years; curves scaled to a typical year.

**Data and method.** All cleaned FPA-FOD records aggregated to day-of-year across 1992–2020 — two series, one counting ignitions, one summing `FIRE_SIZE`. Each curve scaled independently to its own maximum, which is why no axis is shown: the figure asserts *when*, never *how much*.

**Question that raised it.** Does the planning horizon this project assumes — decide before the season — match how fire actually arrives? And is a count of ignitions the same thing as a measure of consequence?

**Findings.** Most fires start in spring; most acres burn in summer. MAM and JJA start nearly the same number of fires and differ 3.9x in acres. The offset, not the seasonality, is the finding: two peaks months apart means counting starts is not measuring consequence — the distinction slide 14 eventually lands on.

The July spike is Independence Day. July 4 is the single highest-start day in the record (16,907 starts, 2.71x the median day); July 5 is second at 15,141. Good verification that human cause shows up in the data; no analysis rests on it.

*Note to self:* NICC (2023), Ch. 60 of the National Interagency Mobilization Guide establishes only that a seasonal-horizon product *exists with a stated purpose* — issued monthly, covers four months, "provides fire managers with the information needed to make long-range decisions concerning resource staffing and allocation." Not what any agency does with it, and not that resources move.

---

## Slide 2 — Cause is regional, not national.

**Figure.** `img/w6_cause_map.png`. Choropleth of CONUS plus an Alaska inset, drawn on EPA Level III ecoregion boundaries rather than state lines. Diverging blue-to-orange ramp from "human-dominated" to "natural-dominated," breaks at 0/5/20/40/60/80/95/100%. Orange west of roughly the 100th meridian, blue east, Alaska almost entirely deep orange, a pale band of mixed regions along the seam through the Plains.

**Caption.** 105 Level III ecoregions; 146.0M resolved acres (missing-cause acres excluded from shading).

**Data and method.** Every cleaned fire placed into an ecoregion by two separate spatial joins — one against the CONUS layer, one against Alaska — then acres summed per region and shaded by natural share of *attributed* acres. Missing-cause acres excluded from the shading; denominator is resolved causes only. 105 ecoregions cover the country.

**Question that raised it.** Is there a single national answer to "what starts fires," or does the answer depend on where you are? And what spatial unit should carry the analysis?

**Findings.** No national answer — regional ones. West/East split at roughly the 100th meridian, and the distribution is bimodal: 50 regions below 20% natural, 28 above 80%, only 27 in between. Bimodality is the load-bearing part, not the split. A gradient would mean every region needs its own blended strategy; two modes mean most regions have a dominant cause a planner can act on.

*Note to self:* the ecoregion unit is a design decision, not a tested result — no state-boundary version was built and beaten. Chosen because Level III ecoregions are delineated from terrain, vegetation, soils and climate, where a state boundary is administrative (Omernik & Griffith 2014). This is the only slide that explains the unit and slides 3–5 all run on it, so it can't be cut for time.

---

## Slide 3 — A region's cause mix is stable enough to forecast.

**Figure.** `img/w6_tier1_tiles.png`. Three tiles, each a labelled baseline over a large percentage, a progress bar, and a span rule beneath. Left to right: the national average mix 42% (typical range 21–61%), an even split across causes 52% (36–67%), the region's own seasonal history 73% (58–91%). Only the winning tile's bar is colored.

**Caption.** 3,949 held-out region-seasons, 2010–2020; 80.0M held-out acres; trailing-mean k=7, forward-chained, acre-weighted TVD.

**Data and method.** Tier 1 of the hierarchical model. For each ecoregion-season the target is the composition of burned acres across three classes — Human / Natural / Unknown — on a total-acres denominator (resolved + missing) so the three sum to 1. Full-record class shares: Natural 58.9%, Human 22.7%, Unknown 18.5%, of 179.3M acres.

Winning baseline is a trailing mean of the region's own prior *same-season* occurrences, k=7, grouped by `(region, season)` and shifted one period so it is strictly pre-season. Acre-weighted, forward-chained on 2010+, 3,949 held-out region-seasons. Tiles plot 1 − TVD; acre-weighted TVD is 0.580 / 0.485 / 0.266.

**Question that raised it.** Given slide 2, can next season's cause mix for a region be forecast at all — and does anything cheap beat the obvious alternatives?

**Findings.** A region's own seasonal history wins by a wide margin, and a settled history forecasts well while a swinging one doesn't. The comparison carries the weight, not any single tile: the national average mix (42%) is worse than assuming you know nothing (52%) — slide 2's bimodality reappearing as forecast error. A national average describes almost no individual region, which is why its first quartile reaches down to 21%.

Unknown is a predicted class in its own right, holding the missing-cause acre mass — not a discard. That's what makes slide 15 a product rather than an apology.

*Notes to self:*
- 73% is an error magnitude (1 − TVD), not a hit rate — no "of the time" attaches. Slides 4 and 5 use the same visual but plot top-1, where "of the time" *is* correct. Not the same scale; don't compare 73% with slide 4's 54%.
- "Seasonal history" means each season is its own series: k=7 is seven prior *same-season* occurrences, about seven years back, not seven consecutive seasons. Consequence: the first seven same-season years of every series are unpredictable, which with the 2010 split is why the held-out population is 3,949 rather than all 10,135.
- The spans are acre-weighted p25–p75 across region-seasons, not confidence intervals.
- Most confusable pair of numbers in the deck: Tier-1 shares by acres are Human 22.7 / Natural 58.8 / Unknown 18.5, but by fire count Human 60.7 / Natural 14.4 / Unknown 24.9 — Human and Natural almost swap. Both true. Every target and score in this project is acres.

---

## Slide 4 — For human-cause wildfires, history names the lead cause more often than not.

**Figure.** `img/w6_human_tiles.png`. Same three-tile visual, one tier deeper, ordered worst to best: an even split across 11 causes 9%, the national human mix 16%, the region's own seasonal history 54%. Beneath the winning tile, instead of a span, a split: "43% most volatile · 68% steadiest."

**Caption.** 3,850 held-out region-seasons (volatility split 3,844), 2010–2020; human-acres denominator; trailing-mean k=7, forward-chained, acre-weighted TVD.

**Data and method.** The Human branch of Tier 2, at Level III region-season grain. Target is the composition of 11 human sub-causes — arson, equipment and vehicle use, debris and open burning, recreation and ceremony, power generation/transmission, railroads, smoking, firearms and explosives, fireworks, misuse of fire by a minor, other — on a *human-acres* denominator, excluding Unknown entirely. Same k=7 trailing mean, same forward-chained split, 3,850 held-out region-seasons; the volatility split is on 3,844. Tiles plot top-1 hit rate out of 11. Acre-weighted TVD 0.489 for history against the national mix's 0.643.

**Question that raised it.** Tier 1 says how a region-season's acres split three ways. Within the human share, can the *specific* cause a planner would act on be named — and is ranking by acres different from ranking by how often each cause starts fires?

**Findings.** History names the leading human cause 54% of the time out of 11 causes, against 16% for the national human mix and 9% for an even guess.

The ranking is not the obvious one. National acre shares: arson 26.5%, equipment and vehicle use 24.4%, debris and open burning 19.2%. But by count, debris burning starts 535,832 fires — the most of any human cause — and is only third in acres, while equipment starts 190,253, about a third as many, and burns more. What's worth preventing isn't what starts most often. That inversion is the argument for ranking by acres.

Confidence is anticipated rather than random: 43.5% top-1 in the most volatile quartile of pre-season dispersion against 68.2% in the steadiest — a 25-point spread, wider than Tier 1's 21, on the weaker of the two products.

*Notes to self:* 54% is the Human floor on Human's own population — not an end-to-end number; end to end is 46.2%. The denominators differ between tiers by design: Tier 1 divides by total acres including Unknown, Human divides by human acres and excludes it. This is the deck's only place where fire *counts* are quoted as a ranking, deliberately, to justify ranking by acres.

---

## Slide 5 — A learned model made naming the leading cause worse.

**Figure.** `img/w6_human_ladder.png`. Four horizontal bars, best at top, against a dashed vertical line marking the floor. The region's own seasonal history 54% (orange, the only colored bar, and the line's position); ridge given that history 52%; gradient boosting given that history 47%; gradient boosting on region character 36%. Axis label: "how often the leading human cause is named correctly." Every learned bar falls short of the dashed line.

**Caption.** 3,846 held-out region-seasons, 2010–2020; all rungs on identical cells, features and weights; ridge and gradient boosting vs. the k=7 floor, acre-weighted TVD and top-1.

**Data and method.** Ablation ladder in `notebook/08_human_cause.ipynb`, all rungs sharing features, split, acre weights, held-out cells (3,846) and simplex projection so only the named ingredient changes. The two plotted boosting rungs are `SimplexRegressor()` wrapping `HistGradientBoostingRegressor` (`max_iter=300`, `learning_rate=0.05`, `max_leaf_nodes=31`). Ridge rung is a per-sub-cause ridge, everything else identical. Top bar is slide 4's winning tile replotted, not a new measurement. Acre-weighted TVD in order: 0.489 / 0.537 / 0.554 / 0.588.

**Question that raised it.** Slide 4's winner is a trailing mean — arithmetic, not learning. Does a real model beat it? And if not, is the learner at fault or is the information not there?

**Findings.** None of the learned rungs beat the region's own seasonal history, including the ones handed that history as features. Losing to history is unremarkable; losing *while holding history* is the finding, and it happened twice with two different model families.

The history-aware rungs were given the 11 trailing human-mix columns — the exact quantity the floor averages — so the floor is a function they could represent by ignoring everything else. Gradient boosting still finished 6.5 TVD points and 6.6 top-1 points short of a quantity it was given. That rules out "you never gave it the right features."

Ridge beats gradient boosting by 4.7 points of top-1, so the booster was paying a variance cost on a small wide panel (~5,300 training cells, 23 features, 11 correlated targets). Correcting that recovers five points and still doesn't reach the trailing mean. Ridge isn't merely rediscovering the floor — 0.283 TVD units away per cell, naming a different top cause in a quarter of them (75.2% argmax agreement).

*Notes to self:* the anti-tuning evidence is the flat alpha sweep — across four orders of magnitude (0.1 → 1000) ridge's top-1 is identical to six decimal places and TVD moves in the fifth. That's an information ceiling, not an under-tuned model. Still untried: a full hyperparameter search over the booster. So the claim is "gradient boosting and ridge both lost," never "machine learning doesn't work here." Figure shows four bars but the ladder has five rungs — ridge on coarse fingerprints scores 35.67%, indistinguishable from the boosting coarse bar, so it isn't plotted. Keep this slide: it's the only one conceding a model was tried and lost, which is what keeps the nulls credible.

---

## Slide 6 — Where fires start is predictable, at the scale where you'd site the work.

**Figure.** `img/w6_siting_glance.png`. One ecoregion — Klamath Mountains/California High North Coast Range — drawn as roughly two hundred res-5 hexagons, with a small CONUS locator inset. Two shaded bands over a pale grey field: a deep maroon band annotated "6% of the region · 32% of the starts," clustered in a dense ridge across the north, and a wider light orange band annotated "29% of the region · 60% of the starts." Most of the region is unshaded.

**Caption.** 198 res-5 hexes, Klamath Mountains, JJA 2020; 366 observed starts; persistence baseline, forward-chained; one season, not pooled.

**Data and method.** The deck's one grain change, and three things change at once: unit drops from 105 ecoregions to 36,234 res-5 H3 hexes (~62,494 acres each), target changes from acres to ignition counts, answer changes from shares to counts.

Counts built from raw ignition points — all ~2.27M fires, no MTBS join — because an ignition location is exactly what FPA-FOD stores correctly; distributing a perimeter would smear one ignition across ~26 hexes and corrupt the count. Ranking skill scored on held-out 2010–2020 after training on 1992–2009 (`src/hex_ignitions.py`, `src/hex_panel.py`).

**Question that raised it.** An ecoregion is the right unit for deciding *what* to target but far too coarse for deciding *where* to put sited work — fuel treatment, defensible space, suppression pre-positioning all pay off only if fire arrives there. At a scale a planner can act on, can next season's ignitions be ranked?

**Findings.** Yes. In the Klamath, 6% of the ground catches 32% of next season's starts (5.2x); a wider band of 29% catches 60% (2.1x). Nationally, held-out rank correlation is human ignitions +0.526, natural +0.344.

The anchor for judging that: dealing the identical predictions to the wrong hexes scores +0.0002 — that's what zero looks like in this data. The typical miss also worsens under shuffling, 0.43 → 0.77 fires per cell, worse than the 0.70 you get predicting the national average everywhere. Misplaced predictions are worse than no predictions, so the skill is spatial, not statistical luck.

Human beats natural because people ignite in the same places year after year — roads, structures, recreation sites — where lightning is more nearly random across a landscape. Slide 9 gives that gap its own slide.

*Notes to self:*
- Starts figure, not an acres figure. Unsaid, the capture curve reads as "32% of the burn under 6% of the ground," a much stronger claim than the one being made.
- The headline asserts a *scale*, not a comparison. No ignition model was ever built at ecoregion grain and beaten, so the hex grain is a design argument, not a head-to-head win.
- This is a distinct sub-project, not a rescue of slide 5. Delivered right after a null, the room will infer the ecoregion model underperformed and the analysis went looking for a better number at finer grain. It didn't.
- The return decays fast: 90% of starts needs 77.8% of the ground at 1.16x.
- "It ranks well," never "it is accurate" — the forecast under-predicts the busiest hexes, 4.7 predicted against 3.7 observed in the top stratum.

---

## Slide 7 — Almost all the area burned is in almost none of the cells.

**Figure.** `img/w6_acres_concentration.png`. A cumulative concentration curve: cells ordered by acres burned least to most along the x-axis, cumulative share of natural acres up the y-axis. The orange curve runs flat along the bottom across most of the width, then turns almost vertically at the right edge; a dashed diagonal labelled "if acres were spread evenly" shows what a uniform distribution would look like. Two annotations with marker dots: "the worst-burning 10% of cells hold 98% of the acres" and "the worst-burning 1% of cells hold 55% of the acres."

**Caption.** 167,768 burning hex-seasons; zero-burn cells excluded; perimeter-corrected acres; descriptive, no model.

**Data and method.** Natural acres per hex-season, from the perimeter-corrected hex panel. Acres come from `src/hex_burn.py`, which applies two rules chosen per fire: a fire linked to an MTBS perimeter has its acres split across the hexes the perimeter covers, weighted by intersected area; a point-only fire puts all its acres on the hex containing the ignition. Per-fire weights sum to 1, so the hex panel reconciles exactly to ecoregion totals — this redistributes acres, never restates them. Perimeter-linked fires are 0.6% of records but 81.6% of acres; point-only fires average 14 acres against a 62,494-acre hex.

167,768 burning cells; zero-burn cells excluded, since 96% of hex-seasons never burn and including them would make the curve a statement about how rare fire is rather than how it concentrates once it happens.

**Question that raised it.** Slide 6 established that starts can be ranked. Before asking whether *acres* can be forecast, where do the acres actually sit — i.e. which cells would a forecast have to get right to be worth anything?

**Findings.** The worst-burning 10% of cells hold 98% of the acres; the worst-burning 1% hold 55%. Stated from the other end, 90% of cells hold 2% of the burn. So a forecast only matters at the right-hand edge — which is the standard slide 8 is then measured against.

This is a concentration claim, not a predictability one. Nothing here says the big cells are *findable* in advance; slide 8 answers that, and the answer is partly no.

*Notes to self:*
- Target switches back to acres here — same hexes and same left-to-right ordering as slide 6, different quantity. Prime spot for a listener to hear "1% of cells hold 55% of the starts."
- Human fire concentrates comparably but the ranking flips depending on where you look: human's worst 1% of burning cells hold 71% of human acres against natural's 55%, but human's worst 10% hold 93.5% against natural's 98.2%. Both extreme; neither branch is "the concentrated one."
- Known defect to volunteer if pressed: the point rule breaks in the tail. 2,710 point fires exceed 1,000 acres and carry 8.9% of all acres, each landing entirely on one cell; 23 rows assign more than a full hex to a single cell, including one at 606,945 acres (971% of a hex). The fix — imputing a circular burn from the ignition point and distributing it the same way — is designed, not built. It doesn't move the argument: the claim is about shape, and slide 8's decile statistics are rank-based.

---

## Slide 8 — Up to a point, human and natural burned area is equally predictable. Past that point, natural is harder.

**Figure.** `img/w6_branch_deciles.png`. Two lines on a log y-axis labelled "how far off the forecast was," against deciles of cells ordered by acres burned least to most. Blue "human" and orange "natural" track together and near 1x across the left two-thirds, then diverge sharply: natural climbs to roughly 690x at the right edge while human reaches about 19x. Every gridline is 10x the one below.

**Caption.** 18,633 natural vs. 149,949 human burning hex-seasons, ≥1 acre, 2010–2020; persistence baseline, forward-chained; median log error by decile.

**Data and method.** Median log error by decile, both branches scored on the persistence baseline at hex-season grain, held-out years. Cells under 1 acre are excluded: 25.3% of cleaned FPA-FOD rows sit at exactly 0.1 acres — 44.5% of natural fires against 19.0% of human ones — a default entered for a fire too small to measure rather than a measurement. Populations differ by an order of magnitude: 18,633 natural cells against 149,949 human.

**Question that raised it.** Slide 7 named the cells a forecast has to get right. Does the acres forecast get them right, and does the answer differ by branch?

**Findings.** The branches track through the smallest third, then separate. At the right edge natural reaches 687x on a median 8,061-acre cell against human's 19x on a median 240-acre cell. At *matched* cell size natural still runs 2–3x worse than human.

This licenses shipping two different products: human acres can be ranked by expected acres, natural cannot — which means for lightning the answer has to be something other than acres. That pivot is what sends the argument to ignition on slide 14.

*Notes to self:*
- Say the y-axis is logarithmic or the figure understates itself: what looks like a moderate separation is 687x against 19x, a 37-fold difference in error. The one slide where the honest reading is worse than the eye's.
- The two top-decile numbers are not on the same cells, so 687-vs-19 is not a controlled comparison. Quote the population with the number: across all JJA natural burning cells the top decile is 269.8x on a median 2,970-acre cell; 854.9x is the six-forest-ecoregion population used for the covariate ladder. The like-for-like against human is 269.8x, not 855x.
- Sub-acre cells are excluded here but kept on slide 7, and the reason differs by figure: here their *error* is a records artifact, there the quantity is acres, which are real however coarsely recorded. Restricting to cells ≥1 acre cuts the smallest decile's apparent error from 10.0x to 4.3x, so the over-prediction of small cells is partly a records artifact.
- Never say "the model fails on large fires" without "before the season."

---

## Slide 9 — Where human fires start is predictable year-round; natural only in summer.

**Figure.** `img/w6_season_skill.png`. Two lines across Winter / Spring / Summer / Fall on a y-axis labelled "how well next season's starts can be ranked," each with a shaded band. Blue "human" runs high and flat — about 0.53 in winter, peaking near 0.60 in spring, easing to 0.47 by fall. Orange "natural" starts near 0.07 in winter, climbs to a summer peak around 0.42, and falls back to 0.19 by fall. The bands overlap only slightly, in summer.

**Caption.** 36,234 hexes per plotted point; 398,574 per season across 11 held-out years; persistence baseline, forward-chained; held-out Spearman, band is min–max.

**Data and method.** Held-out Spearman for the ignition-count target, each branch scored separately in all 11 held-out years and split by season. The band spans the observed year-to-year range (min to max across 11 years), not an error bar. Medians: human DJF 0.529, MAM 0.605, JJA 0.483, SON 0.469; natural DJF 0.072, MAM 0.201, JJA 0.422, SON 0.190. Human ran 0.32–0.67 across all season-years, natural 0.06–0.46; a shuffled control stayed inside ±0.014.

**Question that raised it.** Slide 6 gives one all-season number per branch. Does that skill hold evenly through the year, or does it hide a seasonal structure a planner would need to schedule around?

**Findings.** Human fire is rankable all year — it peaks in spring but never drops far. Natural fire is a summer phenomenon: good in July, essentially nothing by winter. Human beats natural in all 44 season-years without a single exception (11 held-out years x 4 seasons), which is the number that closes the door on "the gap could be noise" given the slight summer overlap.

The operational reading is a real product difference: human ignition is a year-round program, lightning a seasonal one — and lightning is the one that burns the most. This is the one place seasonality returns as an *implementation* question rather than a data pattern, which is what makes slide 1 pay off.

*Notes to self:* target flips back to ignition counts here after two acres slides, and slide 8 also plotted a skill measure, so this can be misheard as continuing its error story. Don't overclaim winter natural — median 0.072 with a best year of 0.180 is near-nothing, and it's not a weak signal to be improved, it's the season where lightning ignition is rare enough that there's little to rank. Bands are min-to-max, not confidence intervals. The deck's only figure showing a distribution rather than a point estimate.

*Open sequencing question:* slide 9 isn't part of the 10–12 repair loop — it characterizes *when* the slide 6 surface works, so it sits naturally beside slide 6. Moving it would make 8 → 9 → 10 a continuous acres-failure-then-repair run and drop the deck from four target flips to three. Not done yet; revisit after a measured run.

---

## Slide 10 — We tried to improve that with drought and fuel, but where fires start is a property of the place, not of the year.

**Figure.** `img/w6_ignition_ladder.png`. Two nearly flat lines across four rungs — "the region's own history," "+ drought," "+ fuel load," "+ both" — on a y-axis running from zero to 0.6. Blue "human fire" sits around 0.48, orange "lightning fire" around 0.42, and neither moves perceptibly across the rungs. A bold annotation reads "nothing we added moved it."

**Caption.** 29,293 held-out hex-seasons, JJA, six forest ecoregions, 2010–2020; covariate ablation over the persistence floor, covariates lagged pre-season; held-out Spearman.

**Data and method.** Covariate ablation on the ignition-count target, both branches on the same 29,293 held-out cells (JJA, the six forest ecoregions). Drought is TerraClimate PDSI / soil moisture / deficit / VPD at hex grain (`src/hex_climate.py`); fuel load is MODIS MOD13A1 NDVI per hex-season via the Planetary Computer STAC API (`src/hex_ndvi.py`). Every covariate is lagged to pre-season availability — aggregated over `preseason_months()`, ending strictly before the target season opens — and missing external data surfaces as NaN, never imputed to zero. The y-axis runs from zero so a real effect would be visible.

**Question that raised it.** Slide 8 leaves a failure on the table. If history alone can't forecast acres in the tail, do physical covariates — how dry it is, how much fuel is there — add anything? Slides 10–12 are the repair attempt.

**Findings.** Nothing moved. Best gain on either branch is +0.0045 — five consecutive covariate nulls across two branches.

The measured reason, spoken rather than drawn: these covariates identify dry *places*, not dry *years*. From raw to within-hex anomaly, PDSI correlation with ignitions goes -0.137 → -0.073 and NDVI +0.228 → +0.098 — both roughly halve. Strip out which cell you're looking at and most of the signal goes with it. Greener cells do get more fires than browner ones, but a cell that's greener *than its own normal* barely gets more fires than its own normal. Place is what history already knows.

The correct compression is "fires happen where fires have happened," not "fires happen where the fuel is."

*Notes to self:* deliver as a result, not an apology — five ablations, a zero-based axis, a stated mechanism. Target flips back to starts here. The figure labels the branch "lightning fire" while slide 8's headline says "natural" — same class; prefer "natural" when speaking so it matches slides 3, 7, 8 and 17. Q&A companion: `img/w6_ndvi_variance.png`, the place-vs-year split at 2.8x.

---

## Slide 11 — The same data does predict how much burns.

**Figure.** `img/w6_acres_ladder.png`. Deliberately the same figure as slide 10 — same four rungs, same axis, same zero-based scale — but one orange "lightning fire" line instead of two. A dashed horizontal reference marks the history-alone baseline. The line dips slightly at "+ drought," returns at "+ fuel load," then rises at "+ both," where an arrow and a bold "+0.049" annotate the step.

**Caption.** 7,799 burning JJA hex-seasons, 2010–2020; burn-conditional baseline, covariate ablation, validated across five split years; held-out Spearman.

**Data and method.** Same rungs and same covariate layers as slide 10, but the target is burned acres rather than ignition counts, and the population is 7,799 burning JJA cells on a burn-conditional baseline. The gain is validated against a covariate-shuffled control and across five forward-chaining split years.

**Question that raised it.** Slide 10 killed the covariates on starts. Do they fail everywhere, or only on that target?

**Findings.** They move here. Climate + NDVI together give +0.049, 26.6 SD above a covariate-shuffled control, holding across five split years (+0.012 to +0.066).

The conjunction is the finding, not the size of the gain: drought alone -0.008, fuel alone +0.001, both together +0.049. Neither half works alone — wet heavy fuel won't carry fire, dry bare ground has nothing to burn. You need both.

Why this worked where slide 10 failed: different target. Where a fire *starts* is a property of the place, which history already knows. How much *burns* depends on conditions that vary year to year — exactly what these covariates measure. That contrast is the reason both slides exist.

*Notes to self:* never quote the level, only the step. The figure annotates +0.049 rather than the level 0.3075 on purpose — the level invites comparison with slide 10's ~0.42–0.48, a different population and a different target. "A fifth better than history alone" is the safe relative statement. This is the deck's one verified covariate win and must not be oversold, because slide 12 takes it away; the closing line hands off rather than banking it.

---

## Slide 12 — But the gain misses where we need it most.

**Figure.** `img/w6_gain_landing.png`. Slide 8's axis again — log "how far off the forecast was" against deciles of cells ordered by acres burned. Two lines: grey "history alone" and blue "+ drought and fuel." A pink lens opens on the left where the covariate line runs *above* the baseline, and a blue lens opens in the middle-right deciles where it runs below, annotated "the gain lands here." At the right edge both lines converge at nearly 1,000x, with a curved arrow labelled "no better where the acres are."

**Caption.** 7,799 held-out hex-seasons, 780 per decile; same cells and model as slide 11; median log error by decile.

**Data and method.** The slide 11 covariate model and the history baseline scored on the same held-out cells and plotted by decile of realized acres, 780 held-out cells per decile.

**Question that raised it.** Slide 11 produced a statistically solid gain. Does it land on the cells slide 7 said actually matter?

**Findings.** No. The gain opens in deciles 6–9, on cells of one to two hundred acres, and closes at the right edge where the two lines finish together — 855x → 868x on a median 5,073-acre cell. The forecast improved exactly where it doesn't matter.

Worse, deciles 1–5 deteriorate: decile 1 nearly doubles, 18.8x → 35.9x. That's the pink lens, and it rules out "well, it helps a bit everywhere" — the model trades accuracy on small cells for accuracy on medium ones and buys nothing where the acres are.

So a gain that survives every statistical test still doesn't buy a planner anything, which says the problem isn't the features. That closing line is the deck's turn: it licenses slide 13's grain argument and, through it, the recommendation.

*Notes to self:* slide 7 is what makes this fatal rather than disappointing — the improvement misses the cells holding 98% of the acres. Say "the cells holding almost all of the burn" rather than re-quoting 98%. Third slide landing the eye on the same right edge, which is the payoff of drawing 7, 8 and 12 on the same axis in the same direction. Don't say the covariate model "failed" — it produced a verified gain at 26.6 SD across five split years; it failed to be *useful*, a different and more interesting claim.

---

## Slide 13 — Predicting where fires start needed a finer spatial scale. Predicting size may need a shorter time scale.

**Figure.** `img/w6_grain_parallel.png`. The deck's only figure that plots no data, and its only one about method rather than fire. Two rows of labelled boxes with an arrow between each pair. Top row, "WHERE IT BURNS": solid boxes reading "the region" → "the hex," marked *solved*. Bottom row, "HOW BIG IT GETS": dashed orange boxes reading "the season" → "the day," marked *untested*. Caption beneath: "one drop is a result. the other is a hypothesis."

**Caption.** No data plotted — method diagram.

**Data and method.** Nothing computed. It's a structural argument drawn from the pattern of results: the spatial drop was made and worked (slide 6), the temporal drop is proposed and untested.

**Question that raised it.** After five nulls and one useless gain, what kind of failure is this? If it isn't the features, is it the unit the question is asked in?

**Findings.** Siting worked once the question stopped being about a whole region and dropped to a hex. The same problem may sit on the other axis: the deck asks how big a fire gets over a whole *season*, and what makes a fire run is the wind on a particular afternoon and whether crews were already committed. A season may simply be too coarse a unit to see that.

This couldn't be tested here — same-day data is a different project with a different data requirement. But the shape of the failure says where to look. It's the fourth time the project has met the same lesson: W4's pooled climate null, slide 10's places-not-years, slide 6's grain drop, now this.

*Notes to self:* say "before the season" whenever the claim is stated as a null — "megafire size is unpredictable" is a much bigger claim than anything measured. Don't apologise for the null: five ablations, a shuffled control at 26.6 SD, and a gain that landed in the wrong deciles is a thorough negative result. "Did you try hard enough?" — pre-season data was tried hard, same-day data wasn't tried at all; the second half is the open question, not a gap.

---

## Slide 14 — One ignition is enough.

**Figure.** `img/w6_one_is_enough.png`. A single stacked horizontal bar under the heading "half of every large fire started with a single ignition," split three ways: a wide orange segment "49% ONE ignition," then grey "21% two" and pale grey "30% three or more." Only the first segment carries color. Caption: "all 2,724 large fires in the held-out years, by how many times their cell ignited that season."

**Caption.** 2,724 large-fire cells (≥1,000 acres), held-out years, JJA natural; descriptive, no model.

**Data and method.** All 2,724 large-fire cells in the held-out years, classified by their hex's natural ignition count that season. The gate statistic is spoken rather than drawn: a hex-season that ignites at all produces a ≥1,000-acre burn 6.7% of the time against 0.29% for one that doesn't — 22.8x, JJA natural, held-out years. (`img/w6_ignition_gate.png` is available if challenged.)

**Question that raised it.** Slide 13 says size isn't forecastable before the season. Is the event *upstream* of size — ignition — worth targeting instead? And if so, how should a planner act on an ignition surface: rank cells by how often they ignite?

**Findings.** Ignition is worth targeting: a cell that ignites at all is about twenty times more likely to produce a thousand-acre fire than one that doesn't. That's the case for going after starts.

But the obvious way to act on it is wrong. Of every large fire in the held-out years, 49% came from a cell that ignited exactly once that season, 21% from two, 30% from three or more. So it isn't a dial you turn up — it's a **gate**: does this place ignite at all. Rank cells by how *often* they ignite and you deprioritise the ground that produced half the big fires.

This is the door slide 13 left open — size isn't forecastable before the season, but the event upstream of it is, and that's what the recommendation acts on.

*Notes to self:* two jobs on this slide — the case for targeting ignition at all (the 22.8x gate) and the instruction for how (the binary rule). If the opening sentence gets cut for time, the deck asserts "target where they start" without ever saying why ignition is worth targeting. Don't oversell the gate: it's necessary, not sufficient — 93% of igniting hex-seasons still produce nothing large. Say "about twenty times" rather than 22.8x; the precision is false comfort on a screening statistic. If asked whether more ignitions carry more risk: the rate does rise (19.1% at 11–20 ignitions vs 5.4% at one), but risk *per ignition* falls 0.054 → 0.014. Also worth knowing: ignition count ranks burned area worse than the hex's own burn history does, +0.253 against +0.357.

---

## Slide 15 — Nearly a fifth of burned acres have no specific cause — and that gap is itself forecastable.

**Figure.** `img/w6_unknown_triage.png`. A ranked horizontal bar chart of eight region-seasons by predicted unattributed acres, each bar labelled inside with its attribution rate and outside with its acre total. Top and highlighted in orange: Southwestern Tablelands MAM, "51% of its acres unattributed," 1,165k acres. Then Central California Foothills and Coastal Mountains JJA (40%, 851k), Columbia Plateau JJA (45%, 831k), Central Great Plains MAM (66%, 703k), Columbia Plateau SON (71%, 538k), High Plains MAM (42%, 441k), Klamath Mountains JJA (16%, 415k), Central Basin and Range JJA (19%, 395k).

**Caption.** 3,949 held-out region-seasons → 393 region-season pairs, 2010–2020; trailing-mean k=7, forward-chained; acre-weighted MAE 0.167 vs. global mean 0.240; top 8 shown, ranked by predicted acres.

**Data and method.** The Unknown branch of Tier 2, at Level III region-season grain (`notebook/09_unknown_dataquality.ipynb`). The Unknown class holds the `missing_acres` mass from Tier 1; the branch predicts next season's unattributed acres per region-season and ranks them. Persistence baseline: acre-weighted MAE 0.167 against the global mean's 0.240. The output is an operational recommendation, not a forecast of fire.

**Question that raised it.** A quarter of fires have no cause recorded, and the missingness is differential across regions — it concentrates in low-Natural, human-dominated regions (Pearson ≈ -0.64 against Natural share). Is that a limitation to caveat, or a thing to predict?

**Findings.** A thing to predict. It's been a class in its own right all along, not a gap to apologise for. Predicting where the record goes dark gives a worklist: the region-seasons where the most acres will go unattributed next season, headed by Southwestern Tablelands in spring at about 1.17M acres.

Ranked by acres, not by rate — and that ordering is the point. Central Great Plains has the worse attribution rate at 66% but sits fourth, because fixing the record where little burns buys nothing. The rate is a data-quality statistic; the acres are what a records fix would recover.

*Notes to self:* this pays off the title slide's voluntary disclosure — without the callback, slide 0 sounds like a caveat and this sounds like a change of subject. The denominator trap returns: slide 0 says "a quarter of fires" (24.9% by count), this headline says "nearly a fifth of burned acres" (18.5%); both correct, and the missing fires are smaller than average. Never claim a *cause* for the missing data — the project has never established why attribution fails in these region-seasons, the missingness is agency-shaped, and triage by reporting stream is explicitly open work. Say where the record is weak; never say who is failing to record it.

---

## Slide 16 — We started with one record of every U.S. wildfire, then layered on what it could not see.

**Figure.** `img/w6_data_sources.png`. A sources layout: FPA-FOD 6th edition set apart at the top in orange with a rule beneath it, labelled as the spine ("2.27M fires, 1992–2020 — date, location, size, cause"). Under "joined onto it," four layers each with citation, DOI, and a right-hand note saying what it contributed: EPA Level III ecoregions ("the regional unit — 105 regions"), MTBS burned-area perimeters ("fire as an area, not a point — 81.6% of acres"), TerraClimate ("drought before the season — PDSI, soil moisture, deficit, VPD"), MODIS MOD13A1 v6.1 ("fuel load — 500 m vegetation index, via Microsoft Planetary Computer").

**Caption.** No data plotted — source layout.

**Data and method.** The slide *is* the method, at the sourcing level. Full citations: Short (2022), `doi.org/10.2737/RDS-2013-0009.6`; U.S. EPA (2025) with the framework from Omernik & Griffith (2014); Eidenshink et al. (2007), USGS, `doi.org/10.5066/P9IED7RZ`; Abatzoglou et al. (2018), Climatology Lab; Didan (2021), NASA LP DAAC, `doi.org/10.5067/MODIS/MOD13A1.061`.

**Question that raised it.** What is this built on, and what did each addition buy?

**Findings.** One federal record is the spine — it knows when a fire started, where, how big it got, and what caused it. What it doesn't know is the shape of the burn, what the ground was like, or how dry the season had been, so four layers were joined onto it to answer specific questions the base record couldn't.

The order is the method: each layer was added for a named deficiency — the perimeters because FPA-FOD stores a *point* with an *area* attached, the covariates because the record says nothing about conditions.

*Notes to self:* the slide exists to show the layering, not to be read — every citation is on screen, and reading DOIs aloud is the worst possible use of thirty seconds. Two of these layers produced nulls, and that's not a failure of sourcing: TerraClimate and MODIS were joined, tested on both branches, and didn't improve ignition prediction — they're what makes slides 10–12 a measured result rather than an untested assumption. The Planetary Computer is an access route, not a source; MODIS is NASA's. If asked about LANDFIRE: pre-rejected for this panel — circa-2001 base map, discrete vintages, Alaska only from the 2016 Remap, so almost no interannual variance. Deliberate exclusion, not oversight.

---

## Slide 17 — Target causes by region. Site the pre-season work by ignition. Fix the record where it says neither.

**Figure.** `img/w6_recommendation.png`. Three stacked rows, one per Tier-1 class, ordered by acre share so the top row is where the acres are. Each row: class name and share on the left, a bordered box with an instruction and a one-line gloss, and the grain on the right. NATURAL 58.9% — "Site the work by ignition / rank ground, treat what ignites at all" — hex-season (orange border). HUMAN 22.7% — "Target causes by region / rank causes by the acres they drive" — ecoregion-season (blue border). UNKNOWN 18.5% — "Fix the record underneath / rank regions by unattributed acres" — ecoregion-season (grey border).

**Caption.** No new computation; composes three branch products. Tier 1 × Human, top-1 0.4619 on 3,850 joined held-out cells.

**Data and method.** No new computation; it composes the three branch products and their grains. Worth carrying: composing Tier 1 x Human gives top-1 0.4619 on 3,850 joined held-out cells — identical to Human scored alone, because Tier 1 contributes one scalar that multiplies all 11 sub-shares and cannot move their argmax. So the ranked profile does not inherit Tier 1's error; the acre level does (predicted human acres: median 1.01x, but 2x low at p10 and 8x high at p90).

**Question that raised it.** Three branches at two grains with different targets — what does the planner actually do with them, and in what order?

**Findings.** Three products, one per class, ordered by where the acres are. For lightning — the majority of the burn — rank the ground and treat what ignites. For human fire, rank the causes by the acres they drive. Where the record says neither, fix the record.

One boundary applies to all three: **trust the order, not the number.** These say which region, which cause, which ground comes first. They don't say how many acres will be saved.

*Notes to self:* a targeting claim, not an efficacy one — nothing in this project measures what a treatment achieves; no before/after, no control, no counterfactual. If asked "so if we treat those hexes, we cut the burn?", say no plainly. Davis et al. (2024) on severity reduction is separate evidence from someone else's study; cite if asked, don't fold it in. The boundary line is spoken only — the figure doesn't print it, so it's the one thing on this slide the audience can't read for themselves. (The script's WATCH claims the figure prints the title verbatim with a subtitle beneath; the current PNG does not — it's three rows only. Either the figure or that note needs fixing before the final.)

---

## Slide 18 — Closing slide

**Figure.** None, by design — two lines and a smaller third, nothing to read while talking:

> **Rank the ground, not the fire.**
> Where fires start is predictable. How big they get, before the season, is not.

**Caption.** No figure.

**Data and method.** Nothing computed.

**Question that raised it.** What is the one thing to leave in the room?

**Findings.** The instruction, restated as a full stop: rank the ground, not the fire — and trust the order, not the number. The first line is the title slide verbatim, so the deck opens on the instruction and closes on it with the boundary added.

*Notes to self:* this is the one place in the deck where reading the slide aloud is correct — elsewhere it's duplication, here the repetition *is* the delivery. Say the two sentences and stop; the silence after them is the point. The small line is context, not a third claim — don't read it; it's there so the sentence stays available while questions start. Slide 17 carries the three products, this carries the instruction: if a question arrives about what to actually do, go back one slide.

*Deck note:* the current PPTX slide 18 shows "Rank the ground, not the fire." plus the small line, but not the second bookend line "Trust the order, not the number" that the script specifies. Add it or accept that the boundary is spoken only.
