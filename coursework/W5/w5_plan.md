# W5 Plan — Build the case for augmenting with satellite imagery

## Context

Week 5 is graded on **executive visuals** (Status Report, 20 pts: 2–3 polished
visuals with assertion headlines; Practice Talk, 20 pts: one visual presented;
Chart Redesign, 20 pts: separate activity). See
[assignment.md](assignment.md).

The substantive goal is to build the case — **before and after** — that FPA-FOD
alone cannot support two things the project needs, and that satellite imagery can:

- **(a)** highest-risk **ignition geocoordinates** within a region
- **(b)** **acres likely to burn**

### The confound that reshaped this plan

FPA-FOD gives a **pinpoint lat/lon** for each fire, but `FIRE_SIZE` describes an
**area**. At EPA Level III grain the error mostly stayed inside the polygon. At
hexgrid grain it becomes the dominant artifact: a 2.8M-acre fire covers ~11,000 km²
— hundreds of 10 km hexes — yet the record assigns every acre to the single hex
containing the ignition point. A naive hex-level acres target would measure
point-attribution error, not fire behavior.

### What the source actually contains (verified this session)

Checked `data/FPA_FOD_20221014.sqlite` directly. **No perimeter geometry was
dropped in cleaning** — the `Shape` column is `POINT`. Nothing was lost. But the
`Fires` table carries **`MTBS_ID`**, a live foreign key into MTBS burn-severity
perimeters:

| | count | acres | share of acres |
|---|---|---|---|
| MTBS-linked | 13,870 (0.6% of rows) | 146,891,427 | **81.6%** |
| point-only | 2,289,696 | 33,157,309 | 18.4% |

- Mean size: MTBS-linked **10,591 ac** vs point-only **14 ac**
- Among fires ≥1000 ac: **93.4% of acres** are MTBS-linked
- Candidate-region coverage: AK **90.0%**, CA **90.2%**, OR **93.7%**

The 0.6% of fires that can be given real perimeters are exactly the fires carrying
82% of the acres — the megafires that broke persistence 40×. The 2.29M point-only
fires average 14 acres, smaller than a single hex, where point attribution is fine.

**This is the argument, not a workaround.** MTBS perimeters are themselves
satellite-derived (Landsat dNBR). The fire record points at imagery through a join
key it cannot resolve on its own. That is a stronger W5 story than an external
raster dependency, and it makes a full ablation achievable inside the week.

### The hypothesis

> Historical fire data reveals *where* fire recurs, but cannot anticipate *when* a
> region-season will burn big. **Satellite imagery describing combustible-fuel
> condition going into the region-season — how much fuel has accumulated and how
> dry it is — supplies the missing signal.**

Two properties make this testable rather than rhetorical:

- **It is a measurement, not a proxy.** Burn history infers fuel from what has been
  *consumed*; imagery observes the fuel that is *present*. The ablation is designed
  so imagery must beat the cheap proxy, not merely beat nothing.
- **It is physically proximate.** TerraClimate already failed at ecoregion grain
  (14.0 → 16.9× — it made things *worse*). Climate says *the weather was dry*.
  Fuel-condition imagery says *the vegetation is dry and there is a lot of it* —
  which is the state that actually burns. That prior null is the motivation for
  this rung, not an experiment being repeated.

The ablation ladder is built to isolate exactly this:

```
persistence  ->  + climate  ->  + prior-burn (proxy)  ->  + fuel condition (imagery)
                   [failed]        [cheap proxy]            [the hypothesis]
```

Prior-burn is kept as its **own rung** precisely because it is partly redundant
with imagery — a recently burned hex has low fuel load, which is why its NDVI is
low. Separating the rungs is what lets the result attribute lift to measurement
rather than to proxy.

**Falsifiable, and a null is publishable.** If the imagery rung does not beat the
prior-burn rung, the honest finding is that fuel condition at this grain and lead
time carries no additional signal — which, combined with the corrected
perimeter-based target, is still a genuine W5 contribution.

