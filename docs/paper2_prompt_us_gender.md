# Research prompt — US gender-extended grid (paste as-is)

Run this **identical prompt** once on ChatGPT (DeepResearch) and once on Claude (Research). Do not edit between runs.

---

You are a comparative social historian. For each of the **12 US social events** below, and for **every one** of the **16 fixed community premises** below, judge **which mode the event landed as** for a person of that premise:

- **PASSIVE** — a background condition passively imprinted (no decision demanded)
- **ACTIVE** — the event forced a decision, action, or mobilization
- **REFRAME** — the event rewrote values, belonging, or reference points

Give a 1–2 sentence rationale per judgment, grounded in comparative social-history literature.

## Events (use event_id verbatim)

| event_id | Event | Year |
|---|---|---|
| us_obergefell_2015 | Obergefell v. Hodges (same-sex marriage legalization) | 2015 |
| us_sept11_2001 | September 11 attacks | 2001 |
| us_lehman_2008 | Lehman Shock (2008 financial crisis) | 2008 |
| us_obama_election_2008 | Obama Election | 2008 |
| us_trump_election_2016 | Trump Election | 2016 |
| us_blm_2013 | Black Lives Matter | 2013 |
| us_dobbs_2022 | Dobbs Decision (abortion) | 2022 |
| us_covid_restrictions_2020 | COVID Restrictions | 2020 |
| us_sandy_hook_2012 | Sandy Hook | 2012 |
| us_student_debt_2012 | Student Debt Crisis | 2012 |
| us_housing_surge_2021 | Housing Surge | 2021 |
| us_civil_rights_act_1964 | Civil Rights Act of 1964 | 1964 |

## Fixed premises (16 — use these canonical strings verbatim, never modify)

```
secular_white_coastal_graduate_female
secular_white_coastal_graduate_male
evangelical_white_bible_belt_no_college_female
evangelical_white_bible_belt_no_college_male
mainline_protestant_white_rust_belt_no_college_female
mainline_protestant_white_rust_belt_no_college_male
secular_black_urban_some_college_female
secular_black_urban_some_college_male
catholic_hispanic_urban_some_college_female
catholic_hispanic_urban_some_college_male
mormon_white_mountain_west_bachelor_female
mormon_white_mountain_west_bachelor_male
mainline_protestant_white_suburban_bachelor_female
mainline_protestant_white_suburban_bachelor_male
evangelical_white_rural_no_college_female
evangelical_white_rural_no_college_male
```

## Output format — strict JSONL, one line per event, nothing else

```json
{"event_id": "us_obergefell_2015", "affected_groups": [{"premise": "secular_white_coastal_graduate_female", "expected_mode": "PASSIVE", "effect_emphasis": ["family_reference"], "rationale": "...", "rationale_scope": "community_interpretation"}, {"premise": "secular_white_coastal_graduate_male", "expected_mode": "PASSIVE", "effect_emphasis": ["family_reference"], "rationale": "...", "rationale_scope": "community_interpretation"}]}
```

## Rules

1. Output **exactly 12 lines** of JSON (one per event). No prose, no code fences, no commentary.
2. Each event's `affected_groups` must contain **all 16 premises** — no gaps, no extras.
3. `premise` strings verbatim from the list above. `expected_mode` is exactly one of PASSIVE / ACTIVE / REFRAME.
4. `effect_emphasis`: 1–3 short snake_case tags naming the engaged axes (e.g. `religious_norm`, `family_reference`, `political_mobilization`, `economic_anxiety`, `national_security`, `bodily_autonomy`, `caregiving_norm`).
5. **Judge each premise independently, on the merits.** Within the same event, different premises may take different modes — and they may also take the **same** mode. Do not force differences, and do not force consistency. There is no expected pattern.
6. No numeric scores. Rationale + tags only.
