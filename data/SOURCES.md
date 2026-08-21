# Data sources — acquisition and rebuild recipe

**Nothing in `data/` is tracked except `_variable_descriptions.csv` and this file.** Everything else is either a third-party source too large to vendor, or an artifact this repo generates. This file is how the analysis stays reproducible without either one being committed: it records where each source came from, which byte-exact copy was used, and the order in which the artifacts are rebuilt from it.

The evidence standard here is the same one `tests/` already applies to the derived artifacts (see `tests/README.md`): **pin the content, not the container.** For a source we did not create, the checksum is the stronger claim — it proves *which vintage* was used, which matters because MTBS re-releases perimeters as fires are mapped, and a re-download next year will not be the file this analysis ran on.

## Verifying a source

Every checksum below is SHA-256 of the file exactly as downloaded, before any extraction. To verify a copy:

```bash
shasum -a 256 data/FPA_FOD_20221014.sqlite
```

Compare against the table. A mismatch means a different edition or vintage — **not** a corrupt download necessarily, and worth resolving before trusting any number downstream.

To verify everything present at once:

```bash
shasum -a 256 -c data/checksums.sha256
```

That file lists only the four acquired artifacts (the two archives and the two shapefile sets); missing files report as such rather than failing the whole run.

## The four sources

| # | Source | File as downloaded | Size | Retrieved |
|---|---|---|---|---|
| 1 | FPA-FOD 6th Edition | `FPA_FOD_20221014.sqlite` | 958,480,384 B | see note |
| 2 | MTBS burned-area perimeters | `mtbs_perimeters/mtbs_perimeter_data.zip` | 389,949,591 B | 2026-07-28 |
| 3 | EPA Level III ecoregions, CONUS | `us_eco_l3_state_boundaries/` (7 files) | 47 MB | 2026-07-07 |
| 4 | EPA Level III ecoregions, Alaska | `ak_eco_l3/` (7 files) | 2.8 MB | 2026-07-19 |

Retrieval dates are the local file mtimes, which are the best available record. **Source 1 carries a publisher mtime of 2023-03-11**, not a download date — the file preserved the archive's timestamp, so the date this project obtained it is not recoverable from disk. The `20221014` in the filename is the publisher's edition stamp, and the checksum pins the rest.

### 1. Fire Program Analysis Fire-Occurrence Database (FPA-FOD), 6th Edition

The spine of the project: ~2.3M U.S. wildfire records, 1992–2020, as SQLite.

- **Citation:** Short, K.C. 2022. *Spatial wildfire occurrence data for the United States, 1992–2020* (FPA_FOD_20221014). 6th Edition. Fort Collins, CO: USDA Forest Service Research Data Archive.
- **Source:** USDA Forest Service Research Data Archive, `doi:10.2737/RDS-2013-0009.6`. Resolve the DOI and take the SQLite distribution.
- **Do not substitute the Kaggle mirror.** Which edition it mirrors is unconfirmed (open student homework item in `CLAUDE.md`), and the checksum below is the arbiter regardless.

```
04f5ab8bff6880a8ee76b4a825a66b5f4db0b800dc5971a919cb743251a965a8  FPA_FOD_20221014.sqlite
```

Place at `data/FPA_FOD_20221014.sqlite` — the path `src/config.py` expects (`Config.fires_db`).

### 2. MTBS burned-area perimeters

Fire *perimeters*, needed because FPA-FOD stores a pinpoint ignition location while `FIRE_SIZE` describes an area. That asymmetry is load-bearing for the hex grain — see the two-grain table in `CLAUDE.md`. Joined to FPA-FOD on the `MTBS_ID` foreign key already present in the `Fires` table.

- **Source:** MTBS (USGS / USDA Forest Service), <https://www.mtbs.gov/direct-download> — the national "Burned Areas Boundaries" shapefile, distributed as `mtbs_perimeter_data.zip`.
- **Vintage matters more here than anywhere else.** MTBS is reissued as additional fires are mapped, so a copy downloaded later will contain *more* fires and will not match this checksum. The analysis reflects the 2026-07-28 release.

