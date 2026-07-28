# W4 Plan — Tier-1 progress + three Tier-2 workstreams

## Context

Week 4's assigned focus is "choose & justify methods." The project's method decision — a
**hierarchical three-branch architecture** (a Tier-1 coarse allocator over Human / Natural /
Unknown, then a purpose-built deep-dive per branch) — is recorded in
`coursework/W4/design_refinement.md`. Tier 1 is substantially built in `notebook/analysis.ipynb`:
the 3-class composition target, three forward-chaining persistence baselines, a k-sweep (shares
window **k=7**), a `log10(total_ac)` **level** predictor (k=6), and the combined acres-per-class
deliverable (72.7% top-1 acre-weighted agreement). **Total variation distance (TVD) is the locked composition metric**; the
forward-chaining split holds out `season_year >= 2010` (4,024 test cells). A companion
`notebook/features.ipynb` already builds a K=7 "fingerprint" feature table with a leakage audit,
but its output isn't generated yet and it isn't wired into `analysis.ipynb`.

What's missing and what this week delivers:
1. The **three Tier-2 branch workstreams** have not been started — each is a *different* question,
   target, and intervention (Natural→location, Human→cause, Unknown→data-quality).
2. Two **Tier-1** items are open: the partial-winter boundary rule (1992 & 2021), and the
   **learned cross-sectional rung** that consumes `features.ipynb` — the ablation ladder's next
   real rung above the persistence floor.
3. The notebook pipeline should be **renumbered with `NN_` prefixes** for legibility.

Goal for the week: a **first working pass on all four models** (Tier 1 + three Tier-2 branches)
giving an early efficacy signal, feeding the W4 Status Report (20 pts) and the Defend-Your-Method
activity. **All notebooks are edited but NOT executed — the student runs them manually.**

## Decisions locked with the user
- **Separate notebook per Tier-2 branch** (not sections in one file).
- **Renumber all notebooks** with numeric prefixes, **exploration-first order** (below), and
  **fix every stale reference everywhere** (including historical W2/W3 docs and the full log).
- **First working pass on all four models** this week.
- **Tier-1: do both** — resolve the partial-winter boundary rule AND wire in the learned rung.
- **Natural branch: forward-chaining predictive** first pass at Level III, with intent to augment
  with **drought + fuel-density** external data *if sourceable* (first activation of the deferred
  climate/fuels layer).

---

## A. Notebook renumbering (exploration-first) + reference cleanup

Rename the 6 notebooks (plain file rename — repo is not git) and add the 3 new Tier-2 notebooks:

| New name | Was |
| --- | --- |
| `01_feasibility.ipynb` | `feasibility.ipynb` |
| `02_eda.ipynb` | `eda.ipynb` |
| `03_missingness.ipynb` | `missingness.ipynb` |
| `04_cleaning.ipynb` | `cleaning.ipynb` |
| `05_features.ipynb` | `features.ipynb` |
| `06_analysis.ipynb` | `analysis.ipynb` (Tier 1) |
| `07_natural_location.ipynb` | *(new — Tier-2 Natural)* |
| `08_human_cause.ipynb` | *(new — Tier-2 Human)* |
| `09_unknown_dataquality.ipynb` | *(new — Tier-2 Unknown)* |

**Fix every reference** (per Explore findings). One is a *live* link that breaks; the rest are
prose/comments that go stale but were requested fixed:
- `CLAUDE.md:53`
- Live link: `features.ipynb` cell 0 `[analysis.ipynb](analysis.ipynb)` → `[06_analysis.ipynb](06_analysis.ipynb)`; plus its prose refs to `analysis.ipynb`/`cleaning.ipynb` (cells 0,1,9).
- Intra-notebook prose refs: `cleaning.ipynb` (→missingness), `eda.ipynb` (→missingness, code comment line 1207), `missingness.ipynb` (→eda, ~10 refs), `analysis.ipynb` cell 0 design-doc link (path unchanged, verify).
- `src/season_maps.py:59`, `src/cell_features.py:9,26` (comment refs to feasibility/missingness/cleaning).
- `coursework/W4/MSDS696_W4_Status_Report.md` (:36,52,94–96), `coursework/W4/design_refinement.md` (:41,115).
- Historical: `W3/MSDS696_W3_Status_Report.md` (:35,87–90), `W2/MSDS696_W2_Status_Report.md` (:30,59), `W2/MSDS696_W2_Practice_Talk_Script.md:54`.
- `coursework/collaboration_log.md` — ~30 markdown links `[notebook/x.ipynb](../notebook/x.ipynb)` at the lines the Explore agent enumerated.

Approach: rename first, then a systematic find/replace pass mapping each old basename → new
basename across the file set above (careful with substrings — `analysis.ipynb` vs
`06_analysis.ipynb`; do longest-safe replacements).

## B. Tier-1 finish (`06_analysis.ipynb`, `05_features.ipynb`)

1. **Partial-winter boundary rule.** DJF winters straddle calendar years; 1992 and 2021 are
   partial by construction. Decide and implement one rule (recommend: **drop the two boundary
   winter cells from train/test** so no season is built from a truncated window), apply it
   consistently in `05_features.ipynb` and the split/scoring cells of `06_analysis.ipynb`, and add
   a short markdown note. Confirm the exact rule with observation of the data before coding.
