# MSDS 696 — Final Talk Script

**Authoritative text for the W7 dry run and the W8 final.** Where this file and `coursework/W7/MSDS696_W7_Deck.pptx` disagree, this file wins and the deck is corrected to match. It supersedes `src/build_deck.py`'s `BEATS` list and the storyboard table in the W6 status report as the source of headline and note text.

Eighteen slides, numbered 0–17 in delivery order, matching the deck. Slide 17 is a data-sources reference, delivered after the recommendation. The final is fifteen minutes with five for questions; the W7 dry run targets about ten minutes of talking, which is **~30 seconds per slide**.

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
| **cause mix** | which causes take a region-season's acres | 3, 4, 5, 15 |
| **ignition counts** | how many fires start in a cell | 6, 9, 10, 14 |
| **burned acres** | how much a cell burns | 7, 8, 11, 12 |

Read down the deck, the target goes: **cause · cause · cause — starts — acres · acres — starts · starts — acres · acres — starts — cause.** It alternates in blocks, and every boundary is a place a listener can carry the wrong quantity forward.

**The dangerous one is 6 → 7**, because nothing else changes: same hexes, same left-to-right ordering, same figure family. Only the quantity flips. Slide 7 opens with "that was where fires start; the other half is how much they burn" for exactly that reason, and that clause is protected in its WATCH.

**8 → 9 flips back to starts** and is the next most likely to be missed, since slide 9 also plots a skill measure and could be heard as continuing slide 8's error story. **12 → 13** is safe (13 plots no data and is explicitly about method), and **13 → 14** is announced by the SAY's opening.

**Open question, deferred to a sanity check after the dry run: does slide 9 belong next to slide 6?** Slides 6–15 run starts → acres → starts → acres → starts, four flips in nine slides. Three of those flips are load-bearing and cannot be sequenced away: the deck runs a **repair loop** — 6 wins on starts, 7–8 lose on acres, 9–12 are the attempted repair, 13 diagnoses grain, 14–15 return to starts. Slides 9–12 only read as a response to 7–8's failure; grouping all the starts slides together would turn "here is what we did about that" into "here are some things we tried."

The one genuinely movable piece is **slide 9**, which is not part of the repair — it characterizes *when* the ignition surface works, so it sits naturally beside slide 6. Moving it makes 8 → 9 → 10 a continuous acres-failure-then-repair run and drops the deck from four flips to three. Costs nothing structurally. **Not done yet** — revisit with fresh eyes after a measured run, when it will be clearer whether the flips actually cost the audience anything.

**Headlines have to name the quantity too, not just the SAY.** Slide 8's read "Up to a point, both are predictable" — where *both* could mean starts-vs-acres and *predictable* could mean starts, so a listener two slides into an acres run had two ways to lose the thread from the headline alone. It now names the branches and the quantity: "human and natural burned area." Check any headline using "predictable," "both," or "it" against this table before the dry run.

**Two anchors worth carrying.** A Spearman of +0.53 sounds middling until you know the shuffled control scores **+0.0002** — that is what zero looks like in this data. And "SD above a shuffled control" (33, 35, 26.6 in various notes) means *how many standard deviations the real result sits above the spread of the shuffled ones*: past about 3 is convincing, so 26 and up is not a close call.

---

## Slide 0 · Title slide

**On the slide:**

> For pre-season planning:\
> **Rank the ground,**\
> **not the fire.**
>
> Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation\
> Craig Rudman · MSDS 696 Practicum II · Week 7

**SAY**

> This is for a state or regional fire planner deciding, before the season starts, where to concentrate a fixed prevention and mitigation budget.
>
> It comes out of the federal record of U.S. wildfire occurrence — two point three million fires, 1992 through 2020, each with a date, a location, a size, and a cause. A quarter have no cause recorded; by acres, nearly a fifth.
>
> The recommendation, up front: **for pre-season planning, rank the ground — not the fire.** Where fires start is predictable. How big they get, before the season, is not.

**WATCH**

