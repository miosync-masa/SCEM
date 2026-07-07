# Supporting Information (SI) — SCEM Paper 2 §5.5 External Validation (GSS + ESS)

**Version:** 1.0 (2026-06-27) / **Parent:** `docs/paper2_gss_ess_spec_v0.3.md` (canonical spec)
**Type:** **complete-reproduction.** Anyone can acquire the raw data from the same DOI → build the same slim → obtain the same results and figures.
**Numbers:** the full per-study results compendium for writing is in [`results_tables.md`](results_tables.md) (S1–S11 + two-tier structure + quick reference).
**License:** MIT (code). Raw data is **not redistributed** under the NORC (GSS) / Sikt (ESS) terms (DOI + acquisition scripts instead).
**Confidential info:** the ESS API User ID is **for usage statistics, not authentication**, but it is read from the env var `ESS_USER_ID` and **never baked into the repository**.

---

## 0. The validation question (drop this and everything drifts — spec 0.3 §0)

This validation is **not "can SCEM accurately predict GSS/ESS attitudes?"**
It is a validity check of **"does an intermediate-level tendency bundle — one that clears the trade-off between personalization (N explosion, non-generalizable) and statistical aggregation (birth-year bucket = bland) — actually exist in reality?"** SCEM does not claim accurate prediction (exactly how things mix is unknown). The claim is a **tendency bundle.** Confounds (period, cross-country, transition stage) are assumed; if an intermediate structure stands up out of them, the standpoint is valid.

**Strength wording (strict, in all outputs):** never write "**confirmation**." Use "**prediction-consistent / suggestive / modest / validity of the tendency bundle**." Sensitivity-robustness does not raise the strength.

**Main finding (two-tier structure):** community premise drives the **level**, `effective_year` drives **slope visibility (transition stage)**.

---

## 1. ★ Three-way mapping table (body claim ⇄ SI file ⇄ reproduction command)

> A table so a reviewer can instantly trace "this number in the body — where is it?" **Every number mentioned in body §5.5 corresponds to somewhere in this table.**
> Code points to the canonical `src/` (not duplicated in SI, to prevent drift). Aggregate outputs `data/*_results/` and figures `figures/` are committed (regenerable).

### §5.5.1 GSS (US)

| Body claim / figure | Data / code (src/) | Output | Reproduction command |
|---|---|---|---|
| Data acquisition (GSS 1972–2024 Cumulative, NORC) | `gss_acquire.py` | `data/gss/gss_slim.parquet` (.gitignore) | `python3 src/adapters/gss/gss_acquire.py` |
| Operationalization of the 8 premise communities (RELTRAD+RACE/HISPANIC+REGION/SRCBELT+DEGREE) | `gss_segments.py` (import) | — | (imported by each analysis) |
| CMR grid integration (interpretations) | `merge_paper2_data.py` | `data/interpretations_{us,uk}_grid.jsonl` etc. | `python3 src/cmr/merge_paper2_data.py --country us --variant grid` (and uk) |
| **SSM core contrast (Coastal 91% [85,95] vs Bible Belt 6→66%, CI-separated, period-robust)** | `gss_core_contrast.py` | `data/gss_results/core_contrast_ssm.csv` / `figures/gss_core_contrast_ssm.png` | `python3 src/adapters/gss/gss_core_contrast.py` |
| **b′ interaction (+2.7 pp/decade, p=0.157 n.s., FE ≈ uncontrolled → period-robust)** | `gss_interaction.py` | `data/gss_results/interaction_ssm.json` | `python3 src/adapters/gss/gss_interaction.py` |
| **Value-pack divergence (4 events × 6 communities, event-preserving)** | `gss_valuepack.py` | `data/gss_results/valuepack_matrix.csv` / `figures/gss_valuepack_slopes.png` | `python3 src/adapters/gss/gss_valuepack.py` |
| **Changepoint > linear (immigration×Coastal linear −3.3 → changepoint 1980 +41.5)** | `gss_valuepack.py` | `valuepack_matrix.csv` (cp_knot=1980, cp_post_extra_slope=41.5) | (same as above) |
| **overlay (single-moment 10/12 = 83%, grid ACTIVE→transition 8/8)** | `gss_overlay.py` | `data/gss_results/overlay_predicted_vs_observed.csv` / `overlay_summary.json` | `python3 src/adapters/gss/gss_overlay.py` |
| **Guns = instrument × time-structure mismatch (EVENT_STRUCTURE single / repeated)** | `gss_overlay.py` (`EVENT_STRUCTURE`) + findings §2.8 | `overlay_summary.json` (`event_structure`, scoped vs incl-guns) | (same as above) |
| Submission figures Fig 1 (mode matrices) / Fig 2 (fingerprints) | `cmr_matrix.py` / `cmr_compare.py` / `figures/generate_figures.py` | `figures/fig1_modematrix.{pdf,png}` / `fig2_fingerprints.{pdf,png}` | `python3 src/cmr/cmr_matrix.py --country us --variant grid` etc. / `python3 figures/generate_figures.py fig1 fig2` |

