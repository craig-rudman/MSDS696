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

## Anticipated questions

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
