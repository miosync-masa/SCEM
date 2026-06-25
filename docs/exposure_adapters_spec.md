# Exposure Adapters 実装仕様書 — SCEM の曝露構造を供給する層

**Status:** specification(将来実装。現時点の本体は curated_event_db + DeepResearch grid のみ稼働)
**Scope:** SCEM Core / CMR Layer の **下に置く曝露供給層(Exposure Adapters)** の設計と、その一つである **GDELT Adapter の仕様**。
**設計原則(巴):** GDELT を本体設計の中核に置かない。無料 API や運用制約に本体を引きずられないため、GDELT は **Information Exposure Adapter の仕様**に留める。本体はあくまで「実体曝露構造・情報曝露構造・Community/Code・年齢同期・3作用モード を分けて、最後に統合する」設計。

---

## 0. 全体アーキテクチャ

SCEM は三層 + 曝露供給層からなる。曝露 Adapter は**差し替え可能なデータ源**であり、本体(Core/CMR)はその出自に依存しない。

```text
┌──────────────────────────────────────────────┐
│ SCEM Core                                     │  Paper 1
│   年齢同期 / 3作用モード(PASSIVE,ACTIVE,REFRAME)│  (実装済)
│   effect_vector / interference / REFRAME fire │
├──────────────────────────────────────────────┤
│ CMR Layer                                     │  Paper 2
│   Community / Code / premise                  │  (実装済)
│   resolved_mode(agree/disagree/operational)   │
│   rationale / effect_emphasis / source_model  │
├──────────────────────────────────────────────┤
│ Exposure Adapters(差し替え可能なデータ源)      │  ← 本仕様書
│   ├ curated_event_db        実装済(JP 156件) │
│   ├ DeepResearch grid       実装済(US/UK grid)│
│   ├ official_statistics     将来(実体曝露)    │
│   ├ policy_datasets         将来(実体曝露)    │
│   └ gdelt_adapter           将来(情報曝露・仕様)│
└──────────────────────────────────────────────┘
```

本体(Core/CMR)が受け取るのは、出自を問わず正規化済みの **Event レコード**(`name / year / effective_year / effect_vector / salience / domain(表示タグ) / sensitivity_peak_age` …)である。Adapter の責務は「各データ源 → この正規化レコード」への変換に限定する。

---

## 1. 二種類の曝露構造を分ける

SCEM の将来拡張の核心は、**実体曝露構造と情報曝露構造を別系統として観測し、最後に統合する**ことにある。両者を混ぜると「報道が多い=生活が変わった」という誤った等値に陥る。

| | Material Exposure Structure(実体曝露) | Informational Exposure Structure(情報曝露) |
|---|---|---|
| 定義 | 制度・経済・物理・インフラの直接の着弾 | 報道・メディア・社会的言説・象徴的注目を介した曝露 |
| 例 | 雇用、就学、住宅、災害被害、法的地位、公衆衛生規制 | ニュース報道量、論調、SNS 言説、注目の集中 |
| データ源 | official_statistics / policy_datasets / 災害・住宅・労働記録 | gdelt_adapter / メディアアーカイブ |
| SCEM での役割 | effect_vector の実体成分・effective_year の接地 | salience・tone・burst・拡散・候補 REFRAME 期 |
| 誤用の禁止 | 「報道量で代理する」ことをしない | 「生活影響そのもの」とみなさない |

統合は **Core の effect_vector 上で行う**:情報曝露は salience と effective_attention_year を、実体曝露は effect_vector の実体成分と reference_value を供給する。どちらか一方では Event は完成しない。

---

## 2. GDELT Adapter Specification

GDELT は「社会そのもの」ではなく、**報道空間上に現れた情報曝露の波**を測る。本体に組み込まず、以下の入出力契約を満たす Adapter 仕様として定義する。