### Existing evidence going in

- **(b) is already proven.** Fire size spans nine orders of magnitude; top 1% of
  fires = 89.7% of acres ([02_eda.ipynb](../../notebook/02_eda.ipynb) cell 9).
  Persistence floor **8.6× off**; best learned model still **5.98× off**
  ([06_analysis.ipynb](../../notebook/06_analysis.ipynb) cells 15, 23). Largest held-out
  cell missed **40×** (Interior Forested Lowlands JJA 2015: 68,570 predicted vs
  2,826,326 actual). On the Natural branch persistence is **14× off** and *loses to
  a national constant* (3.16×); adding TerraClimate made it **worse** (14.0→16.9×)
  ([07_natural_location.ipynb](../../notebook/07_natural_location.ipynb) cells 5, 6, 14).
- **(a) has no computed number** — only the documented ~1 sq mi PLSS inclusion rule
  ([01_feasibility.ipynb](../../notebook/01_feasibility.ipynb) cell 2). Nothing in the
  repo has computed below Level III grain.
- **Nuance to preserve:** *which* regions carry Natural burn **is** predictable
  (train→test Spearman ρ = 0.932); *when* and *where within* is not
  ([07_natural_location.ipynb](../../notebook/07_natural_location.ipynb) cells 9–10).
  Overstating claim (a) weakens it under critique.

---

## Phase 0 — Acquire external data

**MTBS perimeters.** Download the national **burned-area boundaries** shapefile
(1984–2020) from mtbs.gov into `data/mtbs_perimeters/`, following the caching
convention of `data/terraclimate_cache/`. Verify the join: FPA-FOD `MTBS_ID`
against the perimeter `Event_ID`, confirming the match rate against the 13,870
expected rows. Record unmatched IDs — a shortfall is itself reportable.

**MODIS vegetation indices.** Fetch NDVI/EVI (MOD13) and the reflectance bands
needed for NDMI/NBR, 2000–2020, clipped to the **three PoC ecoregions**
(179,553 km²), cached under `data/modis_cache/`. Three cost controls, all
material:

- **Spatial:** clip to the dissolved three-region boundary, not a bounding box —
  the regions are irregular and a bbox roughly doubles the pull.
- **Temporal:** pre-season months only (per `preseason_months()`), plus the prior
  growing season needed for `ndvi_prior_wetseason`. Not all 12 months.
- **Resolution:** MOD13Q1 is 250 m and MOD13A1 is 500 m. Since values are averaged
  to ≥10 km hexes, **500 m is sufficient** and is ~4× cheaper. Do not pull 250 m.

Pull once at native resolution and aggregate to both hex grids — the second grain
costs nothing extra on acquisition.

This is still the acquisition most likely to consume the week. **Start it first**
and let it run while Phase 1 proceeds. If it stalls, Klamath alone (48,358 km²)
is the fallback scope and the ablation still runs.

---

## Phase 1 — Quantify the confound + spatial resolution

**New notebook: `notebook/10_spatial_resolution.ipynb`**, reading
`data/fires_clean.parquet`. No re-cleaning.

1. **The pinpoint-vs-area mismatch — the headline diagnostic.** For each fire,
   compare `FIRE_SIZE` to the area of the hex it would fall in. Report the share of
   *acres* belonging to fires whose footprint provably cannot fit in their assigned
   cell. At ~10 km hexes (~86 km² ≈ 21,000 ac) any fire above ~21,000 ac is
   guaranteed mis-assigned. This is the computed number claim (a) has been missing,
   and it is better than coordinate-rounding stats because it is a *structural*
   defect rather than a precision one.
2. **Coordinate precision.** Decimal-place distribution in `LATITUDE`/`LONGITUDE`;
   share of fires sharing an exact coordinate with ≥1 other fire; largest duplicate
   cluster. Expect clustering on PLSS-section centroids.
