> **⚠️ 本書は [`paper2_gss_ess_spec_v0.3.md`](paper2_gss_ess_spec_v0.3.md)(GSS+ESS 統合版)に統合・置換されました。** 正本は 0.3。本書は GSS 単独の記録として保持。

# SCEM Paper 2 — GSS 実証設計 spec【0.2 差分】

**作成:** 環(Tamaki)／ **確認:** 真道さま
**版:** 0.2 差分(2026-06-26)／ **親:** spec 0.1(同日)+ findings doc §2.5–2.8
**位置づけ:** 0.1 は「実装前の設計」。本 0.2 差分は「**一次実証を回した後の確定事項**」を反映し、**次回そのままペーパー化に入れる**ための更新。
**該当コミット(実ハッシュ・黒子訂正済):** コア対比/β+γ・Wilson CI(429f9e4)/ b′ 交互作用(77cb9d4)/ scope決定 b′(80f3cf6)/ 徳用パック(826ce76)/ overlay(8e512e2)/ 銃の時間構造(30701b8)
**黒子検証(2026-06-26):** 本差分の引用数値を committed 結果と突合済 — overlay 単発 10/12・銃込12/18・ACTIVE→transition 8/0・REFRAME flat 2/transition 2 / SSM 交互作用 +2.69 (p=0.157) / BB 変化点 1975生 +8.1pp/10年 / 移民×Coastal 線形−3.3・変化点1980 +41.5。全一致。

> 読み方は 0.1 を継承(確定 / 一部未決 / 未決)。本差分は主に「**0.1 で未決→0.2 で確定**」と「**新規に確定した発見**」を記す。

---

## A. 実証の到達点サマリ(確定・これが論文の Results 骨格)

GSS 二次分析の正味の結末。**強度を正確に(spin しない)**。

1. **SSM = 共同体ゲートの主実証(確定)**
   同性婚(MARHOMO/MARSAME 接続)で Coastal=飽和高位(91% [85,95%]) vs Bible Belt=単調勾配(6%→66%)。CI 分離・period 頑健(FE≈非統制)。
2. **徳用パックの「割れ」= CMR 事象依存の実証(確定)**
   同性婚・中絶・銃・移民で方向は**一致しなかった**。これは C(事象保持型プール・均さない)設計の勝利。割れ自体が「作用モードは事象に固有でない」の証拠。
3. **overlay で issues-differ 帰無を棄却(確定・ただし modest)**
   grid 事前 resolved_mode を GSS 割れに重ね、**単発事象 10/12 = 83% 的中**。特に **grid ACTIVE → GSS transition = 8/8(パーフェクト)**。base rate 56% への上乗せは中程度＝「予測対応(prediction-consistent)」であって「確証(confirmation)」ではない。
4. **変化点 > 線形 = 方法論貢献(確定)**
   移民×Coastal:線形スロープ −3.3(逆トレンドに見える)が、変化点1980で +41.5(SSE改善)。線形が転換を隠す実例。B(変化点格上げ)が実データで正解だった。
5. **銃 = 観測装置ミスマッチ(確定・概念収穫)** → 下記 C で詳述。

**強度の言葉(厳守):** GSS 節は「CMR を**確証した**」と書かない。「issues-differ より強い**予測対応**を示した(SSM/中絶 83%)、ただし modest」と書く。

---

## B. 0.1 からの確定更新(未決→確定 / 一部未決→確定)

### B.1 §4 セグメント設計:Coastal 薄N → 確定(β+γ・graduate 維持)
- **α(graduate→学士+)却下**:premise の弁別記号を N の都合で変えない(Non-overwrite に近い)。
- **γ**:Coastal は「平坦高位(REFRAME 署名)」を**プール**で主張。
- **β**:Coastal は10年刻みで N を稼ぐ／Bible Belt は5年刻みで勾配。
- 実証:プール 91% [85,95%]、10年ビンで CI 重なる＝平坦は本物(薄N のブレではない)。
- → **§4 の Coastal 定義は無変更で確定**(変更しなかったことが前提に支えられた積極決定)。

