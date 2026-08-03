# W5 Plan — Executive visuals

## Objective

Week 5 is graded on **executive visuals** (60 pts, see [assignment.md](assignment.md)):

| deliverable | pts | status |
|---|---|---|
| Status Report — 2–3 polished visuals, assertion headlines, report template | 20 | visuals rendered; writeup pending |
| Practice Talk — present one visual, record, post, reply to podmates | 20 | pending |
| Chart Redesign Activity — separate, uses D2L chart bank | 20 | pending |

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
  rendered to `img/`, no headline text baked in.

Artifacts on disk: `data/hex_grid_res5.parquet`, `data/hex_acres_res5.parquet`,
`data/mtbs_perimeters/`.

## The visuals (rendered — headlines to finalize)

| file | headline | role |
|---|---|---|
| `w5_v1a_one_fire.png` | *"The record says a fire happened here. It burned all of this."* | **practice talk.** 5 Mile fire 2014, Blue Mountains, 4,620 ac — median-size large fire, chosen for honesty not drama |
| `w5_v1b_before_after.png` | *"We knew how much burned. We didn't know where."* | same acres placed two ways: ignition-point vs. perimeter-distributed |
| `w5_v2_national.png` | *"A tenth of the country carries three quarters of the burning."* | national concentration, 29 years pooled |
| `w5_v2b_season_2020.png` | *"One fire season, everywhere it touched."* | 2020 alone, small/medium burns kept |

**Design constraint:** the audience is non-technical executives. These are maps —
no axes needed. Ablation ladders and sparsity plots are correct evidence in the
wrong encoding; they belong in an appendix slide.

**Status report picks 2–3.** Recommended: V1-A (the gap) → V1-B (the fix) → V2 or
V2-B (what it reveals nationally).

**The V3 timelapse is not committed.** `animate_national()` in
[src/w5_visuals.py](../../src/w5_visuals.py) and the V3 cells in
[notebook/11_w5_visuals.ipynb](../../notebook/11_w5_visuals.ipynb) still build it —
re-run them if a talk asset is wanted. The 4.6 MB gif is not worth carrying in the
repo for a figure the status report does not use.

## Remaining work

1. **Status report** — `coursework/W5/MSDS696_W5_Status_Report.md` on the report
   template, following [MSDS696_W4_Status_Report.md](../W4/MSDS696_W4_Status_Report.md).
   Embed the chosen visuals under their assertion headlines. State the scope limit
   plainly: national perimeter correction, no predictive result yet.
2. **Practice talk** — present V1-A. Record, post with a short self-assessment,
   reply to podmates via the Pod Feedback Card.
3. **Chart Redesign Activity** — independent. One chart from the D2L bank, four-part
   write-up per the handout (name the lie with a number, name the victim and the
   decision, rebuild with each fix labelled, say what you preserved). Do **not** use
   a project figure.
4. **Doc updates** — `CLAUDE.md` (MTBS perimeter join is a new data-source fact; the
   Natural→location grain question is now partly answered),
   [collaboration_log.md](../collaboration_log.md) incrementally per the established
   cadence, [todo.md](../todo.md).

No plan snapshot — this file is under version control, so git history is the
snapshot.

## Deferred — the imagery hypothesis

Not started; no MODIS cache exists. Carried forward as the next arc, unblocked by
W5 grading.

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
