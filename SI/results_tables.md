# SI — 数値一覧(Results Compendium)/ SCEM Paper 2 §5.5 External Validation (GSS + ESS)

**版:** 1.0(2026-07-01)/ **親:** `SI/README.md`(再現の三対応表)/ `docs/paper2_gss_ess_spec_v0.3.md`(正本 spec)
**用途:** §5.5 本文執筆のために、GSS/ESS の**全 study と実数値を1枚に集約**。各値は committed 出力ファイル(`data/{gss,ess}_results/`)から転記。study ID(S1–S11)で本文・図表から参照する。

**強度の言葉(全 study 共通・厳守):** 「**確証(confirmation)**」と書かない。「**予測対応(prediction-consistent)/ suggestive / modest / 傾向束の妥当性**」で記す。感度頑健=操作化非依存であって強い証拠ではない。**検証の問い**=予測精度でなく「個人化↔統計束のトレードオフをクリアした中間傾向束の実在」の妥当性チェック(spec 0.3 §0)。

**主発見(二段構造):** 共同体 premise が **水準(level)** を、`effective_year` が **スロープ可視性(移行段階)** を駆動する。

---

## 0. データ来歴(provenance)

| | GSS (US) | ESS (UK/Europe) |
|---|---|---|
| 出所 | NORC GSS 1972–2024 Cumulative(`gss7224_r3`) | ESS Data Portal / Sikt API(`10.21338/ess7e02_2 … ess11e03_0`) |
| 波 | 反復横断(同性婚旗艦=接続11波 1988–2022) | ESS7–11(2014–2024, 5波) |
| N | 分析により可変(下記各 study) | slim 217,864 行 / 33 か国(GB 在) |
| 重み | 未適用(unweighted; 波跨ぎ weight は未決) | post-strat(`anweight`)適用 |
| period 統制 | 調査年 FE(diff-in-diff) | country + round FE |
| 宗教分類 | 公式 `reltrad`(Steensland 2000; Mormon は `other` で別抽出) | `rlgdgr`(religiosity 0–10)で proxy |
| 手法 | LPM(OLS+HC1)/ ロジット AME / 変化点 / Spearman は **numpy 自前実装**(scipy 不使用) | 同左(重み付き) |

生データは再配布不可 → `.gitignore`・取得スクリプトで再生成(`SI/README.md`)。

---

# Part A. GSS(US)

## S1. SSM コア対比(同性婚 × 出生年コホート)
出力:`data/gss_results/core_contrast_ssm.csv`, `figures/gss_core_contrast_ssm.png` / 再現:`python3 src/adapters/gss/gss_core_contrast.py`

| 共同体 | プール賛成率 [95%CI] | N | コホートの形 |
|---|---|---|---|
| **Coastal Liberal**(secular×hiedu×urban) | **91% [85, 95]** | 116 | 平坦高位(10年ビンで 87–100%、CI 重なる) |
| **Bible Belt**(evangelical×lowedu) | **24% [21, 26]** | 1,166 | 単調勾配(–1944生 6–15% → 1985-89 42% → 1990-94 66%) |

- プール CI が完全分離 = 水準差は頑健。Coastal は **β+γ・graduate 維持**(薄N=116 だが CI で「高位」断言可)。Wilson 95%CI 付き(記述への誤差棒であって検定ではない)。

## S2. b′ 交互作用(community × cohort スロープ差)
出力:`data/gss_results/interaction_ssm.json`(N=1,282, 1988–2022)/ 再現:`python3 src/adapters/gss/gss_interaction.py`

| 指標 | 値 |
|---|---|
| Coastal 出生年スロープ | +1.43 pp/10年 |
| Bible Belt 出生年スロープ | +4.13 ± 0.7 pp/10年 |
| **交互作用(スロープ差=b′)** | **+2.69 ± 1.90 pp/10年, z=1.41, p=0.157 → 非有意** |
| period 統制なし版(頑健性) | +2.8(z=1.45)≈ FE版 → スロープ差は period 交絡でない(diff-in-diff 効く) |
| ロジット AME(頑健性) | Coastal +1.6 / Bible Belt +4.1 pp/10年(LPM と整合) |
| BB 変化点(記述) | **1975年生 前後で加速**(節後 +8.14 pp/10年) |

