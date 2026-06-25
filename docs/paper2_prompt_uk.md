# DeepResearch 投入プロンプト(UK 完全グリッド)— そのまま貼る

> ※ これ1枚を ChatGPT(DeepResearch)と Gemini(DeepResearch)に**それぞれ同一で**貼る。
> 出力 JSONL を `data/events_uk_grid.jsonl`(ChatGPT)/ `data/Gemini_events_uk_grid.jsonl`(Gemini)に保存。

---

あなたは比較社会史の研究者です。**英国(UK)** の以下の **13個の社会事象** それぞれについて、
下記の **9個の固定コミュニティ前提(premise)の すべて** に対し、その事象が各コミュニティにとって
**PASSIVE**(受動的に刷り込まれた背景)/ **ACTIVE**(意思決定・行動・動員を迫った)/
**REFRAME**(価値・所属・基準の書き換えを起こした)の **どれとして着弾したか** を1つ選び、
根拠(rationale)を1-2文で述べてください。

**重要**:同じ event 内であっても、各 premise ごとに mode が同じになる必要はありません。
**共同体前提によって mode が変換されるか**を検出するのが目的です。無理に一貫した mode へ寄せないこと。

## 13 events(event_id / 名前 / おおよその年 / exposure_type)
1. `uk_77_bombings_2005` 7-7 ロンドン同時爆破 / 2005 / crisis_event
2. `uk_financial_crisis_2008` 2008 金融危機 / 2008 / crisis_event
3. `uk_austerity_2010` 緊縮(Austerity)/ 2010 / policy_environment
4. `uk_tuition_fees_2010` 大学授業料引き上げ(£9,000)/ 2010 / policy_environment
5. `uk_section28_repeal_2003` Section 28 撤廃(公教育の Code 変化)/ 2003 / policy_environment
6. `uk_scottish_referendum_2014` スコットランド独立投票 / 2014 / direct_event
7. `uk_same_sex_marriage_2014` 同性婚合法化(婚姻・家族制度の Code 変化)/ 2014 / direct_event
8. `uk_immigration_debate_2015` 移民・難民論争(EU移民/小型ボート)/ ~2015 / policy_environment
9. `uk_brexit_2016` Brexit 国民投票 / 2016 / direct_event
10. `uk_windrush_2018` Windrush スキャンダル / 2018 / direct_event
11. `uk_covid_lockdown_2020` COVID-19 ロックダウン / 2020 / crisis_event
12. `uk_cost_of_living_2022` 生活費危機 / 2022 / crisis_event
13. `uk_nhs_crisis_2022` NHS 待機リスト危機 / 2022 / policy_environment

> 5 と 7 は同じ `event_cluster: "lgbt_rights"` だが、作用ベクトルが違う(学校・公教育 vs 婚姻・家族)ため別イベント。

## 9 communities(正準 premise — **改変せずそのまま使う**)
1. London Multicultural Liberal → `middle_class_london_immigrant_2nd_gen_russell_group`
2. Home Counties Middle Class → `middle_class_home_counties_native_4plus_gen_russell_group`
3. Northern Post-industrial Working Class → `working_class_northern_england_native_4plus_gen_gcse`
4. Scotland Urban → `working_class_scotland_native_4plus_gen_gcse`
5. Northern Ireland Catholic → `working_class_northern_ireland_catholic_4plus_gen_gcse`
6. Northern Ireland Protestant → `working_class_northern_ireland_protestant_4plus_gen_gcse`
7. British Asian → `middle_class_london_asian_2nd_gen_russell_group`
8. Brexit Leave Town → `working_class_leave_town_native_4plus_gen_no_qualifications`
9. University-educated Remain → `middle_class_london_native_2nd_gen_oxbridge`

→ **13 events × 9 communities = 117 セル。affected_groups は毎回 9 premise 全てを必ず網羅(欠損禁止)。**

## 出力スキーマ(JSON Lines, 1行1イベント)
```json
{
  "event_id": "uk_brexit_2016",
  "country": "UK",
  "name": "Brexit referendum and withdrawal / EU離脱国民投票",
  "event_cluster": "eu_sovereignty",
  "exposure_type": "direct_event",
  "year": 2016,
  "effective_year": 2020,
  "domain": "international_geopolitics",
  "possible_modes": ["PASSIVE", "ACTIVE", "REFRAME"],
  "base_effect_vector": {"sovereignty_perception": 1.0, "national_identity": 0.9, "economic_anxiety": 0.6},
  "affected_groups": [
    {"premise": "middle_class_london_native_2nd_gen_oxbridge", "expected_mode": "REFRAME",
     "effect_emphasis": ["national_identity", "belonging_status"],
     "rationale": "国の自己像・欧州への帰属の基準値が揺らぎ、アイデンティティの再定義を迫られる。",
     "rationale_scope": "community_interpretation"},
    {"premise": "working_class_leave_town_native_4plus_gen_no_qualifications", "expected_mode": "ACTIVE",
     "effect_emphasis": ["political_agency", "economic_anxiety"],
     "rationale": "投票による意思表示と地域回復の選択として、能動的に関与した。",
     "rationale_scope": "community_interpretation"}
    /* …残り7 premise も必ず… */
  ],
  "source_scope": "national", "agency": 0.5, "salience": 1.5,
  "sensitivity_peak_age": 18, "sensitivity_spread": 7.0,
  "reframe_group": "sovereignty_eu_baseline", "reference_value": null,
  "source_urls": ["https://..."],
  "confidence": "high",
  "confidence_reason": "directly documented referendum; community interpretation inferred from literature"
}
```

## ルール(厳守)
- `premise` は上の正準文字列を**一字も変えず**使う。
- 各 event の `affected_groups` は **9 community 全て**(欠損禁止)。
- `expected_mode` は PASSIVE / ACTIVE / REFRAME のいずれか1つ。
- `effect_emphasis`(必須):効いた作用軸タグ(例 `class_consciousness` / `national_identity` /
  `economic_anxiety` / `migration_status` / `political_agency` / `belonging_status` / `regional_identity` …)。
- `rationale` は1-2文(なぜその mode か)。
- **数値スコア(code_factors / salience_multiplier / effect_vector_delta 等)は出さない。** mode と rationale + effect_emphasis のみ。
- `base_effect_vector` / `agency` / `salience` / `sensitivity_peak_age` / `sensitivity_spread` は研究者としての較正値でよい(0.0-1.5程度)。
- 出力は **JSONL のみ**(前後の説明やコードフェンス不要)。