```text
GDELT Adapter Specification

目的:
  情報曝露構造 Informational Exposure Structure の自動観測

入力:
  event_keyword     対象事象を表すキーワード/クエリ
  actor             関与アクター(任意)
  location          地理スコープ(国/地域)
  time_range        観測期間
  language          言語
  region            集計地域単位

出力:
  media_observed_salience   報道空間で観測された顕著性
  tone_trajectory           論調(肯定/否定)の時系列推移
  burstiness                報道の集中度(バースト性)
  geographic_spread         地理的拡散
  language_spread           言語的拡散
  effective_attention_year  実効注目年(着弾年齢の計算に使う注目ピーク)
  candidate_reframe_periods  参照点書き換えが起きた候補期間

非対象(NOT measured):
  実体曝露構造そのもの
  個人の心理状態
  実際の制度影響・生活影響の完全測定
```

### 2.1 本体への接続点

- `effective_attention_year` → Core の着弾年齢計算(`year`/`effective_year` の情報曝露版)。報道ピークが実イベント年とずれる事象(遅効性スキャンダル等)で有用。
- `media_observed_salience` → Event の `salience`(情報曝露成分)。実体曝露の salience とは別系統で持ち、統合時に合成する。
- `candidate_reframe_periods` → REFRAME fire の**候補**を提示するに留める。発火判定は Core の reference_value 差分式が行う(Adapter は判定しない)。
- `tone_trajectory` / `burstiness` → CMR の rationale 補助・observer-dependence の文脈(§2.3 の「情報曝露の観測スタンスの差」)。

### 2.2 運用上の境界

- GDELT は **情報曝露 Adapter の一実装**であり、欠落・偏りがある。出力は「報道空間に現れた限りの」量であって母集団ではない。
- 無料 API・レート制限・GKG スキーマ変更などの運用制約は **Adapter 内に閉じ込め**、Core/CMR には波及させない。
- 実体曝露は GDELT で代理しない。必ず official_statistics / policy_datasets と突き合わせる。

---

## 3. 倫理的境界(プロダクト化時も不変)

このエンジンは **個人の内面を断定しない**。出力は次の形でのみ意味を持つ:

> ある出生年・共同体・文化嗜好・制度環境に置かれた人が、**どのような曝露構造を持ちやすいか**の推定。

すなわち SCEM は人を分類・上書き・優劣判定する道具ではなく、**異なる意味世界のあいだの翻訳地図**である(Paper 2 §6.4 の倫理宣言と一致)。Adapter 層がデータ源をどれだけ増やしても、この境界は越えない:

- 個人の心理状態を測定しない(GDELT 非対象に明記)。
- 共同体プロファイルは「その環境に置かれた人が持ちやすい曝露構造」であって、個人の断定ではない。
- 差異の由来(年齢・共同体・規範コード・実体曝露・情報曝露・身体化された参照点)は常に追跡可能に保つ(Provenance)。

---

## 4. 価値の三段(参考)

1. **研究ツール**:世代を出生年ラベルではなく曝露構造として再定義(Paper 1 + Paper 2)。
2. **マーケティングツール**:同じ年齢・嗜好でも Community/Code が違えば「自然だと思う選択肢・胡散臭いと感じる言葉」が変わる。コピー生成の裏側に置ける。
3. **社会分析ツール**:移民・宗教・階級・地域・教育・住宅・雇用・治安・災害・戦争・パンデミックを「出来事」ではなく**共同体ごとの作用変換**として扱う。

いずれも §3 の倫理的境界の下でのみ運用する。

---

## 5. 実装順序(巴の助言)

```text
今やる:    固定イベント × 固定コミュニティの完全グリッド(US/UK 完成済)
将来やる:  GDELT で報道量・トーン・地域拡散・バーストを拾う(本仕様)
もっと将来: 統計データと合わせ、情報曝露と実体曝露を分けて動的更新(Dynamic SCEM)
```

GDELT は Future 仕様に留め、まずは **US/UK 完全グリッド版 CMR** を固めることを最優先とする。