**読み:** 方向は b′ どおり(BB が急)だが**単一旗艦・2共同体では有意に届かない**(Coastal 薄N + BB 非線形)。→ 徳用パック(S3)・二段構造(§C)へ回収。

## S3. 徳用パック(4事象 × 主力6共同体・事象保持)
出力:`data/gss_results/valuepack_matrix.csv`, `figures/gss_valuepack_slopes.png` / 再現:`python3 src/adapters/gss/gss_valuepack.py`
値=出生年スロープ pp/10年(LPM+調査年FE)。•=移行中(有意勾配/変化点)/ ==飽和・平坦 / ·=弱。

| 共同体 | 同性婚 | 中絶 | 銃規制 | 移民増 |
|---|---|---|---|---|
| Coastal Liberal | =+1.2 | •+4.7 | ·−2.2 | ·−3.3(**変化点1980 +41.5**) |
| Bible Belt | •+4.1 | •+2.6 | ·−0.5 | =+1.4(飽和/低) |
| Rust Belt WWC | •+5.4 | •+1.4 | ·−0.8 | =−0.3(飽和/低) |
| Black urban | ·+2.2 | ·−3.1 | ·−1.7 | ·+0.4 |
| Suburban MC | •+7.1 | •+3.2 | ·+1.9 | ·−0.1 |
| Rural Conservative | •+4.5 | •+1.7 | ·−0.9 | =+0.4(飽和/低) |

- **4事象で方向不一致=CMR「事象ごとに解決が違う」の実証**(事象保持設計の勝利。均すと消える)。
- **変化点 > 線形の決定的例**:移民×Coastal は線形 −3.3(逆トレンドに見える)が、変化点1980で後傾斜 **+41.5**(SSE改善0.066)=線形が若年転換を隠す。
- 銃規制は全共同体で移行なし → S5(装置ミスマッチ)。

## S4. overlay(Paper2 グリッド事前予測 × GSS 観測)
出力:`data/gss_results/overlay_summary.json`, `overlay_predicted_vs_observed.csv` / 再現:`python3 src/adapters/gss/gss_overlay.py`
照合:grid ACTIVE→transition / REFRAME→flat。**主集計=単発事象のみ**(銃=反復は射程外=S5)。

| 集計 | 的中 |
|---|---|
| 単発事象(SSM+中絶) 変化点読み | **10/12 = 83%** |
| 単発事象 線形読み | 9/12 = 75% |
| 参考(銃込 18セル) | 12/18 = 67% |

2×2 混同(単発・変化点):**grid ACTIVE→transition 8 / →flat 0(=8/8 パーフェクト)**、grid REFRAME→flat 2 / →transition 2。
外し2件は両方 REFRAME 側(SSM-Suburban / **中絶-Coastal**=Dobbs 2022 再活性化=effective_year 時間発展の証拠)。
**読み:** *issues-differ* 帰無を棄却する方向。ただし base rate 膨れ・n=12 → 「予測対応・modest」。

## S5. 銃 = 観測装置 × 事象の時間構造ミスマッチ(EVENT_STRUCTURE)
出力:`overlay_summary.json`(`event_structure`)+ `docs/gss_validation_findings.md` §2.8

| 型 | 例 | 出生年勾配 | GSS(出生年×態度) |
|---|---|---|---|
| 単発モーメント | Obergefell 2015 / Dobbs 2022 | 出る | 見える |
| 反復バースト | 乱射 Columbine→Uvalde | 原理的に出ない | 見えない |

銃乱射=反復 → 全出生年が感受性窓で食らう → 出生年で差がつかない。GUNLAW は 70%超飽和で論争にならない。**grid の銃=ACTIVE 予測は妥当、GSS が反復イベントを映せないだけ**(grid 失敗でなく装置ミスマッチ)。教訓=測定失敗時は別変数で粘る前に「装置と事象の時間構造が噛み合うか」を先に問う。

---

# Part B. ESS(UK/Europe)

## S6. 水準ゲート(freehms LGBT寛容, Europe-wide)
出力:`data/ess_results/freehms_core.{csv,json}`, `figures/ess_freehms_core.png`(US並置)/ 再現:`python3 src/adapters/ess/ess_core_validation.py`

