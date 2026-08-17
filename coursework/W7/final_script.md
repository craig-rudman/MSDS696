# MSDS 696 — Final Talk Script

**Authoritative text for the W7 dry run and the W8 final.** Where this file and `coursework/W7/MSDS696_W7_Deck.pptx` disagree, this file wins and the deck is corrected to match. It supersedes `src/build_deck.py`'s `BEATS` list and the storyboard table in the W6 status report as the source of headline and note text.

Eighteen slides, numbered 0–17 in delivery order, matching the deck. The final is fifteen minutes with five for questions; the W7 dry run targets about ten minutes of talking, which is **~30 seconds per slide**.

**Be declarative. The headline has already made the claim** — a SAY block that opens by asking whether the claim is true ("So can you forecast that mix?") re-opens a question the slide has settled, and spends words doing it. Open on the substance instead. The same applies to deictics: the figures are captioned, so "the national average" points at its own tile and "notice the middle tile" is both redundant and a chance to point at the wrong one.

Each slide below carries four blocks:

- **SAY** — delivery prose, spoken more or less as written. Present only where it has been written; the rest are marked *(none yet)*.
- **EVIDENCE** — the numbers and what the figure shows.
- **WATCH** — traps, caveats and framing obligations, placed behind the slide where they would be sprung.
- **TIME** — the budget for this slide.

### The five terms these notes keep using

Written out because notes are read under pressure, and a compressed line like "held-out Spearman +0.53" is one more thing to decode at the moment you can least afford it. **None of these words go in a SAY block** — they are for answering questions, not for the talk.

| shorthand | what it means | how to say it aloud |
|---|---|---|
| **held-out** | Scored on years the model never saw: trained on 1992–2009, graded on 2010–2020. The guard against grading your own homework. | "on years the model had never seen" |
| **Spearman** | A rank correlation, −1 to +1. Asks *did the cells I ranked high turn out high* — ordering only, not counts. The right measure here because the product is a ranked list. | "how well the ranking held up" |
| **TVD** (total variation distance) | For a **mix**: how much of the composition sat on the wrong cause. 0 = perfect, 1 = entirely wrong. Slides 3–5 plot `1 − TVD`, so higher is better. | "how much of the mix landed on the right cause" |
| **top-1** | Did the single highest-ranked cause turn out to be the actual biggest? A yes/no per cell, so "of the time" is correct — unlike TVD. | "how often it names the right leading cause" |
| **shuffled control** | Take the real predictions and deal them to the wrong cells. Everything is preserved except the pairing, so whatever collapses was doing real work. | "same numbers, wrong places" |

### Name the target whenever it changes

The deck predicts three different things and it is easy to hear them as one. **Every SAY block that changes the target from the slide before it must say so in its first sentence.** The three, and where each runs:

| target | what is being predicted | slides |
|---|---|---|
| **cause mix** | which causes take a region-season's acres | 3, 4, 5, 16 |
| **ignition counts** | how many fires start in a cell | 6, 9, 10, 14, 15 |
| **burned acres** | how much a cell burns | 7, 8, 11, 12 |

Read down the deck, the target goes: **cause · cause · cause — starts — acres · acres — starts · starts — acres · acres — starts · starts — cause.** It alternates in blocks, and every boundary is a place a listener can carry the wrong quantity forward.

**The dangerous one is 6 → 7**, because nothing else changes: same hexes, same left-to-right ordering, same figure family. Only the quantity flips. Slide 7 opens with "that was where fires start; the other half is how much they burn" for exactly that reason, and that clause is protected in its WATCH.

**8 → 9 flips back to starts** and is the next most likely to be missed, since slide 9 also plots a skill measure and could be heard as continuing slide 8's error story. **12 → 13** is safe (13 plots no data and is explicitly about method), and **13 → 14** is announced by the headline.

**Headlines have to name the quantity too, not just the SAY.** Slide 8's read "Up to a point, both are predictable" — where *both* could mean starts-vs-acres and *predictable* could mean starts, so a listener two slides into an acres run had two ways to lose the thread from the headline alone. It now names the branches and the quantity: "human and natural burned area." Check any headline using "predictable," "both," or "it" against this table before the dry run.

**Two anchors worth carrying.** A Spearman of +0.53 sounds middling until you know the shuffled control scores **+0.0002** — that is what zero looks like in this data. And "SD above a shuffled control" (33, 35, 26.6 in various notes) means *how many standard deviations the real result sits above the spread of the shuffled ones*: past about 3 is convincing, so 26 and up is not a close call.

---

## Slide 0 · Title slide

**On the slide:**

> For pre-season planning:\
> **Stop targeting how big fires get.**\
> **Target where they start.**
>
> Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation\
> Craig Rudman · MSDS 696 Practicum II · Week 7

**SAY**

> This is for a state or regional fire planner deciding, before the season starts, where to concentrate a fixed prevention and mitigation budget.
>
> It comes out of the federal record of U.S. wildfire occurrence — two point three million fires, 1992 through 2020, each with a date, a location, a size in acres, and a cause. A quarter of those fires have no specific cause recorded — and by acres, nearly a fifth. That turned out to be a finding rather than a nuisance.
>
> The recommendation, up front: **for pre-season planning, stop targeting how big fires get. Target where they start.**

**WATCH**

- **Setup is 20 seconds, not a topic.** Three things only — who it is for, what the data is, where it is weak — then the BLUF. Do not narrate the database schema; the grain and the joins belong in questions.
- The missing-cause quarter is stated **here, voluntarily**, because a challenger will find it. Saying it first converts it from an ambush into evidence of rigor, and slide 16 pays it off as a product.
- **Both denominators are said aloud on purpose.** Exact figures: **566,210 of 2,271,343 fires = 24.9% by count**, but **33.2M of 179.4M acres = 18.5% by acres** — the missing fires are smaller than average. Slide 16's headline says "nearly a fifth of burned acres" and Tier 1's Unknown class is 18.5%; without the acres half of this sentence, an attentive listener hears slide 0 and slide 16 contradict each other. They do not — they are two correct numbers on different denominators.
- A TARGETING claim, not an efficacy one. Nothing in this project measures what a treatment achieves; the ranking says where fire is most likely to arrive, which is a necessary condition for sited work to pay off and not a sufficient one.
- The deck closes on this same sentence at slide 17, so first and last statements match.
- **"Pre-season" is the scope of every null in this deck and it is load-bearing.** Same-day conditions — wind, timing, suppression availability — were never tested. Never let the claim widen to "the largest fires are unpredictable": that is a much bigger statement than anything measured here.
- Both halves are **instructions, not predictions**, which is why the opening needs no defense. The predictability claims arrive later, each with its own population.

