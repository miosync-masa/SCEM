# Paper 2 完全グリッド仕様(US / UK)— DeepResearch 再実行用

目的: 現データの `—`(欠損)を消し、「探索結果」ではなく **設計された比較行列** にする。
固定 Community × 固定 Event の **完全グリッド** で DeepResearch を回す(巴さん優先タスク)。

出力は既存パイプライン(`merge_paper2_data.py` → `cmr_matrix.py` / `cmr_compare.py`)に
そのまま流せる JSONL スキーマで返す。

---

## 1. 固定 Community(= premise 文字列)

各 Community に **正準 premise 文字列**を1つ割り当てる(出力の premise をこれに固定 → 照合の曖昧さを排除)。

### US(8 communities)— `religion_race_region_education`

| Community | premise(正準) |
|---|---|
| Coastal Liberal Urban | `secular_white_coastal_graduate` |
| Bible Belt Evangelical | `evangelical_white_bible_belt_no_college` |
| Rust Belt White Working Class | `mainline_protestant_white_rust_belt_no_college` |
| Black Urban Community | `secular_black_urban_some_college` |
| Latino Immigrant Community | `catholic_hispanic_urban_some_college` |
| Mormon / Utah | `mormon_white_mountain_west_bachelor` |
| Suburban Middle Class | `mainline_protestant_white_suburban_bachelor` |
| Rural Conservative | `evangelical_white_rural_no_college` |

### UK(9 communities)— `class_region_origin_generation_education`

| Community | premise(正準) |
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

## 2. 固定 Event

### US(12 events)
同性婚合法化(Obergefell)/ 9.11 / 2008 リーマン / オバマ当選 / トランプ当選 / BLM /
Dobbs(中絶権)/ COVID規制 / 銃乱射・銃規制(Sandy Hook 等)/ 学生ローン / 住宅価格高騰 / 公民権法

### UK(13 events)— LGBT 系は分割(巴さん案A)
Brexit 国民投票 / 7-7 ロンドン爆破 / 2008 金融危機 / 緊縮(Austerity)/ Windrush /
COVID ロックダウン / NHS 危機 / 生活費危機 / 大学授業料引き上げ / 移民・難民論争 /
スコットランド独立投票 /
**Section 28 撤廃(2003, 公教育の Code 変化)** /
**同性婚合法化(2014, 婚姻・家族制度の Code 変化)**

> Section 28 撤廃と同性婚合法化は **作用ベクトルが違う**(学校・公教育 vs 婚姻・家族)ため別イベント。
> 両者は `event_cluster: "lgbt_rights"` で束ねる。

→ **US 8×12 = 96 セル / UK 9×13 = 117 セル**(欠損ゼロ目標)

---

## 3. DeepResearch 出力スキーマ(既存パイプライン互換)