| セグメント | プール寛容 [95%CI] | 出生年スロープ(FE) |
|---|---|---|
| **Secular HiEdu Urban**(Coastal 類似) | **90% [89, 91]** | −0.2 pp/10年(≈0=平坦高位) |
| **Religious LowEdu**(Bible Belt 類似) | **66% [65, 67]** | −0.1 pp/10年(≈0; 変化点1960で頭打ち=移行完了) |

- 交互作用(スロープ差)= z=0.03 ≈ 0(Europe-wide では均しで消える → S7 でクラスタ分解)。
- **US 並置**:GSS Coastal 91% / Bible Belt 6→66%。水準差は US/EU 一貫(=水準ゲートの普遍性)。

## S7. country clusters(freehms スロープの地域分解)
出力:`data/ess_results/freehms_clusters.csv` / 再現:`python3 src/adapters/ess/ess_valuepack.py`

| クラスタ | Secular(level, slope z) | Religious LowEdu(level, slope, **z**) | 判定 |
|---|---|---|---|
| Nordic | 0.984(飽和) | 0.787, −1.84(z−0.79) | 完了(平坦) |
| Western(UK含) | 0.967(飽和) | 0.797, −4.55(z−5.7) | 完了(平坦) |
| **Southern** | 0.946(飽和) | **0.663, +4.35(z=11.78)** | **移行中** |
| Central-East | 0.724(未飽和) | 0.441, +3.83(z1.35) | 後発・未飽和 |

**発見:** Europe-wide の「Religious 平坦」は**均しのアーチファクト**。分解すると **Southern Europe で b′ スロープ・ゲートがクリーン**(移行中)。= US Bible Belt(移行中)と同型。
> 注意:飽和近傍の不安定スロープ(例 Western Secular +37.41)は過適合アーチ(改善0)→**解釈に使わない**。

## S8. Southern の国別分解(b′ 一般化判定)
出力:`data/ess_results/southern_country.csv` / 再現:`python3 src/adapters/ess/ess_southern_country.py`
事前固定基準:複数国正勾配→一般化 / 1国突出→国固有 / 正負混在→集約アーチ。

| 国 | Religious N | プール寛容 | スロープ z | 判定 |
|---|---|---|---|---|
| ES | 1,417 | 80% | **6.86** | 正勾配 |
| PT | 2,165 | 77% | **7.41** | 正勾配 |
| IT | 3,626 | 61% | **14.56** | 正勾配 |
| GR | 2,173 | 57% | **13.90** | 正勾配 |
| CY | 653 | 44% | **3.14** | 正勾配 |

**判定 = 5/5 正勾配・0 ゼロ・0 負 → Southern 一般化OK(集約アーチでも1国フロックでもない)。** Secular は全5国で飽和高位(89–97%)。綻び:ES +27.4 は大(スペイン急速自由化)、GR/CY は2波で period 統制弱・CY 薄。

## S9. effective_year → 移行段階((c)時間発展)
出力:`data/ess_results/effective_year.{csv,json}`, `figures/ess_effective_year.png` / 再現:`python3 src/adapters/ess/ess_effective_year.py`(n=30国)
制度年コーディング=`docs/ess_legal_coding.md`(ILGA-Europe + Wikipedia 国内立法脚注、全件裏取り)。

| Spearman(制度年 vs …) | スロープ z | 変化点出生年 |
|---|---|---|
| 承認年(登録/婚姻の早い方) | **+0.41** | **+0.54** |
| 婚姻年のみ(感度) | +0.34 | **+0.67** |
| 制度あり国のみ(sentinel除外) | +0.47 | — |

**事前固定(ρ≥0.4)→ 単調対応=effective_year が移行段階を駆動(suggestive)。操作化に頑健**(登録↔婚姻で同符号)。
パターン(代表):早期承認 Nordic=完了(変化点1940s, z≈0)/ 遅い承認 South=移行中(**IE rec2011 z10.48 変化点1975**, ES z6.86, IT z14.56, GR z13.9)。
綻び:ρ 中程度・東欧の制度なし国がノイズ(LT/SK 高だが IL/MK/BG/RU 低くばらつく)・BE/GB/CH 中承認だが flat/負。

