# W6 Talk Notes — plain-language framings and anticipated questions

Working notes for the practice talk and the W8 final. **Not a facts file.** Every number here lives
in `CLAUDE.md` or a notebook; what is collected here is *how to say it* and *how to defend it*.
If a figure here disagrees with `CLAUDE.md`, `CLAUDE.md` wins.

---

## The one-line compression

> Where fires start is a property of the place, and the place's own history describes it better than
> any measurement of the place does.

Resist the shorter version — *"fires happen where the fuel is."* It is wrong in a way the results
specifically contradict: fuel state added **+0.004** to ignition prediction. The correct compression
is **fires happen where fires have happened**. Fuel is one of several permanent things that make a
place a fire place; the history encodes all of them at once, which is why adding fuel separately
buys nothing.

Two refinements that must survive any compression:

- **For human fire, fuel is close to irrelevant.** Human ignition is the most predictable surface in
  the project because people are where roads and houses are. That is infrastructure, not fuel.
- **Fuel governs spread, not ignition — and only jointly with dryness.** Wet heavy fuel will not
  carry fire; dry bare ground has nothing to burn. Neither NDVI nor climate works alone.

---

## Explaining raw vs. within-hex, without jargon

The single hardest idea in the talk, and the one that makes the nulls a *finding* rather than a
failure. Say it as two questions, not as two correlations:

- **Raw (+0.228 for NDVI):** *do greener hexes have more fires than browner hexes?* Yes, moderately.
- **Within-hex (+0.098):** *when a hex is greener than its own normal, does it have more fires than
  its own normal?* Barely.

The first question is answered by **which hex you are looking at**. The second is answered by
**which year it is** — and a forecast needs the second. The drop from +0.228 to +0.098 is the
signal leaking away when you stop being allowed to identify the place.

Then the punchline: **persistence already knows which hexes are fire-prone**, because it is built
from each hex's own history. The covariate arrives carrying information the baseline has already
used.

Drought is the same story with a flipped sign: pdsi −0.137 raw, −0.073 within-hex. "This is a dry
place" is strong and already known; "this is a dry year *here*" is weak.

---

## Saying the 73% without saying something false

The beat-3 tiles show **73%**, and the sentence that comes naturally — *"a region's own history is
right 73% of the time"* — is wrong. Say one of these instead:

> **"About three-quarters of the mix lands on the right cause."**
>
> **"On average, 73% of the predicted composition falls where it should."**

**Why the natural phrasing is wrong.** 73% is an accuracy derived from the *magnitude of the error*,
not from counting hits and misses. Nothing is being scored right or wrong: for each region-season we
take the absolute error on each of the three shares, sum them, halve it (that is TVD), and subtract
from 1. What is left is the fraction that was not error. It belongs in the same family as a mean
absolute error, not in the family of classification accuracy — so there is no "of the time" to
attach it to.

What makes this particular error magnitude readable as a percentage is that the three shares are
constrained to sum to 1. On a composition, one minus the error *is* the overlap. A plain MAE on
unconstrained numbers would not give you "share placed correctly."

Worked example, if pressed. A region-season actually burns 70% natural / 20% human / 10% unknown and
the model predicts 60/30/10. The overlap is 60 + 20 + 10 = **90%** — that single prediction is 90%
correct, neither a hit nor a miss. Average that overlap across 3,949 held-out region-seasons,
weighted by acres, and you get 73%.

**The trap: there is a second number that is almost identical and does mean "of the time."**

| number | what it is |
|---|---|
| **73.4%** — what the tiles show | average share of the composition placed on the right cause (1 − TVD) |
| **72.7%** — top-1 agreement, notebook 06 | how often the single *leading* cause is named correctly |

They are 0.7 points apart, so "73%" is ambiguous between them and an audience will hear whichever
one the sentence implies. Only say *"names the leading cause correctly about 73% of the time"* if the
slide on screen is showing top-1 — otherwise the words and the figure are measuring different things.

**If someone asks what TVD is.** It is the share of the predicted mix sitting on the wrong cause;
the tiles show one minus that. On a three-way split, one minus TVD is exactly the overlap between
predicted and actual — which is why "share placed on the right cause" is literal rather than a
convenient gloss.

---

## Crossing into the hex grain (beat 7)

Beat 7 is the deck's only change of grain, and three things change at once: the unit goes from 105
ecoregions to 36,234 hexes, the target goes from a composition of burned acres to a count of
ignitions, and the answer goes from shares to counts. The headline announces the first — *"but not
at ecoregion scale."* The other two have to be said.

**The line to say, roughly:**