### B.2 §6.3/6.4 検定統計量:方向確定・主候補は変化点(0.1 の未決→確定方向)
- **主推定対象(確定)**:community × cohort **交互作用**(出生年スロープの共同体差＝b′ 推定量)。
- **主候補(確定)**:**変化点の有無/位置の共同体差**(線形スロープ差は均しで保守的に外すため。BB 1975生加速 +8.1pp/10年が証拠)。線形は**頑健性チェックとして併走**。
- **period 耐性(確定)**:diff-in-diff(同一波の共同体コントラスト)。FE版≈非統制版で識別が効くことを実証済み。
- **一部未決のまま**:変化点の検出法・閾値の最終確定／Coastal 天井(飽和で変化点が定義不能＝それ自体が REFRAME 署名と記述)。

### B.3 §3.3 徳用パック本体:scoping を確定(単発事象に限定)
- **本検証(出生年勾配で測れる単発イベント)= 同性婚・中絶**。
- **射程外(反復イベント)= 銃**(下記 C)。
- **探索的(grid に予測なし)= 移民**(US グリッドに行が無い。別集計、予測対応の集計に混ぜない)。

---

## C. 新規確定:銃 = 事象の時間構造による観測装置ミスマッチ(概念収穫)

**0.1 には無い軸。今日の最大の概念的発見。**

### C.1 事象の時間構造の二分(確定)

| 型 | 例 | 着弾年齢 | 出生年勾配 | GSS で |
|---|---|---|---|---|
| **単発モーメント** | Obergefell 2015 / Dobbs 2022 | 出生年で変わる | 出る | 見える |
| **反復バースト** | 乱射 Columbine→Uvalde | 全出生年が窓で食らう | 原理的に出ない | 見えない |

- 銃乱射は反復曝露 → 全世代が感受性窓で食らう → 出生年で態度差がつかない。
- かつ GUNLAW(許可制賛否)は1972年以降70%超で飽和＝論争にならない(態度方向が全共同体で一致)。
- 銃の ACTIVE は「反復的に全世代を**同方向に**再起動させる」性質。態度方向にも出生年にも出ない。**強度・行動(投票・献金)に出る**("I am a gun owner, and I vote")。

### C.2 重要な含意(確定)
- **grid に銃があったのは正しい**:曝露構造として超ヘビー級(全年代曝露・態度70%固定・強い姿勢)。検証の都合で grid から抜くのは Non-overwrite 違反。
- **grid 予測の失敗ではない**:grid の銃=ACTIVE 予測は妥当。GSS(出生年×態度)という**観測装置が反復イベントを映せない**だけ。事象とツールのミスマッチ。
- **GUNIMP は撃たない**:2波(1976/1984)・全 Sandy Hook 前でそもそも撃てない。かつ銃の身分は時間構造で先に決まっており、変数を変えて粘る意味がない。

### C.3 方法論教訓(確定・汎用)
> 測定が失敗したら、別変数で粘る前に「**装置と事象の構造が噛み合うか**」を先に問う。
(findings: feedback_check_instrument_phenomenon_fit.md)

### C.4 「根深い」の一文芽出し(従・深追いしない)
- 銃は態度が70%飽和かつ50年動かない＝**態度-政策回路が切断**された争点。態度ベースの観測自体が本質を外す可能性。
- → CMR の射程の**外壁**を示す(態度が生きた争点では効き、岩盤化した争点では効かない)。
- **Discussion に一文のみ**。比較政治・制度論の領域で本稿の射程外。解剖しない。

---

## D. 残る正直な綻び(隠さない・断定しない)

