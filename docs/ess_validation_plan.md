# ESS 実証プラン(UK/Europe secondary validation)— 確定設計

**作成:** 環 → 黒子実装 / **確認:** 真道さま / **日付:** 2026-06-27
**親:** spec 0.2(GSS確定)/ findings §2.5–2.8 / 巴 ESS 設計メモ
**位置づけ:** GSS(US) と**対称**な UK/Europe 外部照合。Paper 2 "A Cross-National Extension" を実証で履行。
**状態:** 設計確定・パイプライン実装済・**ESS 実データ投入待ち**(§D)。GSS と同一作法(確定のみ実装/未決は決め打ちせず/spin しない/綻び記録)。

---

## A. 立ち位置(厳守・GSS と同じ構え)

```
GSS      = US 側 secondary validation(態度軌跡の外部照合)
ESS      = UK/Europe 側 secondary validation ← 本プラン
Prolific = 主観的 mode 経験の本検証(Paper 3)
```

ESS は **mode を直接測らない**。CMR が予測した共同体差が欧州/UK の態度軌跡に対応するかの外部照合。
強度の言葉:「**予測対応・modest**」。「確証」と書かない。

## B. 【最重要・銃の教訓】事象の時間構造で 3 本柱を事前振り分け(EVENT_STRUCTURE)

GSS で銃=反復バースト=出生年で割れない=観測装置ミスマッチ。**ESS でも検証前に必ず時間構造をかける**
(怠ると反復イベントの flat を「CMR 外れ」と誤読=UK で銃の罠を踏み直す)。

| 柱 | ESS変数 | 時間構造 | 出生年勾配 | 扱い |
|---|---|---|---|---|
| **LGBT寛容** | `freehms` | **単発モーメント型**(合法化モーメント・GSS同性婚と対応) | 出る見込み | **主検証(step1)** |
| **EU統合** | `euftf` | **反復バースト疑い**(マーストリヒト→ユーロ危機→難民危機→Brexit) | 出ない可能性 | flat でも事前織込み・誤読しない |
| **移民** | `imbgeco`/`imueclt`/`imwbcnt` | **反復バースト濃厚**(慢性・選挙毎バースト・全世代継続曝露) | 出ない見込み | 同上 |

- **`freehms` を主検証に**(GSS 同性婚と直接対応 → **US-UK 同一事象のクロスナショナル比較**=目玉)。
  freehms = "Gay men and lesbians should be free to live their own life as they wish"(1 Agree strongly … 5 Disagree strongly)。寛容 = {1,2}。
- euftf(0 gone too far … 10 go further、Pro-EU=高)/ 移民 index = mean(imbgeco, imueclt, imwbcnt)(各 0 bad … 10 good、Pro=高)。
- euftf/移民 が flat なら「反復ゆえ出生年軸で観測不能」を**事前の構造的理由**として記述(後付けにしない)。

## C. セグメント(UKグリッド9共同体を再現しない・proxy 2段)

```
A. UK-only replication(補助・N薄): UK内 proxy 近似
   - high-edu London/urban / lower-edu non-metro working-class / immigrant-background
B. Europe-wide validation(本命): country × community proxy × cohort
```

**proxy 軸:** birth cohort(yrbrn)/ country(cntry)/ education(eduyrs, edulvlb)/ urban-rural(domicil)/
religiosity(rlgdgr)/ immigrant background(brncntr,facntr,mocntr,blgetmg)/ class・occupation proxy。
**N 強度ルール(GSS同一):** 厚→検定で強主張、薄(NI 等)→ CI 広く弱主張 or 「ESS では検証力不足」と宣言。
NI 細粒度は BSA/NILT/Understanding Society 向き(Limitation に明記)。
**重み:** ESS は post-strat weight 公開済 → **最初から重み付き**(`anweight` 優先、無ければ `pspwght`×`pweight`)。

## D. データ取得(実データ投入待ち)