### §5.5.2 ESS (UK/Europe)

| Body claim / figure | Data / code (src/) | Output | Reproduction command |
|---|---|---|---|
| Data acquisition (ESS7–11, Sikt API, DOIs stated) | `ess_acquire.py` | `data/ess/ess_slim.parquet` (.gitignore) | `ESS_USER_ID=… python3 src/adapters/ess/ess_acquire.py` |
| Proxy segments / EVENT_STRUCTURE / weight (anweight) | `ess_segments.py` (import) | — | (imported by each analysis) |
| **Level gate (Secular 90% [89,91] vs Religious 66% [65,67], US juxtaposed)** | `ess_core_validation.py` | `data/ess_results/freehms_core.{csv,json}` / `figures/ess_freehms_core.png` | `python3 src/adapters/ess/ess_core_validation.py` |
| **country clusters + euftf + immigration (EVENT_STRUCTURE applied a priori)** | `ess_valuepack.py` | `data/ess_results/valuepack_matrix.csv` / `freehms_clusters.csv` / `figures/ess_valuepack.png` | `python3 src/adapters/ess/ess_valuepack.py` |
| **Southern 5 countries: consistent positive b′ slope (ES z6.86/PT7.41/IT14.56/GR13.9/CY3.14)** | `ess_southern_country.py` | `data/ess_results/southern_country.csv` | `python3 src/adapters/ess/ess_southern_country.py` |
| **effective_year → transition stage (Spearman adoption-year 0.41/0.54, marriage-year 0.34/0.67)** | `ess_effective_year.py` | `data/ess_results/effective_year.{csv,json}` / `figures/ess_effective_year.png` | `python3 src/adapters/ess/ess_effective_year.py` |
| Institutional-year coding (with sources) | `docs/ess_legal_coding.md` | (sourced table; ILGA-Europe + national legislation) | — |
| **overlay UK (7/9 exploratory, euftf↔Brexit 3/3)** | `ess_overlay.py` | `data/ess_results/overlay_uk.csv` / `overlay_uk_summary.json` | `python3 src/adapters/ess/ess_overlay.py` |

> Order dependency: `gss_overlay.py` reads `gss_valuepack.py` output (valuepack_matrix.csv) → run valuepack first.
> `*_overlay` / `*_southern`, etc. require the CMR grid integration (merge) and slim acquisition. `reproduce_all.sh` runs them in the correct order.
> **Submission figures:** all six (`figures/fig1_modematrix` … `fig6_twotier_schematic`, PDF + PNG) are regenerated by `python3 figures/generate_figures.py` (self-contained). Fig 1–2 use the CMR grids, Fig 3 uses GSS `core_contrast_ssm.csv`, Fig 4–5 use the ESS `*_results/` CSVs, Fig 6 is schematic. `reproduce_all.sh` invokes Fig 1–3 & 6 in the GSS stage and Fig 4–5 in the ESS stage.

---

## 2. What the SI includes (4 layers, complete-reproduction)

### 2.1 Data layer
- Acquisition: `src/adapters/gss/gss_acquire.py` (downloads the GSS Cumulative Stata zip directly from NORC → slim) / `src/adapters/ess/ess_acquire.py` (ESS API, direct parquet acquisition).
- DOIs: **GSS** = `gss7224_r3` (2024 release, NORC GSS_stata.zip). **ESS** = `10.21338/ess7e02_2, ess8e02_3, ess9e03_1, ess10e03_1, ess11e03_0` (`ROUND_DOIS` in `ess_acquire.py`).
- Institutional years: `docs/ess_legal_coding.md` (recognition_year / ssm_year / type / primary law; ILGA-Europe + Wikipedia national-legislation footnotes).
- Raw data (GSS 570MB / ESS per-round parquet) is `.gitignore`d. Regenerable via the acquisition scripts.

### 2.2 Operationalization layer
- US 8 communities: `src/adapters/gss/gss_segments.py` (RELTRAD [official variable] + RACE/HISPANIC + REGION/region_7222/SRCBELT + DEGREE. Mormon extracted separately as `other` ∈ {60,64,162}).
- ESS proxy: `src/adapters/ess/ess_segments.py` (secular/religious × edu × urban × immigrant-bg, weight = anweight).
- **EVENT_STRUCTURE**: the `EVENT_STRUCTURE` in `gss_overlay.py` / `ess_segments.py` (single moment vs repeated burst). Guns = repeated, freehms = single, euftf/immigration = repeated.
- **Same-sex-marriage 3-variable splice**: `gss_segments.py:ssm_approve()` (marsame/marsame1/marsamey). ESS uses `ess_segments.py:freehms_tolerant()`.

