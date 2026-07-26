# W2 Practice Talk — Script

**Format:** 60–90 sec record in D2L Video Note; this runs ~120 sec, trim if needed.
**What it must not leave blank:** the question, the stakeholder, the action.
**This week's frame:** data *fit* — why this data answers *my* question, not a nearby one.

Beat labels are for structure only — say them as prose, don't announce them.
Each **ON SCREEN** line is what the viewer sees while you narrate that beat — a shot list, not spoken.

Slides (3): **[1]** title + question · **[2]** hero season map · **[3]** so-what visual.
Assets in [`img/`](../img): `natural_share_seasons.gif` (hero), `dominant_acres_seasons.gif`,
`dominant_count_seasons.png`, `natural_share_seasons.png` (static fallbacks).

---

**[Open — what I did, with the question]**
> **ON SCREEN — Slide 1:** the two-part research question in large type; faint US map behind it. Holds while you state the question.

This week I interrogated one dataset against my research question: across contrasting U.S. region-seasons, which wildfire causes **drive the most burned area**, and do those patterns differ enough to warrant different prevention? Fit, provenance, limits, feasibility — here's what I found.

**[Fit]**
> **ON SCREEN — Slide 2:** hero animated map `natural_share_seasons.gif` — CONUS ecoregions shaded by Natural (lightning) share, looping Winter→Spring→Summer→Fall. The West **ignites deep red across summer** and cools off. Point to it as you give the swing numbers.

The dataset carries exactly the fields that question needs: cause, location, date, and size, on every fire. On a **400,000-fire sample**, the variation is really there. Natural ignitions swing from **1% of fires in winter to 44% in summer**. Across regions, the natural share runs from **under 1%** in places like the Central Appalachians to **over 80%** in the Idaho Batholith. Both halves of the question — seasonal and spatial — have real signal. That's observed, not assumed.

*(The season map on this slide is built from that same 400K sample, pooled across all years 1992–2020.)*

**[Provenance]**
> **ON SCREEN:** hero map still up (no slide change), or a plain text card: "USDA FS · FPA-FOD 6th ed. · 2.3M fires · 1992–2020."

It's the USDA Forest Service's fire-occurrence database — Short, 2022, sixth edition. 2.3 million wildfires, 1992 through 2020. It's a reconciliation of dozens of agency reporting systems, so it reflects what agencies reported, not a clean survey — and I logged those biases in the notebook.

**[Limits — the real one]**
> **ON SCREEN:** hero map still up — gesture to the **hatched** Southwest/Plains regions as you say "differential across regions." (The hatching *is* the ≥40%-missing flag, so the caveat is literally visible.)

The central risk: about **26% of records have no cause**. And it's not random. It's flat across seasons — a 3-point spread — but it swings **62 points across regions**, and the lowest-missing regions are exactly the high-natural West. So missingness could have manufactured the regional result. Because I measured it, I handle it: I report cause as **shares, not counts**, treat the seasonal signal as clean, and the regional signal as directionally reliable but caveated on magnitude.

**[Feasibility — including the product's harder step]**
> **ON SCREEN — Slide 3:** the "so-what" visual — `burn_concentration.png` (Lorenz curve; hero number "top 1% of fires drive 89% of acres"). Optional alternate: `dominant_acres_seasons.gif`, the acres-burned map whose regions recolour by season, showing the burn-leader differ from the ignition-leader.

Can I actually build the product? The product ranks causes by **acres burned, not ignition count** — and the data says that distinction matters: the **top 1% of fires drive 89% of all burn**, and in **45% of region-seasons the cause that ignites most isn't the cause that burns most**. Fire size is present on every single record, so that ranking is feasible now. Whether next-season burn is *predictable* is the modeling question I've scoped for later — but the input and the premise both check out.

**[Close]**
> **ON SCREEN — Slide 1 again** (the question), or hold Slide 3. Return to your face for the verdict.

So the verdict: the data answers the question I actually asked — and I've measured the one reporting bias that could distort it, so I know exactly where the regional signal is solid and where it's only directional.

---

## Delivery notes

- **Stakeholder blank:** the talk implies it ("warrant different prevention"). To name it outright, add ~5 words to the open: *"…a regional fire planner deciding where to concentrate limited pre-season effort."* Recommended — it's a graded blank.
- **If running long,** cut Provenance to one sentence: *"It's the USDA Forest Service database, 2.3M fires, 1992–2020, with the biases logged in my notebook."*
- **All numbers are from** `notebook/feasibility.ipynb`, built on one **400K seeded sample** (seed 696), pooled across all years — so every figure below is reproducible run-to-run and matches what's on the slides: seasonal Natural 1%→44%; regional Natural share 0.7%→84%; missingness 2.5-pt (season) vs 62.6-pt (region) spread; top-1% of fires = 89% of acres; ignition-leader ≠ burn-leader in 45% of region-seasons. The Fit beat cites the 400K sample size aloud.
