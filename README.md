# Predicting Region-Season Wildfire Cause Patterns to Target Prevention and Mitigation

MSDS696 Practicum II — a two-tier model of U.S. wildfire cause and ignition, built on the
Fire Program Analysis Fire-Occurrence Database (FPA-FOD, 6th Edition), 1992–2020.

Prevention and mitigation resources are limited, and wildfires don't start — or burn — the
same way everywhere. This project identifies regional and seasonal patterns in wildfire
cause so that a state or regional fire-agency planner can match the intervention to the
pattern instead of spreading effort uniformly.

**Research questions**

1. *(Descriptive)* Across a set of contrasting U.S. region-seasons, which wildfire causes
   drive the most burned area, and do those patterns differ enough to demand different
   prevention and mitigation strategies?
2. *(Predictive)* Can a next-season cause-risk profile — the expected composition of causes
   for a region and upcoming season, ranked by the burned area each is expected to drive —
   be predicted well enough to pre-target that prevention effort?

> Project requirements, working agreements, and the settled-question record live in
> [CLAUDE.md](CLAUDE.md), which is the single source of truth. This README is the
> outward-facing summary of the architecture and results.

---

## Architecture

### Tier 1 — coarse allocator

For a region-season, predict burned-area composition across three classes —
**Human / Natural / Unknown** — on a *total-acres* denominator (resolved + missing) so the
three shares sum to 1.

| class | share of record |
|---|---|
| Natural | 58.9% |
| Human | 22.7% |
| Unknown | 18.5% |

Across 179.3M acres. **Unknown is a predicted class in its own right**: it holds the
`missing_acres` mass, and its share doubles as a regional attribution-quality signal.

Cause→class mapping: Natural = `Natural`; Human = all other resolved causes, including
`Other causes`; Unknown = the `missing_acres` mass.

### Tier 2 — three branches

Each branch is a different question, target, and grain.

| branch | question | target | grain | notebook |
|---|---|---|---|---|
| **Ignition likelihood** | Where are fires most likely to start? | ignition counts | res-5 hex-season | [12](notebook/12_hex_ignition_baselines.ipynb), [14](notebook/14_hex_human_branch.ipynb) |
| **Human → cause** | What starts them? | sub-cause composition | Level III region-season | [08](notebook/08_human_cause.ipynb) |
| **Unknown → data quality** | Where is the record weak? | operational recommendation | Level III region-season | [09](notebook/09_unknown_dataquality.ipynb) |

RQ2's cause-risk profile is carried by **Tier 1 plus the Human branch**, both at Level III
grain. The hex-grain ignition surface and the Unknown branch are methodologically distinct
sub-projects — different grain, different target, different unit.

### Two grains

| | Level III region-season | res-5 H3 hex-season |
|---|---|---|
| unit | 105 ecoregions × season-year | 36,234 hexes × season-year |
| cell size | variable | ~62,494 acres |
| targets | Tier 1 allocator; Human sub-cause | ignition likelihood |

**Geometry follows the target.** FPA-FOD stores a *pinpoint* `LATITUDE`/`LONGITUDE`, but
`FIRE_SIZE` describes an *area*.

- **Counts → raw points.** All ~2.27M fires, no MTBS join — an ignition location is exactly
  what the record stores correctly.
- **Acres at hex grain → MTBS perimeters**, via [`src/hex_burn.py`](src/hex_burn.py), with
  per-fire weights summing to 1.0 so acres are conserved by construction. A fire larger than
  62,494 acres provably cannot fit in its assigned cell. MTBS-linked fires are 0.6% of rows
  but **81.6% of acres**; point-only fires average 14 acres, where point attribution is fine.

### Prevention vs. mitigation, by lever

Fuel treatment, defensible space, and suppression pre-positioning are all **sited works** —
whether they pay off depends on whether fire arrives there. That makes ignition likelihood a
**mitigation-siting question regardless of cause**.

