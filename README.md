# SCEM — Situated Cohort Exposure Model

[![DOI](https://zenodo.org/badge/1279042311.svg)](https://doi.org/10.5281/zenodo.20827897)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**「世代」を出生年バケツではなく曝露構造として計算し、同じ社会事象が共同体ごとに別の作用モードへ解決される様子を扱う計算フレームワーク。**

SCEM には**二つの顔**がある。同じエンジン(Core / CMR)の上に立つ:

- 🎓 **学術フレームワーク**(↓ Track A)— 世代を計算可能・反証可能に再定義し、GSS/ESS で外部照合した研究基盤。
- 🎭 **ペルソナ生成エンジン**(↓ Track B)— 出生年 × 共同体 premise から、曝露構造に**由来追跡可能な**ペルソナを生成する実装。

> **中核主張(2つ):**
> 1. **世代 = 出生年コホートではない。** 社会事象の作用ベクトルが認知発達上の**感受性窓**にどう着弾したかで決まる連続プロファイル。
> 2. **作用モードは事象に固有ではない。** 共同体の前提(premise)によって解決される —— `Event × Premise → ResolvedImpact`(Contextual Mode Resolver)。

---

## 共通エンジン(層構成)

`src/` はこの層構成に物理対応する。両トラックがこのエンジンを共有する。

| 層 | 役割 | 実装(`src/`) |
|---|---|---|
| **Core**(構造層) | 事象 × 着弾年齢 × 作用モードのテンソル。世代指紋(3軸)・感受性窓・干渉・REFRAME発火・effective_year | `core/` |
| **CMR Layer** | `Event.mode` を作用素 `Event × Premise → ResolvedImpact` へ持ち上げ、複数 LLM 観測者で mode を解決。LOD/CSP でペルソナ生成 | `cmr/` |
| **Exposure Adapters** | 曝露構造の供給層(差し替え可能):curated DB / GSS・ESS / 将来 GDELT 等 | `adapters/{gss,ess}/` |

**3作用モード**(合算せず3軸):**PASSIVE**(受動着弾)/ **ACTIVE**(能動分岐=決断強制)/ **REFRAME**(参照点書き換え)。
**2つの軸**:着弾年齢(何歳で食らうか)× 共同体 premise(どの規範コードで食らうか)。
**Honest Structuralism(4公理)**:Anchor Preservation / Non-overwrite / Projection Consistency / Provenance。生成を数理アンカーに縛り、捏造を CSP/SAT-UNSAT で構造的に拒否する。

---

## 🎓 Track A — 学術フレームワーク

**貢献:** マーケの「Z世代論」の三欠陥(恣意的カットオフ・反証不能・出生年への単一還元)を、計算可能で反証可能な枠組みで置換。Mannheim (1928) を計算可能にし、Strauss & Howe (1991) の恣意的カットオフを連続関数に。

**計算するもの:**
- **世代指紋(3軸)**:任意の出生年 →(PASSIVE, ACTIVE, REFRAME)。例:1981年生 = 0.81 / 0.56 / 0.55。9世代バッチで PASSIVE 密度が 1980–85 でピーク→減衰の非単調構造。
- **設計された比較グリッド**:固定 Community × 固定 Event で mode 変換を測る。US 8×12=96 / UK 9×13=117、Event-level MFR 両国 100%(選定争点)、CDI US 0.289 / UK 0.338。

**外部照合(GSS + ESS)— 強度は正確に(「予測対応・modest」、確証と書かない):**
> 検証の問い=「態度を正確に予測できるか」でなく「個人化↔統計束のトレードオフをクリアした中間傾向束が実在するか」。

US(GSS)+ UK/Europe(ESS 33か国)で立ち上がった **二段構造**:
- **水準ゲート(普遍)**:secular/educated/urban が寛容高位、religious/low-edu が低位(GSS Coastal 91% vs Bible Belt / ESS Secular 90% vs Religious 66%、3柱で一貫)。
- **スロープ・ゲート(移行段階依存)**:出生年スロープは「移行中の共同体」でのみ可視(US Bible Belt 6→66% / Southern Europe 5国すべて正勾配)。承認年(effective_year)と単調対応(Spearman 0.41–0.67)。

**書き出し・数値・再現:**
- 論文:[Paper 1](docs/paper1_media_generation.md)([HTML](docs/paper1.html))/ [Paper 2 (CMR)](docs/paper2_contextual_mode_resolver.md)([HTML](docs/paper2.html))
- 確定 spec:[`docs/paper2_gss_ess_spec_v0.3.md`](docs/paper2_gss_ess_spec_v0.3.md)
- **SI**:[数値一覧 `SI/results_tables.md`](SI/results_tables.md)(全 study S1–S11 の実数)/ [再現の三対応表 `SI/README.md`](SI/README.md) / [`reproduce_all.sh`](SI/reproduce_all.sh)
- findings:[GSS](docs/gss_validation_findings.md) / [ESS](docs/ess_validation_findings.md)

![cohort fingerprint](figures/fig2_cohort_fingerprint.png)
![mode matrix US](figures/fig_p2_modematrix_us_grid.png)

---

## 🎭 Track B — ペルソナ生成エンジン

**何をするか:** `出生年 × 共同体 premise × 自己記述(応答/戦略)` を入力すると、その人が置かれた**曝露構造に由来追跡可能な**ペルソナ(物語 + provenance)を生成する。**同じ出生年・同じ自己記述でも、premise を変えると別のペルソナになる。**

**例(同一入力・premise だけ変える):** 1985年生・"Fight"(自分の選択で介入)固定で —
- **Coastal Liberal**(secular×hiedu×urban):全事象が REFRAME(参照点書き換え)として着弾。「Obama 当選=能動分岐」を Claude 観測者が加えると provenance が分化。
- **Bible Belt**(evangelical×lowedu):同じ Fight でも「9.11 を ACTIVE 分岐として引き受ける」。
→ 出力全文は [`data/personas_grid/`](data/personas_grid/)。

**仕組み:** LOD(Level of Detail)階層 = 曝露構造(LOD0, 数理・固定)→ ペルソナ(LOD3, 解釈)を解像度の階層として扱い、**4公理を制約とする CSP** で生成。**Projection Consistency と Axiom 違反で SAT/UNSAT を判定**(数理アンカーに由来しないペルソナは構造的に拒否)。実装:[`src/cmr/lod_persona.py`](src/cmr/lod_persona.py)、理論:[`LOD_ARCHITECTURE.md`](LOD_ARCHITECTURE.md)。

**倫理境界(製品化時も第一条・不変):** SCEM は**個人の内面を断定しない**。出力は「ある出生年・共同体・制度環境に置かれた人が**どんな曝露構造を持ちやすいか**」の推定であって、個人の決めつけではない。**分類でなく理解 / 操作でなく翻訳 / 断定でなく来歴追跡 / 分断でなく相互理解**(誤用防止の四線)。= 人を分類する道具でなく**異なる意味世界の翻訳地図**。

**使いどころ:** 「同じメッセージが共同体ごとに別の意味に着弾する」を可視化 —— コピー/採用広報/コミュニケーション設計、研究用の由来つきペルソナ。

```bash
# ペルソナ生成(要 OpenAI キー)
cp .env.example .env
arch -arm64 python3.12 src/cmr/lod_persona.py --country us --birth_year 1985 \
  --premise secular_white_coastal_graduate --response Fight --variant grid
```

---

## クイックスタート

```bash
# 【共通/学術】Core は標準ライブラリのみ
python3 src/core/media_generation_v5.py 1981        # 1981年生の3軸プロファイル
python3 src/core/make_figures.py                     # 図 → figures/

# 【学術】CMR グリッド / 外部照合
python3 src/cmr/cmr_matrix.py --country us --variant grid
bash SI/reproduce_all.sh          # GSS=ネット / ESS=ESS_USER_ID(未設定でスキップ)

# 【ペルソナ生成】要 OpenAI キー
arch -arm64 python3.12 src/cmr/lod_persona.py --country us --birth_year 1985 \
  --premise secular_white_coastal_graduate --response Fight --variant grid
```

依存:[`requirements.txt`](requirements.txt)(`numpy` `pandas` `pyarrow` `matplotlib` / LLM層 `openai` `python-dotenv`)。scipy/statsmodels 不使用(OLS+HC1・ロジット・Spearman は numpy 自前実装)。

---

## リポジトリ構成

```
README.md  ARCHITECTURE.md(正典 v6 FIXED)  LOD_ARCHITECTURE.md(LOD/4公理/CSP)  requirements.txt

src/                  全 Python(フレームワーク層構成)
  core/      = SCEM Core(media_generation_v4/v5, event_loader, make_figures, build_html, tests)
  cmr/       = CMR Layer + ペルソナ生成(cmr_matrix/compare, merge_paper2_data, lod_persona[CSP/SAT-UNSAT],
               generate_claude_observer, recover_gemini_jsonl, make_paper2_figures)
  adapters/  = Exposure Adapters(gss/・ess/ = US・UK/Europe 外部照合)
  culture/   Culture/Community 層(culture_axis, generate_picks, community_experiment, lod2_cluster)
  tools/     build_paper_html

data/   events_patched.jsonl(日本156件)/ events_{us,uk}_grid.jsonl(設計グリッド)/
        interpretations_*・disagreements_* / personas_grid/(ペルソナ4本)/ gss_results・ess_results
        ※生データ(GSS/ESS)は .gitignore・取得スクリプトで再生成
docs/   論文(paper1/2 .md+.html)・spec(paper2_gss_ess_spec_v0.3)・findings(gss/ess)・
        ess_legal_coding・exposure_adapters_spec・internal_notes(思想・非公開)
SI/     results_tables.md(数値一覧)・README.md(再現の三対応表)・reproduce_all.sh
figures/ cache/
```

---

## 開発状況

**実装済み:** Core(3軸エンジン・domain純化)/ CMR(複数観測者グリッド)/ ペルソナ生成(LOD/CSP・SAT-UNSAT)/ Exposure Adapters(GSS・ESS 外部照合)/ Honest Structuralism。Paper 1・Paper 2 は構築過程の書き出し(docs/)。
**次:** 論文 §5.5 本文執筆 → 主観的 mode 経験の本検証(Prolific)/ effective_year 時間発展(Dynamic SCEM)→ **CLI / インターフェース(プロダクト化)**。

---

## 引用・ライセンス

Masamichi Iizumi, Tamaki Iizumi (Miosync, Inc.)

```bibtex
@software{iizumi2026scem,
  title     = {Situated Cohort Exposure Model (SCEM): Reconstructing Generations
               from Social Event Impact Vectors and Life-Stage Sensitivity Windows},
  author    = {Iizumi, Masamichi and Iizumi, Tamaki},
  year      = {2026},
  publisher = {Zenodo},
  version   = {1.0.0},
  doi       = {10.5281/zenodo.20827897},
  url       = {https://doi.org/10.5281/zenodo.20827897},
  note      = {Concept DOI (all versions); v1.0.0 = 10.5281/zenodo.20827898}
}
```

© 2026 Masamichi Iizumi, Tamaki Iizumi (Miosync, Inc.). License: [MIT](LICENSE).
