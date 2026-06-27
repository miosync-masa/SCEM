# SCEM Paper 2 — GSS/ESS 実証設計 spec【0.3 統合版】

**作成:** 環(Tamaki)／ **確認:** 真道さま
**版:** 0.3 統合版(2026-06-27)／ **前版:** 0.1(設計)+ 0.2差分(GSS実証)を統合・上書き(0.2 は本書に置換)
**親文書:** Paper 1(SCEM, SocArXiv)／ Paper 2 v0.9("A Cross-National Extension")
**正味:** US(GSS) + UK/Europe(ESS) の二カ国 secondary validation を完了。**検証の問いを「予測精度」から「トレードオフ・クリアの妥当性」へ再定義**し、二段構造(水準=premise / 移行=effective_year)を発見した。**本書1枚で論文化(§5.5 + Discussion)に着手できる正本。**

**黒子検証(2026-06-27):** 本書の引用数値を committed 結果と突合 — 全一致。
GSS overlay 単発 10/12・銃込 12/18・ACTIVE→transition 8/8 / SSM 交互作用 p=0.157 / ESS freehms Secular 90% [89,91]・Religious 66% [65,67] / Southern 国別 z(ES 6.86 / PT 7.41 / IT 14.56 / GR 13.9 / CY 3.14)/ effective_year Spearman(承認年: slope 0.41・変化点 0.54 / 婚姻年感度: 0.34・0.67・制度あり 0.47)。
関連: `gss_validation_findings.md` §2.5–2.8 / `ess_validation_findings.md` §0–6 / `ess_legal_coding.md` / `paper2_gss_spec_v0.2.md`(GSS 単独・本書に統合)。

> 読み方マーク:**確定** = 合意済み・書いてよい ／ **一部未決** = 方向確定・細部要詰め ／ **未決** = 次回決定・決め打ちしない(Non-overwrite)

---

## ★ 0. 検証の問いの再定義(最重要・今回の最大の収穫)

**論文化のとき、ここを外すと全部ブレる。** GSS/ESS 検証の目的を正確に固定する。

### 0.1 SCEM の立脚点(怒りの起点)
- SCEM は「1981年生まれと1995年生まれを一括して "ジェネレーションY" とまとめるな」という、**出生年バケツへの批判**から出発した。
- 対案:**「何年の人が・どこで・何を曝露したか、それでどんな態度を取りやすいかの統計的傾向束を掴む」**。
- = 個人化(N爆発・一般化不能=死)と統計束(バケツに戻る=凡庸)の**トレードオフをクリアする中間レベル**。

### 0.2 検証の問い(ここを取り違えない)
- ❌ **誤**:「SCEM は GSS/ESS の態度を**正確に予測**できるか?」(→ 交互作用 n.s. や magnitude のバラつきが "失敗" に見える)
- ⭕ **正**:「**個人化と統計束のトレードオフをクリアした中間レベルの傾向束が、現実に実在するか**」の妥当性チェック。
- SCEM は「正確な予測」を主張**しない**("何がどう混じってるか厳密には分からん")。主張は**傾向束**。よって混じりもの(period・国差・移行段階)があるのは**前提**。混じりの中から中間構造が立ち上がれば、立脚点は妥当。

### 0.3 採らない検証
- **SCEM vs 出生年バケツの説明力比較は採らない**。SCEM は多変数(cohort × premise × effective_year)、バケツは出生年のみ。**変数数が違いすぎて勝負が成立しない**(「多変数が勝つに決まってる」で終わる)。トレードオフ・クリアは説明力競争ではなく、**中間レベルで傾向束が実在するか**で示す。

### 0.4 強度の言葉(全節で厳守)
- 「**確証(confirmation)**」と書かない。「**予測対応(prediction-consistent)/ 傾向束の妥当性 / suggestive / modest**」で書く。
- 感度頑健が取れても強度は上げない(頑健 = 操作化に左右されない、であって強い証拠ではない)。

---

## ★ 1. 二段構造(今回の主発見・GSS+ESS で確定方向)

GSS(US)+ ESS(UK/Europe 33か国)を貫いて立ち上がった構造:

> **共同体 premise が「水準」を、effective_year が「スロープ可視性(移行段階)」を駆動する。**

| 段 | 駆動因子 | 内容 | 普遍性 | 実証 |
|---|---|---|---|---|
| **第1段:水準ゲート** | 共同体 premise | secular/educated/urban が寛容高位、religious/low-edu が低位 | **普遍**(US/EU・3柱で一貫) | 強い(確定方向) |
| **第2段:スロープ可視性** | effective_year | 出生年スロープ(b′)は「移行中の共同体」でのみ可視。完了/未着手では平坦 | **移行段階依存** | suggestive |