The operative distinction is between **regimes**: a hex can be high-ignition/low-acre (starts
caught small — siting arguably already working) or low-ignition/high-acre (rare starts that
run, where one ignition is expensive). Both are siting-relevant and call for different
treatments.

---

## Method commitments

- **Persistence baseline first** — "region-season = its own last occurrence." Any model must
  beat it; added complexity is justified against it via an **ablation ladder**.
- **Forward-chaining temporal split**, held across five split years.
- **Every external feature lagged to pre-season availability** — aggregated over
  `preseason_months()`, ending strictly *before* the target season opens. A window overlapping
  the season reads the burn scar itself.
- **Missing external data surfaces as NaN, never imputed to zero** — a zero anomaly reads as
  "average fuel," a fabricated observation.
- **Shuffled controls** on every claimed gain.
- **Cause reported as shares, not counts.** ~26% of records carry a Missing/undetermined
  cause; missingness is roughly flat across seasons but **differential across regions**,
  correlating negatively with Natural share (Pearson ≈ −0.64). The seasonal signal is clean;
  the regional signal is directionally reliable but magnitude-caveated.
- **A null is publishable.** If a covariate does not beat the cheaper rung below it, that is
  the finding.

Shared machinery lives in [`src/hex_panel.py`](src/hex_panel.py): one panel assembly, one
persistence baseline, one scorer.

---

## Inputs

**Spine** — FPA-FOD 6th Edition (Short 2022), ~2.3M U.S. wildfires, 1992–2020, SQLite.
Cleaned in [04_cleaning.ipynb](notebook/04_cleaning.ipynb) → `data/fires_clean.parquet`.

- **Region** = EPA Level III ecoregion, via two separate spatial joins (CONUS *and* Alaska).
- **Season** = meteorological season, with a sequential season-year index as the temporal
  spine: `(FIRE_YEAR - 1992) * 4 + season_ordinal`, range 0–115 (winter 1992 → fall 2020).
  December belongs to the *next* winter, handled deliberately so lags line up. The season
  label is kept alongside the index — the index is the ordinal spine, the label carries the
  period-4 seasonal signal.
- `FIRE_YEAR` is preserved in the aggregation grain (ecoregion × season × year).

**Covariate layers**

| module | layer | output |
|---|---|---|
| [`src/terraclimate.py`](src/terraclimate.py) | TerraClimate PDSI / soil moisture / deficit / VPD, area-weighted to Level III | `data/region_season_climate.parquet` |
| [`src/hex_climate.py`](src/hex_climate.py) | the same covariates re-fetched at hex grain | `data/hex_season_climate.parquet` |
| [`src/burn_history.py`](src/burn_history.py) | prior-burn state per hex-season, 4,239,378 cells | `data/hex_burn_history.parquet` |
| [`src/hex_ndvi.py`](src/hex_ndvi.py) | MODIS vegetation density (fuel load) via the Planetary Computer STAC API | `data/hex_season_ndvi.parquet` |

`hex_climate.py` imports `preseason_months` / `season_start` from `terraclimate.py`, so the
December-boundary rule keeps exactly one definition in the project.

Prior burn is a **state, not a forecast** — known with certainty before the season opens.
Point-only fires are excluded from it on semantic grounds: 14 acres against a 62,494-acre hex
(0.02%) would make the feature encode *where small fires get reported*.

**Grid artifacts** — `data/hex_grid_res5.parquet`, `data/hex_acres_res5.parquet`,
`data/mtbs_perimeters/`. National coverage: 36,234 hexes, 105 ecoregions, **99.61% of acres
on-grid** (loss is coastal). Two thirds of perimeter-backed fires span more than one hex.

---

## Outputs

The concrete product is a **next-season cause-risk profile**: for a given region and upcoming
season, the expected composition of ignition causes, ranked for impact by the predicted burn
size they drive rather than by ignition counts, so effort concentrates on what will burn most.

