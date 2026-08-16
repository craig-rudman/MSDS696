# MSDS 696 — Final Talk Script

**Authoritative text for the W7 dry run and the W8 final.** Where this file and
`coursework/W7/MSDS696_W7_Deck.pptx` disagree, this file wins and the deck is
corrected to match. It supersedes `src/build_deck.py`'s `BEATS` list and the
storyboard table in the W6 status report as the source of headline and note text.

Twenty slides. The final is fifteen minutes with five for questions; the W7 dry
run targets about ten minutes of talking, which is **~30 seconds per slide**.

Headings read **`Slide N · Beat K`**. The two numbers diverge from slide 9 on,
because the seasonal-skill beat moved down two places so that beats 10 and 11 —
a matched pair where neither survives alone — sit adjacent and unbroken. **Slide
numbers give position in the deck; beat numbers are stable identities**, which
is what the WATCH cross-references below ("matched pair with 11", "beat 11's
axis again") point at. Do not renumber the beats.

Sections are in delivery order. Beat 9 therefore appears between beats 11 and 12.

Each slide below carries four blocks:

- **SAY** — delivery prose, spoken more or less as written. Present only where it
  has been written; the rest are marked *(none yet)*.
- **EVIDENCE** — the numbers and what the figure shows.
- **WATCH** — traps, caveats and framing obligations, placed behind the slide
  where they would be sprung.
- **TIME** — the budget for this slide.

---

## Slide 0 · Title slide

**On the slide:**

> **The largest fires are unpredictable.**
> **Focus resources where fires start.**
>
> Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation
> Craig Rudman · MSDS 696 Practicum II · Week 6

> [!NOTE]
> **Open on this slide.** The byline still reads **Week 6** — update before the
> W7 recording. And the BLUF here no longer matches the one spoken below or the
> one beat 19 closes on; the deck was built to open and close on the same
> sentence. Decide which sentence is the BLUF and make all three agree.

**SAY**

> Stop targeting how big it gets. Target where it starts.

**WATCH**

- A TARGETING claim, not an efficacy one. Nothing in this project measures what a treatment achieves; the ranking says where fire is most likely to arrive, which is a necessary condition for sited work to pay off and not a sufficient one.
- The deck closes on this same sentence at beat 19, so first and last statements match.

**TIME —** 0:30

---

## Slide 1 · Beat 1 — Wildfires are seasonal.

*Figure:* `img/w6_seasonality.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Most fires start in spring; most acres burn in summer.
- MAM and JJA start nearly the same number of fires and differ 3.9x in acres.

**WATCH**

- No axes and no magnitudes on this one — it is a calendar, not a chart.

**TIME —** 0:30

---

## Slide 2 · Beat 2 — Cause is regional, not national.

*Figure:* `img/w6_cause_map.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- All 105 Level III ecoregions, shaded by natural share of attributed acres.
- A West/East split at roughly the 100th meridian; Alaska almost entirely natural.
- Bimodal: 50 regions below 20% natural, 28 above 80%, only 27 in between.

**TIME —** 0:30

---

## Slide 3 · Beat 3 — A region's cause mix is stable enough to forecast.

*Figure:* `img/w6_tier1_tiles.png`

**SAY**

> About three-quarters of the mix lands on the right cause.

**EVIDENCE**

- Three tiles, worst to best: national average mix 42%, an even split 52%, the region's own history 73%.
- Acre-weighted TVD 0.580 / 0.485 / 0.266, forward-chained on 2010+, 3,949 held-out region-seasons.

**WATCH**

- Do NOT say "right 73% of the time." 73% is an error magnitude (1 - TVD), not a hit rate — there is no "of the time" to attach it to.
- 72.7% top-1 agreement is a different number that DOES mean "of the time." Only use that phrasing if the slide on screen shows top-1.
- The middle tile carries the weight: the national mix at 42% is worse than guessing, which is beat 2 reappearing as forecast error.

**TIME —** 0:30

---

## Slide 4 · Beat 4 — A few years of rolling average is enough.

*Figure:* `img/w6_k_sweep.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Acre-weighted TVD falls 0.331 -> 0.278 from one prior season to three, then flattens.
- Every window from three up sits within 1.4 points of the best.
- Cause composition is a standing property, not a yearly swing.

**WATCH**

- The compression candidate if the talk runs long — it tunes a parameter of beat 3's baseline rather than adding a claim.

**TIME —** 0:30

---

## Slide 5 · Beat 5 — For human-cause wildfires, history names the lead cause more often than not.

*Figure:* `img/w6_human_tiles.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Same three tiles as beat 3, one level deeper: how often the predicted leading human sub-cause is right out of 11.
- An even split 9%, the national human mix 16%, the region's own history 54%.
- Acre-weighted TVD 0.489 against the national mix's 0.643; 3,850 held-out region-seasons.

**WATCH**

- 54% is the Human floor on Human's own population. Do NOT quote it as an end-to-end number — end to end is 46.2%.

**TIME —** 0:30

---

## Slide 6 · Beat 6 — A learned model made it worse.

*Figure:* `img/w6_human_ladder.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Three rungs against the floor line: the region's own history names the leading human cause 54% of the time; gradient boosting on region character 36%; the same model given that history as a feature 47%.
- Acre-weighted TVD 0.489 / 0.588 / 0.554.
- Even handed the winning quantity, the model cannot beat taking its mean.

**WATCH**

- Concede the fair part: the rungs were run once at standard settings and not tuned. What the result rules out is "you never gave it the right features."
- Keep this beat — it is the only one conceding a model was tried and lost, which is what keeps the nulls credible.

**TIME —** 0:30

---

## Slide 7 · Beat 7 — Where fires start is predictable, but not at ecoregion scale.

*Figure:* `img/w6_siting_glance.png`

**SAY**

> Everything so far has been a whole ecoregion — one number for an area the size of a small state. That is the right scale for deciding what to target, and the wrong one for deciding where to put anything. So from here the map breaks into cells of about sixty thousand acres, and the question changes with it: not how much will burn, but where fires start.

**EVIDENCE**

- Klamath hexes in two bands: the deep band is 6% of the region catching 32% of next season's starts (5.2x); the light band 29% for 60% (2.1x).
- Held-out Spearman: Human +0.53, Natural +0.34.

**WATCH**

- The deck's ONE grain change, and three things change at once: unit (105 ecoregions -> 36,234 hexes), target (acres -> ignition counts), answer (shares -> counts). The headline announces only the first; say the others.
- This is NOT an acres model. Unsaid, the audience reads the capture curve as "32% of the burn under 6% of the ground" — a much stronger claim than the one being made. It is 32% of the STARTS.
- The return decays fast: 90% of starts needs 77.8% of the ground at 1.16x. The ranking concentrates return; it does not eliminate the tail.
- Q&A companion: img/w6_capture_curve.png.

**TIME —** 0:30

---

## Slide 8 · Beat 8 — That skill is spatial, not statistical luck.

*Figure:* `img/w6_shuffled_control.png`

**SAY**

> I am not changing how many fires I predict. I am only changing where I say they will be. Same numbers, wrong places — and the prediction stops working.

**EVIDENCE**

- Two lines, forecast and shuffled: mean observed starts against mean predicted for 20 equal-count strata.
- The forecast climbs the diagonal (top stratum predicted 4.7, observed 3.7); the same predictions dealt to the wrong hexes go flat at ~0.4.
- Spearman +0.526 -> +0.0002; MAE 0.43 -> 0.77, worse than the uniform baseline's 0.70. 1.59M held-out hex-seasons.

**WATCH**

- Avoid "the model is accurate" — the line runs below the diagonal and under-predicts the busiest hexes. Say: it ranks well, it does not promise counts.
- The shuffled line is FLAT, not low. It sits at ~0.4, the average across all hexes.
- Why shuffled and not random: shuffling changes exactly one thing (the pairing), so the collapse is attributable to siting alone.

**TIME —** 0:30

---

## Slide 9 · Beat 10 — Almost all the area burned is in almost none of the cells.

*Figure:* `img/w6_acres_concentration.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Cumulative share of natural acres, cells ordered by acres burned, least to most.
- The worst-burning 10% of cells hold 98% of the acres; the worst-burning 1% hold 55%.

**WATCH**

- This sets the stakes for beat 11 — it names which cells a forecast has to get right BEFORE any error is shown. Matched pair with 11; neither survives alone.

**TIME —** 0:30

---

## Slide 10 · Beat 11 — Up to a point, both are predictable. Past that point, natural fire is harder.

*Figure:* `img/w6_branch_deciles.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Typical forecast error against how much a cell burned, both branches on one axis — the same axis and direction as beat 10, so the right edge means "the big burns" on both slides.
- They track through the smallest third, then separate: natural runs 2-3x worse than human at the same cell size, reaching 687x on a median 8,061-acre cell against human's 19x on 240.
- Cells under 1 acre excluded: 25.3% of FPA-FOD rows sit at exactly 0.1 acres (44.5% of natural fires), a reporting default rather than a measurement.

**WATCH**

- Quote the population with the number. Across ALL JJA natural burning cells the top decile is 269.8x on a median 2,970-acre cell; 854.9x is the six-forest-ecoregion population used for the covariate ladder. The like-for-like against Human is 269.8x, not 855x.
- This licenses shipping two DIFFERENT products: Human can be ranked by expected acres, Natural cannot.

**TIME —** 0:30

---

## Slide 11 · Beat 9 — Human fire is predictable year-round; natural fires only in summer.

*Figure:* `img/w6_season_skill.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Held-out Spearman by season, each branch scored separately in all 11 held-out years, band spanning the observed year-to-year range.
- Human runs flat and high (median +0.47 to +0.61, peaking in spring); natural is a summer surface (+0.42 JJA, +0.07 DJF).
- Human beats natural in all 44 season-years without exception.

**WATCH**

- The deck's only figure showing a distribution rather than a point estimate.

**TIME —** 0:30

---

## Slide 12 · Beat 12 — We tried to fix that with drought and fuel, but where fires start is a property of the place, not of the year.

*Figure:* `img/w6_ignition_ladder.png`

**SAY**

> Raw: do greener hexes have more fires than browner hexes? Yes, moderately. Within-hex: when a hex is greener than its own normal, does it have more fires than its own normal? Barely. The first question is answered by which hex you are looking at; the second by which year it is — and a forecast needs the second.

**EVIDENCE**

- Two flat lines, one per branch, across the rungs: the region's own history, + drought, + fuel load, + both. Nothing moves.
- Best gain on either branch is +0.0045; the y-axis runs from zero so a real effect would have been visible.
- Both branches on the same 29,293 held-out cells (JJA, the six forest ecoregions).
- The measured reason, spoken not drawn: pdsi -0.137 -> -0.073 and NDVI +0.228 -> +0.098 from raw to within-hex anomaly.

**WATCH**

- Frame as a REPAIR ATTEMPT, not a new topic — beat 11 leaves a failure on the table and beats 12-14 are what was done about it.
- Resist "fires happen where the fuel is" — fuel state added +0.004. The correct compression is "fires happen where fires have happened."
- Q&A companion: img/w6_ndvi_variance.png, the place-vs-year split at 2.8x.

**TIME —** 0:30

---

## Slide 13 · Beat 13 — The same data does predict how much burns.

*Figure:* `img/w6_acres_ladder.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Deliberately the same figure as beat 12: same rungs, same axis, same zero-based scale, one line instead of two. The shape is the argument.
- Climate + NDVI together +0.049, 26.6 SD above a covariate-shuffled control, holding across five forward-chaining split years (+0.012 to +0.066).
- Neither half works alone — drought alone -0.008, fuel alone +0.001. Wet heavy fuel will not carry fire; dry bare ground has nothing to burn.

**WATCH**

- Different target and population from beat 12 (7,799 burning JJA cells, burn-conditional baseline) — comparable in SHAPE, not cell for cell.

**TIME —** 0:30

---

## Slide 14 · Beat 14 — But the gain misses where we need it most.

*Figure:* `img/w6_gain_landing.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Beat 11's axis again, with the covariate model laid over the baseline.
- The shaded lens opens in deciles 6-9 (1-200 acre cells) and closes at the right edge where the two lines finish together: 855x -> 868x on a median 5,073-acre cell.
- Deciles 1-5 get materially worse — decile 1 nearly doubles, 18.8x -> 35.9x. 780 held-out cells per decile.

**WATCH**

- Beat 10 is what makes this fatal rather than disappointing: the improvement misses the cells holding 98% of the acres.
- Third beat landing the eye on the same right edge — the argument for reframing rather than tuning.

**TIME —** 0:30

---

## Slide 15 · Beat 15 — Predicting where fires start needed a finer spatial scale. Predicting size may need a shorter time scale.

*Figure:* `img/w6_grain_parallel.png`

**SAY**

> Remember what we did to make siting work: the region was too coarse to put anything anywhere, so we dropped down to a hex. This is the same problem on the other axis. We asked how big a fire gets over a whole season, and a season is too coarse a unit to answer that — what makes a fire run is the wind on a particular afternoon, whether crews were already committed, what time of day it started. We could not test that here, because same-day data is a different project. But the shape of the failure tells you where to look.

**EVIDENCE**

- The deck's only figure that plots no data, and its only one about the method rather than the fire. The solved row is closed, the untested row dashed.
- The fourth time the project has met the same lesson: W4's pooled climate null, beat 12's places-not-years, beat 7's grain drop, now this.

**WATCH**

- Say "before the season" whenever the claim is stated as a null. "Megafire size is unpredictable" is a much bigger claim than anything measured here.
- Do not apologise for the null. Five ablations, a shuffled control at 26.6 SD, and a gain that landed in the wrong deciles is a thorough negative result.
- If asked "did you try hard enough?" — pre-season data was tried hard, same-day data was not tried at all. The second half is the open question, not a gap.
- If the room needs "stop targeting it" said aloud, say it as the last sentence rather than the headline.

**TIME —** 0:30

---

## Slide 16 · Beat 16 — Most starts don’t become big fires.  But big fires usually burn in the hex where they started.

> [!WARNING]
> **This headline may restate an artifact as a finding.** "Big fires usually burn
> in the hex where they started" is a spatial-containment claim, and per
> `CLAUDE.md` a point-only fire is assigned entirely to its ignition hex **by
> construction** — 2,710 point fires exceed 1,000 acres, and 23 assign more than
> a full hex to one cell. The figure below it measures the ignition *gate*
> (6.7% vs 0.29%, 22.8x), not containment. The earlier headline, "Every megafire
> was an ignition first," says what the figure shows. Decide before the dry run.

*Figure:* `img/w6_ignition_gate.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Two bars in a common frame, no axis: a hex-season that ignites at all produces a >=1,000-acre burn 6.7% of the time against 0.29% for one that does not — a 22.8x gate.
- JJA natural, held-out years. Percentages printed because at true scale the 0.29% bar is nearly invisible — which is itself the finding.

**WATCH**

- Do not oversell the gate: it is necessary, not sufficient. 93% of igniting hex-seasons still produce nothing large. It narrows the field; it does not identify the fire.
- This is the door beat 15 left open — size is not forecastable, but the event upstream of it is.

**TIME —** 0:30

---

## Slide 17 · Beat 17 — One ignition is enough.

*Figure:* `img/w6_one_is_enough.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- One stacked bar over all 2,724 large-fire cells in the held-out years, split by how many times their hex ignited that season: 49% had exactly one, 21% two, 30% three or more.
- Only the first segment carries color — it is the ground a planner would deprioritise by ranking on ignition count.

**WATCH**

- The rule is binary: does this place ignite, not how often.
- If asked "doesn't a cell with more ignitions carry more risk?" — the rate does rise (19.1% at 11-20 ignitions vs 5.4% at one), but risk PER ignition falls 0.054 -> 0.014, and 49% of large-fire cells had exactly one ignition.
- Ignition count ranks burned area worse than the hex's own burn history does: Spearman +0.253 against +0.357.

**TIME —** 0:30

---

## Slide 18 · Beat 18 — Nearly a fifth of burned acres have no specific cause — and that gap is itself forecastable.

*Figure:* `img/w6_unknown_triage.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- The ranked triage list, headed by Southwestern Tablelands MAM at 1.17M predicted unattributed acres.
- Ranked by acres rather than by rate: Central Great Plains has the worse attribution rate (66%) but a fifth of the burn.
- Unknown-branch persistence: acre-weighted MAE 0.167 against the global mean's 0.240.

**WATCH**

- The third leg of the recommendation, delivered where it is actionable rather than as a finding in its own right.

**TIME —** 0:30

---

## Slide 19 · Beat 19 — Target causes by region. Site the pre-season work by ignition. Fix the record where it says neither.

*Figure:* `img/w6_recommendation.png`

**SAY**

> Stop targeting how big it gets. Target where it starts.

**EVIDENCE**

- Three rows, one per Tier-1 class, ordered by share so the top row is where the acres are: Natural 58.9%, site by ignition, hex-season; Human 22.7%, rank causes by the acres they drive, ecoregion-season; Unknown 18.5%, fix the record underneath, ecoregion-season.
- The boundary, on the line beneath: rank on all three — the order is trustworthy and the acre level much less so.

**WATCH**

- A TARGETING claim, not an efficacy one. Nothing here measures what a treatment achieves — no before/after, no control, no counterfactual.
- If asked "so if we treat those hexes, we cut the burn?" — say no, plainly. Davis et al. (2024) on severity reduction is separate evidence from someone else's study; cite it if asked, do not fold it in.
- If they remember one thing: site the work against where fires start, because that is the one stage of the escalation this data can see in advance.

**TIME —** 0:30

---

## Timing

| | slides | budget |
|---|---|---|
| Title | 1 | 0:30 |
| Beats 1–19 | 19 | 9:30 |
| **Total** | **20** | **10:00** |

Compression candidates, in the order the W6 storyboard nominates them:
**beat 4** (tunes a parameter of beat 3's baseline rather than adding a claim),
then **beats 13–14** (a matched pair that can compress to one).
Beats **10 and 11** are a matched pair and neither survives alone.