### 2.3 Analysis layer
- Each script + output (`data/{gss,ess}_results/*.csv|json` + `figures/*.png`) is as in the §1 table.
- **Strength wording**: each script's tail output states "descriptive + up to CI/estimator, tests not finalized, do not write 'confirmation'" (spin prevention guaranteed at the SI level).
- **Exclusion flags**: unstable near-saturation slopes (overfitting artifacts, improvement 0) carry `saturated`/`thin` flags in the output + an explicit "do not use for interpretation" in findings.

### 2.4 Reproduction procedure
- `SI/reproduce_all.sh`: acquire → slim → segment (import) → analyze → figures, all at once. GSS needs the network; ESS requires `ESS_USER_ID`.
- Environment: Python 3.12 / numpy / pandas / pyarrow / matplotlib. **No scipy/statsmodels** (scipy is broken in this environment, so OLS+HC1, logit Newton, and Spearman are hand-implemented in numpy). See `requirements.txt`.
- Determinism: no randomness (no `Math.random` / `np.random`). pandas groupby uses default sort; country order is `sorted()`. **No seed needed; figures are deterministic** (flagged for re-check in §5).

---

## 3. What the SI does not include (explicit)

- **The raw data itself** (GSS/ESS terms, non-redistributable) → DOI + acquisition scripts instead.
- **The slim intermediate files** (`gss_slim.parquet` / `ess_slim.parquet`) → **not included** by default (derived from raw data; on the safe side of the terms). Regenerated by the acquisition scripts (see §5-1 for confirmation).
- **The Paper 1 engine** (`media_generation_v4/v5.py`) and `events_patched.jsonl` → imported unmodified only. See the Paper 1 SI.
- **Subjective mode experience (Prolific)** → out of scope, Paper 3. Marked "not yet done, future" in the SI.

---

## 4. Guaranteeing strength & honesty (at the SI level)

- Each output carries the strength wording (suggestive, modest, never "confirmation"). This README §0 states the validation question explicitly.
- **Keep the caveats in the SI too** (fully recorded in findings):
  - GSS: b′ interaction p=0.16 (n.s.) / overlay base-rate inflation (discriminative power is the grid-ACTIVE→transition 8/8) / grid REFRAME premature judgment (SSM-Suburban, abortion-Coastal) / guns = instrument mismatch (not a grid failure).
  - ESS: the Europe-wide slope ≈ 0 is a flattening artifact (it appears for Southern once clustered) / near-saturation unstable slopes excluded / effective_year ρ moderate, n=30, GR/CY 2 waves / overlay UK thin, proxy / institutional years still need a final cross-check against the ILGA Rainbow Map.

---

## 5. Items to check (author's judgment → confirm with the team; do not decide unilaterally)

1. **Whether to include slim parquet in the SI** — judgment: **do not include (default)**. GSS is public but ESS has a registration agreement, so on the safe side "DOI + acquisition scripts only." → Can change if bundling slim is preferable under the terms (to confirm).
2. **Blanks in the three-way table** — **all filled in** (changepoint > linear = `gss_valuepack.py`/valuepack_matrix.csv, Southern by country = `ess_southern_country.py`, effective_year = `ess_effective_year.py`). Point out any gaps.
3. **ESS API consent flow** — obtain `ESS_USER_ID` by registering at `https://ess.sikt.no/en/api` → env var. If unset, `reproduce_all.sh` skips ESS with guidance (GSS continues).
4. **figure determinism** — judged **deterministic** (no randomness, fixed sort). No seed needed. → As a precaution, confirm byte-identity across two runs before final submission (a check item).
5. **Whether to duplicate code into SI/** — judgment: **do not duplicate** (point to the canonical `src/`; duplication is a drift source). `reproduce_all.sh` runs `src/`. On Zenodo release the whole repository is one archive, so SI = this README + reproduce_all + the existing src/data/docs, which is complete reproduction. → Object if you disagree.

---

## 6. Deliverables

- `SI/README.md` (this document: three-way table + validation question + reproduction procedure + check items)
- `SI/reproduce_all.sh` (one-shot complete reproduction: GSS network / ESS `ESS_USER_ID`)
- Points to (canonical): `src/` (code), `data/{gss,ess}_results/` (aggregate outputs, committed), `figures/`, `docs/ess_legal_coding.md`.
- → Once this is fixed it becomes the base for repository organization (Core/CMR/Adapters). After that, write body §5.5 with SI references.
