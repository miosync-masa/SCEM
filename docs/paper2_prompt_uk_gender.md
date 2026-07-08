# Research prompt — UK gender-extended grid (paste as-is)

Run this **identical prompt** once on ChatGPT (DeepResearch) and once on Claude (Research). Do not edit between runs.

---

You are a comparative social historian. For each of the **13 UK social events** below, and for **every one** of the **18 fixed community premises** below, judge **which mode the event landed as** for a person of that premise:

- **PASSIVE** — a background condition passively imprinted (no decision demanded)
- **ACTIVE** — the event forced a decision, action, or mobilization
- **REFRAME** — the event rewrote values, belonging, or reference points

Give a 1–2 sentence rationale per judgment, grounded in comparative social-history literature.

## Events (use event_id verbatim)

| event_id | Event | Year |
|---|---|---|
| uk_brexit_2016 | Brexit referendum and withdrawal | 2016 |
| uk_77_bombings_2005 | 7/7 London bombings | 2005 |
| uk_financial_crisis_2008 | 2008 financial crisis | 2008 |
| uk_austerity_2010 | Austerity | 2010 |
| uk_tuition_fees_2010 | Tuition fee rise to £9,000 | 2010 |
| uk_section28_repeal_2003 | Repeal of Section 28 | 2003 |
| uk_scottish_referendum_2014 | Scottish independence referendum | 2014 |
| uk_same_sex_marriage_2014 | Same-sex marriage legalization | 2014 |
| uk_immigration_debate_2015 | Immigration and refugee debate | 2015 |
| uk_windrush_2018 | Windrush scandal | 2018 |
| uk_covid_lockdown_2020 | COVID-19 lockdown | 2020 |
| uk_cost_of_living_2022 | Cost of living crisis | 2022 |
| uk_nhs_crisis_2022 | NHS waiting-list crisis | 2022 |

## Fixed premises (18 — use these canonical strings verbatim, never modify)

```
middle_class_london_immigrant_2nd_gen_russell_group_female
middle_class_london_immigrant_2nd_gen_russell_group_male
middle_class_home_counties_native_4plus_gen_russell_group_female
middle_class_home_counties_native_4plus_gen_russell_group_male
working_class_northern_england_native_4plus_gen_gcse_female
working_class_northern_england_native_4plus_gen_gcse_male
working_class_scotland_native_4plus_gen_gcse_female
working_class_scotland_native_4plus_gen_gcse_male
working_class_northern_ireland_catholic_4plus_gen_gcse_female
working_class_northern_ireland_catholic_4plus_gen_gcse_male
working_class_northern_ireland_protestant_4plus_gen_gcse_female
working_class_northern_ireland_protestant_4plus_gen_gcse_male
middle_class_london_asian_2nd_gen_russell_group_female
middle_class_london_asian_2nd_gen_russell_group_male
working_class_leave_town_native_4plus_gen_no_qualifications_female
working_class_leave_town_native_4plus_gen_no_qualifications_male
middle_class_london_native_2nd_gen_oxbridge_female
middle_class_london_native_2nd_gen_oxbridge_male
```

## Output format — strict JSONL, one line per event, nothing else

```json
{"event_id": "uk_brexit_2016", "affected_groups": [{"premise": "middle_class_london_immigrant_2nd_gen_russell_group_female", "expected_mode": "REFRAME", "effect_emphasis": ["belonging_reference"], "rationale": "...", "rationale_scope": "community_interpretation"}, {"premise": "middle_class_london_immigrant_2nd_gen_russell_group_male", "expected_mode": "REFRAME", "effect_emphasis": ["belonging_reference"], "rationale": "...", "rationale_scope": "community_interpretation"}]}
```

## Rules

1. Output **exactly 13 lines** of JSON (one per event). No prose, no code fences, no commentary.
2. Each event's `affected_groups` must contain **all 18 premises** — no gaps, no extras.
3. `premise` strings verbatim from the list above. `expected_mode` is exactly one of PASSIVE / ACTIVE / REFRAME.
4. `effect_emphasis`: 1–3 short snake_case tags naming the engaged axes (e.g. `class_identity`, `belonging_reference`, `political_mobilization`, `economic_anxiety`, `migration_status`, `bodily_autonomy`, `caregiving_norm`).
5. **Judge each premise independently, on the merits.** Within the same event, different premises may take different modes — and they may also take the **same** mode. Do not force differences, and do not force consistency. There is no expected pattern.
6. No numeric scores. Rationale + tags only.