ESS は登録制で配布が SAS トークン認証付き → **自動 curl 不可**。利用者が取得して配置:
1. ESS Data Portal(europeansocialsurvey.org / ess-search.nsd.no / Sikt)で無料登録・ログイン。
2. **integrated rounds(ESS1–ESS11)** の Stata 形式をダウンロード(per-round でも cumulative でも可)。
3. `data/ess/` に置く(`.dta`/`.sav`)。`data/ess/` は .gitignore(生データはリポジトリに入れない)。
4. `python3 src/adapters/ess/ess_acquire.py` → 必要列を slim parquet 化(`data/ess/ess_slim.parquet`)。

> 取得できれば §B/§C/§E は即走る(コード実装済)。捏造はしない=データが来るまで結果は出さない。

## E. 実装(着手順・巴案=最小一発から)

- **step1(本命):Europe-wide, `freehms` 主検証** — high religiosity vs low / high-edu vs low / country clusters
  で high-flat / transition を見る → **US 同性婚(GSS)と並置**(目玉図)。`src/adapters/ess/ess_core_validation.py`。
- step2:UK-only, `euftf`(出生年スロープ。§B 反復疑い=flat でも誤読しない)。
- step3:`immigration_index = mean(imbgeco,imueclt,imwbcnt)`(国・教育・移民背景・出生年)。§B 反復濃厚。
- step4:overlay — UKグリッドの grid 事前 resolved_mode × ESS 割れ → 予測対応集計。
  Brexit は euftf を proxy(ESS で直接測れない)。grid に無い事象は探索的に分離(GSS 移民と同作法)。

## F. 普遍性の主張(§5・Discussion で効かせる)

US と UK で**共同体軸 that 自体が違う**(US=宗教×人種×地域×学歴 / UK・Europe=階級×地域×移民世代×EU距離×religiosity×country)。
これは弱点でなく **CMR が特定の共同体軸に依存しない普遍的作用素**である証拠:

> ゲートする軸は国で違うが、「共同体コードが事象をモードに解決する」CMR の作用は両国で成立する。

実装では「軸が違っても high-flat/transition の二分が両国で再現するか」を見る。

## G. 主仮説(巴案・確定)

- **H-ESS1**:euftf は出生年だけでなく教育・階級近似・都市性・移民背景でスロープが変わる【反復疑い→§B 織込み】。
- **H-ESS2**:移民態度は London/educated/immigrant-bg 側で高位・平坦/REFRAME的安定、post-industrial/low-edu/leave 側で勾配 or 低位飽和【反復濃厚→§B】。
- **H-ESS3**:freehms は US 同性婚と同様、リベラル高教育都市層で高位平坦、宗教性・低教育・地方保守近似層で出生年勾配【単発→主検証】。

## H. Paper への入れ方(巴案・確定)

```
5.5 External validation with existing surveys
  5.5.1 GSS: US same-sex marriage and issue-specific trajectories
  5.5.2 ESS: UK/Europe — LGBT freedom, immigration, European integration
  5.5.3 What existing surveys can and cannot validate
```

## I. 注意点(巴4 + 環1)

1. UK-only は N 薄 → Europe-wide(B) を本命に。
2. UKグリッド9共同体を再現しない(NI 等は BSA/NILT/USoc 向き→Limitation)。
3. Brexit は ESS で直接測れない → euftf を proxy に。
4. ESS は態度データであって主観的 mode 経験ではない(GSS と同じ構え)。
5. 【銃の教訓】事象の時間構造で単発/反復を事前振り分け(§B)。反復の flat を「CMR 外れ」と誤読しない。

## J. 関連ファイル

- 取得:`src/adapters/ess/ess_acquire.py` / 設計:`src/adapters/ess/ess_segments.py` / step1:`src/adapters/ess/ess_core_validation.py`
- 記録:本プラン + `gss_validation_findings.md`(GSS 側)/ spec 0.2(GSS 確定)
