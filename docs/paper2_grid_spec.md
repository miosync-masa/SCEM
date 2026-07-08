# Paper 2 full-grid specification (US / UK) — for re-running DeepResearch

Goal: eliminate the `—` (gaps) in the current data and turn it from "exploratory results" into a **designed comparison matrix**.
Run DeepResearch over a **full grid** of fixed Community × fixed Event.

The output is returned in a JSONL schema that flows straight into the existing pipeline (`merge_paper2_data.py` → `cmr_matrix.py` / `cmr_compare.py`).

---

## 1. Fixed Community (= premise string)

Each Community is assigned exactly one **canonical premise string** (the output premise is fixed to this → eliminates matching ambiguity).

### US (8 communities) — `religion_race_region_education`

| Community | premise (canonical) |
|---|---|
| Coastal Liberal Urban | `secular_white_coastal_graduate` |
| Bible Belt Evangelical | `evangelical_white_bible_belt_no_college` |
| Rust Belt White Working Class | `mainline_protestant_white_rust_belt_no_college` |
| Black Urban Community | `secular_black_urban_some_college` |
| Latino Immigrant Community | `catholic_hispanic_urban_some_college` |
| Mormon / Utah | `mormon_white_mountain_west_bachelor` |
| Suburban Middle Class | `mainline_protestant_white_suburban_bachelor` |
| Rural Conservative | `evangelical_white_rural_no_college` |

### UK (9 communities) — `class_region_origin_generation_education`

| Community | premise (canonical) |
|---|---|
| London Multicultural Liberal | `middle_class_london_immigrant_2nd_gen_russell_group` |
| Home Counties Middle Class | `middle_class_home_counties_native_4plus_gen_russell_group` |
| Northern Post-industrial WC | `working_class_northern_england_native_4plus_gen_gcse` |
| Scotland Urban | `working_class_scotland_native_4plus_gen_gcse` |
| Northern Ireland Catholic | `working_class_northern_ireland_catholic_4plus_gen_gcse` |
| Northern Ireland Protestant | `working_class_northern_ireland_protestant_4plus_gen_gcse` |
| British Asian | `middle_class_london_asian_2nd_gen_russell_group` |
| Brexit Leave Town | `working_class_leave_town_native_4plus_gen_no_qualifications` |
| University-educated Remain | `middle_class_london_native_2nd_gen_oxbridge` |

---

## 2. Fixed Event

### US (12 events)
same-sex marriage legalization (Obergefell) / 9.11 / 2008 Lehman / Obama's election / Trump's election / BLM /
Dobbs (abortion rights) / COVID restrictions / mass shootings & gun control (Sandy Hook, etc.) / student loans / housing price surge / Civil Rights Act

### UK (13 events) — the LGBT events are split
Brexit referendum / 7-7 London bombings / 2008 financial crisis / Austerity / Windrush /
COVID lockdown / NHS crisis / cost-of-living crisis / university tuition-fee increase / immigration & refugee debate /
Scottish independence referendum /
**Section 28 repeal (2003, a Code change in public education)** /
**same-sex marriage legalization (2014, a Code change in the marriage/family institution)**

> Section 28 repeal and same-sex-marriage legalization are separate events because their **action vectors differ** (school / public education vs. marriage / family).
> The two are bundled under `event_cluster: "lgbt_rights"`.

→ **US 8×12 = 96 cells / UK 9×13 = 117 cells** (target: zero gaps)

---

## 3. DeepResearch output schema (compatible with the existing pipeline)

One line (JSONL) per event. **Include all of the community canonical premises above in affected_groups** (= every event must evaluate every community).

```json
{
  "event_id": "us_obergefell_2015",
  "country": "US",
  "name": "Obergefell v. Hodges (same-sex marriage legalization)",
  "event_cluster": "lgbt_rights",
  "exposure_type": "direct_event",
  "year": 2015,
  "effective_year": 2015,
  "domain": "politics_institution",
  "possible_modes": ["PASSIVE", "ACTIVE", "REFRAME"],
  "base_effect_vector": {"...": 0.0},
  "affected_groups": [
    {"premise": "secular_white_coastal_graduate", "expected_mode": "PASSIVE",
     "effect_emphasis": ["family_reference"], "rationale": "...",
     "rationale_scope": "community_interpretation"},
    {"premise": "evangelical_white_bible_belt_no_college", "expected_mode": "ACTIVE",
     "effect_emphasis": ["religious_norm", "family_reference", "political_mobilization"],
     "rationale": "...", "rationale_scope": "community_interpretation"}
    /* … all communities (US 8 / UK 9) … */
  ],
  "source_scope": "national", "agency": 0.4, "salience": 1.3,
  "sensitivity_peak_age": 16, "sensitivity_spread": 6.0,
  "reframe_group": null, "reference_value": null,
  "source_urls": ["https://..."],
  "confidence": "high",
  "confidence_reason": "directly documented legal event; community interpretation inferred from historical literature"
}
```