**TIME —** 0:45

---

## Slide 1 — Wildfires are seasonal.

*Figure:* `img/w6_seasonality.png`

**SAY**

> Fire runs on a calendar, and the two peaks are months apart. The dashed line is when fires start, the solid one is how much burns. Spring and summer start about the same number of fires — summer burns almost four times the area.
>
> Fire management works on a seasonal horizon — there's a national outlook issued every month, four months ahead, to support long-range decisions about staffing and allocation. Prevention and mitigation are sited work decided months ahead. Planners need to decide what to target, and where, before the season starts.

**EVIDENCE**

- Most fires start in spring; most acres burn in summer.
- MAM and JJA start nearly the same number of fires and differ 3.9x in acres.
- The dashed curve is starts, the solid filled curve is acres. The narrow spike in early July is Independence Day.

**WATCH**

- No axes and no magnitudes on this one — it is a calendar, not a chart.
- **The offset is the point, not the seasonality.** "Fire is seasonal" is not news to this audience. That starts and acres peak in *different months* is what says a count of ignitions is not a measure of consequence — which is the distinction slides 14 and 15 land on.
- **Do not assert what agencies currently do.** What is cited is that a *product exists* with a *stated purpose*, not what anyone does with it. Sources: **NICC (2023), Predictive Services, Ch. 60 of the National Interagency Mobilization Guide** — the National Significant Wildland Fire Potential Outlook is issued monthly, covers four months, and the chapter states it "provides fire managers with the information needed to make long-range decisions concerning resource staffing and allocation"; and **NICC (2026)**, a live issue, whose Outlook Objectives state it is "intended as a decision support tool" for "proactive decisions."
- **Three things the sources do NOT support, and all three are easy to drift into:** that the outlook "positions crews and equipment" (the text says decisions *concerning* staffing and allocation, not that resources move); that this is a **suppression** practice (Ch. 60 scopes Predictive Services to "operational management of and strategic planning for" fire management resources, broader than suppression); and anything about what coordinators think or prioritize. Say "fire management already works on a seasonal horizon," never "suppression coordinators think seasonally."
- If asked about the July spike: it is Independence Day. **July 4 is the single highest-start day in the record — 16,907 starts, 2.71x the median day — and July 5 is second at 15,141.** Verified from `fires_clean.parquet`. It is a good answer to "does human cause really show up in the data," but do not build on it: no analysis in this deck rests on it.

**TIME —** 0:35

---

## Slide 2 — Cause is regional, not national.

*Figure:* `img/w6_cause_map.png`

**SAY**

> The unit here isn't a state. Fire follows terrain, vegetation and climate, not county lines — so every fire is placed into an EPA Level III ecoregion, drawn from exactly those things. A hundred and five cover the country.
>
> Shade each by how much of its burned area is lightning-caused, and the map splits at about the hundredth meridian: natural in the West, human in the East, Alaska almost entirely natural. And it's not a gradient — fifty regions sit below twenty percent natural, twenty-eight above eighty, only twenty-seven in between.
>
> So there's no national answer to what starts fires. There are regional ones.

**EVIDENCE**

- All 105 Level III ecoregions, shaded by natural share of attributed acres.
- A West/East split at roughly the 100th meridian; Alaska almost entirely natural.
- Bimodal: 50 regions below 20% natural, 28 above 80%, only 27 in between.

**WATCH**

- **The ecoregion choice is a design decision, not a tested result.** No state-boundary version was built and compared, so do not say ecoregions "work better than states." Say the unit was chosen because it is delineated from terrain, vegetation, soils and climate — the things that govern how fire behaves — where a state boundary is administrative. Omernik & Griffith (2014) is the framework; Stephens et al. (2026) models fire at Level III grain.
- **This is the only slide that explains the unit,** and slides 3–5 all run on it. If it gets cut for time, the ecoregion grain arrives unexplained.
- Bimodality is the load-bearing part, not the West/East split. A gradient would mean every region needs its own blended strategy; two modes mean most regions have a dominant cause and a planner can act on it.
- Shares of **attributed** acres — the missing-cause mass named on the title slide is excluded from this shading. Slide 16 comes back for it.

**TIME —** 0:40

---

## Slide 3 — A region's cause mix is stable enough to forecast.

*Figure:* `img/w6_tier1_tiles.png`

**SAY**

> The mix is three classes splitting a region-season's burned acres — **natural**, **human**, and **unknown**, the ones whose cause was never determined. By acres, nationally: fifty-nine, twenty-three, eighteen. **Everything in this deck is weighted by acres, not by number of fires** — by fire count those first two numbers almost exactly swap.
>
> Three ways to predict that mix, worst to best. The national average mix — forty-two percent of the acres land on the right cause. An even split: fifty-two. That region's own seasonal history — its own past summers, or winters — seventy-three.
>
> Those are averages, and the range under each is the honest part: history runs sixty to ninety across region-seasons, the national average down to twenty. **And we can tell in advance which end a region-season lands on** — a place whose history has been settled forecasts well; one that's been swinging doesn't.
>
> The national average does worse than assuming you know nothing — that's the last slide's map showing up as forecast error.

**EVIDENCE**

- Three tiles, worst to best: national average mix 42%, an even split 52%, the region's own seasonal history 73%.
- Acre-weighted TVD 0.580 / 0.485 / 0.266, forward-chained on 2010+, 3,949 held-out region-seasons.
- Tier-1 classes and their full-record acre shares: **Natural 58.9%, Human 22.7%, Unknown 18.5%**, on a total-acres denominator (resolved + missing) so the three sum to 1.