## S10. euftf(EU統合)/ immigration(移民)— 反復柱(EVENT_STRUCTURE 事前適用)
出力:`data/ess_results/valuepack_matrix.csv` / 再現:`python3 src/adapters/ess/ess_valuepack.py`
§5.5 では **反復イベント=flat を「CMR外れ」と誤読しない**(銃の教訓の移植)。

| 柱 | Secular(level, slope z) | Religious(level, slope z) | 読み |
|---|---|---|---|
| euftf(0–10, 反復疑い) | 6.14, −1.02(z−4.88) | 5.19, +0.10(z0.97) | 水準差あり・cleanな出生年勾配なし=反復の予測どおり |
| immigration index(0–10, 反復濃厚) | 6.72, −0.07(z−0.34) | 5.11, +1.33(z5.65) | 水準差明確(水準ゲート)・religious 正勾配は反復ゆえ慎重 |

→ **水準ゲートは3柱(freehms/euftf/移民)で再現**。スロープは反復柱で弱い/混在(§3 事前振り分けが機能=銃の罠回避)。

## S11. overlay UK(探索的・UK-only・proxy)
出力:`data/ess_results/overlay_uk.{csv,json}`(UK GB N=9,260)/ 再現:`python3 src/adapters/ess/ess_overlay.py`
UKグリッド事前 resolved_mode × ESS UK 観測。Brexit=euftf proxy。

- **予測対応 7/9**(探索的)。ただし base rate 膨れ(flat 7セル)。**識別力ある grid-ACTIVE→transition は 2/4**。
- 光:**euftf↔Brexit 3/3 的中**(Leave-Town religious=transition/ACTIVE)。proxy が機能。
- 外し2件は Religious-LowEdu(UK は LGBT/移民の移行完了=S7 Western と整合)。9共同体粒度は BSA/NILT 向き。

---

# Part C. 二段構造(cross-national の統合)と綻び

## C1. 二段構造(§5.5.3 の核・結論)
| 段 | 駆動因子 | 内容 | 普遍性 | 実証強度 | 主 study |
|---|---|---|---|---|---|
| 第1段:**水準ゲート** | 共同体 premise | secular/educated/urban 高位・religious/low-edu 低位 | **普遍**(US/EU・3柱) | 強い(確定方向) | S1, S6, S10 |
| 第2段:**スロープ可視性** | effective_year | b′ は移行中の共同体でのみ可視・完了/未着手は平坦 | 移行段階依存 | suggestive | S7, S8, S9 |

= バケツ(出生年のみ)では見えない中間構造が、個人化を要さず premise×effective_year×cohort で国を跨いで立った(=トレードオフ・クリアの妥当性)。第2段は Paper 3 (c) 時間発展の実データ片鱗。

## C2. 綻び一覧(隠さない・本文にも残す)
- GSS b′ 交互作用 p=0.16(単一旗艦・n.s.)→ 二段構造で回収(S2)。
- overlay base rate 膨れ(識別力は grid-ACTIVE→transition 側)(S4, S11)。
- grid REFRAME 過早判定(SSM-Suburban / 中絶-Coastal)(S4)→ Paper 3。
- ESS 飽和近傍の不安定スロープ(過適合アーチ・改善0)→ 解釈に使わない(S7)。
- effective_year ρ 中程度・n=30・GR/CY 2波・東欧ノイズ(S9)。制度年は ILGA Rainbow Map で最終突合(残)。
- ESS は主観的 mode を直接測らない外部照合(Prolific=Paper 3)。

## C3. 数字の早見(本文でよく引く値)
- GSS SSM:Coastal 91%[85,95](N116)/ Bible Belt 24%[21,26](N1166)/ 交互作用 +2.69 z1.41 p.157(N1282)。
- GSS overlay:単発 10/12=83%、ACTIVE→transition 8/8。移民×Coastal 変化点1980 +41.5。
- ESS 水準:Secular 90%[89,91] / Religious 66%[65,67]。
- ESS Southern b′:5/5 正勾配(ES6.86/PT7.41/IT14.56/GR13.9/CY3.14)。
- ESS effective_year:Spearman 承認年 0.41(slope)/0.54(変化点)、婚姻年 0.34/0.67、制度あり 0.47(n=30)。
