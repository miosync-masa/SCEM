# Merge Report — Paper 2 US 版

## 入力

- ChatGPT 版 (`events_us_grid.jsonl`): **12** 件
- Gemini 版 (`Gemini_events_us_grid.jsonl`): **12** 件

## マッチング結果

- consensus(両方で名前一致): **12** 件
- chatgpt_only: **0** 件
- gemini_only: **0** 件
- 統合後 `events_us_merged.jsonl` 総数: **12** 件 (consensus 12 + singleton 0)

> 名前正規化: `/` と `(` の手前で英語部分を抽出(ハイフンは COVID-19/Dot-com 等の語内ハイフンのため切らない)。小文字化・記号除去・`vs`→`v` 統一・空白正規化。完全一致 + エイリアスのみ自動マージ。

### 人間レビュー要: Jaccard 0.7–1.0 候補(自動マージしていない)

- (なし)

### consensus events 一覧

- Black Lives Matter
- Civil Rights Act of 1964 / 公民権法
- COVID Restrictions
- Dobbs Decision
- Housing Surge
- Lehman Shock
- Obama Election / オバマ当選
- Obergefell v. Hodges
- Sandy Hook
- 9.11 同時多発テロ
- Student Debt Crisis
- Trump Election

### chatgpt_only


### gemini_only


## interpretations

- 総レコード数: **180**(chatgpt 96 / gemini 84)
- premise 正規化(religion_race_region_education 順へ並べ替え)した件数: **0**

## disagreements

- 総数: **80**
- premise 単位(解釈ベルト由来):
  - mode: 49
  - premise_only_in_chatgpt: 12
  - premise_only_in_gemini: 0
- event 単位 = observer-dependent labeling(premise=`_event_level`。矛盾ではなく、単一FACTのどの表示タグを選んだかの分散):
  - domain_observer_choice: 6
  - effective_year_interpretation: 3
  - reframe_group_axis_choice: 10

## Observer-dependent labeling(観測者依存ラベリング)

event 単位の不一致は **「矛盾」ではない**。単一の多次元 FACT に対して、どの次元を表示タグ(domain / effective_year の基準点 / reframe 軸)に選ぶかが観測者(LLM)ごとに分散しているだけである。`disagreements_{country}.jsonl` はこの分散を記録する **「LLM 観測者依存の証拠ファイル」** として読む。

- これは Paper 1 §3.4 設計ノート(**「イベントを単一カテゴリに潰さない / domain は表示タグであり計算には使わない」**)の **Paper 2 における反復確認**である。
  - 例(ACA): public_health / politics_institution / economy_employment に**同時に作用した FACT**。domain ラベルが割れるのは、複数次元のどれを表示タグに選ぶかの観測者依存にすぎない。
- 観察された系統的傾向: **ChatGPT は「何が起きたか」(事実層・LOD 0 寄り)**、**Gemini は「社会的に何を意味したか」(意味層・LOD 1 寄り)** に寄る。
  - domain: Apollo 11 / O.J. Simpson を ChatGPT=`media_technology`(技術事象)、Gemini=`lifestyle_culture`(文化的意味)。
  - effective_year: ACA を ChatGPT=2010(成立)、Gemini=2014(施行)。
  - reframe_group: Gemini は 9.11 / Katrina / January 6 を `national_security` / `trust_in_government` に集約しがち。
- 含意: **観測者依存は LOD 1 ではなく LOD 0(表示タグ層)から始まる**。ゆえに domain も本来 interpretation 側に属し得る(各レコードの `interpretation_note` 参照、`interpretive_axis` 列で手動分析)。

## warnings

- reframe_group: 10 件
- domain: 6 件

## 必須カバー event 在否(US)

- N/A(US の必須リストは未設定)