1. **grid の REFRAME 過早判定(系統バイアス)**
   外し2件(SSM-Suburban / 中絶-Coastal)は両方 REFRAME 側。grid は ACTIVE を正確に当てる(8/8)が、REFRAME を**過早に**判定する癖。n=12 小・flat 2セル → 断定しない。
   - 特に**中絶-Coastal**:grid REFRAME 過早判定 ＝ Dobbs(2022) による**再活性化**を織り込めていない ＝ **effective_year の時間発展(c軸)の証拠**。
2. **modest の度合い**:overlay 83% は base rate 56% への中程度上乗せ・n=18・アノテ薄。「予測対応」止まり、「確証」と書かない。

---

## E. GSS 節の構成(確定・次回これで書く)

論理順序は「**割れ＝主結果(CMR 事象依存)/ SSM＝最クリーン例 / 変化点＝方法 / 銃＝観測理論**」。

```
1. 主実証   : SSM = 共同体ゲート(平坦vs勾配・CI分離・period頑健)
2. 予測対応 : SSM+中絶 83%、ACTIVE→transition 8/8 → issues-differ 棄却(modest)
              ※「割れ」を弱点でなく主結果に:CMR は事象ごとに別解決
3. 方法論   : 変化点 > 線形(移民×Coastal +41.5 を線形が隠した)
4. 観測理論 : 銃 = 単発/反復の時間構造二分 → 反復は出生年軸で観測不能(装置ミスマッチ)
5. 正直な綻び: grid REFRAME 過早判定(断定せず)→ Paper 3(c軸・時間発展)への橋
6. 強度宣言 : 全体を「予測対応・modest」として正確に。確証と書かない
```

---

## F. 次セッション(ペーパー化)の着手順

1. **GSS 節ドラフト**:E の構成で本文化。図は core_contrast_ssm.png + overlay マトリクス + 変化点(移民×Coastal)。
2. **Related Work**:Jeannet & Dražanová の diffuse context を計算可能化(0.1 §2.2)＋ period 反論への二重防御(Social Change Report 64 の cohort>period 69% / diff-in-diff)。
3. **Discussion**:(i) 銃＝観測理論＋「根深い」一文、(ii) REFRAME 過早判定→c軸、(iii) ACTIVE は態度でなく強度/行動で測るべき。
4. **Limitations**:modest(n小・アノテ薄・反復横断のサンプリング変動)／Coastal 薄N／Latino 2000- 制約／Mormon "other" 別抽出。
5. **Future(Paper 3 への橋)**:c軸(effective_year 時間発展＝Dobbs 再活性化が実例)／行動指標による ACTIVE 測定／実体曝露(学生ローン・住宅・COVID実体)。

---

## G. 未決(0.2 でも持ち越し・決め打ちしない)

- 変化点検出法・閾値の最終確定(B.2)。
- Coastal 天井効果の正式な扱い(飽和→変化点定義不能の記述方法)。
- 多重比較補正の具体手法(FDR 等)。
- 2024 波の地理(region_7222 が 2022 止まり)を census 4区分で近似補完するか 2022 確定か。
- 重み設計(〜2018 wtssall / 2021+ wtssps・wtssnrps の波跨ぎ統合)。

> これらは**ペーパー化と並行で詰める**。本文の主張(A/B/C)はこれらの未決に依存しない強度で既に確定している。

---

## 関連ファイル

- 一次実証の詳細記録:[`gss_validation_findings.md`](gss_validation_findings.md) §2.5–2.8
- コード(`src/`):`gss_acquire.py` / `gss_segments.py` / `gss_core_contrast.py` / `gss_interaction.py` / `gss_valuepack.py` / `gss_overlay.py`
- 結果(`data/gss_results/`):`core_contrast_ssm.csv` / `interaction_ssm.json` / `valuepack_matrix.csv` / `overlay_predicted_vs_observed.csv` / `overlay_summary.json`
- 図(`figures/`):`gss_core_contrast_ssm.png` / `gss_valuepack_slopes.png`
- Paper 2 本体:[`paper2_contextual_mode_resolver.md`](paper2_contextual_mode_resolver.md)