- **これがトレードオフ・クリアの妥当性証拠**:バケツ(出生年のみ)では二段構造は見えない。個人化を要さず、中間レベル(premise × effective_year × cohort)で傾向束that自体が国を跨いで立った。
- 第2段は **Paper 3 の (c) effective_year 時間発展** の実データ片鱗(後述 §6)。

---

## 2. 論文戦略(確定)

### 2.1 構成:C案(CMR 重心・構造層は台座)
- **主張1個**:作用モードは事象に固有でなく、共同体 premise によって resolve される(CMR)。構造層(Paper 1)は台座として Section 2 に圧縮。
- Paper 1 / v0.9 はプレプリントで priority 確保。ジャーナル版は CMR 焦点の統合版。

### 2.2 投稿先:Social Science Computer Review (SSCR)
- 計算社会科学の方法論ジャーナル。世代論 × LLM-as-annotator × CSP/SAT がスコープ中央。APS 系は独立研究者にデスクリジェクト傾向ゆえ回避。

### 2.3 背骨(立脚点→実証→主張の一直線)
```
先行研究のジレンマ(個人化 vs 統計束・未解決)
  → 二段構造の実証(水準=premise 普遍 / 移行=effective_year 段階依存)
  → SCEM はこのトレードオフをクリアする初の構成的代替
```

---

## 3. 先行研究上の位置(Related Work)(確定)

- **ニッチ**:バケツ批判は飽和(Costanza 2012; Duffy 2021; Rudolph; Parry & Urwin)。だが**構成的代替が空席**。現場がバケツを使い続けるのは代替がないから。
- **個人化 vs 統計束のジレンマ**:これが主張のコア。先行研究にクリティカルな解決なし。
- **最近接:Jeannet & Dražanová (2019)** の "diffuse political context"。intra-cohort variation に気づいたが定性概念に留まる。**CMR はこれを計算可能にした作用素** `Event × Premise → ResolvedImpact`。
- **感受性窓**:Krosnick & Alwin 1989; Schuman & Scott 1989; Ghitza et al. 2023 + **Grasso 2014 / Grasso & Shorrocks 2025**。
- **period 反論への二重防御**:(1) GSS Social Change Report No.64 が 276変数の **69% で cohort > period**(反論者のデータ自身で返す)。(2) SCEM は age と period を分離しない設計(識別問題を踏まない・RPC 思想)。

---

## 4. GSS(US)実証 — 確定

### 4.1 セグメント設計(方針 a・確定)
- 8共同体を GSS 変数の論理式で操作化。**主力6**(Coastal/Bible Belt/Rust Belt/Black/Suburban/Rural)/ **補助2**(Mormon・Latino, N薄・解釈慎重)。
- 宗教 = **RELTRAD**(GSS 公式変数同梱・Steensland 2000、Mormon は other→DENOM別抽出)。人種 = RACE+HISPANIC(Latino 2000-制約)。地理 = REGION(9区分は region_7222・2022止まり)と SRCBELT 併用。学歴 = DEGREE。
- **Coastal 薄N**:β+γ・graduate 維持・α却下(premise 弁別記号を N の都合で変えない)。プール 91% [85,95%]・10年ビンで平坦が CI 付きで確認。

### 4.2 検定設計(確定方向・一部未決)
- **主推定対象**:community × cohort **交互作用**(出生年スロープの共同体差=b′)。
- **主候補**:**変化点 >(線形は均しで保守的)**。線形は頑健性で併走。
- **period 耐性**:diff-in-diff(同一波の共同体コントラスト)。FE版≈非統制版で識別確認済。
- 一部未決:変化点検出法・閾値／Coastal 天井(飽和で変化点定義不能=REFRAME署名と記述)。

### 4.3 結果(確定・記述+CI+推定量、検定の最終確定は据置)
- **SSM**:Coastal 飽和高位 91% vs Bible Belt 単調勾配 6%→66%。CI 分離・period 頑健。**交互作用は方向◯だが p=0.16(n.s.)** ← 後に「水準ゲートは強・スロープは弱」と二段構造で回収(§1)。
- **徳用パックの割れ**:同性婚・中絶・銃・移民で方向不一致。**C(事象保持・均さない)設計の勝利** = CMR 事象依存の実証(潰さず保持)。
- **overlay**:grid 事前 resolved_mode × GSS 割れ。**単発事象 10/12 = 83%、grid ACTIVE→GSS transition = 8/8**。issues-differ 帰無を棄却(ただし modest・base rate 56%上乗せ中程度)。
- **変化点 > 線形**:移民×Coastal 線形 −3.3 が変化点1980で +41.5(線形が転換を隠す実例)。B 格上げが正解。