- **Setup is 20 seconds, not a topic.** Three things only — who it is for, what the data is, where it is weak — then the BLUF. Do not narrate the database schema; the grain and the joins belong in questions.
- The missing-cause quarter is stated **here, voluntarily**, because a challenger will find it. Saying it first converts it from an ambush into evidence of rigor, and slide 15 pays it off as a product.
- **Both denominators are said aloud on purpose.** Exact figures: **566,210 of 2,271,343 fires = 24.9% by count**, but **33.2M of 179.4M acres = 18.5% by acres** — the missing fires are smaller than average. Slide 15's headline says "nearly a fifth of burned acres" and Tier 1's Unknown class is 18.5%; without the acres half of this sentence, an attentive listener hears slide 0 and slide 15 contradict each other. They do not — they are two correct numbers on different denominators.
- A TARGETING claim, not an efficacy one. Nothing in this project measures what a treatment achieves; the ranking says where fire is most likely to arrive, which is a necessary condition for sited work to pay off and not a sufficient one. **"Rank the ground" is the honest verb** — it promises an ordering, where "target" edged toward promising an outcome.
- **The title rhymes with slide 16's closing boundary, deliberately.** "Rank the ground, not the fire" and "trust the order, not the number" are the same shape and the same claim: every product is a **ranking**, and rankings are what this data supports. The bookend is that rhyme, not a repeated sentence.
- **"Pre-season" is the scope of every null in this deck and it is load-bearing.** Same-day conditions — wind, timing, suppression availability — were never tested. Never let the claim widen to "the largest fires are unpredictable": that is a much bigger statement than anything measured here.
- **The second sentence is where the deck's whole argument sits**: where fires start is predictable, how big they get is not — with "before the season" carried by the "for pre-season planning" line above it. Both nulls and both wins hang off that split, so it is worth saying slowly.

**TIME —** 0:40

---

## Slide 1 — Wildfires are seasonal.

*Figure:* `img/w6_seasonality.png`

**SAY**

> Fire runs on a calendar, and the two peaks are months apart. The dashed line is when fires start, the solid one is how much burns. Spring and summer start about the same number of fires — summer burns almost four times the area.
>
> Fire management works on a seasonal horizon — there's a national outlook issued monthly, four months ahead, to support long-range decisions about staffing and allocation. Planners have to decide what to target, and where, before the season starts.

**EVIDENCE**

- Most fires start in spring; most acres burn in summer.
- MAM and JJA start nearly the same number of fires and differ 3.9x in acres.
- The dashed curve is starts, the solid filled curve is acres. The narrow spike in early July is Independence Day.

**WATCH**

- No axes and no magnitudes on this one — it is a calendar, not a chart.
- **The offset is the point, not the seasonality.** "Fire is seasonal" is not news to this audience. That starts and acres peak in *different months* is what says a count of ignitions is not a measure of consequence — which is the distinction slide 14 lands on.
- **Do not assert what agencies currently do.** What is cited is that a *product exists* with a *stated purpose*, not what anyone does with it. Sources: **NICC (2023), Predictive Services, Ch. 60 of the National Interagency Mobilization Guide** — the National Significant Wildland Fire Potential Outlook is issued monthly, covers four months, and the chapter states it "provides fire managers with the information needed to make long-range decisions concerning resource staffing and allocation"; and **NICC (2026)**, a live issue, whose Outlook Objectives state it is "intended as a decision support tool" for "proactive decisions."
- **Three things the sources do NOT support, and all three are easy to drift into:** that the outlook "positions crews and equipment" (the text says decisions *concerning* staffing and allocation, not that resources move); that this is a **suppression** practice (Ch. 60 scopes Predictive Services to "operational management of and strategic planning for" fire management resources, broader than suppression); and anything about what coordinators think or prioritize. Say "fire management already works on a seasonal horizon," never "suppression coordinators think seasonally."
- If asked about the July spike: it is Independence Day. **July 4 is the single highest-start day in the record — 16,907 starts, 2.71x the median day — and July 5 is second at 15,141.** Verified from `fires_clean.parquet`. It is a good answer to "does human cause really show up in the data," but do not build on it: no analysis in this deck rests on it.

**TIME —** 0:35

---

## Slide 2 — Cause is regional, not national.

*Figure:* `img/w6_cause_map.png`

**SAY**

> Fire follows terrain, vegetation and climate — so every fire is placed into an EPA Level III ecoregion. A hundred and five cover the country.
>
> Shade each by how much of its burned area is lightning-caused and the map splits at about the hundredth meridian — natural in the West, human in the East.
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
- Shares of **attributed** acres — the missing-cause mass named on the title slide is excluded from this shading. Slide 15 comes back for it.

**TIME —** 0:30

---

## Slide 3 — A region's cause mix is stable enough to forecast.

*Figure:* `img/w6_tier1_tiles.png`

**SAY**

