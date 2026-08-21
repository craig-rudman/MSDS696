# MSDS 696 Practicum II: LLM Collaboration Log — Distilled
Craig Rudman<br>
crudman@regis.edu<br>

This distills the term's human-LLM collaboration, week by week: what was accomplished, where there was creative conflict, and what was decided. The full record is [collaboration_log.md](../collaboration_log.md) — 149 contemporaneous entries written alongside the work rather than reconstructed at the end.

The weeks are deliberately uneven. Week 1 carries three entries and Week 6 carries fifty-seven; the sections are proportional to what actually happened.

One convention runs through the whole record: **the log is the authority when documents disagree.** It was written contemporaneously with decisions, so when a design document, a status report, and the log conflict, everything reconciles toward the log. That rule was invoked explicitly in Weeks 6 and 7 to resolve real drift, and it is why the raw log is submitted alongside this distillation rather than replaced by it.

Three threads run the length of the term and are easier to see assembled than in sequence. They are stated here because each one was discovered piecemeal — diagnosed separately three or four times before anyone noticed it was one thing.

### Thread 1: The same finding, four times — the grain was always the problem

The project's one recurring result is that **when a signal fails to appear, the usual cause is that the model's grain is wrong, not that the signal is absent.** It was met four times across four weeks and named as a single lesson only in Week 6:

| Week | Where it appeared | The form it took |
|---|---|---|
| 4 | TerraClimate at Level III | A pooled null across 105 ecoregions — per-region correlations ran 0.086–0.529 and *inverted sign* in two, so averaging washed a real signal to zero |
| 6 | Covariates at hex grain | "Dry *places*, not dry *years*" — raw pdsi −0.137 collapses to −0.073 as a within-hex anomaly |
| 6 | Ecoregion → hex | The region was too coarse to site work; dropping to hex is what made ignition predictable |
| 7 | Season → day (untested) | If siting needed a finer *place*, size may need a finer *moment* — same move, other axis |

The fourth instance is the one that generalized it. Standing on the slide conceding the megafire null, I observed that to improve *siting* forecasts we had come down from region to hex, and we might be saying that to improve *size* forecasts we have to come down from season to day. The agent's contribution was recognizing this as the same lesson the project had already met three times — which turned a slide headline into the deck's intellectual spine, and reframed five nulls from a list of disappointments into one diagnosis.

### Thread 2: The internally coherent wrong answer

The characteristic failure of this collaboration was never an obvious error. It was a number that was **plausible in magnitude, correct in sign, consistent with a prior belief, and wrong** — with nothing about the number itself to flag it.

- A missing-cause diagnostic returned **0.0% missing everywhere** — a clean result produced by measuring an already-filtered frame.
- A hex burned-area baseline scored **−0.052 Spearman**, reported to me as "burn size is essentially unpredictable, if anything mildly anti-informative." It was a `LOG_FLOOR = -4` placeholder being scored as a *prediction of 0.0001 acres* against real megafires. Corrected: **+0.37**.
- A state-level scatter read as a **flat cloud** (r ≈ 0.07). The actual shape was a fan, carrying the opposite conclusion — volatility concentrated exactly where the proposed mechanism *cannot* operate.
- A figure caption said **526k acres in a typical week**. That is a 29-year mean at 2.2× the median, inflated by a single year — asserting predictability on the one quantity the deck spends three slides calling unpredictable.
- An NDVI-colored scatter **would have sorted correctly** (+0.385 pooled), leading every reader to conclude NDVI predicts ignition — the exact opposite of the finding, because it shows the marginal rather than the incremental correlation.

What caught each one was never a summary statistic. It was a **physical implausibility check** (an implied error of 10⁸× cannot be real; a hex reporting 213% of its own area cannot be right), or **looking at the rendered shape** rather than the coefficient, or **asking what a word means** ("what does 'typical' actually compute?"). The lesson the record supports is narrow and practical: a metric can only tell you a result is surprising, not that it is wrong — and the checks that work are the ones a summary statistic cannot perform.