```
a15a7580b63ed63e0c0a26435cb5cddb592e40b017834cfbe64ad9d02d623081  mtbs_perimeter_data.zip
```

Unzip in place into `data/mtbs_perimeters/`, yielding `mtbs_perims_DD.{shp,shx,dbf,prj,cpg}` plus `mtbs_perims_DD_metadata.xml`. Keep the zip alongside the extraction — it is the artifact the checksum pins.

`src/hex_burn.py` reads these in their native CRS (EPSG:4269, NAD83 geographic) and reprojects for area work; it does not depend on the zip.

### 3–4. EPA Level III ecoregions — two separate layers

Region is EPA Level III ecoregion, attached by **two spatial joins against two layers**: CONUS and Alaska ship separately, in different projections. Both are required — dropping the Alaska layer silently loses every Alaskan fire's region key, and Alaska carries megafire acreage that moves national totals.

- **Source:** US EPA Ecoregions, <https://www.epa.gov/eco-research/ecoregion-download-files-state-region>
  - CONUS: "Level III Ecoregions of the Conterminous United States, by state" → `us_eco_l3_state_boundaries`
  - Alaska: the Level III Alaska layer → `ak_eco_l3`
- Extract each into its own directory under `data/`, directory name matching the shapefile basename. `src/config.py` resolves `Config.conus_ecoregions` and `Config.ak_ecoregions` to those exact paths.

Per-file checksums for both layers are in `data/checksums.sha256`. Shapefiles are multi-file formats; the `.shp` alone is not sufficient, and the sidecars (`.dbf` attributes, `.prj` projection) are what make the join correct.

## Rebuild order

With the four sources in place and the `msds696` conda environment active. Notebooks are run manually, in this order; each writes the artifacts the next depends on.

**Stage 1 — the fire-level artifact.** `notebook/04_cleaning.ipynb` reads the SQLite, performs both ecoregion joins, derives the season spine, applies the PR/HI/IA exclusion, and writes `fires_clean.parquet`. Requires sources 1, 3, 4. This is the long pole; everything else is downstream of it.

**Stage 2 — Level III grain.** `05_features.ipynb` writes `region_season_cause.parquet` and `region_season_features.parquet`. `src/terraclimate.py` fetches the TerraClimate covariates over the network (THREDDS, no credentials) into `region_season_climate.parquet`, checkpointing per year so an interrupted run resumes.

**Stage 3 — hex grain.** `src/hex_burn.py` distributes acreage across the res-5 H3 grid using source 2, writing `hex_grid_res5.parquet` and `hex_acres_res5.parquet`. Then `src/hex_ignitions.py` (counts, raw points, no MTBS), `src/burn_history.py`, `src/hex_climate.py`, and `src/hex_ndvi.py` (Planetary Computer STAC, no credentials) build their layers; `src/hex_panel.py` assembles the modelling panel.

**Stage 4 — verify.** `pytest` re-checks schema, the exclusion rule, the temporal spine, cross-artifact acre reconciliation, and content fingerprints against `tests/fingerprints.json`. `pytest -m slow` re-derives the published headline numbers against `tests/golden_metrics.json`.

The fingerprints are content hashes — row counts, schema, an order-independent value hash, grand totals — **not** file hashes, because parquet writes are not byte-deterministic and a file hash would false-alarm on an identical rebuild. A clean `pytest` run is the claim that a rebuild reproduced the analysis.

## Two honest caveats

**The network layers are not checksummed.** TerraClimate, MODIS/NDVI, and the two credential-free APIs they come from are fetched at build time, and a re-fetch is only as reproducible as the upstream service. Their caches are gitignored and rebuildable, but nothing here pins the bytes the way the four downloads are pinned. If an upstream reprocessing changed those series, the fingerprint tests over the affected artifacts would catch it — which is detection, not prevention.

**A rebuild reproduces the pipeline, not the environment.** `environment.yml` pins the dependencies, but the numbers in `tests/golden_metrics.json` were captured on the environment that produced them. Model-fitting rungs may move in the last decimals across library versions; the `approx`-at-4-decimals convention in the test suite exists for exactly that reason, and `n_cells` is pinned exactly as the canary.
