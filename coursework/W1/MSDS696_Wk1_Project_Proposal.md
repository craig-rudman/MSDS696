# Week 1 — Project Proposal

The project surfaces regional/seasonal risk hotspots (by fire count and by acres burned) and profiles the dominant cause of each, illustrated through three contrasting archetypes.

**Name:** Craig Rudman

**Problem Statement:** Prevention resources are limited, and wildfires don't start the same way everywhere. Identifying regional and seasonal patterns by cause could help fire prevention planners target resources more effectively.

**The Proposal:**
  - *The question:* For a set of contrasting U.S. region-seasons, which wildfire causes dominate, and do those patterns differ enough to demand different prevention strategies? 
  - *The stakeholder:* A state or regional fire-agency prevention planner deciding where to concentrate limited pre-season prevention effort.
  - *The action:* The planner matches the intervention to the pattern instead of spreading effort uniformly.

**Personal Angle:** This project is my chance to practice policy research: using data to support recommendations that carry real consequence for how public resources are used. Wildfire prevention is the case study, not the commitment. What makes it mine to defend is the discipline of tying each recommendation back to what the evidence can actually support, as the basis for a decision a public planner would have to stand behind.

**Candidate data:**
  - **Source:** FPA FOD — Fire Program Analysis Fire-Occurrence Database (U.S. Forest Service), published on Kaggle as "2.3 Million Wildfires."
    - Kaggle: https://www.kaggle.com/datasets/braddarrow/23-million-wildfires
    - Primary source / USFS archive: https://www.fs.usda.gov/rds/archive/catalog/RDS-2013-0009.6
  - **Coverage:** ~2.3 million geo-referenced wildfire records, 1992–2020 (29 years). This is the extended edition of the same FPA FOD database (same schema and cause fields), bringing coverage nearer to the present and strengthening present-day relevance.
  - **Provenance note:** An earlier, widely-used Kaggle snapshot ("1.88 Million US Wildfires," RDS-2013-0009.4) covers 1992–2015; this proposal uses the later 2.3M-record edition (RDS-2013-0009.6) through 2020 as the primary dataset. To-present ignition data (NIFC / WFIGS open feeds) exists but uses a different schema and is out of scope for the initial analysis.
  - **Fields that answer the question:**
    - *Geographic:* latitude/longitude (point locations), STATE, county FIPS — supports hotspot mapping to county level.
    - *Temporal:* DISCOVERY_DATE, discovery day-of-year, FIRE_YEAR, CONT_DATE — supports seasonality analysis.
    - *Size:* FIRE_SIZE (acres), FIRE_SIZE_CLASS (A–G) — lets risk be weighted by consequence, not just count.
    - *Cause:* STAT_CAUSE_DESCR — 13 categories (Lightning, Equipment Use, Smoking, Campfire, Debris Burning, Railroad, Arson, Children, Miscellaneous, Fireworks, Powerline, Structure, Missing/Undefined) — the backbone of the "different causes → different strategies" assertion.
  - **Known constraint (stated honestly):** The dataset contains *no* suppression cost, crew, budget, or resource-staging data. Therefore the project **informs and targets** a human allocation decision; it does not measure or optimize allocation causally. The core assertion — that regions and causes require different strategies — is fully supported by the cause × location × season × size fields present.

**First milestones / rough plan:**
  1. Acquire FPA FOD 2.3M edition (SQLite/CSV from Kaggle, 1992–2020); load the `Fires` table; confirm schema and record count. [ ]
  2. Data cleaning: handle Missing/Undefined causes, validate lat/long ranges, parse dates, derive month and season, standardize state/county. [ ]
  3. EDA: national and per-state distributions of fires by cause, by season, by size class; count vs. acres-burned views. [ ]
  4. Spatial-temporal hotspot detection: identify concentration clusters (by county/grid × season), ranked by count and by acres. [ ]
  5. Cause profiling: assign the dominant cause to each hotspot; select the three contrasting region–cause archetypes for the narrative. [ ]
  6. Exploratory data integration: Survey candidate public datasets keyed to the existing join fields (lat/long, DISCOVERY_DATE, county FIPS) — e.g., drought/weather indices (PRISM, gridMET, PDSI/SPEI), fuels/vegetation (LANDFIRE, MTBS), wildland-urban-interface / human-exposure (Census WUI), and lightning-strike density — and assess which, if any, are worth integrating to strengthen the cause-by-region-by-season findings. Exploratory; FPA FOD alone remains sufficient for the core assertion. [ ]
  7. Feature engineering: Derive analysis features — from FPA FOD alone (season, day-of-week/weekend flag, fire duration from CONT_DATE − DISCOVERY_DATE, log fire size, per-county dominant-cause share) and, if integration proves fruitful, from the integrated sources (drought index at ignition, days-since-rain, WUI/urban-proximity class, fuel type). [ ]
  8. Predictive extension: Model dominant cause and/or risk level as a function of location + season (plus any engineered features); evaluate. [ ]
  9. Temporal stability check: With the full 1992–2020 record in hand, test whether the cause-by-region-by-season patterns hold across the span (e.g., early vs. late period) rather than reflecting a single era. [ ]
  10. Translate each archetype into its matched prevention strategy; write findings. [ ]