> The mix is three classes splitting a region-season's burned acres — **natural**, **human**, and **unknown**, the ones whose cause was never determined. Nationally: fifty-nine, twenty-three, eighteen. **Everything here is weighted by acres, not fire counts** — by count, the first two nearly swap.
>
> Three ways to predict that mix, worst to best. The national average: forty-two percent of the acres land on the right cause. An even split, fifty-two. The region's own seasonal history — its own past summers, or winters — seventy-three. Ranges shown below.
>
> **We can tell in advance which end a region-season lands on** — a settled history forecasts well, a swinging one doesn't.

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
- **Unknown is a predicted class, not a discard.** It holds the missing-cause acre mass, and its share is a regional attribution-quality signal — which is what makes slide 15 a product rather than an apology. Do not describe the model as predicting "two causes plus leftovers."
- **The comparison carries the weight, not any one tile:** the national mix (42%, left) is worse than the even split (52%, middle) — using the national average is worse than assuming you know nothing, which is slide 2 reappearing as forecast error. Do not say "the middle tile" for this point; the middle tile is the even split, and the claim is about the left one losing to it.
- The 18.5% here and the "nearly a fifth" on the title slide are the same number — the acres denominator. Keep them consistent.
- **The single most confusable pair of numbers in the deck.** Tier-1 shares by acres are Human 22.7 / Natural 58.8 / Unknown 18.5; **by fire count they are Human 60.7 / Natural 14.4 / Unknown 24.9** — Human and Natural almost exactly swap. Both are true. Verified from `fires_clean.parquet`. Every target and every score in this project is **acres** (`panel.tier1_composition()` divides `human_ac`/`natural_ac`/`unknown_ac` by `total_ac`; fire counts appear only under `with_counts=True`, and only as model *features*, never as a target). Name the denominator whenever these numbers are said aloud.
- If challenged "isn't most fire human-caused?" — yes, by count, 61%. Humans start most fires; lightning burns most acres. The deck is about acres because acres are what a mitigation budget is sized against.

**TIME —** 0:45

---

## Slide 4 — For human-cause wildfires, history names the lead cause more often than not.

*Figure:* `img/w6_human_tiles.png`

**SAY**

> Human-caused fires break down to eleven causes: arson, equipment, debris burning, powerlines, and so on. Rank them per region-season by the acres each drives.
>
> And that ranking isn't the obvious one. Debris burning starts the most fires of any human cause and is only third in acres. Equipment starts a third as many and burns more. **What's worth preventing isn't what starts most often.**

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

**TIME —** 0:30

---

## Slide 5 — A learned model made naming the leading cause worse.

*Figure:* `img/w6_human_ladder.png`

**SAY**

> We tried training a few different models on a few different feature sets. **None of them beat the region's own seasonal history** — including the ones we handed that history to.

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

**TIME —** 0:20

---

## Slide 6 — Where fires start is predictable, at the scale where you'd site the work.

*Figure:* `img/w6_siting_glance.png`

**SAY**

> Ecoregion is the right scale for deciding what to target, but the wrong one for deciding where to focus resources. Layer in a hexmap of cells, about sixty thousand acres each, and the target changes with it: not shares of burned area, but counts of ignitions.
>
> One region here — the Klamath Mountains, about two hundred cells. The darker cells show six percent of the ground catches a third of next season's starts; the lighter band, twenty-nine percent for sixty percent of the starts.

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
- **The next slide switches back to acres**, on the same hexes and the same ordering. This slide is the deck's only ignition-target slide until slide 9; 7 and 8 are acres. Land "starts" hard here so the contrast is available when slide 7 announces the switch.
- The return decays fast: 90% of starts needs 77.8% of the ground at 1.16x. The ranking concentrates return; it does not eliminate the tail.
- **This slide's claim is defended nowhere else in the deck, so the control lives here.** If challenged that the ranking could be luck, the answer in one sentence is: **the identical predictions dealt to the wrong hexes go flat.** Then the numbers, on 1.59M held-out hex-seasons:
  - **The ranking collapses to nothing: +0.526 → +0.0002.** That second number is the useful one — it is what "no relationship at all" measures as in this data, which is the anchor for judging the +0.53.
  - **The typical miss gets worse: 0.43 → 0.77 fires per cell** (mean absolute error — average size of the gap between predicted and actual, in the units of the thing predicted). The shuffled version is worse than **0.70**, which is what you get predicting the same national average everywhere. Misplaced predictions are worse than no predictions.
  - **Why shuffling rather than random numbers:** it preserves everything — the same values, the same total, the same distribution — and breaks only which cell each one is attached to. So whatever collapses was being done by the placement, and nothing else.
  - **Have `img/w6_shuffled_control.png` ready to pull up.** Predicted starts along the bottom, what actually happened up the side, twenty groups of cells. The forecast line climbs; the shuffled line is **flat at about 0.4** — the all-hex average — not low. Flat is the tell: it means the prediction carries no information about which cell is which.
