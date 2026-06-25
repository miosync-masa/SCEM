# DeepResearch 投入プロンプト(US 完全グリッド)— そのまま貼る

> ※ これ1枚を ChatGPT(DeepResearch)と Gemini(DeepResearch)に**それぞれ同一で**貼る。
> 出力 JSONL を `data/events_us_grid.jsonl`(ChatGPT)/ `data/Gemini_events_us_grid.jsonl`(Gemini)に保存。

---

あなたは比較社会史の研究者です。**米国(US)** の以下の **12個の社会事象** それぞれについて、
下記の **8個の固定コミュニティ前提(premise)の すべて** に対し、その事象が各コミュニティにとって
**PASSIVE**(受動的に刷り込まれた背景)/ **ACTIVE**(意思決定・行動・動員を迫った)/
**REFRAME**(価値・所属・基準の書き換えを起こした)の **どれとして着弾したか** を1つ選び、
根拠(rationale)を1-2文で述べてください。

**重要**:同じ event 内であっても、各 premise ごとに mode が同じになる必要はありません。
**共同体前提によって mode が変換されるか**を検出するのが目的です。無理に一貫した mode へ寄せないこと。

## 12 events(event_id / 名前 / おおよその年 / exposure_type)
1. `us_civil_rights_act_1964` 公民権法(Civil Rights Act of 1964)/ 1964 / **inherited_baseline**(本分析の対象世代の出生前。直接曝露でなく、その後の社会コードの前提)
2. `us_sept11_2001` 9.11 同時多発テロ / 2001 / crisis_event
3. `us_obama_election_2008` オバマ当選 / 2008 / direct_event
4. `us_lehman_2008` リーマンショック(2008金融危機)/ 2008 / crisis_event
5. `us_student_debt_2012` 学生ローン債務の社会問題化 / ~2012 / policy_environment
6. `us_sandy_hook_2012` Sandy Hook 銃乱射と銃規制論争 / 2012 / crisis_event
7. `us_blm_2013` Black Lives Matter / 2013 / direct_event
8. `us_obergefell_2015` 同性婚合法化(Obergefell v. Hodges)/ 2015 / direct_event
9. `us_trump_election_2016` トランプ当選 / 2016 / direct_event
10. `us_covid_restrictions_2020` COVID-19 規制・ロックダウン / 2020 / crisis_event
11. `us_housing_surge_2021` 住宅価格高騰 / 2021 / diffusion_event
12. `us_dobbs_2022` Dobbs 判決(中絶権)/ 2022 / direct_event

## 8 communities(正準 premise — **改変せずそのまま使う**)
1. Coastal Liberal Urban → `secular_white_coastal_graduate`
2. Bible Belt Evangelical → `evangelical_white_bible_belt_no_college`
3. Rust Belt White Working Class → `mainline_protestant_white_rust_belt_no_college`
4. Black Urban Community → `secular_black_urban_some_college`
5. Latino Immigrant Community → `catholic_hispanic_urban_some_college`
6. Mormon / Utah → `mormon_white_mountain_west_bachelor`
7. Suburban Middle Class → `mainline_protestant_white_suburban_bachelor`
8. Rural Conservative → `evangelical_white_rural_no_college`

→ **12 events × 8 communities = 96 セル。affected_groups は毎回 8 premise 全てを必ず網羅(欠損禁止)。**

## 出力スキーマ(JSON Lines, 1行1イベント)
```json
{
  "event_id": "us_obergefell_2015",
  "country": "US",
  "name": "Obergefell v. Hodges / 同性婚合法化",
  "event_cluster": "lgbt_rights",
  "exposure_type": "direct_event",
  "year": 2015,
  "effective_year": 2015,
  "domain": "politics_institution",
  "possible_modes": ["PASSIVE", "ACTIVE", "REFRAME"],
  "base_effect_vector": {"family_definition": 0.9, "civic_norm": 0.8, "religious_identity": 0.7},
  "affected_groups": [
    {"premise": "secular_white_coastal_graduate", "expected_mode": "PASSIVE",
     "effect_emphasis": ["family_reference"], "rationale": "既に支持が定着しており、当然の権利確定として日常的に受容。",
     "rationale_scope": "community_interpretation"},
    {"premise": "evangelical_white_bible_belt_no_college", "expected_mode": "ACTIVE",
     "effect_emphasis": ["religious_norm", "family_reference", "political_mobilization"],
     "rationale": "宗教的家族規範への挑戦と受け取られ、投票・運動・共同体内態度表明を迫られる。",
     "rationale_scope": "community_interpretation"}
    /* …残り6 premise も必ず… */
  ],
  "source_scope": "national", "agency": 0.4, "salience": 1.4,
  "sensitivity_peak_age": 16, "sensitivity_spread": 6.0,
  "reframe_group": "lgbt_rights_baseline", "reference_value": null,
  "source_urls": ["https://..."],
  "confidence": "high",
  "confidence_reason": "directly documented legal event; community interpretation inferred from literature"
}
```

## ルール(厳守)
- `premise` は上の正準文字列を**一字も変えず**使う。
- 各 event の `affected_groups` は **8 community 全て**(欠損禁止)。
- `expected_mode` は PASSIVE / ACTIVE / REFRAME のいずれか1つ。
- `effect_emphasis`(US も必須):効いた作用軸タグ(例 `religious_norm` / `family_reference` /
  `political_mobilization` / `national_security` / `migration_status` / `economic_anxiety` / `racial_consciousness` …)。
- `rationale` は1-2文(なぜその mode か)。
- **数値スコア(code_factors / salience_multiplier / effect_vector_delta 等)は出さない。** mode と rationale + effect_emphasis のみ。
- `base_effect_vector` / `agency` / `salience` / `sensitivity_peak_age` / `sensitivity_spread` は研究者としての較正値でよい(0.0-1.5程度)。
- 出力は **JSONL のみ**(前後の説明やコードフェンス不要)。