> Everything so far has been a whole ecoregion — one number for an area the size of a small state.
> That is the right scale for deciding *what* to target, and the wrong one for deciding *where* to
> put anything. So from here the map breaks into cells of about sixty thousand acres, and the
> question changes with it: not how much will burn, but where fires start.

**Why the target change matters enough to say out loud.** The rest of the deck is about acres — that
is what the ranking is built on and what makes the profile a planning product. Beat 7 is not an acres
model, and if that goes unsaid the audience will read the capture curve as "32% of the burn under 6%
of the ground," which is a much stronger claim than the one being made and is not supported. It is
32% of the *starts*. Beats 10–11 then show why the distinction is load-bearing: acres have a tail
that starts do not.

**If someone asks why not just do acres at hex grain.** We do — that is beats 10 through 14. The two
targets need different geometry. An ignition is a point and the record stores it correctly, so
counts come straight from the raw points. Acres are an area, and a fire bigger than one cell has to
be spread across the cells it actually covered, which needs the MTBS perimeters. Using points for
acres would put a 600,000-acre fire on one 62,000-acre cell — a defect we found in W6 and are fixing
in W7.

---

## Delivering the concession (beat 15)

The hinge of the talk. Beats 10–14 are five slides of what did not work; beat 16 starts the recovery.
Beat 15 has to make the null *force* the reframe rather than sit next to it — and since the rewrite,
the headline does most of that work: **"Siting needed a finer place. Size needs a finer moment."**

**The line to say, roughly:**

> Remember what we did to make siting work: the region was too coarse to put anything anywhere, so
> we dropped down to a hex. This is the same problem on the other axis. We asked how big a fire gets
> over a whole season, and a season is too coarse a unit to answer that — what makes a fire run is
> the wind on a particular afternoon, whether crews were already committed, what time of day it
> started. We could not test that here, because same-day data is a different project. But the shape
> of the failure tells you where to look.

**Say "before the season" whenever the claim is stated as a null.** It is what keeps it bounded.
"Megafire size is unpredictable" is a much bigger claim than anything measured here and one a fire
scientist in the room could fairly challenge; "not forecastable before the season" is exactly what
was tested.

**Why the headline changed.** It used to read "Megafire size is not forecastable before the season.
Stop targeting it." That is a null plus an instruction, and it left beat 16 looking like an unrelated
consolation. The grain framing turns it into a *diagnosis* — and a diagnosis points somewhere. It
also lets beat 7 pay off twice: the audience has already lived through one grain drop and watched it
work, so the second one arrives as recognition.

**The instruction is not lost.** "Stop targeting it" now lives in the BLUF and beat 19, and beat 16
supplies the alternative one slide later. If the room needs it said aloud here, say it as the last
sentence rather than the headline.

**Do not apologise for the null.** Five ablations, a shuffled control at 26.6 SD, and a gain that
landed in the wrong deciles is a thorough negative result. The project's own method commitment says
*a null is publishable*.

**If someone asks "did you try hard enough?"** — the honest answer has two halves and both are good:
pre-season data was tried hard, same-day data was not tried at all. The second half is the open
question, not a gap in the work.

**If someone asks whether more data or a better model would fix it** — possibly, but not *pre-season*
data, which is what a planner has in hand when the decision gets made. The constraint is the decision
timing, not the algorithm.

**If someone notices the pattern repeating** — they are right, and it is worth conceding warmly. The
same lesson has turned up four times: W4's pooled climate null (real signal, wrong grain), beat 12's
"dry places, not dry years," beat 7's region-to-hex drop, and now this. Every one is a grain
mismatch. That is the closest thing this project has to a general finding.

---

## Describing the shuffled control (beat 8)

**The one-liner.**

> **Same numbers, wrong places — and the prediction stops working.**

**The sentence that makes the control obviously fair — lead with this.**

> **I am not changing how many fires I predict. I am only changing where I say they will be.**

The forecast has two parts: how much fire the region gets, and where in the region it lands.
Shuffling holds the first completely fixed and destroys only the second, so the collapse is
attributable to siting alone.

**The ~30-second version, as prose.**

> The obvious objection to a correlation is that the model might be picking up something about the
> *numbers* rather than something about the *ground*. So I ran a control.
>
> I kept every number the forecast produced and dealt them out to the wrong hexes. The region's
> total is unchanged — same values, same spread, same everything a statistic would see. The only
> thing I broke is which hex each number belongs to.
>
> The orange line is the forecast: places I said would start more fires did start more fires. The
> grey line is those same numbers in the wrong places, and it is flat. The hex I told you would
> start five fires burns the same as the hex I told you would start none.
>
> So the skill is not in the numbers. It is in knowing which place they belong to.

