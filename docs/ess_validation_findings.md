# ESS 二次分析 — 実行結果(黒子 → 環・真道さま)

**版:** 0.1(2026-06-27)/ **親:** `ess_validation_plan.md`(確定設計)/ spec 0.2(GSS)/ findings(GSS) §2.5–2.8
**状態:** ESS API でデータ取得 → step1(freehms 主検証)実行。作法は GSS と同一(確定のみ/未決決め打ちせず/spin しない/綻び記録)。

---

## 0. データ取得(ESS API・確定)

ESS API(`https://api.ess.sikt.no`)で取得成功。エンドポイント `GET /v1/data/dataFile/{doiPrefix}/{doiSuffix}`、
**parquet 直取得**(`fileFormat=parquet&recodeMissingValues=1`)。User ID は認証でなく利用統計用 → `ESS_USER_ID`
環境変数(リポジトリに焼かない)。`src/ess_acquire.py` に DOI と取得を実装。

- 取得:**ESS7–11(2014–2024)5 ラウンド**(ess7e02_2 / ess8e02_3 / ess9e03_1 / ess10e03_1 / ess11e03_0)。
- slim:`data/ess/ess_slim.parquet` = **217,864 行・33 か国・GB 在**。freehms/euftf/移民3項/デモグラ/anweight 全在。
- **period 統制(diff-in-diff)に 5 波 → 十分**。生データは `data/ess/`(.gitignore)。

---

## 1. step1:LGBT寛容(freehms)主検証(Europe-wide・重み付き anweight・country+round FE)

**Secular HiEdu Urban(Coastal 類似) vs Religious LowEdu(Bible Belt 類似)**。`src/ess_core_validation.py`。
出力 `data/ess_results/freehms_core.{csv,json}` / `figures/ess_freehms_core.png`(US 並置=目玉)。

| セグメント | プール寛容 [95%CI] | 線形スロープ(FE) | 変化点 | コホート形 |
|---|---|---|---|---|
| **Secular HiEdu Urban** | **90% [89,91]** | −0.2 pp/10年(≈0) | 改善0.001=なし | **平坦高位(REFRAME署名)** |
| **Religious LowEdu** | **66% [65,67]** | −0.1 pp/10年(≈0) | **1960生で頭打ち**(pre +6.5 / post −6.5) | **1960生まで上昇→以後 saturate** |

**交互作用(スロープ差=b′推定量)= +0.1 pp/10年, z=0.03 → ほぼゼロ。**

![ESS freehms 並置](../figures/ess_freehms_core.png)

### 1.1 正直な読み(spin しない)
1. **大きく頑健な信号は「水準差」**:Secular 90% vs Religious 66%、CI が遠く分離。**共同体 premise が寛容の
   *水準*(REFRAME 飽和の高さ)をゲートしている** ── これは US/Europe 共通(US も Coastal 91% vs Bible Belt 低位)。
2. **コホート *スロープ* のゲート(b′ をスロープ差で見る版)は ESS では ≈0**(z=0.03)。GSS の Bible Belt 型の
   「進行中の勾配」は **Europe では再現しない**。
3. **理由は変化点が露呈(B の教訓再来)**:Religious LowEdu は **1960生まで +6.5pp/10年 で上昇 → 以後頭打ち**
   = 欧州の宗教低学歴は**寛容化の移行を既に概ね完了(saturate)**。線形スロープ ≈0 は「均し」の産物で、
   構造は rise-then-plateau。**線形だけ見たら "flat=動かない" と誤読**するところ。
4. **GSS との対比が示す cross-national 構造**:
   - **US Bible Belt = 移行中**(6%→66%、若年ほど寛容、まだ動いてる)
   - **EU Religious LowEdu = 移行完了**(1960生で頭打ち、既に 66% で安定)
   → **共同体が事象をモードに解決する点は両国共通(水準差は明確)。だが移行段階(REFRAME 完了度)が国で違う。**
   これは [[ess_validation_plan]] §5 普遍性の**部分的**支持:high-flat(secular)は両国再現、religious 側は US=transition /
   EU=completed と段階差。

