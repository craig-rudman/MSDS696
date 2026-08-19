# Weekly Status Report

| Name | | Week / Date | |
| --- | --- | --- | --- |
|  Craig Rudman |  |  Week 7 / 2026-08-18 |  |

## Project title
Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation

## Repo

https://github.com/craig-rudman/MSDS696

The W7 artifacts sit in `coursework/W7/`: the near-final deck (`MSDS696_W7_Deck.pptx`, 19 slides),
the authoritative talk script (`final_script.md`), and the remediation plan that tracked this week's
work to done (`REMEDIATION_PLAN.md`). The decision record is `coursework/collaboration_log.md`,
entries 7.1–7.43.

## Project summary

This project helps a state or regional fire planner match prevention and mitigation effort to the
pattern that actually drives burned acres, instead of spreading it uniformly. The data is the Fire
Program Analysis Fire-Occurrence Database (FPA-FOD), about 2.3M U.S. wildfires from 1992 to 2020,
grouped by cause, EPA Level III ecoregion, and meteorological season.

The model works in two steps. First it splits a region-season's burned acres across three classes —
Human, Natural, and Unknown, where Unknown means no cause was ever recorded. Then each class gets its
own follow-on model, because each raises a different question.

The predictive deliverable comes from the first step plus the Human class, the only class with a
composition of causes to rank. For a region and upcoming season it ranks causes by acres likely to
burn rather than by fires started, so effort goes where the acres are. The ranking is the reliable
part: the cause mix is stable and predictable from history, while the season's total burn is not, so
the acre figures carry much wider error than the order does.

Natural is the largest first-step class at 58.9% of acres, and its branch asks where within a region
fires are most likely to start, on a fine hexagonal grid rather than the whole ecoregion — because
fuel treatment, defensible space and pre-positioned crews are all sited works, and whether they pay
off depends on whether fire arrives there. Unknown is not a forecast but a data-quality signal: where
a region's causes go unrecorded, the record itself is the weak link.

**What changed in the framing this week is the verb.** The deck was titled around *targeting*, and
targeting edges toward promising an outcome that nothing here measures. Every product this project
ships is a **ranking** — of causes within a region, of ground within a region, of regions by how
badly their record fails — and a ranking is scale-invariant in a way an acre count is not. The talk
now opens on **"Rank the ground, not the fire"** and closes on **"trust the order, not the number."**
Same shape, and the second is the boundary the first earns.

## The research questions

The rest of this report refers back to these:

- RQ1 (descriptive): Across a set of contrasting U.S. region-seasons, which wildfire causes (natural
  and human) drive the most burned area, and do those patterns differ enough to demand different
  prevention and mitigation strategies?
- RQ2 (predictive): Can a next-season cause-risk profile — the expected composition of causes for a
  region and upcoming season, ranked by the burned area each is expected to drive — be predicted well
  enough to pre-target that prevention effort?

## Milestones

- **Done** — Data acquisition, feasibility, and EDA: FPA-FOD 1992–2020 loaded and validated; cause
  composition, size distributions, and the differential missing-cause problem characterized.
- **Done** — Cleaning: documented exclusions; EPA Level III spatial join (CONUS and Alaska);
  meteorological season and season-year index derived.
- **Done** — Method design: hierarchical structure settled over a flat classifier.
- **Done** — Perimeter correction and hex grid (W5): MTBS perimeters joined, acres distributed across
  res-5 hexes, conservation verified at 99.61% on-grid.
- **Done** — Feature engineering: trailing cause and burn history; pre-season climate at both region
  and hex grain; prior-burn state per hex-season; MODIS vegetation density. All external features
  lagged to pre-season availability.
- **Done** — Level III and hex-grain modeling (W6): persistence baselines for all three branches,
  forward-chaining splits, learned rungs, shuffled-control tests and covariate ablation ladders.
- **Done (W7)** — **Per-cell confidence from trailing dispersion.** The one substantive new result
  this week, and it is free from a baseline already in use.
- **Done (W7)** — **The model-family question on the Human branch, closed by measurement** rather than
  by a Q&A defense: a ridge rung beats gradient boosting and still loses to the trailing-mean floor,
  and the flat alpha sweep is the evidence that this is an information ceiling.
- **Done (W7)** — **The near-final deck.** 19 slides, 1,379 spoken words, 9:49 at 150 wpm with
  transitions, every headline and all 19 notes panes reconciled to `final_script.md` programmatically.
- **In progress** — The timed dry run, its self-assessment, and the executive-challenge Q&A.

## Last week's "To Do"

