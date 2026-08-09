# W5 Plan — Executive visuals

## Objective

Week 5 is graded on **executive visuals** (60 pts, see [assignment.md](assignment.md)):

| deliverable | pts | status |
|---|---|---|
| Status Report — 2–3 polished visuals, assertion headlines, report template | 20 | visuals rendered; writeup pending |
| Practice Talk — present one visual, record, post, reply to podmates | 20 | track written; recording pending |
| Chart Redesign Activity — separate, uses D2L chart bank | 20 | done (Chart B) |

The substantive goal: show that FPA-FOD alone cannot place burned area on the
landscape, and that satellite-derived perimeters can.

## The confound

FPA-FOD gives a **pinpoint lat/lon** per fire, but `FIRE_SIZE` describes an
**area**. At EPA Level III grain the error stayed inside the polygon; at hexgrid
grain it dominates — a res-5 hex is ~62,494 acres, so any larger fire provably
cannot fit in its assigned cell. A naive hex-level acres target measures
point-attribution error, not fire behavior.

**The fix is in the source.** The `Fires` table carries `MTBS_ID`, a live foreign
key into MTBS burn-severity perimeters (themselves Landsat-derived):

| | count | acres | share of acres |
|---|---|---|---|
| MTBS-linked | 13,870 (0.6% of rows) | 146,891,427 | **81.6%** |
| point-only | 2,289,696 | 33,157,309 | 18.4% |

The 0.6% of fires that can be given real perimeters carry 82% of the acres. The
2.29M point-only fires average 14 acres — smaller than one hex, where point
attribution is fine. The record points at imagery through a join key it cannot
resolve on its own.

## Done

- **`src/hex_burn.py`** — perimeter→hex acre distribution. Weights sum to 1.0 per
  fire, so acres are conserved by construction; point-only fires get `w=1` on
  their containing hex.
- **`notebook/10_hex_burn_demo.ipynb`** — three PoC regions, then scaled
  **national**: 36,234 res-5 hexes across 105 ecoregions, 99.61% of acres landing
  on-grid. Acre conservation passes at both scales. Off-grid loss is coastal and
  small. Point attribution would have misplaced ~half the burned area at this
  grain; two thirds of perimeter-backed fires span >1 hex.
- **`src/w5_visuals.py`** + **`notebook/11_w5_visuals.ipynb`** — all five figures
  rendered to `img/`. V1-A and V1-B now carry their headlines, panel labels, and
  scale **in the figure**, so each reads standalone in a slide or a report; the
  remaining figures are still bare.

Artifacts on disk: `data/hex_grid_res5.parquet`, `data/hex_acres_res5.parquet`,
`data/mtbs_perimeters/`.

## The visuals (rendered — headlines to finalize)

| file | headline | role |
|---|---|---|
| `w5_v1a_one_fire.png` | *"The record says a fire happened here ... it burned all of this."* | **practice talk.** Tepee Springs fire 2015, Idaho Batholith, 95,709 ac across 2 hexes — median-size fire *among those spanning >1 hex* (two thirds of perimeter-backed fires). Larger than the 62,494-ac cell it is filed under, so "cannot fit" is shown rather than asserted |
| `w5_v1b_before_after.png` | *"We knew how much burned, but we didn't know where"* | same acres placed two ways: ignition-point vs. perimeter-distributed, BEFORE/AFTER panels, shared log scale with colorbar |
| `w5_v2_national.png` | *"A tenth of the country carries three quarters of the burning."* | national concentration, 29 years pooled |
| `w5_v2b_season_2020.png` | *"One fire season, everywhere it touched."* | 2020 alone, small/medium burns kept |

**Design constraint:** the audience is non-technical executives. These are maps —
no axes needed. Ablation ladders and sparsity plots are correct evidence in the
wrong encoding; they belong in an appendix slide.

**Status report uses two: V1-A (the gap) → V1-B (the fix).** V2/V2-B are left out
deliberately. The report is framed as an executive ask — fund the imagery arc — and
the national concentration numbers (36,234 hexes, 99.61% of acres on-grid) carry
that credibility better as one line of prose than as a third chart competing for
the same attention.

**The V3 timelapse is not committed.** `animate_national()` in
[src/w5_visuals.py](../../src/w5_visuals.py) and the V3 cells in
[notebook/11_w5_visuals.ipynb](../../notebook/11_w5_visuals.ipynb) still build it —
re-run them if a talk asset is wanted. The 4.6 MB gif is not worth carrying in the
repo for a figure the status report does not use.

## Remaining work

1. **Status report** — drafted at
   [MSDS696_W5_Status_Report.md](MSDS696_W5_Status_Report.md), on the W4 template.
   Framed as an executive ask (fund the imagery arc) with honest status prose
   around the two visuals. Scope limit stated: perimeter correction and the hex
   frame, no predictive result yet. **Remaining:** final read-through.