### 1.2 強度の言葉(厳守)
- **「確証」と書かない。** freehms ESS は「**水準ゲートの予測対応**(secular 高位平坦 / religious 低位)」+
  「**スロープ・ゲートは Europe では成立せず(移行完了)**」。GSS の交互作用も n.s.(p=0.16)だったので、
  **両国一貫して『強い信号は水準/飽和、スロープ交互作用は弱い』**。CMR の核(共同体が解決を変える)は
  *水準*で見え、*出生年スロープ*では弱い ── という cross-national の正直な結論。

### 1.3 綻び・限界(隠さない)
- Europe-wide pooled(country FE)は 33 か国を均す。**UK 単独 / 西欧クラスタ**では slope が違う可能性
  (依頼 step1「country clusters」未実施 → 次)。
- freehms は単発型(§3)で出生年軸 OK。euftf / 移民は反復(§3)で flat を誤読しない設計 ── **step2/3 未実施**。
- overlay(UKグリッド事前予測 × ESS 割れ)**未実施**(step4)。Brexit は euftf proxy。

---

## 2. 次(依頼 §E の残り)

- **step1.5**:country clusters(UK単独 / 西欧 / 中東欧)で freehms スロープを分解(均しの影響を見る)。
- **step2**:euftf(EU統合)。§3 反復疑い=flat でも誤読しない。
- **step3**:immigration_index。§3 反復濃厚。
- **step4**:overlay(UKグリッド grid 事前 resolved_mode × ESS 割れ)。grid 無し事象は探索分離。
- 未決(GSS 同様・決め打ちしない):変化点閾値の確定 / 重みの感度 / country クラスタ定義。

> 正味:**ESS で「共同体が寛容水準をゲートする」は出た(US と一貫)。だが『出生年スロープのゲート』は
> Europe では移行完了ゆえ弱い** ── GSS の「スロープ交互作用 n.s.」と整合。spin せず、これを cross-national の
> 正直な発見として記録。移行段階の国差(US 進行中 / EU 完了)は Paper 3 / (c) effective_year 時間発展へ橋。

---

## 2. step1.5(country clusters)— **金脈:均しが隠した b′ スロープ・ゲートを Southern Europe で発見**

`src/ess_valuepack.py`。Europe-wide(country FE)で消えた freehms 移行が、どのクラスタに在るか分解。

| クラスタ | Secular HiEdu Urban | Religious LowEdu |
|---|---|---|
| Nordic | 98% 飽和/平坦 | 79% flat(完了) |
| Western(UK含) | 97% 飽和/平坦 | 80% flat(完了, slope −4.6 z−5.7) |
| **Southern** | 95% 飽和/平坦 | **66% slope +4.35 (z=11.78)= 移行中** |
| Central-East | 72% 弱(未飽和) | 44% 弱(低位・全体が後発) |

**発見**:Europe-wide の「Religious=移行完了(flat)」は**均しのアーチファクト**。クラスタに割ると、
**Southern Europe では b′ スロープ・ゲートがクリーンに出る**(secular 飽和高位 / religious 強い正勾配 z=11.78)。
Nordic/Western/UK は完了済で flat。Central-East は全体が後発で未飽和。
→ **b′(共同体が出生年スロープをゲート)は「移行中のクラスタ」で出る**。US Bible Belt が移行中で出たのと同型。
**移行段階(REFRAME 完了度)が moderator** = 水準ゲートは普遍、スロープ・ゲートは移行中の時だけ可視。

> 注意(綻び):一部セルのスロープが不安定(例 Native HiEdu Urban freehms −11.32、Western Secular +37.41)。
> 飽和近傍 × country FE × コホート細セルの過適合アーチファクト(改善0 と整合)。解釈に使わない。