- **Fix the point attribution of large unperimetered fires.** **Deferred to W8, deliberately.** The
  fix is designed — impute a circular burn of the correct area from the ignition point and distribute
  it with the same weight machinery `hex_burn` already applies to perimeters. It is not built, because
  rebuilding `hex_acres_res5.parquet` invalidates notebooks 13–15 and every acres figure in the deck,
  and this was the week the deck had to be finished. The defect is now **stated on the slide it
  affects** (slide 7's notes carry it with its bound) rather than sitting silently in the data.
- **Record the practice talk and post it with the self-assessment.** **Not yet done** — this is the
  graded item still outstanding, and it is now unblocked: the deck is finished and reconciled.
- **Run the headline-only test with a podmate reading, and complete the structure peer-review.**
  **Superseded.** W7's version of this is the full timed dry run plus the executive challenge, which
  is the same test with a harder audience.
- **Build the final deck against this storyboard, one slide per assertion.** **Done, and it moved
  well past layout.** Two slides were cut, one added, two swapped, the title rewritten, and 499 words
  removed. Details below.
- **Test whether same-day conditions predict which igniting natural hexes escape.** **Not done, and
  correctly not attempted** — a different data requirement, not a tuning exercise. It remains the
  project's clearest next experiment.
- **Optionally, a hyperparameter search on the Human branch's learned rungs.** **Answered better than
  a search would have.** See the ridge result below: swapping the *family* recovered five points of
  top-1 and the regularization sweep is flat across four orders of magnitude, which makes a booster
  search unpromising rather than merely untried.

## This week's progress

### The one new result: per-cell confidence, and it was free

I asked whether we could state a level of confidence in the cause-mix predictions. The first answer
measured the spread of realized error pooled across all held-out cells, which answers a different
question — realized error is only knowable *afterward*, and a planner needs the flag *before* the
season opens.

The reframe is the finding. Each region carries its own history and **each season within it is its
own series**, so a region-season has its own uncertainty. The right quantity is not "how variable is
the error nationally" but "how settled has *this* cell been" — and that is available pre-season.

`TrailingMean(k=7, how="std")` uses the **same window, same `shift(1)`, same `(region, season)`
grouping** as the prediction itself, so it is strictly pre-season information. It predicts the error
of the trailing mean:

| | Tier 1 | Human |
|---|---|---|
| Spearman(dispersion, realized TVD) | **+0.484** | **+0.577** |
| SD above a 200-run shuffled control | 33 | 35 |
| accuracy, steadiest → most volatile quartile | **83.1% → 61.9%** | **72.5% → 39.4%** |
| series with n≥20 that are positive *within* a region | 74 / 93 | 80 / 92 |

Three things about it matter more than the correlation.

**It is per-cell, not geography.** Across regions the correlation could merely restate "some regions
are stable places." It holds *inside* individual series — 74/93 and 80/92 — so it is about this cell
in this year.

**Each season carries its own level of trust.** Klamath sits at dispersion 0.121 / 75.8% accuracy in
winter and 0.293 / 57.3% in summer. One region, four different answers, and summer — where lightning
competes with human ignition — is the volatile one.

**It ranks confidence; it does not calibrate it.** The honest phrasing is "this cell is in the
steadiest quartile, which historically scored 83%," never "83% likely to be right." And a quiet
history is not a guarantee: **36 of 986 steadiest-quartile cells (3.7%) still scored below 25%**,
several at dispersion exactly 0.000. A settled history can precede a regime break, and those are the
confident-looking misses. That caveat is recorded as prominently as the result.

The spread is widest on the Human branch — the weaker product — which is the useful direction: its
failures are anticipated rather than random.

### The model-family question, closed

Slide 5 is the deck's one conceded loss: a learned model tried and beaten by a trailing mean. Having
approved its script, I stopped and asked how we know the *choice of model* was not at fault.

The honest answer was that we did not. Both learned rungs called `SimplexRegressor()` bare —
`HistGradientBoostingRegressor` at stock settings, one family, one seed, no search. Every prior
write-up conceded only the *tuning* half of that; nothing conceded the *family* half, while the script
said "**the model** could not beat taking its mean," which reads as all learned models.

I asked for the measurement rather than a Q&A defense. A ridge rung — same features, split, acre
weights, held-out cells, simplex projection, only the learner swapped:

| rung | TVD ↓ | top-1 ↑ |
|---|---|---|
| the region's own seasonal history (the floor) | **0.4887** | **54.1%** |
| ridge, with history as a feature | 0.5366 | 52.2% |
| gradient boosting, with history as a feature | 0.5536 | 47.5% |
| gradient boosting on region character | 0.5877 | 35.7% |

**Ridge beats the booster** — the rung I had been presenting was not the best learned model
available. The booster was paying a variance cost on a small wide panel (~5,300 training cells, 23
features, 11 correlated targets). It still loses to the floor, which is what preserves the slide.

**The finding that actually settles the question is the flat alpha sweep**: top-1 identical to six
decimal places from alpha 0.1 to 1000, with alpha verified to propagate through the pipeline. A
four-decade regularization sweep that changes nothing is an **information ceiling, not an under-tuned
model** — a far better answer to "did you tune it?" than anything I had before.

The control I insisted on before believing the near-tie: is ridge just rediscovering the floor? It is
not — 0.283 TVD units from the floor per cell, and it names a different top cause in a quarter of
them. Two learners converging just short of the trailing mean **by different routes** is stronger
evidence than either alone.

The figure gained one bar rather than two. Ridge-on-coarse scores 35.67% against gradient boosting's
35.66%; two identical-length bars both reading "36%" is reading time spent discovering they say the
same thing. **The figure is the argument, not the archive** — the full five-rung table stays in
notebook 08.

### The deck: what changed and why

The deck went from a W6 storyboard port to a near-final talk. `coursework/W7/final_script.md` is now
the **authoritative text** — where it and the .pptx disagree, the file wins and the deck is corrected.
The structural moves, in order of how much they changed the talk:

| change | why |
|---|---|
| **Retitled: "Rank the ground, not the fire"** | The title was set in W6 and every slide since was written toward it. Once seventeen slides had settled what the project actually shows, the promise on slide 0 was the thing out of date. Changing the conclusion to fit the title would have been the mistake. "Rank" is also the more honest verb — "target" edges toward promising an outcome, and nothing here measures what a treatment achieves. |
| **Cut the k-sweep slide** | It tuned a parameter of the baseline rather than adding a claim, and its headline left the target unbound — *enough for what?* W6 had already nominated it as the first to drop. |
| **Cut the shuffled-control slide, over the agent's objection** | It is the most abstract figure in the deck arriving in a 30-second slot right after a grain change. A permutation control is a methods argument, and methods arguments belong in Q&A where I can make them properly. **The condition I attached: it relocates, it does not disappear.** Slide 6's notes now carry the full result and an instruction to have the figure ready. |
| **Cut the ignition-gate slide, kept "one ignition is enough"** | The gate was a *justification* slide — it argued ignition is worth targeting, which an audience grants anyway. "One ignition is enough" is an *instruction*: rank cells by *whether* they ignite, not how often. It is the only place in the deck that says **how** to do what the title and the closer both ask for. The gate folded into one opening sentence. |
| **Added a data-sources slide** | Built as a **stack**, not a bibliography: FPA-FOD in its own band, then four layers each labelled with what it contributed — the regional unit, fire as an area rather than a point, drought, fuel load. Two of the four produced nulls and they stay on the slide; without them slides 10–12 are an untested assumption rather than a measured result. |
| **Moved the data-sources slide off the end** | You do not end a talk on a bibliography. The last thing on screen while the room starts asking questions should be the products and the boundary. |
| **Added a text-only closer** | "Rank the ground, not the fire" was printed beneath three product rows, competing for the same glance and landing as neither. A closing line has to be the only thing on screen or it is a caption. This is the one slide in the deck where reading it aloud is correct — the repetition *is* the delivery. |

**Three ambiguity defects found and fixed, and they are one defect in three places.** The deck
predicts three different things — cause mix, ignition counts, burned acres — and the target flips six
times reading down the slides. A listener carrying the wrong quantity forward hears a different and
usually weaker claim.

- **The silent 6 → 7 switch.** Slide 6 is about where fires *start*; slide 7 opened on where the
  *acres* are, with no acknowledgement. This is the worst boundary in the deck precisely because
  *nothing else changes* — same hexes, same ordering, same figure family. A listener hears "one
  percent of cells hold fifty-five percent of the **starts**." Fixed with one protected clause: *"That
  was where fires start. The other half is how much they burn — same cells, different target."*
- **"Both" on slide 8.** The headline read "Up to a point, both are predictable" — where *both* reads
  as starts-vs-acres, the contrast established two slides earlier, when what is plotted is human vs.
  natural. Two ambiguous words in a row: *both*, and *predictable*.
- **"Predictable" without a quantity on slide 9.** Three headlines used the word; two named their
  quantity and one did not.

The standing rule that came out of it: **headlines have to name the quantity, not just the speaker
notes.** A headline stays on screen while the audience thinks; a spoken correction is gone in a
second. The audit that produced the rule also found slide 6's deck headline had **never been synced**
to the script, which is how the whole-deck reconciliation below got started.

**Length: 1,746 → 1,379 words.** The line-level pass got 216 words without losing a claim, almost all
of it the same defect — **the speaker notes were narrating figures that are already annotated.** My
own targeted cuts got another 250 by removing *content*, which is a judgment about what earns its
place in front of my pod and not something I wanted delegated. The rule I would apply from the start
next time: **if the figure prints it, do not say it.** Say what the figure cannot — why it matters,
what it rules out, what to do about it.

I stopped short of the structural cuts I was offered. **My pace is an unmeasured variable** — at 170
wpm the deck runs 9:00 and needs nothing; at 130 it runs 11:14. Removing load-bearing slides against
an estimate is how you delete the wrong thing. The measurement that settles it costs two minutes and
is the first item in next week's list.

**The timing table had been lying by 1:45.** It read 11:00; measured against actual word counts it was
12:45. Five slides kept a stale budget after their prose was written — slide 6 was labelled 0:30
against 66 seconds of speech. Each slide's budget was updated when written, but slides written before
I started that habit never got revisited, and the running total inherited the error. **The table is
now derived from the file, not maintained by hand**, with a note to re-derive rather than edit a cell.
A trim planned against a fake baseline would have left me two minutes over on the day.

### Verification and repository hygiene

Everything written into `CLAUDE.md`, the script and the deck over the preceding days was a **dry-run
prediction** — code executed outside the notebooks, never inside them. Running notebooks 06, 08 and 16
was the first check of whether any of it was real. **It all held**: the confidence signal at +0.484 /
+0.577 with 33 / 35 SD controls, the quartile splits, the within-region checks, Klamath's four
seasons, the 36-of-986 counterexample, the four-rung ladder, and the flat alpha sweep identical to six
decimals. Nothing needed correcting.

The check I am gladdest we built is the one **inside** notebook 16: its ladder cell asserts all four
rungs against notebook 08's published numbers and fails loudly on drift. It printed *"cross-check vs
08_human_cause.ipynb: all four rungs match"* — two independently written code paths agreeing on live
data, not one path repeated. It has now paid off twice, once catching a NaN-handling bug that only
existed in the figure path.

One apparent discrepancy that is not one: the script says slide 3's tiles are on 3,949 held-out cells
and notebook 06 prints 3,941. Different populations, both right — the confidence work additionally
requires ≥2 prior same-season observations to compute a dispersion, so it loses 8 cells. Worth
recording because it is exactly the kind of thing that looks like an error under questioning.

Two hygiene items closed, both of which were live hazards rather than untidiness:

- **`src/build_deck.py` deleted.** Of its 88 headline and note strings, **two** still matched the
  script. It carried both cut slides, the pre-retitle title, and the retired numbering. A runnable
  script whose stated purpose is building the deck is worse than a stale document — the filename
  invites exactly the command that destroys the deliverable. Git holds the code; `final_script.md`'s
  header records why it is gone.
- **The PowerPoint lock file explained the deck reversion.** A committed `~$*.pptx` means the deck was
  open and being written to while the repo was being changed underneath it — which is the mechanism
  behind the discovery that the deck had silently drifted back to a pre-edit state with **all
  eighteen notes panes stale**. Had I recorded the dry run before that was caught, I would have been
  reading week-six text off the presenter screen. Lock files are now gitignored, and the plan says to
  re-run the git-status check at the **start of any session that edits the deck**, not once.

The deck is now reconciled to the script programmatically after every change: slide count, every
headline, all 17 figure hashes, and no empty notes panes. **That audit is now cheap enough that I
reorder without hesitating**, which was not true three weeks ago.

### Draft LLM reflection

The full record is `coursework/collaboration_log.md`, entries 7.1–7.43. Four things I would say about
the collaboration this week.

**Where it was wrong and I overrode it.** It read a figure's percentile range as though it shared the
headline's weighting when it did not, producing a tile whose 42% headline sat over a 50–79% range —
the range did not contain its own number (7.12). It asserted that natural fire concentrates more
sharply than human; measured directly, the branches **cross over** — human's worst 1% of cells hold
71% of human acres against natural's 55%, while natural's worst 10% hold 98.2% against human's 93.5%
— and the note now forbids answering "more" or "less" (7.19). And it argued to keep two slides I cut
(7.25, 7.29); on both I took the argument, disagreed with the conclusion, and it implemented the cut
with the evidence relocated rather than discarded.

**Where it caught things I would have shipped.** The timing table lying by 1:45 (7.30). A figure
printing the same sentence I had just written into the spoken closer — ten seconds of duplication I
would have delivered without noticing (7.35). And the deck having silently reverted with every notes
pane stale (7.36), found by checking rather than by being asked.

**The division of labour that worked.** It did the mechanical work — audits, syncs, word counts,
cross-reference rewrites, verification — and I made the calls about what earns its place. That split
became explicit during the length pass: its line-level edit got 216 words by removing figure
narration; my targeted cuts got another 250 by removing content. Twice it flagged that a cut I ordered
would remove something its own notes called load-bearing, then made the cut when I confirmed. **Tell
me what I am spending, then spend it** is the behaviour I want.

**The habit that paid off.** Every number in the script was a dry-run prediction until the notebooks
ran, and the standing rule was that a citation existing is not the same as the citation covering the
sentence — checking a drafted line clause by clause caught three overreaches about what a source
actually says (7.8). When the notebooks finally ran, all of it held (7.26).

## Next week's "To Do"

- **Measure the pace, then decide about cutting.** Record slide 14 alone — 100 words, the heaviest —
  against the 40 seconds 150 wpm predicts. That single measurement replaces every pace estimate in the
  timing table and decides whether any further cut is needed at all.
- **Record and post the full timed dry run** with a visible clock, plus the written self-assessment,
  and reply to podmates in writing.
- **Run the executive challenge**: pose three self-authored questions, prepare the four defaults in an
  executive voice, and capture the three toughest received questions with the answers I will give next
  time. The three I have drafted are all questions the deck can answer and none of which it answers on
  a slide — *"most fire is human-caused, so why does your deck say lightning drives the burn?"* (61%
  by count against 58.9% of acres, and a mitigation budget is sized against acres), *"you are telling
  me five things did not work — what did I pay for?"*, and *"if we treat the hexes you rank, how many
  acres do we save?"* (no — a targeting claim, not an efficacy one).
- **Revisit the slide 9 sequencing question with fresh eyes.** Moving it beside slide 6 drops the deck
  from four target flips to three at no structural cost. Deferred deliberately until after a delivered
  run, when it will be clear whether the flips actually cost the audience anything.
- **Fix the point attribution of large unperimetered fires.** Still designed and not built: impute a
  circular burn of the correct area from the ignition point and distribute it with `hex_burn`'s
  existing weight machinery. **2,710 point fires over 1,000 acres carry 8.9% of all acres**, each on
  one cell, and 23 assign more than a full hex, including the record's 606,945-acre maximum at 971% of
  a hex. Two things to carry into the build: fires elongate along wind and terrain, so a circle errs
  directionally in a product that sites work by location; and rebuilding `hex_acres_res5.parquet`
  invalidates notebooks 13–15 and every acres figure in the deck. Rank statistics mean no finding
  moves, which is why it has stayed deferrable.
- **Add the three missing data sources to `literature/literature.md`** — MTBS (Eidenshink et al.
  2007), TerraClimate (Abatzoglou et al. 2018), MODIS MOD13A1 (Didan 2021). The new slide 16 cites
  them; the literature review does not yet list them.
- **Test whether same-day conditions — wind, timing, suppression availability — predict which igniting
  natural hexes escape.** The one question the W6 nulls leave genuinely open, and a different data
  requirement rather than a tuning exercise on the current panel.
- A hyperparameter search on the booster remains the last untried rung on the Human branch, and the
  flat alpha sweep makes it unpromising — which is why it is last.

## Resources (optional)

- W7 assignment: `coursework/W7/assignment.md`
- W7 talk script (authoritative): `coursework/W7/final_script.md`
- W6 status report: `coursework/W6/MSDS696_W6_Status_Report.md`
- Short, K. C. (2022). *Spatial wildfire occurrence data for the United States, 1992–2020* (6th ed.).
  USDA Forest Service Research Data Archive. https://doi.org/10.2737/RDS-2013-0009.6
- Eidenshink, J., Schwind, B., Brewer, K., Zhu, Z., Quayle, B., & Howard, S. (2007). A project for
  monitoring trends in burn severity. *Fire Ecology*, 3(1), 3–21. (MTBS burn perimeters,
  https://doi.org/10.5066/P9IED7RZ)
- Abatzoglou, J. T., Dobrowski, S. Z., Parks, S. A., & Hegewisch, K. C. (2018). TerraClimate, a
  high-resolution global dataset of monthly climate and climatic water balance from 1958–2015.
  *Scientific Data*, 5, 170191.
- Didan, K. (2021). *MODIS/Terra Vegetation Indices 16-Day L3 Global 500m SIN Grid V061* (MOD13A1).
  NASA EOSDIS Land Processes DAAC.
- U.S. EPA. *Level III Ecoregions of the Conterminous United States*; *Level III Ecoregions of Alaska*.