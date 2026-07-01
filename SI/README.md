# Supporting Information (SI) — SCEM Paper 2 §5.5 External Validation (GSS + ESS)

**版:** 1.0(2026-06-27)/ **親:** `docs/paper2_gss_ess_spec_v0.3.md`(正本 spec)
**型:** **完全再現型(complete-reproduction)**。誰でも同じ DOI から生データを取得 → 同じ slim → 同じ結果・図表が出る。
**数値一覧:** 執筆用の全 study 実数値 compendium は [`results_tables.md`](results_tables.md)(S1–S11 + 二段構造 + 早見)。
**ライセンス:** MIT(コード)。生データは NORC(GSS)/ Sikt(ESS)規約に従い**再配布しない**(DOI + 取得スクリプトで代替)。
**秘匿情報:** ESS API の User ID は**認証でなく利用統計用**だが、環境変数 `ESS_USER_ID` から読み**リポジトリに焼かない**。

---

## 0. 検証の問い(これを外すと全部ブレる — spec 0.3 §0)

本検証は **「SCEM が GSS/ESS の態度を正確に予測できるか」ではない**。
**「個人化(N爆発・一般化不能)と統計束(出生年バケツ=凡庸)のトレードオフをクリアした、中間レベルの傾向束が現実に実在するか」** の妥当性チェックである。SCEM は正確な予測を主張しない(何がどう混じるか厳密には不明)。主張は**傾向束**。混じりもの(period・国差・移行段階)は前提であり、その中から中間構造が立ち上がれば立脚点は妥当。

**強度の言葉(全出力で厳守):** 「確証(confirmation)」と書かない。「**予測対応(prediction-consistent)/ suggestive / modest / 傾向束の妥当性**」で記す。感度頑健が取れても強度は上げない。

**主発見(二段構造):** 共同体 premise が **水準** を、effective_year が **スロープ可視性(移行段階)** を駆動する。

---

## 1. ★三対応マッピング表(本文の主張 ⇄ SI ファイル ⇄ 再現コマンド)

> 査読者が「本文のこの数字、どこ?」を即座に辿るための表。**本文 §5.5 で言及する全数字がこの表のどこかに対応する**。
> コードは正本 `src/` を指す(SI で重複保持しない=ドリフト防止)。集計出力 `data/*_results/`・図 `figures/` は committed(再生成可)。

### §5.5.1 GSS(US)

| 本文の主張/図表 | データ/コード(src/) | 出力 | 再現コマンド |
|---|---|---|---|
| データ取得(GSS 1972–2024 Cumulative, NORC) | `gss_acquire.py` | `data/gss/gss_slim.parquet`(.gitignore) | `python3 src/adapters/gss/gss_acquire.py` |
| premise 8共同体の操作化(RELTRAD+RACE/HISPANIC+REGION/SRCBELT+DEGREE) | `gss_segments.py`(import) | — | (各分析が import) |
| CMR グリッド統合(interpretations) | `merge_paper2_data.py` | `data/interpretations_{us,uk}_grid.jsonl` 他 | `python3 src/cmr/merge_paper2_data.py --country us --variant grid`(uk も) |
| **SSM コア対比(Coastal 91%[85,95] vs Bible Belt 6→66%, CI分離, period頑健)** | `gss_core_contrast.py` | `data/gss_results/core_contrast_ssm.csv` / `figures/gss_core_contrast_ssm.png` | `python3 src/adapters/gss/gss_core_contrast.py` |
| **b′ 交互作用(+2.7pp/10年, p=0.157 n.s., FE≈非統制で period頑健)** | `gss_interaction.py` | `data/gss_results/interaction_ssm.json` | `python3 src/adapters/gss/gss_interaction.py` |
| **徳用パックの割れ(4事象×6共同体, 事象保持)** | `gss_valuepack.py` | `data/gss_results/valuepack_matrix.csv` / `figures/gss_valuepack_slopes.png` | `python3 src/adapters/gss/gss_valuepack.py` |
| **変化点>線形(移民×Coastal 線形−3.3 → 変化点1980 +41.5)** | `gss_valuepack.py` | `valuepack_matrix.csv`(cp_knot=1980, cp_post_extra_slope=41.5) | (同上) |
| **overlay(単発10/12=83%, grid ACTIVE→transition 8/8)** | `gss_overlay.py` | `data/gss_results/overlay_predicted_vs_observed.csv` / `overlay_summary.json` | `python3 src/adapters/gss/gss_overlay.py` |
| **銃=観測装置×時間構造ミスマッチ(EVENT_STRUCTURE 単発/反復)** | `gss_overlay.py`(`EVENT_STRUCTURE`)+ findings §2.8 | `overlay_summary.json`(`event_structure`, scoped vs incl-guns) | (同上) |
| Paper2 §5 CMR 図(mode matrix / fingerprint / 指紋) | `cmr_matrix.py` / `cmr_compare.py` / `make_paper2_figures.py` | `figures/fig_p2_*` | `python3 src/cmr/cmr_matrix.py --country us --variant grid` 他 / `python3 src/cmr/make_paper2_figures.py` |