3. **Fine-grid sparsity.** Fires per hex at ~25 km and ~10 km: cells with ≥1 fire
   ever, share with <5 fires across 29 years, median fires-per-cell-year.
4. **Supporting citations, no new compute.** Sub-metre ecoregion-seam
   non-determinism in [FINDINGS.md](../../FINDINGS.md) §1; summer concentration HHI 0.137
   across ~82 regions ([07_natural_location.ipynb](../../notebook/07_natural_location.ipynb)
   cell 3).

**Student runs notebooks manually** — per project convention the agent edits cells
but does not execute them.

---

## Phase 2 — Hexgrid probe with a perimeter-corrected target

**New notebook: `notebook/11_hexgrid_probe.ipynb`**

**Scope — three contrasting CONUS ecoregions.** Measured from the ecoregion
shapefiles this session:

| region | km² | acres 2000–20 | fuel regime |
|---|---|---|---|
| Klamath Mtns / CA High North Coast | 48,358 | 4.37M | Mediterranean mixed conifer |
| Idaho Batholith | 60,283 | 5.53M | high-elevation conifer |
| Blue Mountains | 70,911 | 2.95M | semi-arid conifer/shrub-steppe |
| **total** | **179,553** | **12.85M** | ~2,088 hexes @10 km |

Two reasons this beats the single-region plan:

- **Cheaper.** All three together are ~33% *smaller* than Interior Forested
  Lowlands and Uplands (AK) at 269,627 km² — the originally-planned single region
  was the most expensive pull available. Alaska also carries genuine MODIS quality
  problems at high latitude: extreme solar zenith angles, persistent cloud and
  snow contamination, and short usable compositing windows. Those degrade exactly
  the NDVI/NDMI signal the hypothesis rests on.
- **Stronger evidence.** One region gives one climate regime, so a positive result
  cannot be distinguished from a local quirk. Three contrasting fuel regimes test
  whether fuel condition generalizes — which directly serves RQ1's "do those
  patterns differ enough to demand different strategies."

**Cost, stated plainly:** this drops the AK 2015 megafire that anchors the 40×
failure narrative. That failure is already documented at ecoregion grain in
[06_analysis.ipynb](../../notebook/06_analysis.ipynb) cells 16–17, so the probe does not
need to re-derive it; V1 still cites it. If the three-region pull lands early, AK
Interior is the natural extension.

Region identity enters the model as a categorical/grouping variable so
cross-region generalization can be inspected, not assumed.

1. **Hexgrid.** H3 tessellation over the three dissolved ecoregion polygons at
   **two resolutions (~25 km and ~10 km)** so grain sensitivity is visible — the
   point at which the data stops supporting finer targeting is itself the answer
   to claim (a). Reuse the polygon loading and Albers reprojection in
   [src/cleaning.py](../../src/cleaning.py). Hexes are clipped to the region boundary;
   partial-coverage hexes must carry their **land area** so `burned_frac`
   denominators stay honest at the edges.
2. **Hybrid burned-area target.** The core methodological contribution:
   - **MTBS-linked fires** — intersect the perimeter polygon with the hexgrid and
     distribute `FIRE_SIZE` across hexes **proportional to intersected area**.
     (Scale the perimeter-derived areas to sum to the FPA-FOD `FIRE_SIZE` so hex
     totals still reconcile to the published acre totals.)
   - **Point-only fires** — keep point attribution; at mean 14 ac they are
     sub-hex.
   - **Provenance covariate** — per hex-season, record the fraction of acres
     sourced from perimeters vs. points. This is both a data-quality signal and a
     model feature, and it ties directly to the project's existing Unknown-branch
     attribution-quality framing.
3. **Panel + baselines.** Build a hex × season-year panel reusing the `season_idx`
   spine and aggregation patterns in [src/panel.py](../../src/panel.py) — do not invent a
   second grain vocabulary. Run global-prior and persistence baselines scored with
   the existing acre-weighted log-MAE / "×-off" metrics in
   [src/scoring.py](../../src/scoring.py) and rungs in [src/models.py](../../src/models.py).
   Forward-chaining temporal split, unchanged, so hex numbers are directly
   comparable to published ecoregion numbers.
