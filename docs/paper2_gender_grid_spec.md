# Gender-extended grid specification (US / UK) — premise × gender

**Status:** design (data not yet collected). Extends `paper2_grid_spec.md` by one premise axis: **gender**.
**Motivation:** the current grids have **zero gender tokens** in any premise, so a 1985 Coastal Liberal woman and man share an identical exposure structure — yet the event set already contains events whose landing is plausibly gender-differentiated (US: Dobbs; JP curated DB: MeToo diffusion, paternity-leave promotion). By the paper's own core claim — *the action mode is not intrinsic to an event; it is resolved by the premise* — gender is a premise axis, not an LLM-inference flavor. Modeling it only in interpretation (LOD 1–3) would produce a genderless skeleton with gendered decoration, exactly the "skillful but empty" failure the four axioms exist to prevent.

---

## 1. Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Where gender lives | **premise suffix** `_female` / `_male` | CMR operator `Event × Premise → ResolvedImpact` extends unchanged; existing tooling treats it as an ordinary canonical premise string |
| What is re-collected | **interpretations only** (affected_groups) | Event-level mathematical attributes (year, effective_year, salience, sensitivity, effect_vector) are gender-independent event facts — reuse `events_{us,uk}_grid_merged.jsonl` unchanged; avoids numeric drift; halves prompt size |
| Event set / event_id | **identical to the existing grid** | Stable keys → direct join against the non-gendered grid |
| Observers | **ChatGPT (DeepResearch) × Claude (Research)** | Gemini is excluded for documented reproducibility problems in prior runs (serialization corruption requiring `recover_gemini_jsonl.py`; the broken source is archived). Claude already served as an additional observer in the current grid (Coastal Liberal / London Multicultural columns), so its judgment behavior is characterized |
| Gender coding | binary M/F in this round | Aligns with the external-validation instruments (GSS `SEX`, ESS `gndr` as measured in the analyzed waves). Non-binary premises are a stated limitation, not an oversight — the premise-string design extends to them when instruments allow |
| Demand-characteristics control | the prompt **never mentions gender comparison** | Gendered premises are listed as 16/18 ordinary premises; the prompt explicitly allows identical modes across any premises. Otherwise observers would manufacture gender flips because the design telegraphs them |

**Grid size:** US 16 premises × 12 events = **192 cells** / UK 18 × 13 = **234 cells**; × 2 observers = **852 judgments**.

---

## 2. Canonical premises (gendered)

Every premise from `paper2_grid_spec.md` §1, suffixed with `_female` / `_male`. The community label is unchanged.

### US (8 communities × 2 = 16)

```
secular_white_coastal_graduate_{female,male}
evangelical_white_bible_belt_no_college_{female,male}
mainline_protestant_white_rust_belt_no_college_{female,male}
secular_black_urban_some_college_{female,male}
catholic_hispanic_urban_some_college_{female,male}
mormon_white_mountain_west_bachelor_{female,male}
mainline_protestant_white_suburban_bachelor_{female,male}
evangelical_white_rural_no_college_{female,male}
```

### UK (9 communities × 2 = 18)

```
middle_class_london_immigrant_2nd_gen_russell_group_{female,male}
middle_class_home_counties_native_4plus_gen_russell_group_{female,male}
working_class_northern_england_native_4plus_gen_gcse_{female,male}
working_class_scotland_native_4plus_gen_gcse_{female,male}
working_class_northern_ireland_catholic_4plus_gen_gcse_{female,male}
working_class_northern_ireland_protestant_4plus_gen_gcse_{female,male}
middle_class_london_asian_2nd_gen_russell_group_{female,male}
working_class_leave_town_native_4plus_gen_no_qualifications_{female,male}
middle_class_london_native_2nd_gen_oxbridge_{female,male}
```

## 3. Events (identical to the existing grid; event_id is the join key)

US (12): `us_obergefell_2015, us_sept11_2001, us_lehman_2008, us_obama_election_2008, us_trump_election_2016, us_blm_2013, us_dobbs_2022, us_covid_restrictions_2020, us_sandy_hook_2012, us_student_debt_2012, us_housing_surge_2021, us_civil_rights_act_1964`
UK (13): `uk_brexit_2016, uk_77_bombings_2005, uk_financial_crisis_2008, uk_austerity_2010, uk_tuition_fees_2010, uk_section28_repeal_2003, uk_scottish_referendum_2014, uk_same_sex_marriage_2014, uk_immigration_debate_2015, uk_windrush_2018, uk_covid_lockdown_2020, uk_cost_of_living_2022, uk_nhs_crisis_2022`

---

## 4. Output schema (interpretation-only JSONL)

One line per event; `affected_groups` must cover **all** gendered premises (US 16 / UK 18, no gaps).