各 event を1行(JSONL)。**affected_groups に上記 community の正準 premise を全て含める**(=各イベントで全 community を必ず評価)。

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
  "base_effect_vector": {"...": 0.0},
  "affected_groups": [
    {"premise": "secular_white_coastal_graduate", "expected_mode": "PASSIVE",
     "effect_emphasis": ["family_reference"], "rationale": "...",
     "rationale_scope": "community_interpretation"},
    {"premise": "evangelical_white_bible_belt_no_college", "expected_mode": "ACTIVE",
     "effect_emphasis": ["religious_norm", "family_reference", "political_mobilization"],
     "rationale": "...", "rationale_scope": "community_interpretation"}
    /* … 全 community 分(US 8 / UK 9)… */
  ],
  "source_scope": "national", "agency": 0.4, "salience": 1.3,
  "sensitivity_peak_age": 16, "sensitivity_spread": 6.0,
  "reframe_group": null, "reference_value": null,
  "source_urls": ["https://..."],
  "confidence": "high",
  "confidence_reason": "directly documented legal event; community interpretation inferred from historical literature"
}
```

**必須**:
- **`event_id`**(必須・安定キー):`{country}_{slug}_{year}` 形式。英/日表記ゆれ・後続バージョンに強い。照合は将来 event_id 優先。
- **`exposure_type`**(必須):下記語彙のいずれか。pre-birth event(例:公民権法)を `inherited_baseline` として扱える。
- **`event_cluster`**(必須):関連事象の束(例 `lgbt_rights`)。UK の LGBT 系を分割しても束ねられる。
- 各イベントの `affected_groups` は **固定 community 全てを網羅**(欠損禁止)。
- `premise` は §1 の正準文字列を**そのまま**使う(表記揺れ禁止)。
- `expected_mode` は PASSIVE/ACTIVE/REFRAME のいずれか1つ。
- **`effect_emphasis`**(US/UK 共通・必須):効いた作用ベクトル軸のタグ(例 `religious_norm` / `family_reference` / `political_mobilization` / `national_security` / `migration_status` / `economic_anxiety` …)。後の Code 層数値化の足場。
- `rationale`(なぜその mode か, 1-2文)+ `rationale_scope`(既定 `community_interpretation`)。
- `confidence`(high/medium/low)+ `confidence_reason`(短文)。数値化は無理にさせない(Honest)。
- **数値スコア(code_factors / salience_multiplier / effect_vector_delta 等)は要求しない**(rationale + effect_emphasis で足りる。数値化は別タスク)。

### exposure_type 語彙

| 値 | 用途 |
|---|---|
| `direct_event` | 本人が直接曝露(通常) |
| `diffusion_event` | 技術・文化の普及(effective_year がずれる) |
| `crisis_event` | 危機・災害 |
| `policy_environment` | 制度環境(継続的) |
| `inherited_baseline` | **本人の出生前**の事象。直接曝露でなく、その後の社会コードの前提として継承(例:1964 公民権法を 1985 生まれが「経験」はしないが、その後のコードの中で育つ) |

→ `inherited_baseline` の事象は `age < 0` になるため、**直接の着弾計算(感受性カーブ)には乗せず、Community/Code の baseline として扱う**(`applies_to_birth_cohorts: as_community_code_baseline`)。

---

## 4. DeepResearch プロンプト雛形

> あなたは比較社会史の研究者です。{COUNTRY} の以下の {N} 個の社会事象それぞれについて、
> 下記の {M} 個の固定コミュニティ前提(premise)の **すべて** に対し、その事象が
> 各コミュニティにとって PASSIVE(受動的に刷り込まれた背景)/ ACTIVE(意思決定・行動・
> 動員を迫った)/ REFRAME(価値・所属・基準の書き換えを起こした)の **どれとして着弾したか**
> を1つ選び、根拠(rationale)を1-2文で述べてください。
>
> 出力は §3 の JSONL スキーマ。premise は与えた正準文字列を**改変せず**使うこと。
> 各事象の affected_groups は **全コミュニティを必ず網羅**(欠損禁止)。出典 URL を付けること。
> 数値スコアは不要。mode と rationale + effect_emphasis(US/UK 共通)、event_id / exposure_type / event_cluster を付ける。
>
> **重要**:同じ event 内であっても、各 premise ごとに mode が同じになる必要はない。
> 共同体前提によって mode が変換されるかを検出することが目的である。無理に一貫した mode へ寄せないこと。
>
> [events リスト] … [communities(正準premise)リスト] を貼付。

ChatGPT 版と Gemini 版を**同一プロンプト**で別々に回す → 2モデルの observer-dependence(§Paper2)を保つ。

---

## 5. 取り込み手順

```bash
# 取得した2ファイルを配置(命名規約):
#   data/events_{country}_grid.jsonl          (ChatGPT)
#   data/Gemini_events_{country}_grid.jsonl   (Gemini)
# 破損していれば recover_gemini_jsonl.py で復旧。
# merge は入力名を grid 版に向ければ流せる(or v1 を置換)。
python3 src/merge_paper2_data.py --country us     # consensus/interpretations/disagreements 再生成
python3 src/cmr_matrix.py  --country us           # 欠損ゼロの mode 変換マトリクス
python3 src/cmr_compare.py --country us --birth_year 1985
python3 src/make_paper2_figures.py                # Fig2/Fig3 を欠損なしで再描画
```

完全グリッドになれば、Fig2(Same Event × Community)は `—` の無い密な行列になり、
Event-level / Cell-level MFR・CDI が **設計された母数**の上で算出できる。

---

## 6. 注意(現データとの差)

- 現 v1 データは各イベント 3-6 premise のみ(探索的)。本グリッドは**全 community 網羅**が前提。
- US `Rust Belt`、UK `Scotland / Northern Ireland` は現 v1 で希薄 → 本グリッドで解消される。
- premise 正準文字列(§1)は提案。最終確定は環 & masamichi が監修。