### Thread 3: Every verification rule was bought with a specific failure

The project accumulated a set of standing rules. None was adopted on principle; each has a price attached, and the price is what makes the rule stick.

| The rule | What it cost to learn |
|---|---|
| The executed cell is the authority on numbers; the log is the authority on decisions | Notebooks 12–14 had **zero stored outputs** — every number in their markdown was hand-written by an agent, and ~15 had propagated into `CLAUDE.md` as settled fact |
| The population travels with the number | A load-bearing two-branch comparison paired natural's 855× (JJA, six regions) against human's 12.3× (all seasons, all regions), inflating a 22-fold gap into "two orders of magnitude" |
| One fact, one home | Architecture and covariate status each lived in two auto-loading files; the W6 drift followed, and consolidation only helps if it cannot recur |
| Derive the timing table, never maintain it | Two silent drifts — the second reported 11:00 when the measured total was **12:45**, which would have left me two minutes over on the day |
| Check what you are keying on before reporting a discrepancy | A deck diff keyed on *slide position* reported nine reworded headlines and a scrambled order; matching by image content showed one deleted slide and an off-by-one |
| Verify the module still *contains* everything, not just that it imports | A duplicate-block removal silently deleted four functions two beats depended on |

---

## Week 1 — Framing the question

**What was accomplished.** The project proposal: a two-part research question, a single named stakeholder, and a personal angle. The LLM held my initial framing to a three-part test (question / stakeholder / action), flagged that "local, state, and federal agencies" was too broad a stakeholder to design for, and verified against the USFS source that FPA-FOD carries cause, location, time, and size — but no resource, budget, or crew data.

**Where there was creative conflict.** Three places. The LLM proposed a "one state deep plus national contrast" scope; I overrode it with three region–cause example pairs, because pairing region and cause proves the "different regions need different strategies" assertion more directly. It framed the dataset-extension work as a committed enhancement; I made it exploratory, so a discovery step that didn't pan out couldn't jeopardize the deliverable. And its first draft of the Personal Angle manufactured a commitment to wildfire prevention as a domain — I don't hold that commitment, and I had it cut to the honest version: policy research is the aim, wildfire is the case study.

**What was decided.** "Inform and target" rather than "optimize allocation," because the data has no resource variable and claiming optimization would be an overclaim I couldn't defend. That constraint — say only what the data supports — became the discipline the rest of the term ran on.

---

## Week 2 — Feasibility, and the question changing under it

**What was accomplished.** A feasibility check that came back strongly positive on both axes: the cause mix inverts between winter and summer (Natural swings 1% → 44%), and across 78 ecoregions the Natural share spans 0.5% to 82.6%. Also the literature grounding, two-tier data provenance, a documented bias inventory, and the first measurement of the missing-cause problem.

**Where there was creative conflict.** The spatial-unit decision is the one worth recording. The agent argued for STATE on the grounds that my stakeholder acts within jurisdiction; I redirected it to inventory what the data actually offers, then to search the literature. That surfaced **EPA Level III ecoregions** — the unit the peer-reviewed FPA-FOD cause literature uses, because ignition tracks ecology rather than state lines. I dropped my own earlier hex-grid idea for the same reason. Separately, the agent's first missing-cause diagnostic returned 0.0% missing everywhere; I didn't accept the clean-looking result, and the check surfaced a pipeline bug that had been measuring an already-filtered frame. The corrected finding is the one the whole project now carries: missingness is flat across seasons but spans 2.9%–65.1% across ecoregions.

**What was decided.** Report cause as **shares, not counts**. Also, by the end of the week, that the research question itself had to change: the work had outgrown "which causes dominate" into a two-part RQ — descriptive (which causes drive the most burned area) and predictive (can a next-season profile be forecast). I left the W1 proposal unedited as historical record rather than rewriting it to match, and caught a "measured and bounded" overclaim in my own status report — the bound was next week's work, not done.