## 3. step2 euftf / step3 移民(§3 反復=flat を誤読しない・EVENT_STRUCTURE 事前適用)

`ess_valuepack.py`(柱×セグメント, `figures/ess_valuepack.png`)。**反復イベントは flat でも「CMR外れ」と読まない**設計。

- **euftf(EU統合, 反復疑い)**:水準は secular>religious(6.14 vs 5.18)だが、出生年スロープは小・混在
  (secular −1.0/religious +0.1)。**clean なコホート勾配なし=反復イベントの予測どおり**(§3 事前織込み)。
- **移民 index(反復濃厚)**:水準 secular 6.72 / religious 5.11(水準差は明確=水準ゲート)。religious は
  +1.33(z5.65)の正勾配だが反復イベントゆえ慎重(§3)。immigrant-bg は高位(6.17)。
- 総じて **水準ゲートは 3 柱で再現(secular/educated/urban が高位)、スロープは反復柱では弱い/混在**
  = §3 の事前振り分けが効いた(銃の罠を踏まない)。

## 4. step4 overlay(探索的・UK-only・proxy・Brexit=euftf proxy)

`src/ess_overlay.py`(UK GB N=9,260)。UKグリッド事前 resolved_mode × ESS UK 観測。
照合:grid ACTIVE→transition / REFRAME・PASSIVE→flat。**UK-only・proxy・N薄 → 探索的(確証でない)**。

**予測対応 7/9**(`data/ess_results/overlay_uk.csv`):
- **euftf↔Brexit:3/3 的中**(Secular=flat/REFRAME、**Leave-Town religious=transition/ACTIVE**、Immigrant-bg=flat/REFRAME)。Brexit=euftf proxy が機能。
- freehms↔同性婚:Secular/Immigrant-bg=flat(PASSIVE)○、**Religious LowEdu=grid ACTIVE→実 flat ×**(UK は LGBT 移行完了=step1.5 と整合)。
- 移民↔移民論争:Secular=transition(ACTIVE)○、Immigrant-bg=flat(REFRAME)○、Religious=ACTIVE→flat ×。

**正直な限界**:7/9 は **base rate 膨れ**(9セル中 flat が 7=多数)。**識別力のある grid-ACTIVE→transition 予測は
2/4**(外し2件は Religious-LowEdu で、UK の LGBT/移民の移行完了と整合)。grid-REFRAME/PASSIVE→flat は 5/5。
n=9・UK-only・proxy・Brexit proxy → **「探索的に予測対応・suggestive」止まり、確証と書かない**。
9共同体粒度(NI 等)は ESS で N不足 → BSA/NILT/Understanding Society 向き(Limitation)。

---

## 5. ESS 実証の正味(cross-national の正直な結論)

1. **水準ゲート(REFRAME 飽和の高さ)は普遍**:secular/educated/urban が高位、religious/low-edu が低位 ── US/Europe・3 柱で一貫。**共同体 premise がモードの*水準*を解決する**(CMR の核)。
2. **スロープ・ゲート(b′)は「移行中」でのみ可視**:US Bible Belt(進行中)・Southern Europe religious(z=11.78)で出る。Nordic/Western/UK は完了で flat。**移行段階が moderator**(= Paper 3 / (c) effective_year 時間発展)。
3. **EVENT_STRUCTURE が効いた**:euftf/移民の flat/混在を「CMR外れ」と誤読せず、反復イベントの予測どおりと扱えた(銃の教訓の移植が機能)。
4. **overlay は探索的に suggestive**(euftf↔Brexit 3/3 が光る)が UK-thin・proxy。確証でない。
5. **§5 普遍性=部分支持**:水準ゲートは軸が違っても両国再現(普遍作用素)。スロープは移行段階依存。

> 強度の言葉:全体「**予測対応・modest**」。確証と書かない。ESS は mode を直接測らない外部照合。