4. **Feature engineering** — see the dedicated section below.
5. **Full ablation ladder — the hypothesis test.** Four rungs, run for **both**
   targets: (a) ignition count per hex (validly point-located) and (b) burned acres
   per hex (perimeter-corrected).

   | rung | features | role |
   |---|---|---|
   | 1 | persistence | the floor |
   | 2 | + climate | already failed at ecoregion grain |
   | 3 | + prior-burn | the cheap fuel proxy |
   | 4 | **+ fuel condition (imagery)** | **the hypothesis** |

   The claim is supported only if **rung 4 beats rung 3** — imagery must earn its
   lift above the proxy, not merely above nothing. All rungs scored on the
   2000–2020 panel so the comparison is fair. **Report the result honestly either
   way**; a null is a legitimate W5 finding, and the perimeter-corrected target is
   a contribution regardless of whether the model improves.

---

## Feature engineering — accounting for burn *regions*, not burn points

The whole design problem is that a fire is recorded as a point but behaves as an
area. Every feature below is built so that a hex's value reflects **area actually
burned inside that hex**, never "a fire started here."

### The one primitive everything rests on: `hex_burn_fraction`

Build once, in a new module **`src/hex_burn.py`**, and reuse everywhere:

```
intersect(MTBS perimeter polygon, hexgrid)
  -> for each (fire_id, hex_id): intersected_area / perimeter_total_area = w
  -> hex_acres[fire, hex] = w * FIRE_SIZE      # rescaled to FPA-FOD acres
```

`w` sums to 1.0 across hexes for each perimeter-backed fire, so **acres are
conserved by construction** — the reconciliation check in Verification is a direct
test of this. Point-only fires (mean 14 ac, sub-hex) get `w = 1` on their
containing hex. Output is a tidy `(fire_id, hex_id, hex_acres, source)` frame where
`source ∈ {perimeter, point}`.

Everything downstream aggregates *this*, never `FIRE_SIZE` on a point.

### Four feature families

**1. Target / response features (per hex × season × season-year)**

| feature | definition | why |
|---|---|---|
| `burned_acres` | Σ `hex_acres` in cell | the corrected (b) target |
| `burned_frac` | `burned_acres` / hex area | scale-free; comparable across hex sizes and the only version portable between the ~25 km and ~10 km grids |
| `n_ignitions` | count of ignition **points** in hex | the valid (a) target — points *are* correctly located |
| `acres_per_ignition` | `burned_acres` / `n_ignitions` | escape propensity; the project already uses this framing at ecoregion grain |

Note the deliberate split: **ignitions are a point process, burned area is an area
process.** Modeling them as one target is what the confound punishes. `n_ignitions`
is honest at the ignition point; `burned_acres` requires the perimeter distribution.

**2. Fuel-consumption history — the cheap proxy rung (ablation rung 3)**

Derived from accumulated `hex_burn_fraction` over prior seasons. This is the
*proxy* the imagery rung must beat:

- `years_since_last_burn` (censored at 29; explicit sentinel for never-burned)
- `cum_burned_frac_5y` / `_10y` / `_since_1992` — cumulative fraction of the hex's
  area burned in trailing windows. Values > 1 are legitimate (reburn) and must not
  be clipped.
- `nbr_burned_frac_prior` — same quantity over the hex's **immediate neighbors**.
  Fire crosses hex boundaries; a hex ringed by recently-burned ground faces a
  different fuel situation than an isolated one. H3 gives ring adjacency directly
  (`k_ring`) — the main practical reason to prefer H3 over an ad-hoc grid.

Burned area **removes fuel**, so this infers fuel state from consumption. Point
records cannot express it at hex grain because they cannot say which hexes burned.