### What the modeling established

**Persistence is the model to beat, everywhere.** Ignition Spearman: Human **+0.526**
all-season (+0.593 MAM), Natural **+0.344** (+0.411 JJA). Shuffled controls fall within
±0.003 of zero on ignition and ±0.007 on acres, so the skill is spatial, not statistical luck.

**Where fires start is a property of the place, not the year.** Five consecutive covariate
nulls on ignition targets — drought, prior burn, NDVI, and combinations, on both branches.
The measured reason: these covariates identify dry *places*, not dry *years*. Under a
within-hex anomaly, pdsi goes −0.137 → −0.073 and NDVI +0.228 → +0.098. Place is what history
already knows.

**One verified covariate gain, on burned area only.** Climate + NDVI together, **+0.0493**,
**26.6 SD** above a shuffled control, holding across five split years. Both parts are jointly
necessary — fuel load and fuel dryness. The gain lands in deciles 6–8 (1–20 acre fires); the
top decile goes 855× → 868×.

**Ignition is a gate, not a dial.** A hex-season that ignites at all is **22.8×** more likely
to produce a ≥1,000-acre burn (6.7% vs 0.29%), but escape probability *per ignition* falls
with count, and 49% of large fires came from hexes with exactly one natural ignition. The rule
is binary — *does this place ignite* — not graded.

**The two branches' tails differ by more than an order of magnitude**, which licenses
different products. Quote the population with the number:

| population | top-decile under-prediction | median cell |
|---|---|---|
| Human, all seasons, all regions | 12.3× | 135 acres |
| Natural, all JJA burning cells | 269.8× | 2,970 acres |
| Natural, six forest ecoregions (covariate ladder) | 854.9× | 5,073 acres |

The like-for-like comparison against Human is **269.8×**. Human can therefore be ranked by
expected acres; Natural is delivered as a siting surface instead.

---

## Repository layout

```
coursework/W1–W8   weekly assignments and work products; each week's
                   requirements are in that week's assignment.md
notebook/          analysis notebooks, numbered in pipeline order
src/               extracted modules
literature/        literature review, with its own citation and sourcing rules
data/              inputs and generated artifacts (not tracked)
img/               figures
tests/             regression suite for the pipeline modules
archive/           superseded documents kept for history
```

**Pipeline order** — cleaning ([04](notebook/04_cleaning.ipynb)), EDA
([02](notebook/02_eda.ipynb), [03](notebook/03_missingness.ipynb)), features
([05](notebook/05_features.ipynb)), analysis ([06](notebook/06_analysis.ipynb)), Level III
branch notebooks ([07](notebook/07_natural_location.ipynb)–[09](notebook/09_unknown_dataquality.ipynb)),
hex burn distribution ([10](notebook/10_hex_burn_demo.ipynb)), W5 visuals
([11](notebook/11_w5_visuals.ipynb)), hex-grain modeling
([12](notebook/12_hex_ignition_baselines.ipynb)–[14](notebook/14_hex_human_branch.ipynb)),
W6 visuals ([15](notebook/15_w6_visuals.ipynb)).

The [collaboration log](coursework/collaboration_log.md) records decisions contemporaneously
and is the authority when documents disagree.

---

## Environment

Dependencies are declared in [environment.yml](environment.yml), each with a comment
explaining why it is there. Install from the file rather than ad-hoc:

```bash
conda env create -f environment.yml
conda activate msds696
```

Run the regression suite with `pytest`.

External data sources are open: TerraClimate over OPeNDAP, and MODIS via the Microsoft
Planetary Computer STAC API, which serves the collections anonymously — no account, no API
key, no OAuth flow.

---

## Source

Short, Karen C. 2022. *Spatial wildfire occurrence data for the United States, 1992–2020:
FPA_FOD_20221014* (6th Edition). Forest Service Research Data Archive.
