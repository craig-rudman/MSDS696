# W4 — Defend-Your-Method Activity

Craig Rudman · Week 4 / 2026-07-25

I came into this week planning to model the region-season as a flat composition over all 12 wildfire causes. Analysis of the cleaned region-season-cause data pointed me to a two-pass hierarchy instead. What follows defends the method I moved to, against the method I moved away from. My research questions and my deliverable did not change. What changed is the structure of the model that produces them, and what I do about the 18.5% of burned area that has no attributed cause. That was my largest known liability. It is now its own branch of the model, with its own deliverable.

## The research questions, restated

This document refers to my two research questions, so I'll restate them here:

- RQ1 (descriptive): Across a set of contrasting U.S. region-seasons, which wildfire causes (natural and human) drive the most burned area, and do those patterns differ enough to demand different prevention and mitigation strategies?
- RQ2 (predictive): Can a next-season cause-risk profile — the expected composition of causes for a region and upcoming season, ranked by the burned area each is expected to drive — be predicted well enough to pre-target that prevention effort?

## What the data showed

The move follows directly from a snapshot of burned area across the three coarse classes, taken over the full record (1992–2021, post-cleaning):

| Coarse class | Burned acres | Share of total |
| --- | --- | --- |
| Natural | 105.5M | 58.9% |
| Human | 40.6M | 22.7% |
| Unknown | 33.1M | 18.5% |
| Total | 179.3M | 100% |

Two facts in this table drove the redesign. First, most acres burn from a cause the planner cannot prevent. Prevention has no lever against lightning; the only lever is mitigation, and mitigation is about where fuel and exposure sit, not what started the fire. A cause-composition model is the wrong tool for that 58.9%. Second, the Unknown class is too large to ignore. At 18.5% it is nearly as large as the entire Human class, and it is not neutral noise spread evenly across the map. It is a regional data-quality signal.

Those three classes are not three slices of one problem. They are three different problems, and that is what the method reflects going forward.

## My method

I use a first-pass allocator over three classes — Human / Natural / Unknown — followed by a separate, purpose-built deep-dive for each branch. The three branches answer different questions; each has a different prediction target for a different intervention.

The first pass predicts, for a region-season, the composition across Human / Natural / Unknown by burned-area share. The denominator is total burned acres, so the three shares sum to 1.

The second pass is three heterogeneous branch deliverables.

| Branch | Question | Prediction target | Grain | Planner's intervention |
| --- | --- | --- | --- | --- |
| Natural | Where will it burn? | burned-area concentration | region-season (spatial) | mitigation siting (e.g. fuel treatment, defensible space, suppression pre-positioning) |
| Human | What starts it? | cause composition (sub-causes) | region-season × sub-cause | prevention targeting matched to the dominant human cause |
| Unknown | Where is the record weak? | attribution-quality | region-season | data-quality improvement, investing in cause reporting where the record can't support a decision |

The Natural branch drops the cause question entirely. Lightning is effectively the only natural cause in the record, so there is nothing to resolve and no prevention to target. Knowing a region-season will burn from lightning tells a planner nothing they can act on. What they can act on is location. So this branch predicts where the acres concentrate, not what starts them. That output feeds mitigation work: fuel treatment, defensible space, and pre-positioning suppression resources ahead of the season. The grain may need to go finer than the Level III ecoregion for that to be useful, which is an open question I have not settled.

The Unknown branch is not a fire cause and impact prediction at all. It predicts how much of a region-season's burned area will have no attributed cause. That number is a statement about the record, not about fire. A high Unknown share means the planner's own inputs are weak there, and the rest of the profile for that region-season should be trusted less. The deliverable is an operational recommendation: where to invest in better cause reporting so the record can support a decision. Predicting that share directly is more useful than imputing causes the data does not contain.

The Human branch keeps the original 12-cause structure, filtered to the human causes. This is the one place the sub-causes still matter, because each one calls for a different prevention effort. Arson is a law-enforcement problem. Debris and open burning is a permit and burn-ban problem. Equipment and vehicle is a roadside and right-of-way problem. Powerlines is a utility problem. Recreation is a campground and public-messaging problem. A planner cannot act on "human-caused" alone. They need to know which of these drives the acres in their region.

Every branch has to earn itself. The floor is persistence: last season's composition, carried forward unchanged. Any model I build has to beat that floor on a forward-chaining temporal split, so nothing from the future leaks into training. From there I add complexity one step at a time up an ablation ladder, and each step has to pay for itself in accuracy or it comes back out.

## The named alternative — a flat 12-cause classifier

The alternative is to model the region-season as a single composition vector over all 12 causes at once, in one fit, with no Human/Natural/Unknown split above it.

The case for it is simplicity. One model, one target, one metric, one training loop. There is far less to build, tune, document, and defend than four coupled models, and much less surface area for leakage or plumbing bugs. It answers RQ1 directly, with no coarse layer to reconstruct on top of the sub-causes. It keeps every cause on a common footing, so comparing causes across regions needs no extra work. It also avoids a real risk in my design: errors in the first pass propagate into every branch below it, and a region-season the allocator gets wrong is wrong in the deep-dive too.

The stronger version of the argument is about sequencing. Start with the flat model and find out what the base data can actually do. Build the end-to-end composition forecast and measure it against persistence. Add hierarchy only where the flat model demonstrably fails. Committing to a three-branch structure before that evidence exists is a bet that the added complexity will pay for itself, and that bet is not free.

## My defense

I decided to move ahead with the two-pass hierarchical model. The flat model gets its simplicity by treating three different problems as one, and my data already shows where that breaks.

A flat 12-cause vector has nowhere to put the 18.5% of burned area with no cause. I can drop it, which quietly rescales every share I hand a planner. Or I can keep it as a twelfth pseudo-cause, which contaminates the other eleven shares and forecasts a reporting gap as if it were fire behavior. Neither is acceptable. The first pass predicts the Unknown share directly, so the gap stays visible and the planner knows how much to trust the rest of the profile. The unknown mass belongs to Human and Natural in some proportion, and that proportion varies by region and season and shifts over time. So both resolved shares are floors, and no single correction fixes them. Predicting the Unknown share directly means I never have to guess the split.

The flat model also asks the wrong question of the Natural mass. There is one cause behind 58.9% of the acres, and the planner's only lever is where the fire burns. A sub-cause axis has no work to do there. The output that branch needs is spatial, and a composition vector cannot express it.

The cascade objection is fair, but it cuts the other way here. The first pass is a coarse three-class split, and persistence already predicts it well. That makes it the stable part of the system, not the fragile part. The hard problem is sub-cause composition, and the hierarchy isolates it in the one branch that needs it.

I grant the alternative its real virtue. If this were a description of clean labels, the flat model would be the right call, and I would use it. But my question is forward-looking, the missing-cause mass is large and not random, and most of the acres come from a cause no one can prevent. For that question the hierarchy is not extra complexity. It is what keeps each share meaning what the planner needs it to mean. The ablation ladder is the check against over-engineering: every branch still has to beat its persistence floor to earn its place.