**WATCH**

- Do NOT say "right 73% of the time." 73% is an error magnitude (1 - TVD), not a hit rate — there is no "of the time" to attach it to.
- 72.7% top-1 agreement is a different number that DOES mean "of the time." Only use that phrasing if the slide on screen shows top-1.
- **Confirmed: these tiles plot 1 − TVD, an error magnitude. Slides 4 and 5 use the same three-tile visual but plot top-1 hit rates.** Same look, different quantity — so "of the time" is wrong here and right there. If asked to compare the 73% with slide 4's 54%, say they are not on the same scale.
- **"Seasonal history" means each season is its own series.** The grouping is `(region, season)`, so Klamath summer sees only prior Klamath summers — and **k=7 is seven prior *same-season* occurrences, about seven years back, not seven consecutive seasons.** Say "its own past summers" if the room looks unsure. If challenged "why not pool all four seasons?": slide 1 is the answer — seasonality is the strongest signal in the record, so pooling would average a region's human-dominated winter against its lightning-dominated summer and predict neither.
- Consequence worth knowing: with k=7 the first seven same-season years of every series are unpredictable, which together with the 2010 split is why the held-out population is 3,949 cells rather than all 10,135.
- **The span under each tile is a spread across region-seasons, NOT a confidence interval.** Say "typical range" or "where individual region-seasons land," never "plus or minus" or "we're 50% confident." Acre-weighted p25–p75, matching the headline's weighting: history **58–91%**, national **21–61%**, even split **36–67%**.
- **The national tile's low end is the argument.** Its 42% is not a middling result evenly spread — the first quartile reaches down to 21%. That is slide 2's bimodality returning as forecast error: a national average describes almost no individual region.
- **If asked "so which ones land at the bottom?"** — that is answered, and it is the strongest unpublished result in the project. A cell's own **pre-season** history dispersion predicts its error: Spearman **+0.484** here and **+0.577** on the human branch, **33 and 35 SD** above a shuffled control, holding *within* individual regions (74/93 and 80/92 series positive). By quartile of pre-season dispersion, accuracy runs **83% → 62%** on Tier 1 and **73% → 39%** on Human. `06_analysis.ipynb`, final section.
- **State its limit in the same breath: it ranks confidence, it does not calibrate it.** "This cell is in the steadiest quartile, which historically scored 83%" — never "83% likely to be right." And 36 of 986 steadiest-quartile cells still scored below 25%, several at dispersion exactly 0.000: a settled history can precede a regime break.
- **Unknown is a predicted class, not a discard.** It holds the missing-cause acre mass, and its share is a regional attribution-quality signal — which is what makes slide 16 a product rather than an apology. Do not describe the model as predicting "two causes plus leftovers."
- **The comparison carries the weight, not any one tile:** the national mix (42%, left) is worse than the even split (52%, middle) — using the national average is worse than assuming you know nothing, which is slide 2 reappearing as forecast error. Do not say "the middle tile" for this point; the middle tile is the even split, and the claim is about the left one losing to it.
- The 18.5% here and the "nearly a fifth" on the title slide are the same number — the acres denominator. Keep them consistent.
- **The single most confusable pair of numbers in the deck.** Tier-1 shares by acres are Human 22.7 / Natural 58.8 / Unknown 18.5; **by fire count they are Human 60.7 / Natural 14.4 / Unknown 24.9** — Human and Natural almost exactly swap. Both are true. Verified from `fires_clean.parquet`. Every target and every score in this project is **acres** (`panel.tier1_composition()` divides `human_ac`/`natural_ac`/`unknown_ac` by `total_ac`; fire counts appear only under `with_counts=True`, and only as model *features*, never as a target). Name the denominator whenever these numbers are said aloud.
- If challenged "isn't most fire human-caused?" — yes, by count, 61%. Humans start most fires; lightning burns most acres. The deck is about acres because acres are what a mitigation budget is sized against.

**TIME —** 0:55

---

## Slide 4 — For human-cause wildfires, history names the lead cause more often than not.

*Figure:* `img/w6_human_tiles.png`

**SAY**

> "Mostly human" doesn't tell a planner what to do, so open that slice up: eleven specific causes — arson, equipment, debris burning, recreation, powerlines, and so on. The goal is to rank them per region and season, by the acres each one drives.
>
> And that ranking isn't the obvious one. Debris burning starts the most fires of any human cause; it's only third in acres. Equipment starts a third as many and burns more. **What's worth preventing isn't what starts most often.**
>
> Same three predictors, one level down. An even guess across eleven names the top cause by acres nine percent of the time; the national human mix, sixteen; that region's own seasonal history — fifty-four.
>
> Same split, wider: settled past, sixty-eight percent. Swinging past, forty-three.

**EVIDENCE**

- Same three tiles as slide 3, one level deeper: how often the predicted leading human sub-cause is right out of 11.
- An even split 9%, the national human mix 16%, the region's own seasonal history 54%.
- Split by the cell's own **pre-season** dispersion: **68.2% top-1 in the steadiest quartile against 43.5% in the most volatile**, on 3,844 held-out cells. Acre-weighted, same window and grouping as the prediction.
- Acre-weighted TVD 0.489 against the national mix's 0.643; 3,850 held-out region-seasons.
- The 11 sub-causes by national acre share: **arson 26.5%, equipment and vehicle use 24.4%, debris and open burning 19.2%**, recreation and ceremony 11.4%, power generation/transmission 8.6%, railroads 2.3%, smoking 2.3%, firearms and explosives 1.6%, fireworks 1.3%, misuse of fire by a minor 1.2%, other 1.1%. 40.6M human acres.
- **Counts rank differently from acres:** debris burning starts 535,832 fires (the most of any human cause) but is third in acres; equipment starts 190,253 — about a third as many — and burns more. Verified from `fires_clean.parquet`.

**WATCH**

