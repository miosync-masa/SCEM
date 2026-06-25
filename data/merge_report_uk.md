# Merge Report — Paper 2 UK 版

## 入力

- ChatGPT 版 (`events_uk_v1.jsonl`): **80** 件
- Gemini 版 (`Gemini_events_uk_v1.jsonl`): **28** 件

## マッチング結果

- consensus(両方で名前一致): **10** 件
- chatgpt_only: **70** 件
- gemini_only: **18** 件
- 統合後 `events_uk_merged.jsonl` 総数: **98** 件 (consensus 10 + singleton 88)

> 名前正規化: `/` と `(` の手前で英語部分を抽出(ハイフンは COVID-19/Dot-com 等の語内ハイフンのため切らない)。小文字化・記号除去・`vs`→`v` 統一・空白正規化。完全一致 + エイリアスのみ自動マージ。

### 人間レビュー要: Jaccard 0.7–1.0 候補(自動マージしていない)

- (なし)

### consensus events 一覧

- 7/7 London bombings / ロンドン同時爆破
- EU enlargement migration / EU拡大後の移民増加
- Good Friday Agreement / 北アイルランド和平合意
- Grenfell Tower fire / グレンフェル火災
- NHS waiting-list record crisis / NHS待機リスト記録的危機
- Partygate scandal / パーティーゲート
- Queen Elizabeth II death / エリザベス2世崩御
- Scottish independence referendum / スコットランド独立投票
- Suez Crisis / スエズ危機
- Windrush scandal / ウィンドラッシュ・スキャンダル

### chatgpt_only

- 1973 oil crisis and inflation shock / オイルショック
- 1975 EEC referendum / EEC残留国民投票
- 1981 inner-city riots / ブリクストン等都市暴動
- 2008 global financial crisis / 2008金融危機
- 2011 England riots / 2011年イングランド暴動
- 2015 majority Conservative government / 保守党単独政権
- 2024 general election and Starmer government / 2024総選挙・労働党政権
- Abolition of death penalty in Great Britain / 死刑廃止
- AIDS crisis in the UK / AIDS危機
- Austerity begins / 緊縮財政開始
- Beatlemania and 1960s youth culture / ビートルズと若者文化
- Big Bang deregulation of the City / シティ金融ビッグバン
- Brexit referendum / EU離脱国民投票
- Brexit transition ends / EU離脱完了
- BSE mad cow disease crisis / BSE危機
- Channel crossings become national issue / 小型ボート海峡横断問題
- Channel Tunnel opens / 英仏海峡トンネル開通
- Charles III coronation / チャールズ3世戴冠
- Civil Partnership Act / シビルパートナーシップ法
- Climate Change Act 2008 / 気候変動法
- Coal power phase-out completed / 石炭火力終了
- Commonwealth Immigrants Act 1962 / 英連邦移民法
- Cost of living and energy price crisis / 生活費・エネルギー危機
- COVID-19 lockdown regulations / コロナ規制
- COVID vaccine rollout / ワクチン展開
- Decimalisation of UK currency / 十進法通貨移行
- Devolution: Scotland and Wales / 分権改革
- England wins the FIFA World Cup / 1966年W杯優勝
- Equality Act 2010 / 平等法
- EU referendum aftermath and hate-crime anxiety / Brexit直後の所属不安
- Falklands War / フォークランド戦争
- Foot-and-mouth disease outbreak / 口蹄疫
- Help to Buy begins / Help to Buy開始
- Hong Kong handover / 香港返還
- House price boom 1997-2007 / 住宅価格一次高騰
- Human Rights Act 1998 / 人権法
- Hunting Act / 狐狩り禁止
- IMF crisis and sterling bailout / IMF危機
- Iraq War vote and invasion / イラク戦争
- London 2012 Olympics / ロンドン五輪
- London wins 2012 Olympics bid / ロンドン五輪決定
- Maastricht Treaty and ERM crisis / マーストリヒトとERM危機
- Millennium Dome and new millennium / ミレニアム
- Miners strike / 炭鉱ストライキ
- Mini-budget and mortgage shock / ミニ予算と住宅ローンショック
- MPs expenses scandal / 議員経費スキャンダル
- Net zero law / ネットゼロ法制化
- New Labour landslide / ブレア政権成立
- NHS post-austerity capacity strain / NHS緊縮後の逼迫
- Notting Hill race riots / ノッティングヒル人種暴動
- Poll Tax crisis / 人頭税危機
- Post-war rationing ends / 戦後配給終了
- Powell Rivers of Blood speech / パウエル演説
- Princess Diana death / ダイアナ妃死去
- Privatisation wave / 民営化の波
- Record net migration debate / 純移民数記録と政治争点化
- Right to Buy introduced / 公営住宅購入権
- Same-sex marriage legalised in England and Wales / 同性婚合法化
- Section 28 enacted / セクション28
- September 11 and UK security alignment / 9.11と対テロ同盟
- Thatcher election and market turn / サッチャー政権成立
- The Troubles intensify / 北アイルランド紛争の激化
- Top-up fees 3000 pounds / トップアップ授業料
- Tuition fee cap reaches 9250 pounds / 授業料9250ポンド化
- Tuition fees introduced / 大学授業料導入
- UK joins the EEC / EEC加盟
- UKIP and immigration politics surge / UKIP躍進と移民政治化
- University tuition cap raised to 9000 pounds / 大学授業料9000ポンド化
- Welfare Reform Act and benefits restructuring / 福祉改革
- Winter of Discontent / 不満の冬

### gemini_only

- 2008 Financial Crisis and Austerity (リーマンショックと緊縮財政)
- Aberfan Disaster (アベルファン炭鉱ボタ山崩落事故)
- Black Wednesday (ブラックウェンズデー/ポンド危機)
- Brexit referendum and withdrawal (EU離脱国民投票と完了)
- Channel Crossings Small Boats Surge (英仏海峡小型ボート移民問題)
- Cost of Living Crisis and House Price Surge (生活費危機と住宅価格再高騰)
- COVID-19 Pandemic and Lockdowns (新型コロナとロックダウン)
- Death of Diana, Princess of Wales (ダイアナ妃死去)
- EEC Accession (EEC加盟)
- Fuel Protests (燃料税抗議デモ)
- Maastricht Treaty (マーストリヒト条約)
- Miners' Strike and Coal Closures (炭鉱ストライキと民営化)
- NHS Establishment (国民保健サービス設立)
- Right to Buy Scheme Introduction (公営住宅払下げ政策)
- Section 28 Enactment (セクション28/同性愛宣伝禁止法)
- Stephen Lawrence Macpherson Report (マクファーソン報告書/制度的人種差別)
- University Tuition Fees Hike to £9,000 (大学授業料大幅引き上げ)
- Welfare Reform Act and Bedroom Tax (寝室税/福祉改革)

## interpretations

- 総レコード数: **273**(chatgpt 245 / gemini 28)
- premise 正規化(religion_race_region_education 順へ並べ替え)した件数: **0**

## disagreements

- 総数: **52**
- premise 単位(解釈ベルト由来):
  - mode: 0
  - premise_only_in_chatgpt: 30
  - premise_only_in_gemini: 9
- event 単位 = observer-dependent labeling(premise=`_event_level`。矛盾ではなく、単一FACTのどの表示タグを選んだかの分散):
  - domain_observer_choice: 3
  - effective_year_interpretation: 4
  - reframe_group_axis_choice: 6

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

- reframe_group: 6 件
- domain: 3 件
- effective_year: 1 件
- year: 1 件

## 必須カバー event 在否(UK)

- N/A(UK の必須リストは未設定)
