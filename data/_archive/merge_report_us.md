# Merge Report — Paper 2 US 版

## 入力

- ChatGPT 版 (`events_us_v1.jsonl`): **83** 件
- Gemini 版 (`Gemini_events_us_v1.jsonl`): **81** 件

## マッチング結果

- consensus(両方で名前一致): **24** 件
- chatgpt_only: **59** 件
- gemini_only: **57** 件
- 統合後 `events_us_merged.jsonl` 総数: **140** 件 (consensus 24 + singleton 116)

> 名前正規化: `/` と `(` の手前で英語部分を抽出(ハイフンは COVID-19/Dot-com 等の語内ハイフンのため切らない)。小文字化・記号除去・`vs`→`v` 統一・空白正規化。完全一致 + エイリアスのみ自動マージ。

### 人間レビュー要: Jaccard 0.7–1.0 候補(自動マージしていない)

- (なし)

### consensus events 一覧

- Affordable Care Act / オバマケア成立
- Black Monday stock crash / ブラックマンデー
- Brown v. Board of Education / ブラウン判決
- ChatGPT public release and generative AI shock / ChatGPT公開
- Civil Rights Act of 1964 / 公民権法
- Dobbs v. Jackson Women’s Health Organization / Dobbs判決
- Edward Snowden NSA disclosures / スノーデン暴露
- Fall of the Berlin Wall / ベルリンの壁崩壊
- Hurricane Katrina / ハリケーン・カトリーナ
- January 6 Capitol attack / 連邦議会議事堂襲撃
- Loving v. Virginia / 異人種間結婚合法化
- Montgomery Bus Boycott / モンゴメリー・バス・ボイコット
- Moon landing Apollo 11 / アポロ11号月面着陸
- O.J. Simpson trial verdict / OJシンプソン裁判
- Obergefell v. Hodges / 同性婚全国合法化
- Occupy Wall Street / オキュパイ運動
- Oklahoma City bombing / オクラホマシティ爆破事件
- Parkland shooting and March for Our Lives / パークランド銃乱射
- Roe v. Wade / ロー対ウェイド判決
- Sandy Hook Elementary shooting / サンディフック銃乱射
- September 11 attacks / 9.11同時多発テロ
- Three Mile Island nuclear accident / スリーマイル島事故
- Uvalde Robb Elementary shooting / ユヴァルディ銃乱射
- Voting Rights Act of 1965 / 投票権法

### chatgpt_only

- 1973 Oil crisis / 第一次石油危機
- 2020 election and mail voting dispute / 2020年選挙と郵便投票論争
- 2024 presidential election and Trump return / 2024年大統領選・トランプ復帰
- Afghanistan War begins / アフガニスタン戦争開始
- Afghanistan withdrawal / アフガニスタン撤退
- AIDS crisis recognized / AIDS危機
- Americans with Disabilities Act / 障害者法
- Bakke decision and affirmative action debate / バッキ判決
- Black Lives Matter hashtag begins / BLM起点
- Bush v. Gore and 2000 election dispute / 2000年大統領選挙訴訟
- Challenger disaster / チャレンジャー号爆発事故
- Charlottesville Unite the Right rally / シャーロッツビル事件
- Citizens United decision / シチズンズ・ユナイテッド判決
- Clinton impeachment / クリントン弾劾
- Columbine High School shooting / コロンバイン高校銃乱射
- COVID-19 pandemic restrictions / コロナ規制
- COVID vaccines and mandates / コロナワクチン・義務化
- Crack cocaine epidemic becomes national issue / クラック流行
- Cuban Missile Crisis / キューバ危機
- Dot-com bubble peak / ドットコム・バブル
- Ebola scare in the United States / エボラ不安
- Facebook launch and social networking / FacebookとSNS普及
- Family separation at US border / 国境家族分離
- Ferguson unrest after Michael Brown / ファーガソン抗議
- Financial crisis and Lehman collapse / リーマンショック
- First Trump impeachment / 第一次トランプ弾劾
- George Floyd killing and BLM peak / ジョージ・フロイド後BLMピーク
- Gulf War / 湾岸戦争
- Housing bubble and subprime lending peak / 住宅バブル・サブプライム
- Housing price surge and affordability crisis / 住宅価格高騰
- Inflation surge and gas prices / インフレ・ガソリン高
- iPhone launch / iPhone登場
- Iraq War begins / イラク戦争開始
- Israel-Hamas war and US campus protests / ガザ戦争と米大学抗議
- Kent State shootings / ケント州立大学銃撃
- March on Washington and I Have a Dream / ワシントン大行進
- MeToo movement / #MeToo運動
- MTV launch and cable youth culture / MTVとケーブル文化
- NAFTA passage / NAFTA成立
- Nixon ends gold convertibility / ニクソン・ショック
- No Child Left Behind / 落ちこぼれ防止法
- Obama elected president / Obama当選
- PATCO strike firing / 航空管制官スト解雇
- Plaza Accord and dollar realignment / プラザ合意
- Reagan election and conservative turn / レーガン革命
- Rodney King beating and LA riots / ロドニー・キング事件とLA暴動
- Russia invades Ukraine / ロシアのウクライナ侵攻
- Same-sex marriage public majority and pre-Obergefell shift / 同性婚世論多数化
- Sputnik launch and space race shock / スプートニク・ショック
- Students for Fair Admissions decisions / 大学入試アファーマティブアクション判決
- Tea Party movement / ティーパーティー運動
- Telecommunications Act and media deregulation / 通信法改正
- Trump elected president / Trump当選
- TSA and airport security normalization / TSAと空港保安常態化
- USA PATRIOT Act / 愛国者法
- Vietnam War escalation and draft / ベトナム戦争拡大と徴兵
- Watergate and Nixon resignation / ウォーターゲートとニクソン辞任
- World Wide Web enters mass culture / ウェブ普及
- YouTube launch and online video norm / YouTube普及