- 54% is the Human floor on Human's own population. Do NOT quote it as an end-to-end number — end to end is 46.2%.
- **Why this tile shows a split and slide 3 shows a span.** Slide 3's metric is `1 − TVD`, continuous per cell, so quartiles are meaningful. Top-1 is **0/1 per cell** — its quartiles are 0 and 1 and an interval would say nothing. The stated split is the honest equivalent: the hit rate at each end of the signal that predicts it. Do not describe it as a confidence interval.
- The confidence spread is **wider on this branch than on Tier 1** (25 points against 21 on the same metric family), which matters because this is the weaker product. Its failures are anticipated, not random.
- **These tiles are a hit rate — "of the time" is correct here.** Slide 3's identical-looking tiles are 1 − TVD, an error magnitude, where it is not. Never compare the 54% here with slide 3's 73%; they are not on the same scale.
- **This is the tier change, and it needs saying:** slide 3 predicted the three-class split, this predicts *within* the human class only. The denominator is human acres, not all acres.
- Do not list all eleven aloud — name four or five and move. The full list is above for questions.
- The counts-vs-acres inversion is the argument for ranking by acres rather than by ignition count. It is also the one place in the deck where a planner's intuition is most likely to be wrong, so it is worth the five seconds.
- **This slide is the deck's only place where fire *counts* are quoted as a ranking, and that is deliberate** — it exists to justify ranking by acres. Say "by acres" on the 9/16/54 line immediately after, because the audience has just heard "starts the most fires" and could carry the count sense forward. `panel.human_subcause_shares()` sums `acres` on a human-acres denominator; counts are never a target.
- **The denominators differ between the two tiers, by design.** Tier 1 divides by *total* acres including the Unknown mass; Human divides by *human* acres only and excludes Unknown entirely. Correct — Unknown is a Tier-1 class, not a human sub-cause — but a challenger with a modeling background will probe it.

**TIME —** 0:45

---

## Slide 5 — A learned model made naming the leading cause worse.

*Figure:* `img/w6_human_ladder.png`

**SAY**

> A trailing mean is a low bar, so it's worth testing against something that learns. Gradient boosting, first on what kind of place the region is — thirty-six percent, well short of the history. Then the same model handed that history as a feature — the exact numbers the winning bar averages — forty-seven. A second kind of model, given that same history, gets to fifty-two.
>
> The dashed line is the bar at the top, and it's the same fifty-four percent from the last slide. **Two families, and neither one beat taking the average of the thing we handed it.**

**EVIDENCE**

- Four rungs against the floor line: the region's own seasonal history names the leading human cause 54% of the time; ridge given that history 52%; gradient boosting given that history 47%; gradient boosting on region character 36%.
- Bars read top to bottom, best to worst: 54%, 52%, 47%, 36%. The dashed vertical is the 54% floor.
- The top bar is slide 4's winning tile, replotted — not a new measurement.
- Acre-weighted TVD, same order: 0.489 / 0.537 / 0.554 / 0.588. 3,846 held-out cells.
- **Ridge beats gradient boosting by 4.7 points of top-1.** Everything else about the two rungs is identical — features, split, acre weights, held-out cells, simplex projection — so the gap is the learner alone.
- Even handed the winning quantity, neither family beats taking its mean.

**WATCH**