- **Say "it ranks well," never "it is accurate."** On that same figure the forecast line runs *below* the diagonal and under-predicts the busiest hexes — top stratum predicted 4.7 against 3.7 observed. The product is an ordering, not a promised count, and slide 16's closing line says the same thing about all three branches.
- Q&A companions: `img/w6_capture_curve.png` (the full decay curve) and `img/w6_shuffled_control.png` (the permutation control).

**TIME —** 0:35

---

## Slide 7 — Almost all the area burned is in almost none of the cells.

*Figure:* `img/w6_acres_concentration.png`

**SAY**

> Now acres instead of starts — same cells. Ninety percent of them hold two percent of the burn; **one percent hold more than half.**
>
> So a forecast only matters at the right-hand edge.

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

**TIME —** 0:20

---

## Slide 8 — Up to a point, human and natural burned area is equally predictable. Past that point, natural is harder.

*Figure:* `img/w6_branch_deciles.png`

**SAY**

> Still on acres burned — same cells, same ordering. Across the left two thirds they track together more or less. Then they split — and watch the scale, because every gridline is ten times the one below. At the right edge, on the cells that hold the acres, human fire is off by a factor of nineteen. Lightning, by nearly seven hundred.
>
> **So these ship as two different products.** Human acres burned you can rank by expected acres. Nature fires you can't — which means for lightning the answer has to be something other than acres.

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
- **The closing line is the deck's pivot, not a summary of this slide.** "For lightning the answer has to be something other than how much" is what sends the argument to ignition — slide 14 — and eventually to the recommendation. Slide 7 set the stakes, this slide fails them, and that failure is the reason the product changes shape.
- **Sub-acre cells are excluded here but kept on slide 7**, and the reason differs by figure: here their *error* is a records artifact (25.3% of rows sit at exactly 0.1 acres, 44.5% of natural fires), while there the quantity is acres, which are real however coarsely recorded. If challenged on inconsistency, that is the answer — the exclusion follows what is being measured.
- Do not say "the model fails on large fires" without "before the season." Same-day conditions were never tested, and that scope caveat is what keeps this from being a much bigger claim than was measured.

**TIME —** 0:40

---

## Slide 9 — Where human fires start is predictable year-round; natural only in summer.

*Figure:* `img/w6_season_skill.png`

**SAY**

> Ranking cells by where fires start splits by season. Human in blue, natural in orange.
>
> Human fire is rankable all year. It peaks in spring, but it never drops far. Natural fire is a summer phenomenon — good in July, and by winter it's essentially nothing.
>
> That matters because they call for different work. **Human ignition is a year-round program. Lightning is a seasonal one**, and its the one that burns the most.

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

**TIME —** 0:30

---

## Slide 10 — We tried to improve that with drought and fuel, but where fires start is a property of the place, not of the year.

*Figure:* `img/w6_ignition_ladder.png`

**SAY**

> I layered in data about drought and fuel density over time. Nothing moved. The axis starts at zero, so a real effect would show, and the best gain here is four thousandths.
>
> Here's why. Greener cells do get more fires than browner ones. But when a cell is greener **than its own normal**, it barely gets more fires than its own normal. These covariates find dry *places* — and where those are, history already knows. **Where fires start is a property of the place, not of the year.**

**EVIDENCE**

- Two flat lines, one per branch, across the rungs: the region's own history, + drought, + fuel load, + both. Nothing moves.
- Best gain on either branch is +0.0045; the y-axis runs from zero so a real effect would have been visible.
- Both branches on the same 29,293 held-out cells (JJA, the six forest ecoregions).
- The measured reason, spoken not drawn: pdsi -0.137 -> -0.073 and NDVI +0.228 -> +0.098 from raw to within-hex anomaly.

**WATCH**

- Frame as a REPAIR ATTEMPT, not a new topic — slide 8 leaves a failure on the table and slides 10-12 are what was done about it. The SAY opens "so we tried to fix it" for that reason; without it this reads as an unrelated experiment rather than as a response.
- **Target flips back to starts here**, after two acres slides. The SAY says "back to starts" in the first sentence. The figure's y-axis is ignition ranking, not acres.
- Resist "fires happen where the fuel is" — fuel state added +0.004. The correct compression is "fires happen where fires have happened."
- **The raw-versus-anomaly contrast is the mechanism and it is the only part worth saying slowly.** The numbers behind it, if asked: drought correlation with ignitions goes **-0.137 raw to -0.073** within-hex; NDVI **+0.228 to +0.098**. Both roughly halve. That is what "identifies places, not years" means numerically — strip out which cell you are looking at and most of the signal goes with it.
- **This is a null and it should be delivered as a result, not an apology.** Five ablations across two branches, a zero-based axis, and a stated mechanism. If asked "did you try hard enough?" — pre-season covariates were tried hard; same-day conditions were not tried at all, and that is slide 13's open question rather than a gap here.
- **Vocabulary note: this figure labels the branch "lightning fire" while slide 8's headline says "natural."** Both are in the deck. If it comes up, they are the same class — natural is the Tier-1 label, lightning is what it is. Prefer "natural" when speaking so it matches slides 3, 7, 8 and 17.
- Q&A companion: img/w6_ndvi_variance.png, the place-vs-year split at 2.8x.