### gemini_only

- Agentic AI & Generative Video Boom / Sora Release (2024-2025 Creative AI Inception / Soraなどの超リアルな生成動画・AIエージェントの爆発的台頭)
- Bill Clinton Presidential Election (1992 'It's the Economy, Stupid' / ビル・クリントン大統領選出と中道第三の道)
- Black Lives Matter Inception (2013 Zimmerman Verdict / 『ブラック・ライブズ・マター』運動の創設と人種正義)
- Boston Marathon Bombing (2013 Sports Terror Event / ボストンマラソン爆弾テロ事件による監視の肯定)
- Bush v. Gore / 2000 Election Crisis (Democracy Trust Controversy / 2000年大統領選挙紛争と最高裁判断)
- Citizens United v. FEC (2010 Corporate Political Speech Landmark / 政治資金無制限化を認めた最高裁判決)
- Clinton Impeachment and Lewinsky Scandal (1998 Presidential Trust / クリントン大統領弾劾裁判とモラルの揺らぎ)
- Columbine High School Massacre (1999 Gun Violence Inception / コロンバイン高校銃乱射事件と学校安全神話の崩壊)
- COVID-19 Pandemic Lockdowns & Business Closures (2020 State of Emergency / 新型コロナウイルスパンデミックに伴う全米ロックダウン)
- COVID-19 Vaccine Rollout and Mandates Polarization (2021 Polarization Crisis / ワクチン義務化と社会的分裂)
- Deepwater Horizon Oil Spill (2010 Environmental Disaster / メキシコ湾原油流出事故と環境規制不信)
- DOMA Struck Down and Windsor Verdict (2013 LGBTQ Landmark Precursor / 連邦結婚保護法の否定と同性婚合法化の前哨戦)
- Donald Trump Criminal Conviction & 2024 Trials (National Trust Polarization / トランプ前大統領への有罪判決と司法の二極化)
- Donald Trump Presidential Election (2016 Red/Blue Polarization / ドナルド・トランプ大統領当選とポピュリズムの台頭)
- Election of Barack Obama (2008 Racial Reframe / オバマ大統領選出と『Yes We Can』人種対立の変容)
- Emergence of the AIDS Crisis and Naming (1982 LGBTQ Crisis Peak / AIDS危機の本格化と社会的混乱)
- Fall of Saigon and End of Vietnam War (1975 Loss of Hegemony / サイゴン陥落とベトナム戦争の終結による挫折感)
- Federal TikTok Ban Bill Signed (2024 Social Platform Geopolitics / TikTok強制売却・禁止法の署名成立)
- First Oil Crisis and Energy Panic (1973 Inflation Surge / 第一次オイルショックとエネルギー危機)
- Garn-St. Germain Depository Institutions Act (1982 Housing Finance Deregulation / 貯蓄貸付組合の自由化と住宅市場金融化)
- George Floyd Murder & BLM Peak Protests (2020 Anti-racist Awakening / ジョージ・フロイド殺害事件とBLM大抗議運動)
- Great Recession and Lehman Shock (2008 Financial Meltdown / リーマン・ショックと世界同時金融危機)
- Inflation Reduction Act of 2022 (Green Energy Funding / インフレ抑制法の成立とグリーンテクノロジー投資への大転換)
- Invasion of Iraq (2003 Pre-emptive War Controversy / イラク戦争と予防戦争をめぐる世界的抗議)
- JFK Assassination (1963 National Trauma / ケネディ大統領暗殺事件と国民的喪失)
- Kent State Shootings and Vietnam War Protest Peak (1970 Activism Crackdown / ケント州立大学銃撃事件と反戦運動の絶頂)
- Launch of Bitcoin and Genesis Block (2009 Cryptography Currency Inception / ビットコインの誕生とデジタル資産思想の創始)
- Launch of Facebook (2004 Social Media Era / Facebookの登場とソーシャルネットワーキングの常識化)
- Launch of the IBM Personal Computer (1981 Digitalization Dawn / IBM PC発売とパソコン時代の夜明け)
- Launch of the iPhone (2007 Mobile Internet Dawn / 初代iPhone発売と常時接続社会の到来)
- Launch of Twitter (2006 Real-time Broadcast Shift / Twitterの登場と情報流通のリアルタイム化)
- Launch of YouTube (2005 UGC and Online Video Dawn / YouTubeの誕生とオンライン動画の普及)
- MeToo Movement Peak (2017 Gender and Power Shift / MeToo運動の世界的爆発とジェンダーパワーバランスの変容)
- NAFTA Agreement Signed (1994 Globalization Shift / 北米自由貿易協定の本格稼働と雇用のグローバル化)
- Netscape IPO / Dot-com Boom Start (1995 Internet Publicization / ネットスケープのIPOとインターネットの商用化)
- Nixon Shock / Gold Standard Abandonment (1971 Decoupling of Dollar / ニクソン・ショックと金本位制からの離脱)
- Persian Gulf War (1991 Operation Desert Storm / 湾岸戦争とアメリカの圧倒的軍事力の再確認)
- Plaza Accord (1985 Inter-governmental Dollar Depreciation / プラザ合意とドル高修正)
- Post-Pandemic Inflation and Housing Price Surge (2021 Case-Shiller Peak / パンデミック後の超インフレと狂乱の住宅価格急騰)
- Reagan Presidential Election and Conservative Triumph (1980 Reaganomics Beginning / レーガン大統領誕生と保守革命)
- Rise of Netflix Streaming and Cord-cutting (2011 Media Revolution / Netflixのストリーミング台頭とテレビ離れ)
- Rise of Uber and Sharing Economy (2012 Gig Work Evolution / Uberの台頭とギグエコノミーによる労働の流動化)
- Rodney King Riots / LA Riots (1992 Social Justice Movement / ロドニー・キング判決とLA暴動)
- Savings and Loan Crisis Peak and Bailout (1989 Financial Crisis / S&L危機の露呈と金融救済法成立)
- Silicon Valley Bank Collapse (2023 High-Tech Financial Run / シリコンバレー銀行の破綻とスタートアップ金融パニック)
- Space Shuttle Challenger Disaster (1986 National Loss / スペースシャトル・チャレンジャー号爆発事故)
- Sputnik Launch and Shock (1957 Space Race Trigger / スプートニク・ショックと宇宙競争の幕開け)
- Stonewall Riots (1969 LGBTQ Awakening / ストーンウォール暴動とゲイ・リベレーションの起源)
- Strong Dollar Peak & Fed Rate Hikes (2022 Global Monetary Tightening / FRBによる積極利上げとドル高のピーク)
- Subprime Mortgage Crisis Peak (2006 Foreclosure Waves / サブプライム住宅ローン危機の表面化と住宅バブルの崩壊)
- Supreme Court Ends College Affirmative Action in SFFA v. Harvard (2023 Education Merit Shift / 最高裁による大学入試優遇措置の廃止判決)
- Waco Siege (1993 Federal Overreach Controversy / ウェーコ包囲事件と連邦政府への懐疑)
- Watergate Scandal and Resignation of Richard Nixon (1974 Distrust of Power / ウォーターゲート事件とニクソン大統領辞任)
- Weak Dollar Low Point (2008 Aggressive Monetary Policy / 超低金利とドル指数の歴史的低水準)
- Welfare Reform Act of 1996 (Personal Responsibility Legislation / 福祉改革法の成立と個人責任原則の徹底)
- WGA & SAG-AFTRA Hollywood Strike (2023 Creative Labor Battle / ハリウッド脚本家・俳優組合ストライキによるAI対抗運動)
- WikiLeaks Disclosures and Manning Scandals (2010 Geopolitical Truth Leak / ウィキリークス外交電文リークとチェルシー・マニング事件)

## interpretations

- 総レコード数: **450**(chatgpt 249 / gemini 201)
- premise 正規化(religion_race_region_education 順へ並べ替え)した件数: **60**

## disagreements

- 総数: **150**
- premise 単位(解釈ベルト由来):
  - mode: 1
  - premise_only_in_chatgpt: 69
  - premise_only_in_gemini: 62
- event 単位 = observer-dependent labeling(premise=`_event_level`。矛盾ではなく、単一FACTのどの表示タグを選んだかの分散):
  - domain_observer_choice: 4
  - effective_year_interpretation: 3
  - reframe_group_axis_choice: 11

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

- reframe_group: 11 件
- domain: 4 件
- effective_year: 1 件

## 必須カバー event 在否(US)

- [x] Roe v. Wade
- [x] Dobbs
- [x] Obergefell
- [x] 9.11 / September 11
- [x] Lehman / リーマン
- [x] Obama当選
- [x] BLM
- [x] Trump当選
- [x] コロナ規制
- [x] 銃乱射 (shooting)
- [x] AIDS
- [x] 公民権法 / Civil Rights Act
- [x] 投票権法 / Voting Rights Act