**If pressed on the detail.**

- *What is each dot?* Every held-out hex-season, sorted by prediction and grouped into twenty
  equal-sized buckets. Each dot is one bucket: mean predicted against mean observed. Bucketed
  because 84% of cells have zero fires — 1.6M raw points is a black smudge on the origin.
- *What is the dashed line?* Perfect calibration. Say two fires, two fires happen, you sit on it.
  The forecast runs just below — consistently over-predicting a little, which is fine, because the
  order is what a planner uses.
- *Isn't the shuffled line still above zero?* It sits at about 0.4, which is the average across all
  hexes. That is the point: the same answer everywhere, because a shuffled prediction carries no
  information about the specific place. **Flat, not low.**
- *How much does shuffling cost?* Correlation +0.53 → +0.0002. And the error gets *worse than making
  no prediction at all* — MAE 0.77 against 0.70 for guessing the average everywhere. A confident
  wrong answer costs more than admitting you do not know.
- *Why "shuffled" and not "random"?* Because random would be a weaker control. Random noise changes
  two things at once — the values *and* the pairing — so if it fails you cannot tell which caused
  it. Shuffling changes exactly one thing. It also lands differently on a skeptic: "random" invites
  *of course noise does not predict fires*, while "shuffled" invites *wait, those are the real
  numbers in the wrong places* — which is the realisation the figure exists to produce.
- *Was the random control run too?* Yes, separately in `12_hex_ignition_baselines.ipynb`: rho −0.001
  against shuffled's +0.0006. The two land in the same place, and that is itself the finding — once
  the pairing is broken, the predictions carry no more information than noise.

**The phrase to avoid: "the model is accurate."** The line runs below the diagonal; it under-predicts
the busiest hexes. What it does well is *order* them, which is a different claim and the one the
product actually needs. Say instead:

> **It ranks well. It does not promise counts.**

---

## Anticipated questions

### "So if we treat those hexes, we cut the burn?" — the one over-claim to refuse

**Say no, and say it plainly.** Nothing in this project measures what a treatment achieves. There is
no before/after, no control, no counterfactual — only where fire is likely to arrive. The gate result
says igniting hex-seasons are **22.8x** more likely to produce a 1,000-acre burn. It does *not* say
that working those cells makes the burn smaller.

The distinction to hold:

| what the deck supports | what it does not |
| --- | --- |
| **targeting** — if sited work is going to happen somewhere, this ranking says where fire is most likely to arrive | **efficacy** — that the work reduces ignitions, severity, or acres |

This is the project's own working agreement: *never assert current fire policy or practice; ground
every claim in observation.* Whether fuel treatment reduces severity is a real literature with real
numbers — Davis et al. (2024) is the meta-analysis, reporting roughly 62–72% severity reduction for
thinning-plus-burning — and it is **separate evidence from someone else's study**. Cite it if asked;
do not fold it into this project's findings.

The clean formulation:

> Fuel treatment, defensible space and pre-positioned crews are all **sited** works. Whether they pay
> off depends on whether fire arrives there — that is a necessary condition, not a sufficient one.
> This ranks the ground by that condition. It does not tell you what the treatment then does.

**The second half of the caution: the return decays fast.** "Big return on predicting ignitions" is
true only at the top of the ranking. 32% of starts sit under 6.1% of the ground — a **5.23x** lift —
but 90% of starts needs **77.8%** of the ground at **1.16x**, which is near-uniform treatment. If
someone reads the ignition surface as "we found the 6% that matters and the rest is safe," correct
it: the ranking concentrates return, it does not eliminate the tail.

### "But doesn't a cell with more ignitions carry more risk?" — beat 17's counter-argument

Yes, and it still does not license ranking on count. Three answers, in the order they land:

**The rate does rise.** A cell with 11–20 natural ignitions has a **19.1%** chance of a 1,000-acre
burn against **5.4%** at a single ignition. That is real and it is not the objection being dodged.

**But risk per ignition falls, steadily.** 0.054 at one start down to **0.014** at 11–20. A
twenty-fold increase in ignitions buys about 3.5x the escape probability. Cells that ignite often are
cells where fires get *caught small* — the high-ignition/low-acre regime, which usually means access,
detection and crews are already close.

**And the fires were not there.** Of 2,724 large-fire cells in the held-out years, **49% had exactly
one ignition** and 70% had two or fewer. This is the one that settles it, because it is about where
the consequential burns actually were rather than a conditional rate. Rank on expected count and you
deprioritise the ground that produced half of them.