---

## Week 3 — EDA, and a fifth of the data going missing

**What was accomplished.** Exploratory analysis across cause-by-year burned-area trends, a Natural-cause deep dive, the human sub-cause mix, and a full characterization of the missing-cause bucket — including three indirect probes testing whether missingness hides any one cause preferentially. Then the cleaning pipeline.

**Where there was creative conflict.** Mostly about plot form and about not accepting the first reading. A scatter of 327k points became a boxplot, then a violin, because the scatter buried the distribution the question was about. Stacked area and stacked bar both got rejected for small multiples, because in any stack only the bottom band sits on a flat baseline. More substantively: I read a state-level scatter as a **fan** where the agent had reported a flat cloud, and the fan carried the opposite meaning. Then at ecoregion grain the fan didn't survive, and I directed the conclusion down to "weakly consistent, not evidence" — keeping the finer-grain result even though it weakened my own earlier claim.

**What was decided.** Drop PR, HI, and the remaining `IA` rows (32,223 records) as functionally unattributed rather than merely caveat-worthy. EDA and missingness notebooks keep reading **raw** data — I overrode the agent's proposal that they consume the cleaned artifact, because those notebooks are the diagnosis that justifies the cleaning, and a cleaned input would make EDA assume its own conclusion.

**The week's most consequential catch was the agent's.** Building the ecoregion join, it flagged that Alaska was being *dropped, not handled* — the CONUS shapefile is explicitly conterminous, so Alaskan points simply vanished. Every plan document since Week 2 had said "AK/HI at state grain," and nothing had ever implemented it. The stake was **20.4% of all burned acres** disappearing silently. I overrode my own earlier state-grain plan in favor of a second spatial join against the Alaska ecoregion layer, which keeps one region column and one grain with no downstream special case.

---

## Week 4 — The architecture pivot

**What was accomplished.** The model went from a flat 12-cause composition to a **hierarchical three-branch architecture**: a Tier-1 Human/Natural/Unknown allocator over a total-acres denominator, then three heterogeneous Tier-2 branches. All four models got a first pass, with persistence floors established for each.

**Where there was creative conflict.** The pivot itself was mine, and it retired what every prior planning document implied. The flat model lets the 18.5% Unknown mass contaminate every share and applies a cause frame to a branch (Natural) that has essentially one cause. Then a sequence of results overturned expectations — including mine:

- I predicted a **shorter** trailing window would sharpen the Human branch. The sweep showed short windows are *worse* (k=1 scores 0.546 against k=7's 0.489). I kept the negative result about my own hypothesis.
- The agent's initial framing assumed persistence would beat a global constant on the Natural branch, as it had elsewhere. The dry run overturned it: persistence wins unweighted and **loses acre-weighted**, because a region's own calm-year history is actively misleading on the megafire years that carry the acres.
- The Unknown branch contradicted a claim written into three project documents — that missingness concentrates in the high-Natural West. Measured directly, the correlation is **negative** (Pearson ≈ −0.64). A provenance check showed the original missingness notebook never made that claim; it was an interpretive leap I had introduced downstream.

**What was decided.** Predict Unknown as a first-class class rather than renormalizing it away, because a planner has to deal with the unattributed mass. Report the overturned caveat honestly rather than burying it — the Human-floor *conclusion* survives with its mechanism reversed. And establish the working rhythm the rest of the term used: **work in small iterations and write log entries as we go**, which I installed by interrupting the agent mid-build.

---

## Week 5 — Sourcing covariates, and finding the key already in the database

**What was accomplished.** The TerraClimate covariate layer, an object-oriented refactor with a 55-test suite, and the MTBS perimeter join that solved a confound I had raised.

**Where there was creative conflict.** Two agent catches I would not have made, and one of mine that mattered more.

The agent's: my own documented stub named **gridMET** and **nClimGrid** as drought sources. Both are CONUS-only, and my grain includes 20 Alaska ecoregions — either would have silently dropped every AK cell. It proposed TerraClimate instead and verified the endpoints live rather than trusting documentation. It also rejected LANDFIRE for this panel on vintage grounds (circa-2001 base map, Alaska only from 2016), because a fuel-load feature would carry almost no interannual variance — which is exactly the variance the megafire problem needs.

Mine: I raised that FPA-FOD stores a **pinpoint** lat/lon while `FIRE_SIZE` describes an **area**, so assigning a 2.8M-acre fire's whole acreage to one hex measures attribution error rather than fire behavior. The agent's first instinct was an external satellite raster pipeline. I told it to check the original database first — and it found `MTBS_ID`, a live foreign key to burn perimeters covering **81.6% of all burned acres**. The confound was solvable with a join, not a new data pipeline.

I also made it verify rather than accept twice: it asserted a merge bug in my published numbers and **retracted it** when I asked it to check; and when I said I had about a terabyte of storage, it measured 213 GB free and flagged the gap rather than accepting my premise.

**What was decided.** Fuel *condition* over fuel *load*. Baseline-before-anything — the project wasn't a git repository, so the executed notebooks were the only unversioned copy of every result. And the honest position on a genuine ambiguity: 14 fires sit within centimetres of an ecoregion seam, so region assignment there is **undefined**, and the test asserts an acreage bound rather than pinning a PROJ release.

---

## Week 6 — The hex grain, five nulls, and building the narrative

The heaviest week of the term: fifty-seven entries covering a product redefinition, a full second modeling grain, five consecutive covariate nulls, and nineteen slides built one at a time.

**What was accomplished.** The prediction product was redefined around "where in my region are fires most likely to start?", which required a res-5 hex grain (36,234 hexes) alongside the existing Level III grain. Ignition, burned-area, and covariate layers were built at that grain; both Human and Natural branches were modeled; and the entire W6 narrative — nineteen assertion headlines, seven figures built from scratch, a generated deck with speaker notes — came out of it.

**Where there was creative conflict.**

*The framing correction was mine.* The agent inherited a prevention-versus-mitigation partition from `CLAUDE.md` that split by **cause** (lightning can't be prevented, so Natural → mitigation). I argued they partition by **lever**: fuel treatment, defensible space, and suppression pre-positioning are all *sited works*, and whether they pay off depends on whether fire arrives there. The agent conceded and named its own error precisely — then found that the original W4 document had it right all along, and the error was `CLAUDE.md`'s compression of it.

*The point-vs-area asymmetry was the agent's.* W5's central problem — a point can't carry acres — **does not apply to an ignition target**, because an ignition location is exactly what the record stores correctly. That insight is what made the whole hex build cheap.

*Three times the agent refused to draw a figure I asked for*, and gave the measurement that made it wrong each time: a scatter colored by NDVI would have shown the marginal correlation and led a reader to the opposite of the finding; a map of where NDVI adds signal would have drawn sampling variability at ~21 observations per hex; and a four-color outcome map reads as failure by arithmetic regardless of ranking quality. A compliant agent would have produced three misleading slides.

*The agent also refused to publish its own numbers.* Its ablation harness produced three contradictory results for the same rung (−30%, −115%, +3.4%). It stopped, said plainly that the instrument was untrustworthy, and excluded the ladder from the notebook with a section explaining why. A caveat does not repair an instrument. When the harness was later fixed — the root cause was the trailing-mean idiom retyped roughly eight times across throwaway scripts — the ladder produced identical numbers three runs running.

*And it corrected me on my own conclusion.* I said nothing we had done improved our ability to infer. It pushed back that this treats the baseline as zero: persistence cuts deviance ~50% below the global rate, so the accurate statement is that we *can* predict well above chance and what failed is the covariates improving on it. That distinction is the difference between a dead end and a finding.

**What was decided.**

- **Persistence is the model to beat, everywhere.** Human ignition ranks at +0.526, Natural at +0.344, with shuffled controls within ±0.003 of zero.
- **Five consecutive covariate nulls on ignition**, with a measured reason rather than a shrug: these covariates identify dry *places*, not dry *years*. Raw pdsi correlates −0.137 with ignitions; as a within-hex anomaly it collapses to −0.073. Where fires start is a property of the place, not the year.
- **One verified covariate gain, on burned area only** — climate and NDVI together, +0.049 at 26.6 SD above a shuffled control — that is **real but not useful**, because the gain lands on 1–20 acre fires and the top decile goes 855× → 868×.
- **Ignition is a gate, not a dial.** An igniting hex-season is 22.8× more likely to produce a ≥1,000-acre burn, but escape probability *per ignition* falls with count and 49% of large fires came from hexes with exactly one ignition.

**Two process decisions shaped everything after.** First, a full documentation consolidation into a single `CLAUDE.md` — the drift the log had caught happened because architecture facts lived in two auto-loading places, and consolidation only helps if that can't recur. Second, a regression that found notebooks 12–14 had **zero stored outputs**: every number in their markdown had been hand-written by an agent rather than read off a computed cell. That produced the rule the rest of the term ran on — **the log is the authority on decisions; the executed cell is the authority on numbers** — and the corollary that a population travels with every figure, after a load-bearing comparison turned out to pair natural's 855× (JJA, six regions) against human's 12.3× (all seasons, all regions).

---

## Week 7 — Rehearsal, and the deck saying what it means

**What was accomplished.** The W6 deck became a delivered talk: a `final_script.md` declared authoritative, every slide's speaker notes written, two slides cut and two added, a retitle, and a 1,746 → 1,379 word trim to fit ten minutes. Plus two genuine analytical additions and a repository cleanup.

**Where there was creative conflict.**

*The deck's real weakness was mine to name.* It moves between predicting shares, ranking, where fires start, and how many acres burn — and a listener has no reliable cue for which is on screen. The audit found three axes changing, not one, and the sharpest instance was the word "predictable" carrying a **rank** claim on one slide and a **level** claim three slides later, with the entire conclusion turning on that distinction. I fixed it in headlines rather than speaker notes, because a headline stays on screen while the audience thinks and a spoken correction is gone in a second.

*I overrode the agent on cutting a slide.* It argued against cutting the shuffled-control figure — it was the only on-screen defense of the one thing that works, and an executive audience's natural challenge to five nulls is "is the working part actually working?" I cut it anyway: a permutation control is a methods argument and belongs in Q&A where I can make it properly, rather than asserted badly in twelve seconds. But I attached a condition, and the agent implemented it: the control relocated into the neighboring slide's notes, which now say explicitly that this is the deck's only remaining defense of the claim.

*And I asked the question that reopened a closed finding.* Standing on the one slide conceding a model lost, I asked how we knew the **choice of model** wasn't at fault. We didn't — both learned rungs called one estimator at stock settings, and every prior write-up conceded only the tuning half. The ridge rung I then commissioned **beat gradient boosting** (52.2% vs 47.5% top-1) and still lost to the floor's 54.1%. The rung I had been presenting was not the best learned model available. The finding that actually settles it is the flat alpha sweep — identical to six decimals across four orders of magnitude, which is an information ceiling rather than an under-tuned model.

*The per-cell confidence result came from a reframing I made.* The agent's first answer measured the spread of realized error pooled nationally, which answers a different question. Each region-season is its own series with its own settledness, and that is knowable **before** the season opens. Trailing dispersion predicts trailing-mean error at +0.484 and +0.577 Spearman, 33 and 35 SD above a shuffled control — and it holds *within* individual regions, so it isn't just restating "some places are stable."

**What was decided.** Retitle the deck to **"Rank the ground, not the fire"** — the inverse of how it was built. The title was set in W6 and every slide written toward it; once seventeen slides had settled what the project shows, the promise on slide 0 was the thing out of date. Changing the conclusion to fit the title would have been the mistake. "Rank" is also the more honest verb: "target" edges toward promising an outcome, and nothing in this project measures what a treatment achieves.

Also settled: the script is what I study from, the deck is what I deliver from, and the deck's notes carry the spoken line only — 2,000–6,000 characters of caveats per slide is the right density for preparing and exactly wrong for presenting.

**The verification habit paid off repeatedly.** A claim I asked the agent to write — that natural fire concentrates more sharply than human — came back **wrong on measurement**: the branches cross over. A geography claim sourced from my own `CLAUDE.md` didn't survive recomputation: the well-attributed end is Alaska specifically, not "the West," and Coast Range sits among the ten worst at 53% missing. And a correction I recorded in one entry turned out never to have been *applied* to the document — the agent caught that while staging a commit and flagged it rather than fixing it silently.

---

## Week 8 — Submission

**What was accomplished.** The three final artifacts: the raw collaboration log covering all weeks, this distilled summary, and a reflection produced through interview.

**What was decided.** That the raw log ships **as written**, including the entries later corrected by subsequent entries. Rewriting an early entry to match a later finding would falsify the contemporaneous record that makes the log worth submitting at all — the same reasoning that left the W1 proposal unedited in Week 2, amended `design_refinement.md` with a dated note rather than editing it in Week 6, and preserved historical file references in Week 7. One structural fix was applied: the Week 7 heading was missing, so fifty entries sat under Week 6.

---

## What the division of labour actually turned out to be

The three threads above describe what was learned. This is about who learned it, and the split is sharper than I expected going in.

**The agent's decisive contributions were almost entirely catches on work already in flight** — not proposals, and not analysis. Alaska vanishing from a join nobody had noticed was incomplete. Two CONUS-only drought sources named in *my own* documented plan. A foreign key already sitting in the database I was about to build a satellite pipeline to replace. Three refusals to render a figure I had asked for, each with the measurement that made it wrong. Notebooks whose numbers had never been computed. A correction I had reasoned through, recorded, and never actually applied to the file.

The pattern is that these are all **defects in the premises of a task**, found by an agent that checked the ground before standing on it. None required domain insight about wildfire. All of them required reading what was actually there rather than what the plan said was there.

**My decisive contributions were reframings — and, more often, refusals to accept a clean result.** The hierarchical architecture that retired the flat model. The lever-not-cause partition. The pinpoint-versus-area confound that reshaped two weeks of work. Per-cell confidence reframed as a quantity knowable *before* the season rather than after. Asking whether the model family, not just its tuning, was at fault — which reopened a closed finding and showed the rung I had been presenting was not the best one available.

But the refusals did more work than the reframings. The 0.0% missing rate, the flat cloud that was a fan, the ablation table that changed three times, the "more sharply concentrated" claim that came back wrong on measurement, the geography claim sourced from my own requirements file that didn't survive recomputation. In each case the available number looked fine and the correct move was to distrust it.

**Where the collaboration worked worst is worth naming too.** The agent over-claimed on first pass more than once — asserting a merge bug in my published numbers and retracting it when challenged, proposing a "fix" that made results dramatically worse before isolating the real cause, reporting a scrambled slide order that was an artifact of its own diff method. Its instinct under uncertainty was to reach for an external solution (a raster pipeline, a new data source) before exhausting what was already in hand. And it inherited framings from project documents without examining them — the cause-based prevention/mitigation partition rode in `CLAUDE.md` for two weeks before I pushed on it.

**What made both halves work was writing it down while it happened.** Roughly fourteen entries record the agent correcting itself mid-task; a comparable number record me overriding my own earlier decisions. Neither is recoverable from the code. Several settled findings exist only because a contemporaneous entry preserved a reasoning chain a later session would otherwise have re-litigated from scratch — and at least three of the term's corrections were caught precisely *because* the log said something a document didn't.
