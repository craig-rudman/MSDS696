# W5 Practice Talk — Present One Visual

**Figure:** `img/w5_v1a_one_fire.png` — one fire: the point the record stores vs. the area that burned
**Audience:** non-technical executives (a state/regional fire planner and the person who funds them)
**Target:** ~2 minutes. One message: *we fixed* where *— now fund the imagery that tells us* when.
**The ask:** executive support to acquire pre-season fuel-condition satellite imagery. The figure is the setup; the ask is the payload.

Beat labels are structure only — say them as prose, don't announce them.

---

## Describe

This is one wildfire. Tepee Springs, central Idaho, 2015.

The orange dot is everything my dataset knows about where it was — one latitude, one longitude. The blue shape is what actually burned: 95,709 acres, mapped from satellite.

The faint outlines are the grid cells I analyze on. Each holds about 62,494 acres. So this fire is half again bigger than the cell it's filed under, and it crosses into a second one. It cannot fit where the record puts it.

And it's not the freak case. It's the *median* fire among those with satellite perimeters that cross more than one cell — which is two thirds of them.

## Interpret

So the record tells me *how much* burned, but not *where* — and you can't prevent lightning, so where is the only useful answer. Fixing that took the grid you're looking at: acres spread across the cells a fire actually covered, 0.6% of fires carrying **82% of the acres**.

But that fix only exposes the harder question — *when*. History tells me which places burn. It doesn't tell me which season is the bad one; how much a place burns is almost uncorrelated with how much it burned before. The past is a map, not a warning.

## Implication

**So I'm asking for investment in the effort to acquire satellite imagery of fuel condition — how much fuel has built up, and how dry it is, going into the season.** That's the missing signal, and it's the one thing we don't already have.

The grid is what makes it possible. That imagery only comes gridded — it could never have been laid over the old irregular regions, and now it overlays these cells directly. Burned area and fuel condition finally sit on the same row.

That's real work — imagery access, processing, a season of engineering — which is why I'm asking rather than just doing it. And if fuel condition turns out not to predict the bad seasons, that's a real answer too.

---

## Delivery notes

- **If they remember one thing:** *fund the fuel imagery.* Not "the record stores points" — that's the setup. Land the talk on the ask and don't trail off after it.
- **Don't say** hex, res-5, H3, MTBS ID, foreign key, NDVI, ablation, or Tier 2. Say grid cell, satellite perimeter, "a link in the record," "how much fuel and how dry it is."
- **Two numbers, that's all.** **0.6% of fires carry 82% of the acres** (the fix was cheap) and **how much burns one year barely predicts the next** (why imagery is needed). Everything else is texture.
- **If running long,** compress Describe — the picture is doing that work anyway. Do not cut the ask or the "past is a map, not a warning" line.
- **Say the cost honestly.** "A season of engineering" is the estimate; don't inflate it into a crisis or shrink it into a favor. An ask that sounds free reads as one nobody needed to approve.
- **Chart honesty (the graded check):** no axes to distort — it's a map. Both shapes are true geographic scale on one projection, so the dot-vs-area comparison is literal, not schematic. The 95,709 acres is the published MTBS figure, and the 62,494-acre cell size is spoken, so the size claim is auditable rather than eyeballed.
- **Pod Q — "isn't 0.6% of fires a tiny sample?"** It's 0.6% of *rows*, 82% of *acres*. The target is acres, so acre coverage is the coverage that matters.
- **Pod Q — "why not use satellite perimeters for everything?"** They only exist for large fires, and only within the MTBS coverage window. The point records carry the cause attribution — the other half of the project.
- **Pod Q — "isn't burn history already a fuel proxy, and free?"** Yes, and it's in the plan as its own rung — the imagery has to beat it, not beat nothing. But a place that burned recently looks fuel-poor to the imagery *because* it burned; that's a scar, not a forecast. Measuring fuel directly is the point.
- **Pod Q — "what if the imagery doesn't help?"** Then that's the finding, and it's worth knowing: fuel condition carries no extra signal at this grain and this lead time. The comparison is built to show either answer, which is why I can ask for it without promising a win.

## Self-assessment (post with the recording)

**What I was going for.** An ask, not a status update. The figure earns the right to make it: the record stores a point, the fire burned an area, and one picture shows that gap without me asserting it. Fixing *where* is what makes the real request — pre-season fuel imagery, to get at *when* — both possible and obviously next.

**What worked.** The figure survives without narration; the two annotations carry the argument. Using the median multi-cell fire rather than the largest keeps it honest — a cherry-picked megafire would have proved less. And I ask for the imagery without promising it will work, which I think is the more credible version of the pitch.

**What I'd fix.** The talk asks an executive to fund something on the strength of a *negative* result — that history doesn't predict which season burns big. That's an honest argument but a cold one, and I have no visual for it; the one number carrying the whole ask is spoken, not shown. If I rebuilt the deck, that number gets its own slide. The figure also needs a scale bar — the 62,494-acre cell size is currently spoken, not drawn.
