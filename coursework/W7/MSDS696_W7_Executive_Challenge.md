# Executive Challenge

| Name | | Week / Date | |
| --- | --- | --- | --- |
|  Craig Rudman |  |  Week 7 / 2026-08-20 |  |

## Project title
Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation

## Audience

A **state or regional fire-agency planner** deciding, before the season opens, where to concentrate a fixed prevention and mitigation budget.

## The three challenges

### Challenge 1

> You have told me five things did not work. What does the agency have at the end of it?

Slides 10 through 13 are four consecutive negative results, and slide 13's figure plots no data at all. Roughly two of the ten talking minutes go to things that failed. Delivered in a block, the nulls read cumulatively, and a listener tracking the spend hears a project that did not produce.

**Answer.** Three products, and none of them depends on the covariates that failed. The first is a ranked list of where to site mitigation work, at a scale of about ninety-seven square miles per cell. It beats the national average, an even split, and every covariate-assisted version I tested, and the same test on shuffled data scores effectively zero, so the ordering is real and not an artifact of the scoring. The second is a ranked cause profile for each region and season, so prevention effort goes at the causes that drive the acres in that region, rather than the ones that start the most fires. The third is a worklist of the region-seasons where the most burned acres will go unattributed next season.

The five negative results are a separate kind of return. I tested drought and fuel-density data as predictors of where fires start, on both branches, and the best gain was four thousandths on a zero-based axis. That is a procurement finding: those feeds do not need to be bought, built, or maintained for this purpose. The reason is measurable rather than a guess — strip out which cell you are looking at and the drought correlation halves, from −0.137 to −0.073, and the vegetation correlation halves as well. Those covariates identify dry places, and history already knows where the dry places are.

### Challenge 2

> If we treat the ground you rank, how many acres do we save?

Slide 17 recommends siting pre-season work by ignition, which is an instruction to spend money on specific ground. Nothing in the project measures what a treatment achieves — there is no before and after, no control, no counterfactual. The claim is targeting, not efficacy, so the number this question asks for does not exist in the work.

**Answer.** I cannot give you that number, and any number I did give you would be invented. Measuring acres saved requires treating some ground and not treating comparable ground, then comparing outcomes. This project has no treatment, no control, and no counterfactual — it observes twenty-nine years of the federal fire record and predicts what the next season looks like.

What the work supplies is the input that an efficacy estimate requires. Fuel treatment, defensible space, and pre-positioned suppression are all sited works: they pay off only if fire arrives where they were placed. A cell that ignites at all is about twenty times more likely to produce a thousand-acre fire than one that does not, so ranking ground by ignition puts the work where fire is most likely to arrive. That is a necessary condition for a treatment to return anything, and it is not a sufficient one. Your own people can estimate what a treatment achieves per acre. What they did not have is a defensible order to spend in.

### Challenge 3

> A quarter of your records have no cause. You built a cause model on data that is missing the cause. Why isn't that fatal?

The missingness is not evenly spread across regions, which leaves open whether it distorts the regional cause contrast the deck is built on.

**Answer.** The missing quarter is not dropped and it is not imputed. It is one of the three classes the model predicts, alongside Human and Natural, on a denominator of total acres so the three shares sum to one. A region-season's predicted Unknown share is a statement about the quality of that region's records, which is what makes the third product possible at all.

On whether it distorts the regional contrast: the missingness runs against the deck's main claim rather than manufacturing it. Missing share correlates negatively with Natural share across ecoregions, about −0.64 — the gap concentrates in low-Natural, human-dominated country. The unattributed acres are therefore not hiding inside the Natural class, so the claim that lightning drives most of the burn is not an artifact of missing cause, and the Human share of 22.7 percent is a floor rather than an estimate. If those unattributed acres were resolved tomorrow, the Human share would go up, not down.

Two limits I hold to because of this. Cause is reported as shares rather than counts, so a region with poor reporting does not look like a region with little fire. And the seasonal pattern is clean, while the regional pattern is directionally reliable with its magnitudes caveated. What I have not established is why attribution fails where it does — the pattern is agency-shaped, and identifying which reporting streams drive it is open work.