**TIME —** 0:35

---

## Slide 11 — The same data does predict how much burns.

*Figure:* `img/w6_acres_ladder.png`

**SAY**

> Same rungs, same axis, same zero — one line this time, because this is lightning only. And it moves.
>
> Drought alone does nothing. Fuel alone does nothing. Together they give a real gain — a fifth better than history, holding across every way we split the years. Which makes sense: wet heavy fuel won't carry fire, dry bare ground has nothing to burn. **You need both.**
>
> So the data does know something about how much burns. The question is whether it knows it anywhere useful.

**EVIDENCE**

- Deliberately the same figure as slide 10: same rungs, same axis, same zero-based scale, one line instead of two. The shape is the argument.
- Climate + NDVI together +0.049, 26.6 SD above a covariate-shuffled control, holding across five forward-chaining split years (+0.012 to +0.066).
- Neither half works alone — drought alone -0.008, fuel alone +0.001. Wet heavy fuel will not carry fire; dry bare ground has nothing to burn.

**WATCH**

- **Target flips back to acres.** The SAY says "this is lightning only" and the figure draws one line for that reason; slide 10 drew two. If the room is tracking branches rather than quantities, that single line is the visual cue.
- Different target and population from slide 10 (7,799 burning JJA cells, burn-conditional baseline) — comparable in SHAPE, not cell for cell.
- **Never quote the level, only the step.** The figure annotates **+0.049** rather than the level **0.3075** on purpose: the level invites comparison with slide 10's ~0.42–0.48, which is a different population and a different target. If asked "so it's worse than the ignition model?" — those numbers are not on the same scale and the comparison is meaningless. "A fifth better than history alone" is the safe relative statement, and it is within this slide.
- **The conjunction is the finding, not the size of the gain.** Drought alone −0.008, fuel alone +0.001, both together +0.049. A viewer reading left to right will credit "+ both" to the last thing added rather than to the combination, which is why the SAY says "you need both, and only both."
- **This is the deck's one verified covariate win and it must not be oversold**, because slide 12 takes it away. Say "it holds up" — 26.6 SD above a covariate-shuffled control, stable across five split years (+0.012 to +0.066) — and stop. The closing line hands off to slide 12 rather than banking the result.
- **If asked why this worked when slide 10 failed:** different target. Where a fire *starts* is a property of the place, which history already knows. How much *burns* depends on conditions that vary year to year — which is exactly what these covariates measure. That contrast is the reason both slides exist.

**TIME —** 0:35

---

## Slide 12 — But the gain misses where we need it most.

*Figure:* `img/w6_gain_landing.png`

**SAY**

> But look at where it lands. Same axis as before, with the covariate model laid over the baseline.
>
> The blue lens is the gain. It's real, and it's on cells of one to two hundred acres. At the right edge, where almost all the burn is, the two lines finish together.
>
> **We improved the forecast exactly where it doesn't matter.** And on the smallest cells it's actually worse. So a gain that survives every statistical test still doesn't buy a planner anything — which says the problem isn't the features.

**EVIDENCE**

- Slide 8's axis again, with the covariate model laid over the baseline.
- The shaded lens opens in deciles 6-9 (1-200 acre cells) and closes at the right edge where the two lines finish together: 855x -> 868x on a median 5,073-acre cell.
- Deciles 1-5 get materially worse — decile 1 nearly doubles, 18.8x -> 35.9x. 780 held-out cells per decile.

**WATCH**

- Slide 7 is what makes this fatal rather than disappointing: the improvement misses the cells holding 98% of the acres. **Say "the cells holding almost all of the burn" rather than a number** — slide 7 already established it, and re-quoting 98% spends a beat re-proving a settled point.
- Third slide landing the eye on the same right edge — the argument for reframing rather than tuning. This is the payoff of having drawn 7, 8 and 12 on the same axis in the same direction.
- **The left end getting worse is on the figure but not labelled, and it is worth saying.** Deciles 1-5 deteriorate — decile 1 nearly doubles, 18.8x to 35.9x. The pink lens is that damage. It matters because it rules out "well, it helps a bit everywhere": the model trades accuracy on small cells for accuracy on medium ones and buys nothing where the acres are.
- **The closing line is the deck's turn.** "The problem isn't the features" is what licenses slide 13's grain argument and, through it, the whole recommendation. Without it, three slides of covariate work read as a dead end rather than as a diagnosis.
- **Do not say the covariate model "failed."** It produced a verified gain at 26.6 SD that held across five split years — slide 11 is not retracted here. It failed to be *useful*, which is a different and more interesting claim, and the distinction is what keeps the deck honest rather than defeatist.