**One more, if pressed on whether count is useful at all:** ignition count ranks burned area *worse*
than the hex's own burn history does — Spearman +0.253 against +0.357. It is not a better acres model
either.

### "Isn't this just descriptive analytics?"

No — every headline number is scored on **held-out future seasons** (train `< 2010`, score `>= 2010`,
forward-chaining). A description does not have a test set. The confusion is that the winning model is
simple: a k=7 trailing mean *feels* like a summary statistic, but it is a forecast whose answer could
have been "no" and was tested against shuffled controls that came back at ±0.003.

What is genuinely not descriptive: five covariate families tested against a baseline with a measured
mechanism for their failure; a permutation control separating spatial skill from luck; a verified
gain that was then shown to be useless by decile; and a bug caught because its implied error was
physically impossible.

**Where the question has teeth — concede this.** The learned rungs lost. Gradient boosting lost on
Tier 1, on Human sub-cause, and on hex ignition. If "predictive" means "a trained model beat the
baseline," that is not what happened. Five well-tested nulls and one verified-but-unusable gain is
what happened, and `CLAUDE.md`'s standing rule is that a null is publishable.

### "Did you choose your covariates poorly?"

Partly fair, and the honest answer is a **scope** statement rather than a defence.

What rules out the easy explanations:

- **Not the estimator.** A GBM given *only* the persistence feature reproduces the persistence floor
  almost exactly. The model class is capable; it is not underfitting.
- **Not the modelling.** The raw-vs-anomaly decomposition is measured *before* any model is fit, so
  the failure cannot be blamed on a modelling choice.

Where the criticism lands:

1. **The covariates are all fuel-and-moisture.** Drought, prior burn and greenness are three readings
   of roughly one thing. That is one hypothesis tested three ways, not five independent shots.
2. **Never tested: ignition *sources*** — lightning strike density, road and powerline proximity,
   population — **or same-day weather.** For the Human branch especially, fuel has no mechanism to
   move where roads and houses are.
3. **Seasonal aggregation may be destroying the signal.** A season-mean PDSI cannot represent the
   week that matters; fire weather is episodic.

Fuel state was the defensible *first* hypothesis. "We chose narrowly" is fair. "We chose poorly" is
not.

### "Why not a CNN on satellite imagery?"

Because the project already ran the experiment that decides it. A CNN would be a better extractor of
the same signal NDVI extracts — vegetation state — and that signal was measured to be
**cross-sectional**: it identifies which place this is, which persistence already knows perfectly.
Better feature extraction cannot recover information that is not in the input.

Where a CNN *would* have a real shot: **burned-area magnitude**, where fuel state does pay off, and
where spatial *texture* — fuel continuity, patchiness, edges — is exactly what a hex-mean throws
away. That is a defensible proposal. Two constraints to state with it: the test population is 7,799
cells in six ecoregions (thin for training from scratch), and the tail is the part that matters,
where nothing so far has moved 855× → 868×.

### "What about demographics / road density?"

A genuinely different hypothesis, aimed at the right branch — human ignition is about people, not
fuel. But it has the **same structure** as everything that failed: where people live is a *place*
fact, stable across seasons, and human ignition is already the most predictable surface in the
project precisely because that geography does not move.

There is a cheap test before any build: correlate the candidate against human starts raw and
within-hex. If the within-hex correlation collapses the way NDVI's did, persistence already has it.
TIGER road data is also effectively **static** at hex scale, so it could only ever be a
cross-sectional feature.

### "How do you know it's the roads?"

**I don't — that is an inference, and it should be spoken as one.** What is measured is that human
ignition persists spatially better than anything else in the project (Spearman +0.53 all-season,
+0.59 in spring, shuffled controls within ±0.003 of zero). Roads and settlement are the *explanation*
offered for that persistence; no road layer was ever built and joined to the hex grid.

Say "consistent with," not "because." The defensible chain is: human ignition is highly stable in
space; fuel state does not explain it (five nulls, and fuel has no mechanism to move where people
are); infrastructure is the obvious remaining candidate, untested here.

**Why it was not built.** TIGER road density is effectively **static** at hex scale, so it could only
ever be a cross-sectional feature — and cross-sectional is exactly the structure that failed five
times. The cheap check before any build is the raw-vs-anomaly test: if the within-hex correlation
collapses the way NDVI's did, persistence already carries it. Expected outcome is a sixth null, which
would *support* the interpretation rather than undermine it: roads would be shown to carry the same
place-information the ignition history already holds.

### "Did you give the model a fair chance, or is the baseline just cheap to beat?"

This is the right challenge to beat 6, and the third bar is the answer. Two learned rungs were
tried, not one:

- **Gradient boosting on region character** — 36% top-1 against the floor's 54%. Fair criticism
  available here: the model never saw the cell's own human sub-cause past, only its Tier-1
  character. Losing is unsurprising.
- **The same model handed that history as a feature** — 47.5%. It got the *exact quantity the floor
  averages*, plus everything else, and still finished 7 points short of simply taking its mean.

So the comparison is not "persistence versus a model that never saw the data." The information was
in the feature set and the model could not use it as well as arithmetic did. With 3,846 training
cells and 11 correlated targets there is not enough signal to learn a better function of the history
than its average.

**Concede the part that is fair.** The rungs were run once at the project's standard
`SimplexRegressor` settings and not tuned. A hyperparameter search might close part of the 7-point
gap, and nothing in the result rules that out. What it does rule out is "you never gave it the right
features."

### "Doesn't Tier 1's error compound into Tier 2?"

**For the ranking, no — and the reason is structural rather than lucky.** Tier 1 predicts one number
for a region-season: the human share of its acres. Tier 2 predicts eleven numbers that are shares
*within* Human. Composing them multiplies all eleven by that single scalar, and multiplying a vector
by a positive constant cannot move its largest element. Measured end to end on the 3,850 joined
held-out cells, top-1 is **0.4619** — identical to Tier 2 scored on its own.

So the deliverable that is actually ranked does not inherit Tier 1's error at all.

**For the acre level, yes, fully.** Predicted human acres run a median 1.01x off but with a wide
spread: **2x low at the 10th percentile, 8x high at the 90th.** That is the number a planner would
read off a profile, and it carries Tier 1's error whole. This is the measured version of what the
project summary already says — the order is reliable, the acre figures are not.

**Do not quote 54% as end-to-end.** Beat 5's 54% is the Tier 2 floor on Tier 2's own population.
The end-to-end figure is 46.2%, on the smaller set of cells where both tiers produce a prediction.
Different populations, both correct for what they claim.

### "Is there a Bayesian angle here?"

The hierarchy is already a factorization of the chain rule:

> P(cause) = P(class) x P(sub-cause | class)

Tier 2 is literally a conditional distribution, and three things follow.

1. **That factorization is why the ranking survives.** Conditioning on Human normalizes away Tier
   1's scale, so uncertainty in P(Human) does not propagate into the conditional ordering. The
   answer to the compounding question above is a consequence of the structure, not a happy accident.
2. **The global-prior tiles are priors in the Bayesian sense.** The 42% (Tier 1) and 16% (Human)
   baselines are what the population prior gives with no regional evidence; the history tiles are
   the posterior after conditioning on the region. The lift between them *is* the information a
   region's own history carries.
3. **What is genuinely missing: no uncertainty is propagated.** Every prediction is a point
   estimate. A Dirichlet over the composition would give credible intervals, and the acre level —
   the quantity with 2x-8x spread — is exactly where an interval would be worth more than a number.

That last point is the honest "what I would do next," and it is stronger than the generic version
because it comes with a reason to expect it to matter in one place and not the other: the ranking is
scale-invariant and does not need it; the level is not and does.

### "Isn't 73% just a coin flip with three options?"

No, and the third tile is the answer: an uninformed even split scores **52%**, not 33%. A three-way
guess does better than a third because two of the three classes are usually small, so spreading mass
evenly still overlaps a lot of the truth. 52% is the floor to beat, and history clears it by 21
points.

The tile that carries more weight is the middle one. **The national average mix scores 42% — worse
than guessing.** Applying the country's overall composition to a specific region is actively
harmful, because the national number is dominated by a handful of very large natural-burning regions
and describes almost no region in particular. That is the map from beat 2 reappearing as forecast
error, and it is the strongest argument in the deck for doing this per region at all.

### "So nothing predicts megafires?"

Narrower than that, and the distinction is what leaves the question open: **pre-season** covariates
do not predict which igniting hexes escape. Same-day conditions — wind, timing, suppression
availability — are a different model with a different data requirement, and they are untested.

---

## Delivery notes

- **If they remember one thing:** site the work against where fires *start*, because that is the one
  stage of the escalation this data can see in advance.
- **Do not oversell the gate.** It is necessary, not sufficient: 93% of igniting hex-seasons still
  produce nothing large. It narrows the field; it does not identify the fire.
- **Lead the covariate arc with what it buys, not what it cost.** Beats 13–15 are a contrast — fuel
  says nothing about *where*, something real about *how much*, and nothing about the fires that
  matter. Told as three failures it is a third of the deck spent apologising.
- **Never claim what agencies currently do or fund.** Every claim is grounded in what the data shows.