### §5.5.2 ESS(UK/Europe)

| 本文の主張/図表 | データ/コード(src/) | 出力 | 再現コマンド |
|---|---|---|---|
| データ取得(ESS7–11, Sikt API, DOI 明記) | `ess_acquire.py` | `data/ess/ess_slim.parquet`(.gitignore) | `ESS_USER_ID=… python3 src/adapters/ess/ess_acquire.py` |
| proxy セグメント / EVENT_STRUCTURE / 重み(anweight) | `ess_segments.py`(import) | — | (各分析が import) |
| **水準ゲート(Secular 90%[89,91] vs Religious 66%[65,67], US並置)** | `ess_core_validation.py` | `data/ess_results/freehms_core.{csv,json}` / `figures/ess_freehms_core.png` | `python3 src/adapters/ess/ess_core_validation.py` |
| **country clusters + euftf + 移民(EVENT_STRUCTURE 事前適用)** | `ess_valuepack.py` | `data/ess_results/valuepack_matrix.csv` / `freehms_clusters.csv` / `figures/ess_valuepack.png` | `python3 src/adapters/ess/ess_valuepack.py` |
| **Southern 5国 b′ 正勾配一貫(ES z6.86/PT7.41/IT14.56/GR13.9/CY3.14)** | `ess_southern_country.py` | `data/ess_results/southern_country.csv` | `python3 src/adapters/ess/ess_southern_country.py` |
| **effective_year→移行段階(Spearman 承認年0.41/0.54, 婚姻年0.34/0.67)** | `ess_effective_year.py` | `data/ess_results/effective_year.{csv,json}` / `figures/ess_effective_year.png` | `python3 src/adapters/ess/ess_effective_year.py` |
| 制度年コーディング(出典付き) | `docs/ess_legal_coding.md` | (出典付き表; ILGA-Europe + 国内立法) | — |
| **overlay UK(7/9 探索的, euftf↔Brexit 3/3)** | `ess_overlay.py` | `data/ess_results/overlay_uk.csv` / `overlay_uk_summary.json` | `python3 src/adapters/ess/ess_overlay.py` |

> 順序依存:`gss_overlay.py` は `gss_valuepack.py` 出力(valuepack_matrix.csv)を読む → valuepack を先に。
> `*_overlay` / `*_southern` 等は CMR グリッド統合(merge)と slim 取得が前提。`reproduce_all.sh` が正しい順で実行。

---

## 2. SI に含めるもの(4層・完全再現型)

### 2.1 データ層
- 取得:`src/adapters/gss/gss_acquire.py`(GSS Cumulative Stata zip を NORC から直 DL → slim)/ `src/adapters/ess/ess_acquire.py`(ESS API, parquet 直取得)。
- DOI:**GSS** = `gss7224_r3`(2024 release, NORC GSS_stata.zip)。**ESS** = `10.21338/ess7e02_2, ess8e02_3, ess9e03_1, ess10e03_1, ess11e03_0`(`ess_acquire.py` の `ROUND_DOIS`)。
- 制度年:`docs/ess_legal_coding.md`(recognition_year/ssm_year/種別/primary law、ILGA-Europe + Wikipedia 国内立法脚注)。
- 生データ(GSS 570MB / ESS per-round parquet)は `.gitignore`。取得スクリプトで再生成可。

### 2.2 操作化層
- US 8共同体:`src/adapters/gss/gss_segments.py`(RELTRAD[公式変数]+RACE/HISPANIC+REGION/region_7222/SRCBELT+DEGREE。Mormon は `other`∈{60,64,162} で別抽出)。
- ESS proxy:`src/adapters/ess/ess_segments.py`(secular/religious×edu×urban×immigrant-bg、weight=anweight)。
- **EVENT_STRUCTURE**:`gss_overlay.py` / `ess_segments.py` の `EVENT_STRUCTURE`(単発モーメント vs 反復バースト)。銃=反復、freehms=単発、euftf/移民=反復。
- **同性婚3変数接続**:`gss_segments.py:ssm_approve()`(marsame/marsame1/marsamey)。ESS は `ess_segments.py:freehms_tolerant()`。