**TIME —** 0:40

---

## Slide 13 — Predicting where fires start needed a finer spatial scale. Predicting size may need a shorter time scale.

*Figure:* `img/w6_grain_parallel.png`

**SAY**

> Siting worked once we stopped asking about a whole region and dropped to a hex. This is the same problem on the other axis. We asked how big a fire gets over a whole season — and what makes a fire run is the wind on a particular afternoon, whether crews were already committed. A season is too coarse a unit to see that.
>
> We couldn't test it here; same-day data is a different project. But the shape of the failure tells you where to look.

**EVIDENCE**

- The deck's only figure that plots no data, and its only one about the method rather than the fire. The solved row is closed, the untested row dashed.
- The fourth time the project has met the same lesson: W4's pooled climate null, slide 10's places-not-years, slide 6's grain drop, now this.

**WATCH**

- Say "before the season" whenever the claim is stated as a null. "Megafire size is unpredictable" is a much bigger claim than anything measured here.
- Do not apologise for the null. Five ablations, a shuffled control at 26.6 SD, and a gain that landed in the wrong deciles is a thorough negative result.
- If asked "did you try hard enough?" — pre-season data was tried hard, same-day data was not tried at all. The second half is the open question, not a gap.
- If the room needs "stop targeting it" said aloud, say it as the last sentence rather than the headline.

**TIME —** 0:35

---

## Slide 14 — One ignition is enough.

*Figure:* `img/w6_one_is_enough.png`

**SAY**

> So target ignition. A cell that ignites at all is about twenty times more likely to produce a thousand-acre fire than one that doesn't — that's the case for going after starts.
>
> But the obvious way to act on that is wrong. Every large fire in the held-out years, sorted by how many times its cell ignited that season: **half of them ignited exactly once.**
>
> So this isn't a dial you turn up. **It's a gate — does this place ignite at all.** Rank cells by how often they ignite and you deprioritise the ground that produced half of the big fires.

**EVIDENCE**

- One stacked bar over all 2,724 large-fire cells in the held-out years, split by how many times their hex ignited that season: 49% had exactly one, 21% two, 30% three or more.
- Only the first segment carries color — it is the ground a planner would deprioritise by ranking on ignition count.
- **The gate figure, carried over from a cut slide and now spoken rather than drawn:** a hex-season that ignites at all produces a ≥1,000-acre burn **6.7%** of the time against **0.29%** for one that does not — **22.8x**. JJA natural, held-out years. `img/w6_ignition_gate.png` is available if it is challenged.

**WATCH**

- The rule is binary: does this place ignite, not how often.
- **This slide now carries two jobs**: the case for targeting ignition at all (the 22.8x gate, first sentence) and the instruction for how (the binary rule). The gate had its own slide and lost it; if the opening sentence gets cut for time, the deck asserts "target where they start" without ever saying why ignition is worth targeting.
- **Do not oversell the gate: it is necessary, not sufficient.** 93% of igniting hex-seasons still produce nothing large. It narrows the field; it does not identify the fire. Say "about twenty times" rather than 22.8x — the precision is false comfort on a screening statistic.
- **This is the door slide 13 left open** — size is not forecastable before the season, but the event upstream of it is, and that is what the recommendation acts on.
- If asked "doesn't a cell with more ignitions carry more risk?" — the rate does rise (19.1% at 11-20 ignitions vs 5.4% at one), but risk PER ignition falls 0.054 -> 0.014, and 49% of large-fire cells had exactly one ignition.
- Ignition count ranks burned area **worse** than the hex's own burn history does — +0.253 against +0.357 on the same ranking measure. Counting starts is a poorer guide to where acres will burn than knowing what has burned there before.

**TIME —** 0:40

---

## Slide 15 — Nearly a fifth of burned acres have no specific cause — and that gap is itself forecastable.

*Figure:* `img/w6_unknown_triage.png`

**SAY**

> One thing left — the quarter of fires I mentioned at the start with no cause on record, nearly a fifth by acres. That's been a class to predict all along, not a gap to apologise for.
>
> Because predicting where the record goes dark gives you a worklist: the region-seasons where the most acres will go unattributed next season. Southwestern Tablelands in spring, about a million.
>
> **Ranked by acres, not by rate.** Central Great Plains is worse — two thirds unattributed — and sits fourth, because fixing the record where little burns buys you nothing.