**3. Fuel condition from imagery — THE HYPOTHESIS (ablation rung 4)**

Direct observation of combustible-fuel state in each hex in the months **before**
the target season opens. Two complementary signals, both requested:

*Fuel dryness — live fuel moisture proxy*
- `ndmi_preseason` — Normalized Difference Moisture Index (NIR vs. SWIR) averaged
  over the pre-season window. SWIR reflectance responds directly to water content
  in vegetation, making this the closest optical measure of "how dry is the fuel."
- `ndmi_anomaly` — departure from that hex's own season-specific climatology.
- `nbr_preseason` — live-vegetation NBR, retained because MTBS is dNBR-based, so
  it shares units with the perimeter product.

*Fuel load — accumulated biomass*
- `ndvi_anomaly` / `evi_anomaly` — greenness vs. the hex's own seasonal
  climatology. Answers "how much combustible material accumulated."
- `ndvi_prior_wetseason` — greenness during the **preceding growing season**. This
  is the mechanism climate alone inverts: a *wet* prior season builds grass and
  fine fuel that later cures into the thing that carries fire. A model given only
  dryness sees wet-and-safe; a model given fuel load sees wet-then-loaded.

**Anomalies, not levels, are the primary form.** Absolute greenness and moisture
differ enormously between boreal AK and Mediterranean CA. *Departure from that
hex's own normal* is the megafire signal, and pooling raw levels across regions is
a plausible reason the ecoregion-grain climate rung failed.

**Temporal coverage — a real constraint, handled explicitly.** MODIS begins in
2000; the panel runs 1992–2020. The imagery rung is therefore run on the
**2000–2020 era**, and **every rung is re-scored on that same shortened panel** so
the ladder stays apples-to-apples. This costs 8 years but retains ~21, including
the 2015 AK megafire year that anchors the whole argument. The full 1992–2020
results remain reported separately for the non-imagery rungs. Landsat could extend
NDMI/NBR to 1992 but the scene mosaicking, cloud masking, and sensor
harmonization are out of scope for one week.

Source: MODIS surface-reflectance / vegetation-index composites (MOD13 for
NDVI/EVI; MOD09-derived indices for NDMI/NBR), aggregated to hex means over the
pre-season window. Cache under `data/modis_cache/` following the
`data/terraclimate_cache/` pattern.

**4. Pre-season climate (already built — reuse, do not rewrite; ablation rung 2)**

TerraClimate PDSI, soil moisture, climatic water deficit, VPD at hex centroids via
the existing fetch and `data/terraclimate_cache/`. Aggregate over
`preseason_months()` in [src/terraclimate.py](../../src/terraclimate.py) — the leakage
window is implemented and correct. Add anomaly forms alongside levels, for the same
reason given above.

**5. Data-quality / provenance covariates**

- `perimeter_acre_frac` — share of the cell's acres sourced from perimeters vs.
  points. Directly parallels the existing `acre_missing_rate` weight in
  [src/cell_features.py](../../src/cell_features.py) and plugs into the project's
  established attribution-quality framing.
- `missing_rate` / `acre_missing_rate` — carried down from `build_cell_targets`,
  which is **already grain-agnostic** (`cell_keys` is a parameter) and works at hex
  grain unchanged.

### Two code changes required

- **`src/cell_features.py`** — `build_cell_targets` aggregates whole `FIRE_SIZE`
  per row, i.e. it hardcodes the point-attribution assumption. Add an optional
  `size_col`-style hook (or accept the exploded `hex_acres` frame) so it can
  aggregate distributed acres. Its `cell_keys` parameter already handles the grain
  change; only the size semantics need touching.
- **`src/trailing.py`** — `GROUP_KEYS` is hardcoded to `("region", "season")`. Hex
  features need `("hex_id", "season")`. Make it a parameter rather than
  copy-pasting the module. **Keep `assert_sorted`** — the leakage guard it
  implements matters more at hex grain, where there are far more series and
  mis-attribution would be even harder to spot.