### 4.4 銃 = 観測装置 × 事象の時間構造ミスマッチ(確定・概念収穫)
| 型 | 例 | 着弾年齢 | 出生年勾配 | GSS |
|---|---|---|---|---|
| 単発モーメント | Obergefell/Dobbs | 出生年で変わる | 出る | 見える |
| 反復バースト | 乱射 Columbine→Uvalde | 全出生年が窓で食らう | 原理的に出ない | 見えない |
- 銃は反復バースト → 出生年で割れない。GUNLAW は70%超飽和で論争にならない。grid に銃があるのは正しい(曝露構造ヘビー級)が、GSS(出生年×態度)が反復イベントを映せない。**grid 失敗でなく装置ミスマッチ**。
- 教訓:**測定が失敗したら別変数で粘る前に「装置と事象の構造が噛み合うか」を先に問う**(EVENT_STRUCTURE)。
- 「根深い」一文芽出し:銃は態度が70%飽和かつ50年動かない=態度-政策回路の切断。CMR の射程の外壁。Discussion に一文のみ(深追いしない)。

---

## 5. ESS(UK/Europe)実証 — 確定方向

### 5.1 データ・構え
- ESS API(Sikt)で **ESS7–11(2014–24・33か国・217,864行・GB在)**取得。anweight 重み付き、country+round FE。**mode は直接測らない外部照合**(GSS と同じ構え)。
- 3本柱に **EVENT_STRUCTURE を事前適用**(銃の教訓の移植):freehms=単発(主検証)／ euftf・移民=反復疑い(flat を CMR外れと誤読しない)。

### 5.2 水準ゲート(普遍・確定方向)
- freehms:**Secular HiEdu Urban 90% [89,91] vs Religious LowEdu 66% [65,67]**、CI 分離。US(Coastal 91% vs Bible Belt 低位)と一貫。3柱(freehms/euftf/移民)で secular/educated/urban が高位=水準ゲート再現。

### 5.3 スロープ可視性 = 移行段階依存(金脈・確定方向)
- Europe-wide では freehms スロープ交互作用 ≈0(z=0.03)。だが**均しのアーチファクト**——クラスタ分解で:
  - **Southern Europe = 移行中**(b′ 正勾配がクリーン)。**5国一貫**(ES z=6.86 / PT z=7.41 / IT z=14.56 / GR z=13.9 / CY z=3.14)。事前固定基準(正勾配5/0/0)→ 一般化OK。1国フロックでも集約アーチでもない。
  - Nordic/Western/UK = 移行完了(flat)。Central-East = 未飽和(後発)。
- **US Bible Belt(移行中)+ Southern Europe 5国(移行中)で b′ 再現** = 「移行中の共同体でスロープ・ゲートが可視」が**国・地域・軸を跨いで再現**。軸が違っても(US 宗教×人種 / EU religiosity×education)水準ゲートは普遍 → **CMR は特定軸に依存しない普遍作用素**(普遍性を強く支持)。

### 5.4 effective_year → 移行段階(二段構造の第2段・suggestive・出典頑健)
- 制度年(同性婚承認年)と freehms 変化点/スロープの対応:

| effective_year 定義 | vs スロープz | vs 変化点出生年 |
|---|---|---|
| 承認年(登録/婚姻の早い方) | +0.41 | **+0.54** |
| 婚姻年のみ(感度) | +0.34 | **+0.67** |

- 事前固定基準(ρ≥0.4)→「effective_year が移行段階を駆動」を支持。**操作化(登録 vs 婚姻)に頑健**(同符号・近似、婚姻年版で +0.67)。
- パターン:早期承認 Nordic = 完了(変化点1940s)／遅い承認カト・正教会 South = 移行中(IE 変化点1975=若年集中)。**遅い国ほど若い変化点(ρ=0.54〜0.67)が最もきれい**。
- **制度年コーディングは出典で固定**:`docs/ess_legal_coding.md`(ILGA-Europe + Wikipedia 国内立法脚注、ES Ley13/2005・PT Lei9/2010・IT Cirinnà法・GR 4356/2015&5089/2024・IE Marriage Act 2015 …全件裏取り)。