**EVIDENCE**

- The ranked triage list, headed by Southwestern Tablelands MAM at 1.17M predicted unattributed acres.
- Ranked by acres rather than by rate: Central Great Plains has the worse attribution rate (66%) but a fifth of the burn.
- Unknown-branch persistence: acre-weighted MAE 0.167 against the global mean's 0.240.

**WATCH**

- The third leg of the recommendation, delivered where it is actionable rather than as a finding in its own right.
- **This pays off the title slide's voluntary disclosure**, and the SAY says "I mentioned at the start" to close that loop out loud. Stating the weakness first and returning to it as a product is the deck's whole posture on this data; without the callback, slide 0 sounds like a caveat and this sounds like a change of subject.
- **The denominator trap returns here.** Slide 0 says "a quarter of fires" (24.9% by count) and this headline says "nearly a fifth of burned acres" (18.5%). Both correct, different denominators, and the SAY carries both in one sentence for that reason. If challenged, the missing fires are smaller than average — that is why the acre share is lower.
- **Ranked by acres, not by rate — say why, or the ordering looks wrong.** Central Great Plains at 66% unattributed sits below Southwestern Tablelands at 51%, and an attentive listener will notice. The rate is a data-quality statistic; the acres are what a records fix would recover.
- **This is an operational recommendation, not a forecast of fire.** The branch predicts where attribution will be weak — `CLAUDE.md` scopes it as "operational recommendation, not a forecast," and it is a different kind of product from the other two. Do not let it get quoted as a burned-area prediction.
- **Do not claim a cause for the missing data.** The project has never established *why* attribution fails in these region-seasons — the missingness is agency-shaped and that triage is explicitly open work. Say where the record is weak; never say who is failing to record it.

**TIME —** 0:40

---

## Slide 16 — Target causes by region. Site the pre-season work by ignition. Fix the record where it says neither.

*Figure:* `img/w6_recommendation.png`

**SAY**

> Three products, one per class, ordered by where the acres are. For lightning — the majority of the burn — rank the ground and treat what ignites. For human fire, rank the causes by the acres they drive. And where the record says neither, fix the record.
>
> One boundary on all three: **trust the order, not the number.** These will tell you which region, which cause, which ground comes first. They won't tell you how many acres you'll save.

**EVIDENCE**

- Three rows, one per Tier-1 class, ordered by share so the top row is where the acres are: Natural 58.9%, site by ignition, hex-season; Human 22.7%, rank causes by the acres they drive, ecoregion-season; Unknown 18.5%, fix the record underneath, ecoregion-season.
- The line beneath states the finding the recommendation rests on: where fires start is predictable; how big they get, before the season, is not. **The boundary — trust the order, not the number — is spoken only**, so it is the one thing on this slide the audience cannot read for themselves.

**WATCH**

- A TARGETING claim, not an efficacy one. Nothing here measures what a treatment achieves — no before/after, no control, no counterfactual.
- If asked "so if we treat those hexes, we cut the burn?" — say no, plainly. Davis et al. (2024) on severity reduction is separate evidence from someone else's study; cite it if asked, do not fold it in.
- If they remember one thing: site the work against where fires start, because that is the one stage of the escalation this data can see in advance.
- **The figure now prints the title verbatim — "Rank the ground, not the fire" — so the bookend is visual and costs no speaking time.** Do not read it aloud; the SAY's boundary line is what the screen does not say. The figure's subtitle carries the finding underneath ("where fires start is predictable; how big they get, before the season, is not"), which is also not worth reading out.
- **"Trust the order, not the number" is the deck's most important limitation and this is its last statement.** Every product ships as a ranking. The Human branch's composed acre level runs 2x low at p10 and 8x high at p90; the ignition surface ranks well and under-predicts the busiest cells. Rankings are scale-invariant and survive that; acre counts do not.

**TIME —** 0:35

---

## Slide 17 — We started with one record of every U.S. wildfire, then layered on what it could not see.

*Figure:* `img/w6_data_sources.png`

**SAY**

> Everything here starts from one federal record — every U.S. wildfire, nineteen ninety-two to twenty twenty. It knows when a fire started, where, how big it got and what caused it.
>
> What it doesn't know is the shape of the burn, what the ground was like, or how dry the season had been. So four things were joined onto it: ecoregions for the regional unit, satellite perimeters so a fire is an area rather than a dot, drought, and fuel load.

**EVIDENCE**