```json
{
  "event_id": "us_dobbs_2022",
  "affected_groups": [
    {"premise": "secular_white_coastal_graduate_female", "expected_mode": "ACTIVE",
     "effect_emphasis": ["bodily_autonomy", "political_mobilization"],
     "rationale": "...", "rationale_scope": "community_interpretation"},
    {"premise": "secular_white_coastal_graduate_male", "expected_mode": "REFRAME",
     "effect_emphasis": ["family_reference"], "rationale": "...",
     "rationale_scope": "community_interpretation"}
    /* … all 16 (US) / 18 (UK) premises … */
  ]
}
```

Same field rules as `paper2_grid_spec.md` §3 (mode is exactly one of PASSIVE/ACTIVE/REFRAME; premise strings verbatim; no numeric scores). `effect_emphasis` may add gender-relevant tags (e.g. `bodily_autonomy`, `caregiving_norm`, `breadwinner_norm`) alongside the existing vocabulary.

**File naming (both observers symmetric, interpretation-only):**
```
data/observers/ChatGPT_interps_{country}_gender_grid.jsonl
data/observers/Claude_interps_{country}_gender_grid.jsonl
```
Merged outputs: `data/interpretations_{country}_gender_grid.jsonl` / `disagreements_{country}_gender_grid.jsonl` (LOD 0 events reused from `events_{country}_grid_merged.jsonl`; a small dedicated merger is required — see §7).

---

## 5. Metrics

- **Event-/Cell-level MFR** — as in the existing grid, now over gendered premises.
- **GFR (Gender Flip Rate)** — new: the share of (community × event) pairs whose operational resolved mode **differs between the two genders of the same community**. Computed per country and per event; reported per observer and on the merged operational value.
- **Gender-CDI** — CDI computed over the 16/18 gendered fingerprints; and the within-community gender fingerprint distance (per community: Euclidean distance between its two gendered 3-axis fingerprints).
- **Observer agreement on flips** — a gender flip is *observer-robust* when both observers flip the same (community × event) pair in the same direction. Report the robust subset alongside per-observer GFR (do not silently pool).

## 6. Pre-fixed criteria (declared before data collection)

Event classes are fixed now, before any collection:

| Class | US | UK |
|---|---|---|
| **Gender-charged** (body / family-institution) | `us_dobbs_2022`, `us_obergefell_2015` | `uk_same_sex_marriage_2014`, `uk_section28_repeal_2003` |
| **Gender-peripheral** (macro-economic) | `us_lehman_2008`, `us_student_debt_2012`, `us_housing_surge_2021` | `uk_financial_crisis_2008`, `uk_tuition_fees_2010`, `uk_cost_of_living_2022` |

- **P1 (concentration):** median GFR over gender-charged events > median GFR over gender-peripheral events, **in both countries**. Satisfied → "prediction-consistent"; violated → reported as-is (no rescue analysis).
- **P2 (non-manufacture):** GFR over gender-peripheral events stays low (≤ 25% of pairs). If observers flip everything, the instrument is manufacturing differences and the round is flagged, not spun.
- Strength wording as everywhere in this project: *prediction-consistent / suggestive / modest*; never "confirmation."

## 7. Pipeline & external validation

1. Run the two research prompts (`paper2_prompt_us_gender.md` / `paper2_prompt_uk_gender.md`) once each on ChatGPT DeepResearch and Claude Research (same prompt verbatim → observer-dependence preserved).
2. Place outputs under `data/observers/` (naming in §4). Validate strict JSONL (one event per line) before merging.
3. Merge: reuse LOD 0 from `events_{country}_grid_merged.jsonl`; build `interpretations_{country}_gender_grid.jsonl` (source_model stamped from filename) and `disagreements_{country}_gender_grid.jsonl` (mode mismatches per cell). A small dedicated merger (`merge_gender_grid.py`) is needed — `merge_paper2_data.py` assumes Gemini as the second observer.
4. Metrics + figures: extend `cmr_matrix.py` / `cmr_compare.py` / `figures/generate_figures.py` with the `gender_grid` variant (GFR matrix = the flagship figure: rows events, columns communities, cell shows F/M mode pair, highlight flips).
5. **External validation hook:** GSS `SEX` × abortion/SSM attitudes within Bible Belt vs Coastal (gender gaps are classic robust findings); ESS `gndr` × freehms. The two-tier method (level gate / slope visibility) applies verbatim with gender as an additional premise token.

## 8. Limitations (stated up front)

- Binary gender only in this round (instrument alignment); non-binary premises are future work, not a claim of completeness.
- LLM observers judge *community-typical* gendered interpretation from social-history literature — not individual experience; the ethical boundary (estimate of what a position tends to hold; never a verdict on a person) applies unchanged.
- Gender interacts with community (intersectionality); this grid measures the interaction only at the premise-pair granularity designed here.
