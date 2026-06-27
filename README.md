# SCEM — Situated Cohort Exposure Model

[![DOI](https://zenodo.org/badge/1279042311.svg)](https://doi.org/10.5281/zenodo.20827897)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**「世代」を出生年バケツではなく曝露構造として計算し、同じ社会事象が共同体ごとに別の作用モードへ解決される様子を扱う計算フレームワーク。**

> **中核主張(2つ):**
> 1. **世代 = 出生年コホートではない。** 社会事象の作用ベクトルが認知発達上の**感受性窓**にどう着弾したかで決まる連続プロファイルである。
> 2. **作用モードは事象に固有ではない。** 共同体の前提(premise)によって解決される —— `Event × Premise → ResolvedImpact`(Contextual Mode Resolver)。

マーケティングの「Z世代論」の三欠陥(恣意的カットオフ・反証不能・出生年への単一還元)を、計算可能で反証可能な枠組みで置き換える。Mannheim (1928) の定性的世代論を計算可能にし、Strauss & Howe (1991) の恣意的カットオフを連続関数に置き換える。

---

## フレームワーク構成(層)

リポジトリの `src/` はこの層構成に物理対応する。

| 層 | 役割 | 実装(`src/`) |
|---|---|---|
| **Core**(構造層) | 事象 × 着弾年齢 × 作用モードのテンソル。世代指紋(3軸)・感受性窓・干渉・REFRAME発火・effective_year を計算 | `core/`(`media_generation_v4/v5`, `event_loader`) |
| **CMR Layer** | `Event.mode` を固定値から作用素 **`Event × Premise → ResolvedImpact`** へ持ち上げる。複数 LLM 観測者で mode を解決、observer-dependence を測る。LOD/CSP でペルソナ生成 | `cmr/`(`cmr_matrix/compare`, `merge_paper2_data`, `lod_persona`, …) |
| **Exposure Adapters** | 曝露構造の供給層(差し替え可能)。curated DB / 外部サーベイ(GSS, ESS)/ 将来 GDELT 等 | `adapters/{gss,ess}/` |
| Culture/Community | 嗜好分岐の仮説生成器・環境変調(マーケ応用) | `culture/` |

> 実体曝露(統計・政策)と情報曝露(報道・GDELT 等)を**別系統で観測し Core で統合**する設計は [`docs/exposure_adapters_spec.md`](docs/exposure_adapters_spec.md)。GDELT は本体に組み込まず Information Exposure Adapter 仕様に留める。

---

## 中核概念

**3作用モード**(合算せず3軸として保持):
- **PASSIVE**(受動着弾):身体・原風景への刷り込み。質感・「当たり前」感。
- **ACTIVE**(能動分岐):意思決定を強制する作用。人生分岐の傷・癖。
- **REFRAME**(参照点書き換え):基準値を書き換え、後続事象との差分で発火する隠れた物差し。

**2つの軸**(SCEM は元から動的):
- **着弾年齢軸**(Core):同じ事象でも何歳で食らうかで mode が変わる(非対称ガウス感受性窓・`effective_year`)。
- **共同体 premise 軸**(CMR):同じ事象・同じ年齢でも、どの規範コードで食らうかで mode が変わる。
  - 例:同じ Brexit が、ロンドン移民二世には**所属基準の書き換え(REFRAME)**、Leave タウン労働者には**投票による意思表示(ACTIVE)**。

**EVENT_STRUCTURE**(事象の時間構造):単発モーメント(Obergefell/Dobbs=出生年で着弾年齢が変わる→観測可能)vs 反復バースト(乱射 Columbine→Uvalde=全出生年が窓で食らう→出生年では原理的に観測不能)。**検証前に必ず振り分ける。**

**Honest Structuralism(4公理)**:Anchor Preservation / Non-overwrite / Projection Consistency / Provenance。生成を数理アンカーに縛り、捏造を CSP/SAT-UNSAT で構造的に拒否する。倫理境界 = SCEM は人を分類する道具でなく、異なる意味世界の**翻訳地図**。

---

## フレームワークが計算するもの

- **世代指紋(3軸プロファイル)**:任意の出生年 → (PASSIVE, ACTIVE, REFRAME)。例:1981年生まれ = 0.81 / 0.56 / 0.55(PASSIVE突出)。9世代バッチ(1970–2010)で PASSIVE 密度が 1980–85 でピーク(0.80)→減衰の非単調構造。
- **設計された比較グリッド**:固定 Community × 固定 Event で mode 変換を測る。US 8×12=96 / UK 9×13=117 セル、Event-level MFR 両国 100%(選定争点)、CDI US 0.289 / UK 0.338。同一事象の共同体間モード分岐(Brexit: London=REF / Leave Town=ACT)。
- **同一入力ペルソナの premise 分岐**:出生年・自己記述を固定し premise だけ変えると provenance が体系的に割れる(`data/personas_grid/`)。
- **外部サーベイによる照合**(下記)。

![cohort fingerprint](figures/fig2_cohort_fingerprint.png)
![mode matrix US](figures/fig_p2_modematrix_us_grid.png)

---

## 外部照合(GSS + ESS)— 妥当性チェック(強度は正確に)

> **検証の問い:** 「SCEM が態度を*正確に予測*できるか」ではない。**「個人化(N爆発)と統計束(出生年バケツ=凡庸)のトレードオフをクリアした中間レベルの傾向束が実在するか」**の妥当性チェック。強度は「**予測対応・suggestive・modest**」と書き、「確証」とは書かない。

US(GSS 1972–2024)+ UK/Europe(ESS 2014–24, 33か国)を貫いて立ち上がった **二段構造**:

> **共同体 premise が「水準」を、`effective_year` が「スロープ可視性(移行段階)」を駆動する。**

- **水準ゲート(普遍)**:secular/educated/urban が寛容高位、religious/low-edu が低位 —— US/EU・3柱で一貫(GSS Coastal 91% vs Bible Belt / ESS Secular 90% vs Religious 66%)。
- **スロープ・ゲート(移行段階依存)**:出生年スロープ(b′)は「移行中の共同体」でのみ可視 —— US Bible Belt(移行中, 6→66%)/ Southern Europe 5国(ES/PT/IT/GR/CY 全て正勾配・有意)。Nordic/Western は移行完了で平坦。承認年(effective_year)と移行段階に単調対応(Spearman 0.41–0.67)。
- 完全再現は [`SI/`](SI/README.md)(本文の全数字 ⇄ コード ⇄ 再現コマンドの三対応表 + `reproduce_all.sh`)。

詳細・綻び(p=0.16 / base rate / 不安定セル除外 等)は findings に正直に記録:[`docs/gss_validation_findings.md`](docs/gss_validation_findings.md) / [`docs/ess_validation_findings.md`](docs/ess_validation_findings.md)。

---

## クイックスタート

```bash
# Core(構造層)は標準ライブラリのみ
python3 src/core/media_generation_v5.py 1981       # 1981年生まれの3軸プロファイル
PYTHONPATH=src/core python3 -c "import media_generation_v5 as v5; v5.batch_compare([1970,1980,1990,2000,2010], v5.load_events())"
python3 src/core/make_figures.py                    # 図 → figures/

# CMR(設計グリッド)
python3 src/cmr/merge_paper2_data.py --country us --variant grid
python3 src/cmr/cmr_matrix.py        --country us --variant grid
python3 src/cmr/make_paper2_figures.py

# Exposure Adapters(外部照合・完全再現)
bash SI/reproduce_all.sh             # GSS=ネット / ESS=ESS_USER_ID 環境変数(未設定でスキップ)

# LLM 層(Culture / CMR ペルソナ)は OpenAI キーが必要
cp .env.example .env                 # .env は .gitignore 済み
arch -arm64 python3.12 src/cmr/lod_persona.py --country us --birth_year 1985 \
  --premise secular_white_coastal_graduate --response Fight --variant grid
```

依存:[`requirements.txt`](requirements.txt)(`numpy`, `pandas`, `pyarrow`, `matplotlib` / LLM層は `openai`, `python-dotenv`)。scipy/statsmodels 不使用(OLS+HC1・ロジット・Spearman は numpy 自前実装)。

---

## リポジトリ構成

```
README.md  ARCHITECTURE.md(正典 v6 FIXED)  LOD_ARCHITECTURE.md(LOD/4公理/CSP)  requirements.txt

src/                  全 Python(フレームワーク層構成)
  core/      = SCEM Core(media_generation_v4/v5, event_loader, make_figures, build_html, tests)
  cmr/       = CMR Layer(cmr_matrix/compare, merge_paper2_data, generate_claude_observer,
               recover_gemini_jsonl, lod_persona[CSP/SAT-UNSAT], make_paper2_figures)
  adapters/  = Exposure Adapters
    gss/  acquire・segments・core_contrast・interaction・valuepack・overlay(US 二次分析)
    ess/  acquire・segments・core_validation・valuepack・southern_country・effective_year・overlay(UK/Europe)
  culture/   Culture/Community 層(culture_axis, generate_picks, community_experiment, lod2_cluster)
  tools/     build_paper_html

data/   events_patched.jsonl(日本156件)/ events_{us,uk}_grid.jsonl(設計グリッド)/
        interpretations_*・disagreements_*(観測者依存の証拠)/ personas_grid/ /
        gss_results・ess_results(集計出力)  ※生データ(GSS/ESS)は .gitignore・取得スクリプトで再生成
docs/   論文書き出し(paper1/paper2 .md+.html)・確定spec(paper2_gss_ess_spec_v0.3)・
        findings(gss/ess)・ess_legal_coding・exposure_adapters_spec・internal_notes(思想・非公開)
SI/     §外部照合の完全再現(README 三対応表 + reproduce_all.sh)
figures/ cache/
```

---

## 開発状況と書き出し

フレームワークは反復的に構築され、各段階を**書き出し(write-up)**として記録している(以下は中間プロセスの記録であり、フレームワーク本体ではない):

- **Paper 1**(SCEM 構造層・SocArXiv 用 preprint, DOI 取得済):[`docs/paper1_media_generation.md`](docs/paper1_media_generation.md) · [HTML](docs/paper1.html)
- **Paper 2**(Contextual Mode Resolver, working draft):[`docs/paper2_contextual_mode_resolver.md`](docs/paper2_contextual_mode_resolver.md) · [HTML](docs/paper2.html)
- **確定 spec / SI**:[`docs/paper2_gss_ess_spec_v0.3.md`](docs/paper2_gss_ess_spec_v0.3.md) / [`SI/README.md`](SI/README.md)

**実装済み:** Core(3軸エンジン・domain純化)/ CMR(複数観測者グリッド・LOD/CSP ペルソナ)/ Exposure Adapters(GSS・ESS 外部照合)/ Honest Structuralism。
**次:** 主観的 mode 経験の本検証(Prolific)/ effective_year 時間発展(Dynamic SCEM)/ 観測者の Claude 拡張・GDELT 情報曝露 Adapter。

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