**Required:**
- **`event_id`** (required, stable key): `{country}_{slug}_{year}` form. Robust to EN/JP naming variation and later versions. Matching prefers event_id going forward.
- **`exposure_type`** (required): one of the vocabulary below. A pre-birth event (e.g. the Civil Rights Act) can be treated as `inherited_baseline`.
- **`event_cluster`** (required): a bundle of related events (e.g. `lgbt_rights`). Lets the split UK LGBT events be bundled.
- Each event's `affected_groups` must **cover all fixed communities** (no gaps allowed).
- `premise` must use the canonical string from §1 **verbatim** (no variation).
- `expected_mode` is exactly one of PASSIVE/ACTIVE/REFRAME.
- **`effect_emphasis`** (US/UK common, required): tags for the action-vector axes that were engaged (e.g. `religious_norm` / `family_reference` / `political_mobilization` / `national_security` / `migration_status` / `economic_anxiety` …). A scaffold for the later Code-layer quantification.
- `rationale` (why that mode, 1–2 sentences) + `rationale_scope` (default `community_interpretation`).
- `confidence` (high/medium/low) + `confidence_reason` (short). Do not force quantification (Honest).
- **Do not request numeric scores** (code_factors / salience_multiplier / effect_vector_delta, etc.) — rationale + effect_emphasis suffice; quantification is a separate task.

### exposure_type vocabulary

| Value | Use |
|---|---|
| `direct_event` | the person is directly exposed (normal) |
| `diffusion_event` | diffusion of technology/culture (effective_year shifts) |
| `crisis_event` | crisis / disaster |
| `policy_environment` | institutional environment (ongoing) |
| `inherited_baseline` | an event **before the person's birth**. Not direct exposure, but inherited as a premise of the later social code (e.g. someone born 1985 does not "experience" the 1964 Civil Rights Act but grows up inside the code that followed it) |

→ `inherited_baseline` events have `age < 0`, so they are **not fed into the direct impact computation (sensitivity curve) but treated as a Community/Code baseline** (`applies_to_birth_cohorts: as_community_code_baseline`).

---

## 4. DeepResearch prompt template

> You are a comparative social historian. For each of the following {N} social events in {COUNTRY}, and for **every one** of the {M} fixed community premises below, choose **which mode the event landed as** for each community — PASSIVE (a background passively imprinted) / ACTIVE (forced a decision, action, or mobilization) / REFRAME (rewrote values, belonging, or reference points) — and give a rationale in 1–2 sentences.
>
> Output uses the JSONL schema of §3. Use the given canonical premise strings **without modification**. Each event's affected_groups must **cover all communities** (no gaps). Attach source URLs.
> No numeric scores are needed; attach mode + rationale + effect_emphasis (US/UK common), and event_id / exposure_type / event_cluster.
>
> **Important:** even within the same event, the mode need not be the same across premises. The purpose is to detect whether the community premise transforms the mode. Do not force a consistent mode.
>
> [paste the events list] … [paste the communities (canonical premise) list].

Run the ChatGPT and Gemini versions with the **same prompt** separately → this preserves the 2-model observer-dependence (§Paper 2).

---

## 5. Ingestion procedure

```bash
# Place the two acquired files (naming convention):
#   data/events_{country}_grid.jsonl             (ChatGPT)
#   data/observers/Gemini_events_{country}_grid.jsonl   (Gemini)
# If corrupted, recover with recover_gemini_jsonl.py.
python3 src/cmr/merge_paper2_data.py --country us --variant grid   # regenerate merged/interpretations/disagreements
python3 src/cmr/cmr_matrix.py  --country us --variant grid         # gap-free mode-transformation matrix
python3 src/cmr/cmr_compare.py --country us --variant grid --birth_year 1985
python3 figures/generate_figures.py fig1 fig2                      # redraw Fig 1 (matrix) / Fig 2 (fingerprints), gap-free
```

Once it is a full grid, Fig 1 (Same Event × Community) becomes a dense matrix with no `—`, and Event-level / Cell-level MFR and CDI can be computed over a **designed denominator**.

---

## 6. Notes (differences from the current data)

- The current v1 data has only 3–6 premises per event (exploratory). This grid assumes **full community coverage**.
- US `Rust Belt` and UK `Scotland / Northern Ireland` are thin in the current v1 → resolved by this grid.
- The canonical premise strings (§1) are proposals; finalized under review.