2. **Wire in the learned cross-sectional rung.**
   - `05_features.ipynb`: no logic change needed; it already emits `region_season_features.parquet`
     (K=7 fingerprint features + leakage audit). Just apply the boundary rule.
   - `06_analysis.ipynb`: add a new section that loads `region_season_features.parquet` read-only
     and fits a learned model on the **same forward-chaining split** (`season_year>=2010`):
     - **Shares:** a multi-output learner on the 3-class composition (e.g. gradient-boosted
       regressors per class then renormalize, or a Dirichlet/softmax-style fit), scored with the
       **same acre-weighted TVD** vs. the k=7 persistence floor (~0.27).
     - **Level:** a regressor on `log_total`, scored with log-space MAE vs. the k=6 floor (~9×).
   - Report the ablation delta (learned vs. persistence) on both metrics — this is the efficacy
     signal for Tier 1.

## C. Three Tier-2 first-pass notebooks

All three read `data/region_season_cause.parquet` (+ `region_season_features.parquet` where useful)
and reuse the **forward-chaining split** and metric idioms from `06_analysis.ipynb`. Cause→class
map from the design doc: Natural = `Natural`; Human = all other resolved causes incl. `Other
causes`; Unknown = `missing_acres` mass.

### `07_natural_location.ipynb` — Natural → location (predictive, Level III)
- Target: **burned-area concentration of Natural fires** across region-seasons — forward-chaining
  persistence forecast at Level III (parallel to Tier-1 structure), so it earns an efficacy read.
- Concentration measure: predict Natural acres per region-season and/or a concentration index
  (e.g. share of Natural acres in top-N regions, or Gini/HHI over regions within a season) with a
  trailing-mean baseline; score log-space (heavy-tailed, same rationale as Tier-1 level).
- **External-data stub (drought + fuel density).** Add a clearly-marked section that (a) lists
  candidate sources — e.g. **drought:** US Drought Monitor / PDSI / SPEI; **fuels:** LANDFIRE
  fuel/canopy layers — with join grain (region-season, lagged to pre-season, no leakage), and
  (b) leaves a wired placeholder for merging once data is in hand. Do **not** assume the data;
  if a quick source check fails, keep it a documented next step rather than blocking the branch.

### `08_human_cause.ipynb` — Human → cause (predictive; RQ2 partner)
- Target: **sub-cause composition conditioned on Human** — the 11 non-Natural resolved causes,
  renormalized within Human (use `acres` restricted to Human causes; `cause_share` is close but is
  computed over all attributed fires, so recompute a Human-only denominator).
- Forward-chaining persistence baseline (trailing-mean of the Human sub-cause share vector),
  scored with acre-weighted TVD over the sub-cause simplex + a top-cause hit-rate for planner
  legibility. This is where the 12-cause structure earns its keep and drives prevention targeting.

### `09_unknown_dataquality.ipynb` — Unknown → data quality (operational)
- Target: **attribution quality** = `missing_acre_frac` by region-season (the Unknown-share signal).
- First pass: characterize + a forward-chaining persistence forecast of `missing_acre_frac`;
  test the design's key empirical claim — that **Unknown concentrates in the high-Natural West**
  — by correlating `missing_acre_frac` with the Natural share across region-seasons.
  > **Outcome (as built):** the claim was **refuted**. The correlation is negative
  > (Pearson ≈ −0.64): Unknown concentrates in low-Natural, human-dominated regions
  > (Central Great Plains, Southern Texas Plains, Flint Hills), while the high-Natural
  > Alaskan/Arctic ecoregions are near-zero-missing. The Human-floor conclusion survives
  > with the opposite mechanism. See collaboration log Entry 4.13.
- Deliverable framed as an **operational recommendation** (which region-seasons have attribution
  too weak to trust), NOT a fire forecast.

## D. Status report update (`coursework/W4/MSDS696_W4_Status_Report.md`)

Update the existing draft to reflect: the four-model first pass and their efficacy numbers
(learned-vs-floor deltas for Tier 1; baseline scores for each Tier-2 branch), the renumbered
pipeline, the resolved partial-winter rule, and the newly-activated external-data workstream for
Natural. Keep the Defend-Your-Method framing (hierarchy vs. flat 12-cause). *Numbers filled in
after the student runs the notebooks.*

## E. Collaboration-log entry (`coursework/collaboration_log.md`)

Add an entry (5-field convention: Date / What was going on / The exchange / What kept & why /
What rejected & why) covering this planning + build session — the renumbering decision, the
all-four-models scope, both Tier-1 items, and the Natural external-data direction.

---

## Verification (student runs; agent does not execute notebooks)

1. **Renaming/refs:** `grep -rn` for each *old* basename across `notebook/`, `src/`, `coursework/`,
   `CLAUDE.md` returns only intentional/historical mentions; the 9 files exist with new names; the
   `features → analysis` link resolves.
2. **Tier 1:** student runs `05_features.ipynb` → `region_season_features.parquet` exists; runs
   `06_analysis.ipynb` → learned rung prints TVD (shares) and log-MAE (level) alongside the
   persistence floors; the ablation delta is visible; boundary-rule cells run without the 1992/2021
   partials contaminating windows.
3. **Tier 2:** each of `07/08/09` runs top-to-bottom on the manual run, prints its baseline score
   on the held-out tail, and produces its branch deliverable (Natural concentration forecast;
   Human sub-cause profile + top-cause hit-rate; Unknown `missing_acre_frac` forecast +
   Natural-share × missing-share correlation).
4. **Docs:** status report reads coherently with real numbers once run; collaboration log has the
   new entry.

## Open items intentionally NOT closed this week
- Sourcing the actual drought/fuels data (stubbed; may become a next-week task).
- Whether the Natural branch ultimately needs a finer-than-Level-III grain (still deferred).
- Full hyperparameter tuning of the learned models (first pass = defensible defaults vs. the floor).
