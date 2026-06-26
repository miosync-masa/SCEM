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
