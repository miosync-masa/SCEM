# SCEM — Situated Cohort Exposure Model

[![DOI](https://zenodo.org/badge/1279042311.svg)](https://doi.org/10.5281/zenodo.20827897)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**社会事象の作用ベクトルが、ライフステージの感受性窓にどう着弾したか**から「世代」を計算するモデル。

> **中心的主張:** 世代とは出生年コホートではなく、**社会事象の作用ベクトルが認知発達上の感受性窓(life-stage sensitivity windows)にどう着弾したかで決まる連続プロファイル**である。

マーケティングの「Z世代論」が抱える三つの欠陥——恣意的なカットオフ・反証不能性・出生年への単一還元——を、計算可能で反証可能なモデルで置き換える。Mannheim (1928) の定性的世代論を計算可能にし、Strauss & Howe (1991) の恣意的カットオフを連続関数に置き換える。

- 📄 Paper 1(preprint draft, 日本語): [`docs/paper1_media_generation.md`](docs/paper1_media_generation.md) · [HTML](docs/paper1.html)
- 📄 Paper 2 — Contextual Mode Resolver(海外版, draft): [`docs/paper2_contextual_mode_resolver.md`](docs/paper2_contextual_mode_resolver.md) · [HTML](docs/paper2.html)
- 🔁 §5.5 外部照合(GSS+ESS)完全再現 SI: [`SI/README.md`](SI/README.md)(三対応表)· [`SI/reproduce_all.sh`](SI/reproduce_all.sh)
- 🏛 正典アーキテクチャ(v6 FIXED): [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## モデル構造(3層 + 意図的スコープ)

| 層 | 役割 | 実装 |
|---|---|---|
| **構造層** | 事象 × 着弾年齢 × 作用モードのテンソル。世代指紋(3軸)・干渉・REFRAME発火を計算 | `media_generation_v4.py` / `v5.py` / `event_loader.py` |
| **Community層** | 環境による曝露変調。閉鎖度(離散アーキタイプ)× 伝播速度(連続offset) | `community_experiment.py` |
| **Culture層** | 嗜好分岐の仮説生成器(マーケ応用) | `culture_axis.py` / `generate_picks.py` |

**3作用モード**(生の合計で同列にしない、3軸として保持):

- **PASSIVE**(受動着弾):身体・原風景への刷り込み。質感・懐かしさ・「当たり前」感。
- **ACTIVE**(能動分岐):意思決定を強制する作用。人生分岐の傷や癖。
- **REFRAME**(参照点書き換え):基準値を書き換え、後続事象との差分で発火する隠れた物差し。

**設計の要点:** イベントを単一カテゴリに潰さない(domainは表示タグ、計算には作用ベクトルのコサインのみを使う)。これは「出生年という離散バケツを拒む」という中心的主張の、イベント側への自己適用である。

**スコープ外(意図的境界):** 個人層(self-efficacy)/ 個人の情報–具現化ラグ / 地域間波及ダイナミクス。SCEM は**集団の曝露構造**を対象とする。

---

## 主要な結果

- **1981年生まれの世代指紋**: PASSIVE **0.81** / ACTIVE 0.56 / REFRAME 0.55(PASSIVE突出)。人格形成期(14–15歳)に「安全神話の崩壊 × 掘って楽しむ消費文化」が同時着弾し、翌年 PlayStation と Windows95 が二重着弾。
- **9世代バッチ(1970–2010)**: PASSIVE 密度は **1980–85年生まれでピーク(0.80)** を取り以降減衰、ACTIVE/REFRAME は単調上昇し2000年前後で接近(3軸の均衡化)。
- **文化選択肢空間の断絶**: 1985→1990(「掘る文化→流される文化」)、1995→2000(「アイドル前提→TikTok前提」)。

![Figure 2](figures/fig2_cohort_fingerprint.png)

![Figure 3](figures/fig3_music_disruption.png)

---

## Paper 2 — Contextual Mode Resolver(同一事象の文脈依存変換)

Paper 1 では各事象に**単一の作用モード**を固定していた。だがモードは事象に固有ではない。**同じ「Brexit」が、ロンドン移民二世中産層には所属基準の書き換え(REFRAME)として、Leave タウンの労働者層には投票による意思表示(ACTIVE)として着弾する。** Paper 2 は `Event.mode` を固定値から作用素 **`Event × Premise → ResolvedImpact`(Contextual Mode Resolver, CMR)** へ持ち上げる。

二つの独立な LLM 観測者(ChatGPT / Gemini)に固定 premise 上でモードを判定させ、不一致を消さず **observer-dependence として測る**。生成は **Honest Structuralism の4公理**(Anchor Preservation / Non-overwrite / Projection Consistency / Provenance)と CSP/SAT-UNSAT で数理アンカーに縛る。

**設計された完全比較グリッド(designed comparison matrix):**

| | 共同体 × 事象 | セル | Event-MFR | Cell-MFR | 観測者間モード不一致 | CDI |
|---|---|---|---|---|---|---|
| **US grid** | 8 × 12 | 96 | 12/12 = **100%** | 75% | 49 | 0.289 |
| **UK grid** | 9 × 13 | 117 | 13/13 = **100%** | 63% | 48 | 0.338 |

> Event-level MFR は **選定した高争点事象集合**での値(ランダムな全社会事象の母数ではない)。

**主要結果:**
- **同一事象の共同体間モード分岐**(Brexit: London=REFRAME / Leave Town=ACTIVE / NI Protestant=ACTIVE / Scotland=REFRAME)。
- **同年生まれ・別共同体**で世代指紋が反転(US: Coastal Liberal=REFRAME支配 ⇄ Bible Belt=ACTIVE支配、CDI 0.32–0.34)。
- **同一入力ペルソナの分岐**:1985生まれ・Fight 固定で premise だけ変えると provenance が体系的に割れる(Coastal は全REFRAME、Bible Belt は 9.11 を ACTIVE 分岐として引き受ける)。`data/personas_grid/`。

![Paper2 US mode matrix](figures/fig_p2_modematrix_us_grid.png)

![Paper2 UK mode matrix](figures/fig_p2_modematrix_uk_grid.png)

```bash
# 二観測者マージ → モード変換マトリクス / 同年生まれ指紋 / 図
python3 src/cmr/merge_paper2_data.py --country us --variant grid
python3 src/cmr/cmr_matrix.py        --country us --variant grid
python3 src/cmr/cmr_compare.py       --country us --variant grid
python3 src/cmr/make_paper2_figures.py

# CMR ペルソナ(要 OpenAI; 同一入力・premise だけ変える)
arch -arm64 python3.12 src/cmr/lod_persona.py --country us --birth_year 1985 \
  --response Fight --strategy "自分の選択で状況に介入する" \
  --premise secular_white_coastal_graduate --variant grid
```

> **データ収集メモ:** グリッドは ChatGPT × Gemini で構築。Gemini は*内容*(rationale)は良質だが*梱包*が壊れる(出力のシリアライズ破損で各事象の先頭共同体を喪失。`recover_gemini_jsonl.py` で決定論復旧・捏造なし)。方針は **Gemini 全置換ではなく複数観測者化**:Gemini の回収済み内容は保持し(公理4)、破損で欠けた所を Claude で埋め、可能な所は **ChatGPT × Gemini × Claude** の追加観測者にする(置換ではなく追加)。

---

## クイックスタート

```bash
# 構造層(エンジン)は標準ライブラリのみで動く
python3 src/core/media_generation_v5.py 1981       # 1981年生まれの3軸プロファイル

# 9世代バッチ
PYTHONPATH=src/core python3 -c "import media_generation_v5 as v5; v5.batch_compare([1970,1975,1980,1985,1990,1995,2000,2005,2010], v5.load_events())"

# 図の生成(matplotlib が必要)→ figures/ に出力
python3 src/core/make_figures.py

# Culture層・Community層(LLM)は OpenAI API キーが必要
cp .env.example .env   # 各自のキーを記入(.env は .gitignore 済み)
python3 src/culture/generate_picks.py --batch
python3 src/culture/community_experiment.py
```

依存(LLM層・図のみ): [`requirements.txt`](requirements.txt) を参照(`openai`, `python-dotenv`, `matplotlib`)。

---

## リポジトリ構成

```
README.md  ARCHITECTURE.md  LOD_ARCHITECTURE.md  requirements.txt  .env.example
  (LOD_ARCHITECTURE.md = LOD と4公理による解像度制御 / Paper 2 理論基盤)

src/                         全 Python コード(Paper2 §8.1 の層構成に対応)
  core/                      = SCEM Core(Paper 1 構造層)
    media_generation_v4.py   構造層 計算コア(感受性カーブ/3モード/干渉/REFRAME/被り判定)
    media_generation_v5.py   データ接続・3軸レポート・多世代バッチ
    event_loader.py          156件DB ローダー
    make_figures.py          Figure 2 / 3 生成 / build_html.py 印刷用HTML / test_domainless.py test_lag.py
  culture/                   Paper 1 Culture/Community 層
    culture_axis.py  generate_picks.py  compare_picks.py  culture_interactive.py
    community_experiment.py(閉鎖度×伝播速度の分岐ペルソナ)  lod2_cluster.py
  cmr/                       = CMR Layer(Paper 2 本体)
    merge_paper2_data.py     国別 event DB 統合(LOD0事象/LOD1解釈を物理分離; --country us|uk --variant v1|grid)
    cmr_matrix.py  cmr_compare.py(mode変換マトリクス / 指紋・MFR・CDI)
    generate_claude_observer.py  recover_gemini_jsonl.py(第2観測者/破損復旧)
    lod_persona.py(CSP/SAT-UNSAT)  make_paper2_figures.py
  adapters/                  = Exposure Adapters(外部照合)
    gss/  gss_acquire・segments・core_contrast・interaction・valuepack・overlay(US二次分析)
    ess/  ess_acquire・segments・core_validation・valuepack・southern_country・effective_year・overlay(UK/Europe)
  tools/                     build_paper_html.py(docs/*.md → 投稿体裁の単一HTML)

data/    events_patched.jsonl   社会事象DB(日本, 156件, 出典URL付き)
         events_{us,uk}_v1.jsonl / Gemini_events_*_v1.jsonl  Paper2 探索版入力(ChatGPT/Gemini)
         events_{us,uk}_grid.jsonl / Gemini_events_*_grid.jsonl  設計グリッド(US 96 / UK 117 セル)
         events_*_merged.jsonl(LOD0)/ interpretations_*.jsonl(LOD1, source_model付)
         disagreements_*.jsonl(観測者依存の証拠)/ merge_report_*.md
         cmr_compare_{us,uk}_1985_grid.json(同年生まれ指紋/CDI)
         personas_grid/  CMR ペルソナ(同一入力・premise だけ変えた4本)
docs/    paper1_media_generation.md / paper1.html   Paper 1 本文(全7章 + 付録A–D)
         paper2_contextual_mode_resolver.md / paper2.html   Paper 2 本文(CMR)
         paper2_cmr_report.md(巴向け報告)  paper2_grid_spec.md  paper2_prompt_{us,uk}.md(再現プロンプト)
         paper2_gss_ess_spec_v0.3.md(GSS+ESS 統合 正本spec)  paper2_gss_spec_v0.2.md(GSS単独・0.3に統合)
         gss_validation_findings.md(GSS結果 §2.5-2.8)
         ess_validation_plan.md(ESS設計)  ess_validation_findings.md(ESS結果 §0-6)  ess_legal_coding.md(制度年 出典)
figures/ fig2_cohort_fingerprint.png  fig3_music_disruption.png(Paper1)
         fig_p2_modematrix_*_grid.png  fig_p2_fingerprints_*_1985_grid.png(Paper2)
cache/   picks_cache/(9世代)  community_experiment_cache.json(Appendix D)
```

---

## ステータス

**Paper 1: Preprint v1**(タイムスタンプ確保, DOI 取得済)。構造層 + Culture層(仮説生成器)を収録。

**Paper 2: working draft**([`docs/paper2_contextual_mode_resolver.md`](docs/paper2_contextual_mode_resolver.md))。Contextual Mode Resolver を実装し、米英の設計グリッド(US 96 / UK 117 セル)で観測者依存性・モード分岐・共同体間発散・同一入力ペルソナの分岐を報告済み。**実証(Prolific)は Paper 3 へ。**

達成済み:
- **Contextual Mode Resolver**: `Event × Premise → ResolvedImpact` を二観測者マージで実装。Event-level MFR 両国 100%(選定争点事象)、CDI 0.32–0.34。
- **LOD アーキテクチャ**([`LOD_ARCHITECTURE.md`](LOD_ARCHITECTURE.md)): 曝露構造(LOD 0, 数理)からペルソナ(LOD 3, 解釈)までを解像度の階層として扱い、4公理(Anchor Preservation / Non-overwrite / Projection Consistency / Provenance)を制約とする CSP として定式化。[`lod_persona.py`](src/cmr/lod_persona.py) は Projection Consistency と Axiom 違反で SAT/UNSAT を判定(`arch -arm64 python3.12 src/cmr/lod_persona.py ... --variant grid`)。
- **3C フレームワーク**: Culture / Community / **Code**(=共同体の「許可・禁止・黙認・推奨」の規範コード。プログラミング技能ではない)。

次の課題:
- **実証(Prolific パネル)**: プロファイル一致率・断絶境界・干渉特異性・CMR 解決モードの人手検証。
- **複数観測者化(ChatGPT × Gemini × Claude)**:Gemini は内容良質・梱包破損(先頭共同体を喪失)。置換ではなく、欠けた所を Claude で補完(US Coastal Liberal / UK London Multicultural は **Claude で2観測者化済み**、`generate_claude_observer.py`、Claude×ChatGPT mode不一致 US6/UK2)。可能な所を3観測者へ拡張するのが次段階。
- **Exposure Adapters / Dynamic SCEM**([`docs/exposure_adapters_spec.md`](docs/exposure_adapters_spec.md)): 実体曝露(統計・政策データ)と情報曝露(GDELT 等)を別系統で観測し Core で統合。**GDELT は本体に組み込まず Information Exposure Adapter 仕様に留める**(報道空間の波の観測であって実体曝露・個人内面の測定ではない)。まずは US/UK 完全グリッド版 CMR の確立を最優先。

---

## 著者・引用

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