### 5.5 overlay(UK-only・探索的)
- UK グリッド grid 事前 resolved_mode × ESS UK(GB N=9,260, proxy, Brexit=euftf proxy)。**予測対応 7/9 だが base rate 膨れ(flat 7セル)。識別力ある grid-ACTIVE→transition は 2/4**。
- 光:**euftf↔Brexit 3/3 的中**(Leave-Town religious=transition/ACTIVE)。proxy が機能。
- 「探索的に suggestive」止まり。NI 等 9共同体粒度は ESS で N不足 → BSA/NILT/Understanding Society 向き(Limitation)。

---

## 6. 二段構造 → Paper 3 への橋(確定方向)

- **第2段(effective_year が移行段階を駆動)= Paper 3 の (c) 時間発展の実データ片鱗**。「将来構想」から「出典付き・操作化頑健な suggestive 証拠」へ二段昇格(ただし suggestive 据置)。
- 中絶×Coastal(GSS)の REFRAME 過早判定 = Dobbs(2022) による再活性化 = effective_year 時間発展の同方向の証拠。
- WWW 思考実験(モード境界が暦年でスライド)が、ESS(Southern=移行中 / Nordic=完了)で裏取り。

---

## 7. 残る綻び(隠さない・断定しない)

- grid の REFRAME 過早判定(系統バイアス・n小)→ 断定せず、Paper 3(c軸)の種。
- ESS の飽和近傍不安定セル(過適合アーチ・改善0)→ 解釈に使わない。
- overlay の base rate 膨れ(識別力は grid-ACTIVE→transition の方)。
- effective_year:ρ 中程度・n=30・GR/CY 2波 → exploratory/suggestive、確証と書かない。
- 制度年:ILGA Rainbow Map 最新版で1国ずつ官報突合(最終投稿前・土台は固めた)。

---

## 8. 論文構成(次回これで書く)

```
§5.5 External validation with existing surveys
  5.5.1 GSS (US): SSM・徳用パックの割れ・overlay・変化点>線形・銃=装置ミスマッチ
  5.5.2 ESS (UK/Europe): 水準ゲート普遍・Southern 5国 b′・effective_year→移行段階
  5.5.3 What existing surveys can and cannot validate
        =二段構造(水準=premise普遍 / 移行=effective_year段階依存)
        =個人化と統計束のトレードオフを中間レベルでクリアした妥当性
Discussion:
  - 二段構造 → (c) effective_year 時間発展(Paper 3 の片鱗が実データに)
  - 銃=観測理論+「根深い」一文
  - ACTIVE は態度でなく強度/行動で測るべき
  - period 反論への二重防御
Conclusion:
  既存サーベイは主観的 impact mode を直接測らない。しかし GSS/ESS は、
  CMR 予測の共同体差が観測可能な cohort-attitude 軌跡に対応するかの外部照合を提供し、
  個人化と統計束のトレードオフをクリアした中間レベルの傾向束の実在を suggestive に示す。
```

---

## 9. この後のタスク(今日〜次回)

1. **Repository 整理:研究コア / TOOL(Exposure Adapter 層)の分離**
   - 研究コア = SCEM エンジン(v4/v5)・CMR resolver・lod_persona・cmr_compare/matrix
   - TOOL = gss_acquire / ess_acquire / RELTRAD適用 / segments / overlay / valuepack
   - → Paper 2 §8.1 の Core/CMR/Exposure Adapters 層構成にリポジトリ構造を対応させる。
2. **SI(Supporting Information)を先に完全確定**(本文の前に)
   - GSS/ESS 全データ・コード・再現手順・セグメント定義・EVENT_STRUCTURE・ess_legal_coding.md
   - 生データは .gitignore(再取得可)。本文は SI を参照するだけにして手戻りを消す。
3. **(次回)本文 §5.5 + Discussion を SI 参照で執筆。**

---

## 10. 未決(決め打ちしない・持ち越し)

- 変化点検出法・閾値の最終確定。
- Coastal 天井効果の記述方法(飽和→変化点定義不能)。
- 多重比較補正(FDR 等)。
- ESS 重み(anweight)感度・country クラスタ定義の頑健性・飽和近傍不安定セルの最終扱い。
- 制度年:ILGA Rainbow Map 最新版での1国突合(最終投稿前)。
- GSS 2024 波の地理(region_7222 が 2022止まり)の扱い。

> **本文の主張(§0 立脚点・§1 二段構造)は、これら未決に依存しない強度で既に確定している。** 未決はペーパー化と並行で詰める。