- **The family question is answered: a second learner was run and also lost.** `08_human_cause.ipynb`, final section: ridge per sub-cause, same features, split, acre weights, held-out cells and simplex projection, only the learner changed. **Ridge with history scores 52.2% top-1 against gradient boosting's 47.5% — better — and still under the floor's 54.1%** (TVD 0.537 vs the floor's 0.489). So the booster *was* paying a variance cost on a small wide panel, and fixing that recovers five points and does not reach the trailing mean.
- **The strongest anti-tuning evidence is the flat `alpha` sweep.** Across four orders of magnitude (0.1 → 1000) ridge's top-1 is **identical to six decimal places** and TVD moves in the fifth. A regularization sweep that changes nothing is what an information ceiling looks like, not what an under-tuned model looks like. Use this if someone presses "did you tune it?"
- **Ridge is not just rediscovering the floor** — it sits 0.283 TVD units away per cell and names a different top cause in a quarter of them (75.2% argmax agreement). Two different learners arriving near the same score by different routes is stronger evidence than either alone.
- **Still concede what remains untested:** a full hyperparameter search over the booster, and any family beyond these two. Say "gradient boosting and ridge both lost," never "machine learning doesn't work here." *Settings on the plotted rungs:* `SimplexRegressor()` bare — `HistGradientBoostingRegressor`, `max_iter=300`, `learning_rate=0.05`, `max_leaf_nodes=31`, `random_state=0`.
- **The figure shows four bars; the ladder has five rungs.** Ridge on the coarse fingerprints scores 35.67%, indistinguishable from the gradient-boosting coarse bar's 35.66%, so it is not plotted. Notebook 08 has the full table. Do not imply the figure is the whole ladder.
- **What the result does rule out is "you never gave it the right features."** The history-aware rung was handed the 11 trailing human-mix columns — the exact quantity the floor averages — so the floor is a function it could represent by ignoring its other features. It is **6.5 TVD points and 6.6 top-1 points short of a quantity it was given.** That gap is an order of magnitude past what tuning moves, which is the answer to "isn't this just a hyperparameter problem?"
- **The top bar reads "the region's own seasonal history," the same words as slide 4's winning tile** — one baseline, one name, one 54%. If the room hears them as two different things, say "the same baseline as the last slide."
- **The two "given that history" rungs are the whole argument and they are easy to skip.** Losing to history is unremarkable; losing *while holding history* is the finding — twice, with two different learners. If only one sentence survives a time cut, keep that one.
- **Do not name ridge aloud unless asked.** The SAY says "a second kind of model" because the bar is labelled and the audience is executives; the word buys nothing spoken and costs a beat. The label is there for anyone who wants it.
- Do not say "the model failed." The best learned rung scored 52% out of 11 classes — far above the 9% even guess on slide 4. It lost to a cheaper thing, which is a different claim and the one the ablation ladder is built to make.
- Keep this slide — it is the only one conceding a model was tried and lost, which is what keeps the nulls credible.
- The bars are a **hit rate** — how often the leading cause is named right, out of 11 — so "of the time" is the correct phrasing here, unlike slide 3. The TVDs are in the evidence above but are **not what is plotted**; do not quote them off this figure.

**TIME —** 0:40

---

## Slide 6 — Where fires start is predictable, at the scale where you'd site the work.

*Figure:* `img/w6_siting_glance.png`

**SAY**

> Everything so far has been a whole ecoregion — one number for an area the size of a small state. That is the right scale for deciding what to target, and the wrong one for deciding where to put anything.
>
> So the question changes — and it isn't a finer-grained version of the last one. The map breaks into cells of about sixty thousand acres, and the target changes with it: not shares of burned area, but counts of ignitions, per cell.
>
> This is one region — the Klamath Mountains, about two hundred cells. Rank them on their own history and the dark band is six percent of the region catching a third of next season's starts. Go wider, to the light band: twenty-nine percent of the ground for sixty percent of the starts.
>
> The return decays from there — chasing ninety percent of the starts takes seventy-eight percent of the ground, which is barely better than treating everywhere. Ranking concentrates the return; it doesn't eliminate the tail.

**EVIDENCE**

- Klamath hexes in two bands: the deep band is 6% of the region catching 32% of next season's starts (5.2x); the light band 29% for 60% (2.1x).
- **How well the ranking holds up on years the model never saw: human ignitions +0.53, natural +0.34.** These are rank correlations (Spearman), scored on 2010–2020 after training on 1992–2009.
  - *What the number is:* a score from −1 to +1 for **whether the hexes ranked high turned out high**. It looks only at the ordering, not the counts — which is the right measure because the product is a ranked list of where to site work, not a promised number of fires per cell.
  - *What counts as good:* the honest anchor is this project's own control, not a textbook band. Dealing the same predictions to the wrong hexes scores **+0.0002**. That is what zero looks like in this data, so +0.53 is a long way from luck.
  - *Why human beats natural:* people ignite in the same places year after year — roads, structures, recreation sites. Lightning is more nearly random across a landscape. Slide 9 is where that gap gets its own slide.

**WATCH**

- The deck's ONE grain change, and three things change at once: unit (105 ecoregions -> 36,234 hexes), target (acres -> ignition counts), answer (shares -> counts). The headline announces only the first; say the others.
- **This is a distinct sub-project, not a rescue of slide 5.** Delivered in sequence — a null, then a grain drop — the room will infer that the ecoregion model underperformed so the analysis went looking at a finer grain for a better number. It did not: per `CLAUDE.md` the hex ignition surface is "methodologically distinct," a different target at a different grain answering a different planner question, and the Human product ships at 54% on its own terms. The SAY blocks this with "it isn't a finer-grained version of the last one"; if asked directly, say the two are different questions and neither result depends on the other. Do NOT defend it by re-arguing 54%.
- **The headline asserts a scale, not a comparison — keep it that way.** No ignition model was ever built at ecoregion grain and beaten, so never say or imply the hex grain "scored better." The hex grain is a **design argument** — an ecoregion is too coarse to site work *inside* — exactly the same shape as slide 2's ecoregion choice, and it takes the same honest answer: the unit was chosen to match the decision. If asked why not ecoregions for this, say a planner cannot act on one number for an area the size of a small state; do not imply a head-to-head.
- **The region is "Klamath Mountains/California High North Coast Range"** — verified from `data/hex_grid_res5.parquet`. The SAY shortens it to "the Klamath Mountains," which is fine as a spoken shorthand, but do not name states or add "northern California and southwest Oregon": the Level III unit also covers the California High North Coast Range, and the locator inset shows the full extent.
- This is NOT an acres model. Unsaid, the audience reads the capture curve as "32% of the burn under 6% of the ground" — a much stronger claim than the one being made. It is 32% of the STARTS.
- **The next slide switches back to acres**, on the same hexes and the same ordering. This slide is the deck's only ignition-target slide until slide 14; 7 and 8 are acres. Land "starts" hard here so the contrast is available when slide 7 announces the switch.
- The return decays fast: 90% of starts needs 77.8% of the ground at 1.16x. The ranking concentrates return; it does not eliminate the tail.
- **This slide's claim is defended nowhere else in the deck, so the control lives here.** If challenged that the ranking could be luck, the answer in one sentence is: **the identical predictions dealt to the wrong hexes go flat.** Then the numbers, on 1.59M held-out hex-seasons:
  - **The ranking collapses to nothing: +0.526 → +0.0002.** That second number is the useful one — it is what "no relationship at all" measures as in this data, which is the anchor for judging the +0.53.
  - **The typical miss gets worse: 0.43 → 0.77 fires per cell** (mean absolute error — average size of the gap between predicted and actual, in the units of the thing predicted). The shuffled version is worse than **0.70**, which is what you get predicting the same national average everywhere. Misplaced predictions are worse than no predictions.
  - **Why shuffling rather than random numbers:** it preserves everything — the same values, the same total, the same distribution — and breaks only which cell each one is attached to. So whatever collapses was being done by the placement, and nothing else.
  - **Have `img/w6_shuffled_control.png` ready to pull up.** Predicted starts along the bottom, what actually happened up the side, twenty groups of cells. The forecast line climbs; the shuffled line is **flat at about 0.4** — the all-hex average — not low. Flat is the tell: it means the prediction carries no information about which cell is which.
- **Say "it ranks well," never "it is accurate."** On that same figure the forecast line runs *below* the diagonal and under-predicts the busiest hexes — top stratum predicted 4.7 against 3.7 observed. The product is an ordering, not a promised count, and slide 17's closing line says the same thing about all three branches.
- Q&A companions: `img/w6_capture_curve.png` (the full decay curve) and `img/w6_shuffled_control.png` (the permutation control).

**TIME —** 0:30

---

## Slide 7 — Almost all the area burned is in almost none of the cells.

*Figure:* `img/w6_acres_concentration.png`

**SAY**

> That was where fires start. The other half is how much they burn — same cells, different target. And before asking how good a size forecast is, it's worth knowing where the acres are.
>
> Every burning cell, ordered least-burned to most. Spread evenly, you'd get the dashed line. Instead it stays flat across almost the whole country and goes vertical at the end: ninety percent of cells hold two percent of the burn; **one percent hold more than half.**
>
> So a forecast is only as good as it is on the right-hand edge. Everywhere else, being right is cheap.

**EVIDENCE**

- Cumulative share of natural acres, cells ordered by acres burned, least to most.
- The worst-burning 10% of cells hold 98% of the acres; the worst-burning 1% hold 55%.
- Both figures are printed on the plot, with the even-spread diagonal labelled — do not read them off aloud, land the shape.

**WATCH**

- **This slide switches the target back to acres, and the switch has to be said aloud.** Slide 6 is ignition *counts*; slides 7 and 8 are *acres*. Same hexes, same left-to-right ordering, different quantity — which is precisely the setup for a listener to carry "starts" forward and hear "1% of cells hold 55% of the starts." The SAY opens with "that was where fires start; the other half is how much they burn" for that reason. **Do not cut that clause for time.**
- This sets the stakes for slide 8 — it names which cells a forecast has to get right BEFORE any error is shown. Matched pair with slide 8; neither survives alone.
- **The last sentence is the whole reason the slide exists.** It converts a distribution into a standard for judging what comes next, and slide 8 opens against that standard. If it gets dropped for time, slide 8's decile chart arrives with nothing to be measured against.
- **"Ninety percent of cells hold two percent" is the same fact as the printed "worst-burning 10% hold 98%"** — stated from the other end because the flat stretch is what the eye is looking at while you say it. Do not say both; they sound like two findings.
- **Natural acres only** — 167,768 burning cells, zero-burn cells excluded (96% of hex-seasons never burn, and including them would make the curve a statement about how rare fire is rather than how it concentrates once it happens).
- **If asked whether human fire concentrates the same way: yes, and the ranking flips depending on where you look — so do not answer "more" or "less."** Measured from `hex_acres_panel.parquet`: human's worst 1% of burning cells hold **71%** of human acres against natural's **55%**, but human's worst 10% hold **93.5%** against natural's **98.2%**. Human is more top-heavy at the very tip, natural more so across the top decile. Both are extreme; neither branch is the concentrated one.
- A concentration claim, not a predictability one. Nothing here says the big cells are *findable* in advance — slide 8 is where that gets answered, and the answer is partly no.
- **"How do you know how much burned in a given cell?" — the 10-second answer, said first:**
  > The record stores a fire as a dot but a size in acres. So where a fire has a mapped perimeter — and that's most of the burned area — we spread its acres across the cells it actually covered, instead of piling them all on the dot.

  Name the problem before the method: "a dot with an acreage attached" is what makes an executive see why it breaks at this scale, and it pre-empts the sharper follow-up (*did you just assign every fire to one cell?*). **Do not lead with "0.6% of fires but 81.6% of acres"** — unexplained it sounds like a coverage gap. It is the right answer to the *second* question.
- **The full version, if pressed — two rules chosen per fire.** A fire linked to an **MTBS perimeter** has its acres split across the hexes the perimeter covers, weighted by intersected area. A **point-only** fire puts all its acres on the hex containing the ignition. Perimeter-linked fires are 0.6% of records but **81.6% of acres**; point-only fires average 14 acres against a 62,494-acre hex, so crediting them whole is accurate. Per-fire weights sum to 1, so the hex panel reconciles exactly to the ecoregion totals — this redistributes acres, it never restates them. `src/hex_burn.py`.
- **Volunteer the limitation if the question goes a second round.** The point rule breaks in the tail: **2,710 point fires exceed 1,000 acres and carry 8.9% of all acres**, each landing entirely on one cell, and 23 rows assign more than a full hex to a single cell. So some of this curve's sharpness at the very tip is the attribution rule rather than fire behavior. The fix — imputing a circular burn from the ignition point and distributing it the same way — is designed and not built. **It does not move the argument:** the claim is about shape across the whole distribution, and slide 8's decile statistics are rank-based, so redistributing a few thousand cells changes neither direction nor conclusion.

**TIME —** 0:35

---

## Slide 8 — Up to a point, human and natural burned area is equally predictable. Past that point, natural is harder.

*Figure:* `img/w6_branch_deciles.png`

**SAY**

> Still acres, not starts — same cells, same ordering, big burns on the right. What's new is how far off the acres forecast was. Human in blue, natural in orange.
>
> Across the left two thirds they track together and they're close. Then they split — and watch the scale, because every gridline is ten times the one below. At the right edge, on the cells that hold the acres, human fire is off by a factor of nineteen. Lightning, by nearly seven hundred.
>
> **So these ship as two different products.** Human burn you can rank by expected acres. Lightning you can't — which means for lightning the answer has to be something other than how much.

**EVIDENCE**

- Typical forecast error against how much a cell burned, both branches on one axis — the same axis and direction as slide 7, so the right edge means "the big burns" on both slides.
- They track through the smallest third, then separate: natural runs 2-3x worse than human at the same cell size, reaching 687x on a median 8,061-acre cell against human's 19x on 240.
- Cells under 1 acre excluded: 25.3% of FPA-FOD rows sit at exactly 0.1 acres (44.5% of natural fires), a reporting default rather than a measurement.
- Populations differ by an order of magnitude: 18,633 natural cells against 149,949 human.

**WATCH**

- **"Predictable" here means the acres forecast, and the headline had to say so.** "Both are predictable" invited two wrong readings at once: *both* could mean starts-vs-acres (the contrast slide 6 just set up) rather than human-vs-natural, and *predictable* could mean starts. The headline now names the branches and the quantity, and the SAY opens "still acres, not starts." This is the third slide in a row on acres, and the one where a listener is most likely to have drifted.
- **Say the y-axis is logarithmic, or the figure understates itself.** Every gridline is 10x the one below, so the visual gap at the right edge — which looks like a moderate separation — is **687x against 19x, a 37-fold difference in error.** This is the one slide where the honest reading is *worse* than the eye's, and the SAY calls out the scale for exactly that reason.
- **The two top-decile numbers are not on the same cells.** Natural's 687x is on a median **8,061-acre** cell; human's 19x is on a median **240-acre** cell. So the headline pair is not like-for-like — natural's worst decile is a far bigger fire. The defensible statement is the one in the SAY's third paragraph plus this: *at matched cell size natural still runs 2–3x worse.* Do not present 687-vs-19 as a controlled comparison.
- Quote the population with the number. Across ALL JJA natural burning cells the top decile is 269.8x on a median 2,970-acre cell; 854.9x is the six-forest-ecoregion population used for the covariate ladder. The like-for-like against Human is 269.8x, not 855x.
- This licenses shipping two DIFFERENT products: Human can be ranked by expected acres, Natural cannot.
- **The closing line is the deck's pivot, not a summary of this slide.** "For lightning the answer has to be something other than how much" is what sends the argument to ignition — slides 14 and 15 — and eventually to the recommendation. Slide 7 set the stakes, this slide fails them, and that failure is the reason the product changes shape.
- **Sub-acre cells are excluded here but kept on slide 7**, and the reason differs by figure: here their *error* is a records artifact (25.3% of rows sit at exactly 0.1 acres, 44.5% of natural fires), while there the quantity is acres, which are real however coarsely recorded. If challenged on inconsistency, that is the answer — the exclusion follows what is being measured.
- Do not say "the model fails on large fires" without "before the season." Same-day conditions were never tested, and that scope caveat is what keeps this from being a much bigger claim than was measured.

**TIME —** 0:45

---

## Slide 9 — Where human fires start is predictable year-round; natural only in summer.

*Figure:* `img/w6_season_skill.png`

**SAY**

> Back to where fires start — and this splits by season. Human in blue, natural in orange, each dot a season, the band showing the spread across eleven separate years.
>
> Human fire is rankable all year. It peaks in spring, but it never drops far. Natural fire is a summer phenomenon — good in July, and by winter it's essentially nothing.
>
> That matters because they call for different work. **Human ignition is a year-round program. Lightning is a seasonal one**, and the season it needs is the one that burns.

**EVIDENCE**

- **How well the ranking held up, season by season** (Spearman, on years the model never saw). Each branch is scored separately in all 11 held-out years; the band spans the observed year-to-year range rather than being an error bar.
- Human runs flat and high (median +0.47 to +0.61, peaking in spring); natural is a summer surface (+0.42 JJA, +0.07 DJF).
- Human beats natural in all 44 season-years without exception.

**WATCH**

- **This slide flips the target back to ignition counts** after two acres slides, and it is the second most missable boundary in the deck — slide 8 also plotted a skill measure, so this can be heard as continuing its error story. It is not: this is how well *starts* were ranked, season by season. The SAY opens "back to where fires start" and the y-axis says so too.
- **The strongest number is not on the figure: human beats natural in all 44 season-years, without a single exception.** 11 held-out years x 4 seasons, and the ranking never once reverses. Use it if challenged that the gap could be noise — the bands overlap slightly in summer, and this is what closes that door.
- **The bands are min-to-max across the 11 held-out years, not confidence intervals.** Say "the spread across eleven years" or "the best and worst year." Never "plus or minus," never "we're confident to within." Human ran 0.32-0.67 across all season-years, natural 0.06-0.46; a shuffled control stayed inside +/-0.014.
- **Do not overclaim winter natural.** Median 0.072 with a best year of 0.180 — that is near-nothing, and "essentially nothing" is the honest phrasing. It is not a weak signal to be improved; it is the season where lightning ignition is rare enough that there is little to rank.
- **The medians, if quoted:** human DJF 0.529, MAM 0.605 (its peak), JJA 0.483, SON 0.469. Natural DJF 0.072, MAM 0.201, JJA 0.422 (its peak), SON 0.190. Human's worst season still beats natural's best.
- **The operational reading is the closing line and it is a real product difference**, not a rhetorical flourish: a year-round program versus a seasonal one. It is also the one place in the deck where seasonality returns as an *implementation* question rather than as a data pattern, which is what makes slide 1 pay off.
- The deck's only figure showing a distribution rather than a point estimate.

**TIME —** 0:35

---

## Slide 10 — We tried to fix that with drought and fuel, but where fires start is a property of the place, not of the year.

*Figure:* `img/w6_ignition_ladder.png`

**SAY**

> Raw: do greener hexes have more fires than browner hexes? Yes, moderately. Within-hex: when a hex is greener than its own normal, does it have more fires than its own normal? Barely. The first question is answered by which hex you are looking at; the second by which year it is — and a forecast needs the second.

**EVIDENCE**

- Two flat lines, one per branch, across the rungs: the region's own history, + drought, + fuel load, + both. Nothing moves.
- Best gain on either branch is +0.0045; the y-axis runs from zero so a real effect would have been visible.
- Both branches on the same 29,293 held-out cells (JJA, the six forest ecoregions).
- The measured reason, spoken not drawn: pdsi -0.137 -> -0.073 and NDVI +0.228 -> +0.098 from raw to within-hex anomaly.

**WATCH**

- Frame as a REPAIR ATTEMPT, not a new topic — slide 8 leaves a failure on the table and slides 10-12 are what was done about it.
- Resist "fires happen where the fuel is" — fuel state added +0.004. The correct compression is "fires happen where fires have happened."
- Q&A companion: img/w6_ndvi_variance.png, the place-vs-year split at 2.8x.

**TIME —** 0:30

---

## Slide 11 — The same data does predict how much burns.

*Figure:* `img/w6_acres_ladder.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Deliberately the same figure as slide 10: same rungs, same axis, same zero-based scale, one line instead of two. The shape is the argument.
- Climate + NDVI together +0.049, 26.6 SD above a covariate-shuffled control, holding across five forward-chaining split years (+0.012 to +0.066).
- Neither half works alone — drought alone -0.008, fuel alone +0.001. Wet heavy fuel will not carry fire; dry bare ground has nothing to burn.

**WATCH**

- Different target and population from slide 10 (7,799 burning JJA cells, burn-conditional baseline) — comparable in SHAPE, not cell for cell.

**TIME —** 0:30

---

## Slide 12 — But the gain misses where we need it most.

*Figure:* `img/w6_gain_landing.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Slide 8's axis again, with the covariate model laid over the baseline.
- The shaded lens opens in deciles 6-9 (1-200 acre cells) and closes at the right edge where the two lines finish together: 855x -> 868x on a median 5,073-acre cell.
- Deciles 1-5 get materially worse — decile 1 nearly doubles, 18.8x -> 35.9x. 780 held-out cells per decile.

**WATCH**

- Slide 7 is what makes this fatal rather than disappointing: the improvement misses the cells holding 98% of the acres.
- Third slide landing the eye on the same right edge — the argument for reframing rather than tuning.

**TIME —** 0:30

---

## Slide 13 — Predicting where fires start needed a finer spatial scale. Predicting size may need a shorter time scale.

*Figure:* `img/w6_grain_parallel.png`

**SAY**

> Remember what we did to make siting work: the region was too coarse to put anything anywhere, so we dropped down to a hex. This is the same problem on the other axis. We asked how big a fire gets over a whole season, and a season is too coarse a unit to answer that — what makes a fire run is the wind on a particular afternoon, whether crews were already committed, what time of day it started. We could not test that here, because same-day data is a different project. But the shape of the failure tells you where to look.

**EVIDENCE**

- The deck's only figure that plots no data, and its only one about the method rather than the fire. The solved row is closed, the untested row dashed.
- The fourth time the project has met the same lesson: W4's pooled climate null, slide 10's places-not-years, slide 6's grain drop, now this.

**WATCH**

- Say "before the season" whenever the claim is stated as a null. "Megafire size is unpredictable" is a much bigger claim than anything measured here.
- Do not apologise for the null. Five ablations, a shuffled control at 26.6 SD, and a gain that landed in the wrong deciles is a thorough negative result.
- If asked "did you try hard enough?" — pre-season data was tried hard, same-day data was not tried at all. The second half is the open question, not a gap.
- If the room needs "stop targeting it" said aloud, say it as the last sentence rather than the headline.

**TIME —** 0:30

---

## Slide 14 — Most starts don’t become big fires.  But big fires usually burn in the hex where they started.

> [!WARNING] **This headline may restate an artifact as a finding.** "Big fires usually burn in the hex where they started" is a spatial-containment claim, and per `CLAUDE.md` a point-only fire is assigned entirely to its ignition hex **by construction** — 2,710 point fires exceed 1,000 acres, and 23 assign more than a full hex to one cell. The figure below it measures the ignition *gate* (6.7% vs 0.29%, 22.8x), not containment. The earlier headline, "Every megafire was an ignition first," says what the figure shows. Decide before the dry run.

*Figure:* `img/w6_ignition_gate.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- Two bars in a common frame, no axis: a hex-season that ignites at all produces a >=1,000-acre burn 6.7% of the time against 0.29% for one that does not — a 22.8x gate.
- JJA natural, held-out years. Percentages printed because at true scale the 0.29% bar is nearly invisible — which is itself the finding.

**WATCH**

- Do not oversell the gate: it is necessary, not sufficient. 93% of igniting hex-seasons still produce nothing large. It narrows the field; it does not identify the fire.
- This is the door slide 13 left open — size is not forecastable, but the event upstream of it is.

**TIME —** 0:30

---

## Slide 15 — One ignition is enough.

*Figure:* `img/w6_one_is_enough.png`

**SAY**

> *(none yet)*

**EVIDENCE**

- One stacked bar over all 2,724 large-fire cells in the held-out years, split by how many times their hex ignited that season: 49% had exactly one, 21% two, 30% three or more.
- Only the first segment carries color — it is the ground a planner would deprioritise by ranking on ignition count.

**WATCH**

- The rule is binary: does this place ignite, not how often.
- If asked "doesn't a cell with more ignitions carry more risk?" — the rate does rise (19.1% at 11-20 ignitions vs 5.4% at one), but risk PER ignition falls 0.054 -> 0.014, and 49% of large-fire cells had exactly one ignition.
- Ignition count ranks burned area **worse** than the hex's own burn history does — +0.253 against +0.357 on the same ranking measure. Counting starts is a poorer guide to where acres will burn than knowing what has burned there before.

**TIME —** 0:30

---

## Slide 16 — Nearly a fifth of burned acres have no specific cause — and that gap is itself forecastable.

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

## Slide 17 — Target causes by region. Site the pre-season work by ignition. Fix the record where it says neither.

*Figure:* `img/w6_recommendation.png`

**SAY**

> Stop targeting how big fires get. Target where they start.

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

Summed from the per-slide **TIME** lines. Re-derive it from those rather than editing this table by hand — the total has drifted from it twice already.

| slide | budget | why it is over 0:30 |
|---|---|---|
| 0 — title | 0:45 | the deck's only setup: stakeholder, data source, missing-cause caveat |
| 1 — seasonality | 0:35 | carries the seasonal-horizon citation |
| 2 — the cause map | 0:40 | the only slide that explains the ecoregion unit |
| 3 — Tier-1 tiles | 0:55 | names the three classes, the acres denominator, and the spread |
| 4 — human tiles | 0:45 | the tier change, the 11 causes, and the counts-vs-acres inversion |
| 5 — the ladder | 0:40 | four rungs and two model families |
| 7 — acres concentration | 0:35 | sets the standard slide 8 is judged against |
| 8 — branch deciles | 0:45 | the pivot: needs the log-scale warning to not undersell itself |
| 9 — season skill | 0:35 | two branches x four seasons, and the program split |
| 6, 10–17 | 0:30 each | 9 slides at the standard budget |
| **Total** | **10:45** | against a ~10:00 target |

Nine slides carry more than an even share, and each is the only place its content appears. The other nine get **30 seconds**, which is why every one of them has to open on its assertion rather than a wind-up.

**Currently 45 seconds long.** Re-time after the first full run — measured pace beats estimated pace, and the trim comes out of whatever actually ran long rather than out of whatever looks longest on the page.

**Next compression candidate: slides 11–12** (a matched pair that can compress to one). Slides **7 and 8** are also a matched pair, but neither survives alone — cut both or neither.

**Word budget.** At a measured 150 wpm, 10 minutes is about **1,500 words** total. Time each SAY block as it is written rather than at the end — a block that reads fast on the page runs 20% longer aloud.