### Leakage discipline

The prior-burn and imagery families are the sharpest risks in the project so far.

- **Prior-burn.** A hex's own burn in season *S* must never inform its prediction
  for *S* — and neither may its neighbors'. All burn-history features go through
  the trailing machinery in [src/trailing.py](../../src/trailing.py) at strictly earlier
  `season_idx`, with `assert_sorted` active. Neighbor features must be built from
  **already lagged** hex values; aggregating first and shifting second leaks
  same-season neighbor burn into the target.
- **Imagery.** The hazard is subtler and would be invisible in the metrics: a
  vegetation index composited over a window that overlaps the fire season reads
  the *burn scar itself*, producing a spectacular and entirely circular result.
  Every index must be aggregated over `preseason_months()` — the same window
  function the climate covariates already use — ending strictly before the target
  season opens. `ndvi_prior_wetseason` reaches further back, which is safe, but
  its window must still be asserted to end before season start.
- **Explicit test.** Add a check that the maximum source date contributing to any
  feature row is strictly less than that row's season start date. Cheap, and it
  catches the entire class.

---

## Phase 3 — W5 visuals: a three-beat executive story

The audience is **non-technical executives**. The story is three sentences, one
visual each:

> **(1)** We don't have the right data to build a useful model.
> **(2)** We ran a proof of concept that layers in additional data.
> **(3)** This is what we found.

**Design constraint — legibility over rigor of encoding.** These are not analyst
charts. The ablation ladder, concentration curves, and sparsity plots are correct
evidence in the *wrong encoding* for this audience; they move to an appendix slide
for anyone who asks. Beats 1 and 2 are **maps**, which need no axis at all.

Load the `dataviz` skill before writing any chart code. Every visual carries an
**assertion headline** — a claim, not a description. Save to `img/` following
existing naming.

### V1 — The data gap (also the practice-talk visual)

**Headline:** *"The record says a fire happened here. It burned all of this."*

One real large fire from the PoC regions: its true MTBS perimeter drawn as a
shape, with the single FPA-FOD ignition point overlaid as a dot. No axes, no
units, no legend beyond two labels. The mismatch is self-evident to a reader who
knows nothing about the project.

Pick the example for honesty, not drama — a fire near the median of the
large-fire distribution, not the largest available. Note its acreage in the
caption so the scale is explicit.

**Carries the practice talk.** It is fully verified today, independent of how the
probe lands, and carries zero risk of presenting an unmeasured result.

### V2 — What we added

**Headline:** *"The fire record can't see fuel. Satellites can."*

Three small maps in a row, same hexgrid, same extent:
1. **What the record sees** — ignition points.
2. **What imagery sees** — pre-season fuel condition (NDMI/NDVI anomaly) per hex.
3. **What actually burned** — perimeter-derived acres per hex.

Shows the added information rather than asserting it, and makes the hexgrid method
legible without explaining it. Use a single sequential ramp per panel; do not
introduce a diverging scheme unless the anomaly genuinely centers on zero.

### V3 — The finding

**Headline written after the result, and matched to it.**

One **stat tile**: a single large number — the change in prediction error — with a
plain-language subtitle saying what it means for a planner. Not a bar chart: the
×-off metric is a log-scale error *ratio*, and bar length invites a reader to
misjudge it in either direction. That is precisely the axis-honesty failure the
Chart Redesign activity is about, so the deck must not commit it.

**Pre-committed honesty.** The result does not exist yet. Both outcomes are
publishable and the visual is built to state either:
- *Imagery helped* → report the error reduction, and state plainly that it is
  measured on 3 regions over 2000–2020, not nationally.
- *Imagery did not help* → the headline becomes *"Fuel condition didn't close the
  gap at this grain"*, and the finding is that the remaining barrier is grain or
  lead time, not data availability. This is a legitimate executive finding and
  must not be retrofitted into a success.

### Appendix slide (not graded, for questions)