2. **Practice talk** — present V1-A. Track drafted at
   [practice_talk_track.md](practice_talk_track.md): Describe/Interpret/Implication
   beats, delivery notes, jargon blocklist, two anticipated pod questions, and the
   self-assessment to post with the recording. **Remaining:** record it, post to the
   pod discussion, reply to podmates via the Pod Feedback Card.
3. **Chart Redesign Activity** — **done.** Chart B (highway fatalities), four-part
   write-up plus rebuilt figure at
   [chart_redesign/w5-chart-redesign.md](chart_redesign/w5-chart-redesign.md) and
   the accompanying PDF.
4. **Doc updates** — `CLAUDE.md` (MTBS perimeter join is a new data-source fact; the
   Natural→location grain question is now partly answered),
   [collaboration_log.md](../collaboration_log.md) incrementally per the established
   cadence. (The separate `todo.md` was folded into `CLAUDE.md` in W6; it is the
   single requirements file now.)

No plan snapshot — this file is under version control, so git history is the
snapshot.

## Deferred — the imagery hypothesis

> **Superseded in part, 2026-08-04 (W6).** This section is preserved as the W5
> snapshot; two of its rungs have since been built and the target changed. See
> `CLAUDE.md` and collaboration log Entries 6.1–6.6 for current state.
>
> - **"No climate layer" was wrong even at W5.** `src/terraclimate.py` was built and
>   run 2026-07-26. Only *fuels imagery* is blocked on Earthdata/GEE credentials.
> - **The prior-burn rung is built** (`src/burn_history.py`), and hex-grain climate
>   has been re-fetched (`src/hex_climate.py`).
> - **The target changed** from acres/burn-concentration to **hex-grain ignition
>   likelihood**, which uses raw ignition points rather than the perimeters this
>   week built. The perimeter work remains load-bearing — but for the *burn-history
>   covariate*, not for the target itself.

Not started as of W5; no MODIS cache exists. Carried forward as the next arc,
unblocked by W5 grading.

> Burn history reveals *where* fire recurs but cannot anticipate *when* a
> region-season will burn big. **Pre-season fuel-condition imagery — how much fuel
> has accumulated and how dry it is — supplies the missing signal.**

Ablation ladder, if resumed:

```
persistence  ->  + climate  ->  + prior-burn (proxy)  ->  + fuel condition (imagery)
                   [failed]        [cheap proxy]            [the hypothesis]
```

- **Framing:** ranking, not magnitude. Primary metric **top-k acre capture** —
  *"we pointed at 20% of the landscape and caught X% of the burn"* — vs. a
  random-targeting reference, reported with Spearman ρ. The ecoregion work showed
  the two verdicts diverge: *which* regions carry Natural burn was predictable
  (ρ = 0.932) while *how much* was not (8.6–14× off).
- **Keep the prior-burn rung.** Imagery must beat the cheap proxy, not beat
  nothing — a recently burned hex has low NDVI *because* it burned.
- **Leakage is the sharpest risk.** Every index must aggregate over
  `preseason_months()`, ending strictly before the target season opens; a window
  overlapping the season reads the burn scar itself and produces a spectacular,
  circular result. Neighbor features must be built from **already lagged** values.
- **Missing imagery must surface as NaN**, never imputed to zero — a zero anomaly
  reads as "average fuel," a fabricated observation.
- **A null is publishable:** if imagery does not beat prior-burn, the finding is
  that fuel condition carries no additional signal at this grain and lead time.

Measured facts that shaped this framing (res-5 panel, three PoC regions):

- **Burn recurs, it does not suppress.** A hex that burned k years ago is ~1.6×
  *more* likely to burn substantially again (k=1,2,5). Fuel limitation operates at
  finer grain than a 62,494-acre hex over a season. Features must still let the
  model find either direction.
- **A burn/no-burn target would be useless.** 75% of hex-years have *some* burn,
  but the median burning hex burns 1.5 acres of 62,494; only 3.1% exceed 10% of
  the hex.
- **Magnitude is barely autocorrelated** (Pearson r = 0.072, ρ = 0.120). A hex's
  own history says almost nothing about next season's magnitude — which is the
  strongest argument that imagery would be new information rather than a proxy.

Also deferred: ignition-count target, second hex resolution (res 4 comparator /
res 6 escalation), `acres_per_ignition`, provenance and neighbor-ring features,
AK Interior as a boreal generalization test.

## Verification

- **Acre conservation** — per-fire distributed acres sum to `FIRE_SIZE`; hex totals
  reconcile to `region_season_cause.parquet`. Passing nationally.
- **No negative or NaN hex acres**; perimeter portions never exceed `FIRE_SIZE`
  after rescaling.
- **Off-grid acres accounted for, not silently dropped** (0.38%, coastal).
- **Visuals** — one message each, units stated, honest scale, single sequential
  ramp per panel.
- Student runs notebooks manually; the agent edits cells but does not execute them.