- One base record, four joined layers, each labelled with what it contributed.
- **FPA-FOD 6th ed.** — Short (2022), Forest Service Research Data Archive, `doi.org/10.2737/RDS-2013-0009.6`. 2.27M fires, 1992–2020.
- **EPA Level III ecoregions** — U.S. EPA (2025); framework from Omernik & Griffith (2014). The regional unit, 105 regions.
- **MTBS burned-area perimeters** — Eidenshink et al. (2007), USGS, `doi.org/10.5066/P9IED7RZ`. 0.6% of fires, 81.6% of acres.
- **TerraClimate** — Abatzoglou et al. (2018), Climatology Lab. ~4 km monthly grids; PDSI, soil moisture, deficit, VPD.
- **MODIS MOD13A1 v6.1** — Didan (2021), NASA LP DAAC, `doi.org/10.5067/MODIS/MOD13A1.061`, accessed via the Microsoft Planetary Computer. 500 m, 16-day vegetation index.

**WATCH**

- **This slide exists to show the layering, not to be read.** Every citation is on screen; say the shape of the stack and stop. Reading DOIs aloud is the worst possible use of thirty seconds.
- **The order is the method, and it is worth landing:** FPA-FOD is the spine, everything else is joined onto it. Each layer was added because the base record could not answer a specific question — the perimeters because FPA-FOD stores a *point* with an *area* attached, the covariates because the record says nothing about conditions.
- **Two of these produced nulls, and that is not a failure of the sourcing.** TerraClimate and MODIS were joined, tested on both branches, and did not improve ignition prediction. If asked why they are still on the slide: they are what makes slides 10–12 a measured result rather than an untested assumption.
- **The Planetary Computer is an access route, not a source.** MODIS is NASA's; the Planetary Computer is how it was fetched without Earthdata credentials. Do not cite it as the data's origin.
- **If asked about LANDFIRE or a fuels model:** pre-rejected for this panel — circa-2001 base map, discrete vintages, and Alaska only from the 2016 Remap, so it carries almost no interannual variance. That is a deliberate exclusion, not an oversight.
- **The full literature review is in the repo** (`literature/literature.md`), with the method precedents as well as the data sources. This slide is the data only.

**TIME —** 0:35

---

## Timing

**Derived from the SAY blocks, not maintained by hand.** Budgets are the measured word count at 150 wpm rounded up to five seconds. Re-derive after any edit rather than adjusting a cell.

| slide | words | budget | |
|---|---|---|---|
| 0 | 90 | 0:40 | Title slide |
| 1 | 80 | 0:35 | Wildfires are seasonal |
| 2 | 65 | 0:30 | Cause is regional, not national |
| 3 | 102 | 0:45 | A region's cause mix is stable enough to f |
| 4 | 64 | 0:30 | For human-cause wildfires, history names t |
| 5 | 30 | 0:20 | A learned model made naming the leading ca |
| 6 | 83 | 0:35 | Where fires start is predictable, at the s |
| 7 | 32 | 0:20 | Almost all the area burned is in almost no |
| 8 | 93 | 0:40 | Up to a point, human and natural burned ar |
| 9 | 72 | 0:30 | Where human fires start is predictable yea |
| 10 | 87 | 0:35 | We tried to improve that with drought and  |
| 11 | 83 | 0:35 | The same data does predict how much burns |
| 12 | 89 | 0:40 | But the gain misses where we need it most |
| 13 | 85 | 0:35 | Predicting where fires start needed a fine |
| 14 | 100 | 0:40 | One ignition is enough |
| 15 | 92 | 0:40 | Nearly a fifth of burned acres have no spe |
| 16 | 77 | 0:35 | Target causes by region. Site the pre-seas |
| 17 | 81 | 0:35 | We started with one record of every U.S. w |
| **Total** | **1405** | **10:20** | against a ~10:00 target |

**1405 spoken words, cut from 1,746 in the W7 content pass.** The rounded budget total is 10:20; raw prose is shorter, because per-slide rounding adds about a minute of slack across 18 slides.

**What it runs at, by pace.** The second column adds two seconds per slide for advancing and letting a claim land — 18 slides, so 36 seconds.

| pace | prose | + transitions |
|---|---|---|
| 130 wpm | 10:48 | 11:24 |
| 140 wpm | 10:02 | 10:38 |
| **150 wpm** | **9:22** | **9:58** |
| 160 wpm | 8:46 | 9:22 |

**Inside ten minutes at every pace tested**, including a deliberate 130 wpm. **Measure before cutting anything else:** record slide 3 alone — 102 words, the densest in the deck — and time it. Around 41 seconds means 150 wpm; 47 seconds means 130.

**Headroom exists.** The deck was 2:45 over before the content pass. Further cuts should be driven by what does not earn its place rather than by the clock. The heaviest remaining are slides **3** (102 words) and **14** (100).