### 2.3 分析層
- 各スクリプト+出力(`data/{gss,ess}_results/*.csv|json` + `figures/*.png`)は §1 表のとおり。
- **強度の記述**:各スクリプトの末尾出力に「記述+CI/推定量まで・検定最終確定せず・確証と書かない」を明記(spin 防止を SI レベルで担保)。
- **除外マーク**:飽和近傍の不安定スロープ(過適合アーチ・改善0)は出力で `saturated`/`thin` フラグ + findings に「解釈に使わない」明記。

### 2.4 再現手順
- `SI/reproduce_all.sh`:取得 → slim → segment(import)→ analyze → figures を一括。GSS は network、ESS は `ESS_USER_ID` 必須。
- 環境:Python 3.12 / numpy / pandas / pyarrow / matplotlib。**scipy/statsmodels 不使用**(本環境 scipy 破損のため OLS+HC1・ロジット Newton・Spearman を numpy 自前実装)。`requirements.txt` 参照。
- 決定性:乱数なし(`Math.random`/`np.random` 不使用)。pandas groupby は既定ソート、国順は `sorted()`。**seed 不要・図は決定的**(§5 で要再確認項目に挙げる)。

---

## 3. SI に含めないもの(明示)

- **生データ本体**(GSS/ESS 規約・再配布不可)→ DOI + 取得スクリプトで代替。
- **slim 中間ファイル**(`gss_slim.parquet`/`ess_slim.parquet`)→ 既定で**含めない**(生データ派生・規約安全側)。取得スクリプトで再生成(§5-1 要確認)。
- **Paper 1 エンジン**(`media_generation_v4/v5.py`)・`events_patched.jsonl` → 無改変 import のみ。Paper 1 の SI を参照。
- **主観的 mode 経験(Prolific)** → 射程外・Paper 3。SI に「未実施・future」と明記。

---

## 4. 強度・誠実さの担保(SI レベル)

- 各出力に強度の言葉(suggestive・modest・確証と書かない)。本 README §0 に検証の問いを明記。
- **綻びを SI にも残す**(findings に全記録):
  - GSS:b′ 交互作用 p=0.16(n.s.)/ overlay base rate 膨れ(識別力は grid-ACTIVE→transition の 8/8)/ grid REFRAME 過早判定(SSM-Suburban・中絶-Coastal)/ 銃=装置ミスマッチ(grid 失敗でない)。
  - ESS:Europe-wide スロープ≈0 は均しアーチ(クラスタで Southern に出る)/ 飽和近傍不安定スロープ除外 / effective_year ρ 中程度・n=30・GR/CY 2波 / overlay UK-thin・proxy / 制度年は ILGA Rainbow Map 最終突合が残る。

---

## 5. 要チェック項目(黒子の判断 → 環/真道さま確認・決め打ちしない)

1. **slim parquet を SI に含めるか** — 黒子判断:**含めない(既定)**。GSS は公開だが ESS は登録規約があり、安全側で「DOI+取得スクリプトのみ」。→ 規約上 slim 同梱が望ましければ変更可(要確認)。
2. **三対応表の空欄** — 黒子が**全て埋めた**(変化点>線形=`gss_valuepack.py`/valuepack_matrix.csv、Southern 国別=`ess_southern_country.py`、effective_year=`ess_effective_year.py`)。漏れがあれば指摘を。
3. **ESS API 同意フロー** — `ESS_USER_ID` を `https://ess.sikt.no/en/api`(登録)で取得 → 環境変数。`reproduce_all.sh` が未設定なら ESS をスキップして案内(GSS は続行)。
4. **figures 決定性** — 乱数なし・ソート確定で**決定的**と判断。seed 不要。→ 念のため2回実行のバイト一致確認は最終投稿前に(要確認項目)。
5. **コードを SI/ に複製するか** — 黒子判断:**複製しない**(正本 `src/` を指す。複製はドリフト源)。`reproduce_all.sh` が `src/` を実行。Zenodo 公開時はリポジトリ全体を1アーカイブにするので SI=この README + reproduce_all + 既存 src/data/docs を指す形で完全再現になる。→ 異論あれば。

---

## 6. 成果物

- `SI/README.md`(本書:三対応表 + 検証の問い + 再現手順 + チェック項目)
- `SI/reproduce_all.sh`(ワンショット完全再現:GSS network / ESS `ESS_USER_ID`)
- 指す先(正本):`src/`(コード)・`data/{gss,ess}_results/`(集計出力, committed)・`figures/`・`docs/ess_legal_coding.md` / `gss_validation_findings.md` / `ess_validation_findings.md`。
- → これが固まったら Repository 整理(Core/CMR/Adapters)の土台。その後 本文 §5.5 を SI 参照で執筆。