The four-rung ablation ladder, MTBS coverage (0.6% of fires / 82% of acres), and
the existing ecoregion-grain evidence — top 1% of fires = 89.7% of acres, the 40×
miss on AK 2015 ([06_analysis.ipynb](../../notebook/06_analysis.ipynb) cells 16–17),
and climate's 14.0 → 16.9× failure.

**Practice talk:** present **V1**. Record the talk, post it with a short
self-assessment, and reply to podmates in writing using the Pod Feedback Card.

**Chart Redesign Activity:** independent deliverable. Pick one of the four charts
from the D2L chart bank, redesign it, name the specific lie, four-part write-up per
the handout.

---

## Phase 4 — Write-ups

- **`coursework/W5/MSDS696_W5_Status_Report.md`** — on the report template,
  following [MSDS696_W4_Status_Report.md](../W4/MSDS696_W4_Status_Report.md).
  Embeds V1–V3 in the three-beat order (gap → what we added → finding), each under
  its assertion headline. States plainly what the probe showed, including nulls,
  and names the scope limit: 3 regions, 2000–2020, not national.
- **No plan snapshot.** W4 used `w4_plan_snapshot.md` to capture plan state at a
  point in time. This week's plan lives at `coursework/W5/w5_plan.md` under version
  control, so git history *is* the snapshot — a separate frozen copy would only
  drift. Commit plan revisions as they happen rather than writing a snapshot at
  the end.
- **Update [CLAUDE.md](../../CLAUDE.md)** — the Natural→location branch's grain question,
  which W4 left explicitly unsettled, is now being answered; and the MTBS
  perimeter join is a new data-source fact worth recording.
- **Update [coursework/collaboration_log.md](../collaboration_log.md)**
  incrementally as work happens, per the established cadence — not batched.
  The MTBS discovery (checking the source before reaching for external rasters)
  is a log-worthy exchange.
- **Update [coursework/todo.md](../todo.md)** — Natural-branch grain and
  the satellite/fuels integration items both move.

---

## Verification

- **Phase 0:** MTBS join match rate against the expected 13,870 rows; unmatched IDs
  listed, not silently dropped.
- **Phase 1:** fire counts reconcile to known totals (2,271,343 cleaned rows;
  179.3M acres).
- **Phase 2 — the critical check:** hex-grain acres per season-year, summed over
  each of the three regions, must reconcile **exactly** to
  `region_season_cause.parquet`. Both the perimeter-distributed and
  point-attributed portions must be conserved, and the check must pass at **both**
  hex resolutions. If it doesn't reconcile, the intersection or the rescaling is
  wrong. Perimeters crossing a region boundary are the expected failure mode —
  acres landing outside the three-region footprint must be accounted for, not
  silently dropped.
- Perimeter portions must never exceed the fire's FPA-FOD `FIRE_SIZE` after
  rescaling; no hex may receive negative or NaN acres.
- **Scoring:** reuse [src/scoring.py](../../src/scoring.py) unchanged for comparability.
- **Leakage:** every climate/prior-burn feature's source window must end strictly
  before its target season begins. Prior-burn history is the sharpest risk — a
  hex's burn in season S must never inform its own prediction for S.
- **Visuals:** one message, honest axis, units stated, log scales labeled.

## Open decisions to confirm during execution

- **Descope trigger.** If the MODIS pull stalls, drop to Klamath alone
  (48,358 km²) — the ablation still runs, with generalization evidence lost and
  said so plainly.
- **Hex resolutions** — ~25 km and ~10 km proposed; adjust once Phase 1 reports
  actual sampling density. If 10 km proves too sparse to fit, *that is the
  finding for claim (a)*, not a failure.
- **Naive-vs-corrected target comparison** — reporting both would quantify how much
  point attribution inflated apparent skill. High evidential value; add only if
  Phase 2 lands with time to spare.
- **AK Interior as extension** — if the three-region pull finishes early, adding it
  restores the 2015 megafire and tests boreal generalization.
