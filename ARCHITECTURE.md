# SCEM — Architecture (v7)

**Status: FIXED (2026-07-01).** 正典(single source of truth)。以降のコード・論文はこの仕様に従う。仕様変更はバージョンを上げること。
v6(2026-06-24, 構造層のみ)+ LOD Architecture(2026-06-25, ペルソナ生成)を **Track A / Track B に統合**したのが v7。

**対象:** 集団の曝露構造(collective exposure structure)。**個人の内面・個人ラグは対象外**(→ [スコープ外](#スコープ外意図的境界))。
略称 **SCEM**。Paper 1 和名「年齢同期型メディア世代論」は本モデルの世代論的提示。

---

## 0. 位置づけ — 二つの顔・一つのエンジン

SCEM は **共通エンジン(Core = LOD 0 = 曝露構造の数理)** の上に二つの顔を持つ:

- **Track A(構造・学術)** — LOD 0 を**世代論**として使う。事象×着弾年齢×作用モードのテンソルで世代指紋を計算し、共同体 premise でモードを解決する(CMR)。→ [Part A](#part-a--構造学術のアーキテクチャtrack-a)
- **Track B(ペルソナ生成)** — LOD 0 を**生成のアンカー**として使う。曝露構造(LOD 0)からペルソナ(LOD 3)を、4公理を制約とする CSP で由来追跡可能に生成する。→ [Part B](#part-b--ペルソナ生成のアーキテクチャtrack-b)

**中心原理(両トラック共通):**
> **数理(Python)= 事象 = 固定 = 曝露構造 / 解釈(LLM)= 反応 = 分岐可能 = ペルソナ表現。**

数理は安定して数値化できるもの(年齢・感受性カーブ・cos・effective_year)を、解釈は数値化すると痩せるもの(質感・規範・文脈)を担う。**相互に代替不能**で、cos と Projection を接続点に組み合わさる。この役割分担が両トラックの土台。

---

# Part A — 構造・学術のアーキテクチャ(Track A)

## A1. 構造層(Core)— 事象 × 着弾年齢 × 作用モード  〔実装済: `src/core/media_generation_v4.py` / `v5.py` / `event_loader.py`〕

- **3作用モード** PASSIVE / ACTIVE / REFRAME。生の合計で同列にせず **3軸**で保持(`mode_density`, `report_3axis`):
  - PASSIVE(受動着弾):$w = s\cdot\lambda$
  - ACTIVE(能動分岐=決断強制):$w = s\cdot(0.30+0.70\alpha)\cdot\lambda$
  - REFRAME(参照点書き換え):$w = s\cdot(0.50+0.50\alpha)\cdot\lambda$
- **感受性カーブ** 非対称ガウス・**個別 peak 優先ハイブリッド**(個別 `sensitivity_peak_age` があれば使用、無ければ領域×モードのフォールバック33本):
  $g(a)=\max(\phi,\ \exp[-(a-\mu)^2/2\sigma(a)^2])$、$\sigma=\sigma_L\,(a\le\mu)\ /\ \sigma_R\,(a>\mu)$。
- **REFRAME 発火** 同一 `reframe_group` 内のアンカー→トリガーで `reference_value` の**対数比**で差分発火:
  $\delta=\min(1,\ \log(\max/\min)/\log 2)$、$\text{fire}=w_a(0.35+0.65\,w_t)\,\delta$。
- **干渉** 同一認知バンドへの同時着弾のみ。**作用直交性** $D=1.6-1.05\min(\cos,1)$ で増幅(cos=0→1.6 / cos=1→0.55):
  $\text{score}=\frac{w_a+w_b}{2}\cdot D\cdot(0.5+0.5\,p)$、$p=1-\min(\delta a/W,1)$。
- **被り判定** `effect_vector` の**コサインのみ**で4段階(duplicate/sibling/interference/independent)。**domain は計算に非関与**。
- **イベントを単一カテゴリに潰さない**=連続作用ベクトル $\mathbf{v}_e$。domain は**人間用の表示タグ**にすぎず計算に入らない(設計根拠は §C3)。

## A2. Community層 — Situated(環境)の変調  〔プロトタイプ: `src/culture/community_experiment.py`〕

- **閉鎖度** = **離散アーキタイプ**(開放/中間/閉鎖)。**塊(クラスタ)を作る**。Code(規範コード=許可・禁止・黙認・推奨)を内包。
  - 実測根拠:閉鎖度固定(速度可変)の平均cos=0.90 > 速度固定=0.86。閉鎖型は速度に依らず一点収束(内部cos=0.93)→ 離散扱いが妥当。
- **伝播速度** = **連続 offset**。`effective_year` を地域で変調(速0/中+1/遅+2年)。**塊を作らない**(同一閉鎖度内をなめらかにずらす)。
- 閉鎖度が個人の具現化遅延を生むが、**個人ラグ自体は測らない**(集団曝露構造として扱う)。

## A3. Culture層 — 嗜好分岐(仮説生成器)  〔実装済: `src/culture/culture_axis.py` / `generate_picks.py` / `compare_picks.py`〕

- 4軸 pickリスト(音楽/スポーツ/文学/映画)を世代別に LLM 生成。構造プロファイル+嗜好で文化サブクラスタを生成。
- 位置づけは**仮説生成器**。実在分布の測定ではない。

## A4. CMR Layer — 文脈依存モード解決(Paper 2 で追加)  〔実装済: `src/cmr/`〕

- `Event.mode` を固定値から**作用素 `Event × Premise → ResolvedImpact`** へ持ち上げる。同じ事象でも共同体 premise で PASSIVE/ACTIVE/REFRAME が変わる。
- 複数 LLM 観測者(ChatGPT × Gemini × Claude)で mode を解決し、不一致を消さず **observer-dependence として測る**(`cmr_matrix.py` / `cmr_compare.py` / `merge_paper2_data.py`)。
- 設計済み比較グリッド(US 8×12 / UK 9×13)で mode 変換・MFR・CDI を測定。詳細は `docs/paper2_contextual_mode_resolver.md`。

## A5. Exposure Adapters — 曝露構造の供給層  〔`src/adapters/{gss,ess}/`〕

- 曝露構造の**差し替え可能なデータ源**:curated DB(`events_patched.jsonl`)/ 外部サーベイ(GSS=US, ESS=UK/Europe)/ 将来 GDELT 等。
- 実体曝露(統計・政策)と情報曝露(報道)を別系統で観測し Core で統合する設計は `docs/exposure_adapters_spec.md`。

## A6. グラウンディング — プロンプト調整(アーキテクチャ非依存)

- LLM 側の地域特性解像度を磨く=**唯一の残調整**。アーキテクチャは変えない、プロンプト品質の問題。

## スコープ外(意図的境界)

「対象=集団の曝露構造」を保つために**やらない**と決めた境界:
- **個人層**(self-efficacy、個人の能力・意志)。※ ただし Track B は「個人ペルソナ表現」を LOD 3 として扱う — これは**個人の断定でなく**「その位置の人が持ちやすい曝露構造」の解釈生成(→ Part B 倫理境界)。
- **個人の情報-具現化ラグ**(`test_lag.py` で味見 → 集団普及ラグは仮説と逆向き+右側打ち切り汚染。個人の「知る vs なる」ギャップは本プロキシで測れず境界外)。
- **地域間具現化波及の動的モデル**(キャズム/普及の地域間ダイナミクス)。

## 検証アーキテクチャ(外部照合の位置づけ)

- Core/CMR の妥当性は **外部サーベイ(GSS/ESS)との照合**で見る。**検証の問い=予測精度でなく「個人化↔統計束のトレードオフをクリアした中間傾向束の実在」**。強度は「予測対応・suggestive・modest」、確証と書かない。
- 主結果=**二段構造**:premise が水準を、`effective_year` がスロープ可視性(移行段階)を駆動。数値は `SI/results_tables.md`、再現は `SI/reproduce_all.sh`。

---

# Part B — ペルソナ生成のアーキテクチャ(Track B)

Paper 1 が「個人層は射程外」とした境界の**その先**を、LOD 0(曝露構造)→ LOD 3(個人ペルソナ)の**解像度の階層**として定式化する。Core エンジン(`v4/v5`)には**一切変更を加えない**。

## B1. LOD 階層(Level of Detail)

3D グラフィックスの LOD と同型。用途(カメラ距離)が LOD を、LOD がスコープを決める。

| LOD | 名称 | 内容 | 数理:解釈 | 担当 |
|-----|------|------|-----------|------|
| 0 | ExposureStructure | 曝露プロファイル(3軸指紋・主要事象・干渉・REFRAME発火) | 100:0 | Python(Core) |
| 1 | ResponseOrientation | 応答方向(Fight / Flight 等) | 50:50 | LLM |
| 2 | StrategyBranch | 戦略分岐(技術で攻める / 大企業で守る 等) | 25:75 | LLM |
| 3 | PersonalContext | 個人文脈(職種・家族・地域・資産・学歴・関係資本) | 5:95 | LLM |

**遷移:** `refine: LOD_n → LOD_{n+1}`(解釈追加=分岐)/ `project: LOD_{n+1} → LOD_n`(要約=射影)。
```
LOD₀ = ExposureStructure
LOD₁ = refine(LOD₀, response_orientation)
LOD₂ = refine(LOD₁, strategy_branch)
LOD₃ = refine(LOD₂, personal_context)
```
**用途対応:** 社会学=LOD 0 で十分 / マーケ=LOD 1〜2(Paper 1 Appendix D の正体)/ カウンセリング=LOD 3。**用途を超えた LOD は冗長**。
**連続性:** LOD は離散スイッチでなくシームレス(LOD 1.5 も許す)。「世代を連続プロファイルとして扱う」と構造的に同型。

## B2. 4公理(Honest Structuralism / SCEM Axioms)

LOD 操作が満たすべき正当性条件。同時に LLM 生成のバリデーション基準。

- **Axiom 1: Anchor Preservation(固定点保存)** — 低LODの事象・年齢・mode・weight は保存される(数理は不動の骨格)。違反例:LOD 3 で「就職氷河期の影響を受けていない」と生成し LOD 0 と矛盾。
- **Axiom 2: Non-overwrite(非上書き)** — 高LODの解釈は数理結果を書き換えない。情報を**足す**のは可、**書き換え**は不可。違反例:「Fight型だから感受性ピークが若年化」と解釈で数理を変更。
- **Axiom 3: Projection Consistency(射影整合性)** — `project(LOD₃→LOD₀)=LOD₀`。生成ペルソナを要約すると元の曝露構造が復元される(LOD 3 が LOD 0 を包含する操作的定義)。違反例:LOD 3「大学進学なし」だが LOD 0 に「大学進学19歳ACTIVE」が高重み。
- **Axiom 4: Provenance Traceability(由来追跡可能性)** — すべての解釈枝は、どの事象・干渉・REFRAME から派生したか追跡できる。違反例:「不安を抱えている」が LOD 0 の何に対応するか不明。

**2軸整理(対称・レトラクション構造):**

| | 静的制約(構造) | 動的制約(過程) |
|---|---|---|
| **refine時(下→上)** | Axiom 2: Non-overwrite | Axiom 4: Provenance |
| **project時(上→下)** | Axiom 1: Anchor Preservation | Axiom 3: Projection Consistency |

上り下り両方向に2つずつ制約 → refine で足した解釈は project で落ちるが元の LOD 0 は保存(=情報損失なき往復)。

## B3. CSP(制約充足問題)としての定式化

```
変数 = 各LODの解釈内容 / ドメイン = LLM生成可能な全パターン / 制約 = 4公理 + ユーザー指定
```
LOD が上がるごとに制約が**増え**、解空間が狭まる(LOD 3 で「この人」に絞られる)。どの LOD でも LOD 0 の制約は保存(=Anchor Preservation)。

**SAT / UNSAT 検出**(単なるエラー処理でなく診断信号):
- **SAT**: 全制約充足 → 有効ペルソナとして出力。
- **UNSAT**: 矛盾 → リジェクト・再生成。用途:
  - **LLM 幻覚検出**(もっともらしいが LOD 0 と矛盾 → Projection Consistency 違反で捕捉)。
  - **自己認識のズレ可視化**(「Flight のつもりだが構造的には Fight」— カウンセリング応用の設計機能)。
  - **制約組合せの矛盾発見**。

制約(LOD 0 という数理アンカー)が LLM の自由度を絞り、生成を**観測**に近づける(「次どうする?」でなく「この人はこう反応する」)。

## B4. 実装プロトタイプ仕様(`src/cmr/lod_persona.py`)

Core エンジンには触らない。
```
入力 LODConstraints: lod0_exposure / lod1_response(Fight|Flight|None) / lod2_strategy / lod3_context
出力 dict: status(SAT|UNSAT) / persona{summary, narrative, provenance} / attempts
```
**検証フロー:** (1) 4公理を明示したプロンプト構築 → (2) LLM 呼び出し → (3) 生成ペルソナを `project(LOD0)` で射影 → (4) 元 lod0_exposure と比較(一致=SAT / 不一致=UNSAT 再試行)→ (5) max_retries 超過で理由付き UNSAT。
**Projection Consistency の MVP:** ペルソナの `provenance` から LOD 0 要素を抽出し、**核事象(上位重み・REFRAME発火ペア・主要干渉)の大半**(閾値 MVP 70%)が現れるかで判定。厳密一致は要求しない。
**MVP 範囲外(意図的):** 完全 CSP ソルバー / LOD0↔3 双方向変換の数学的厳密性 / ペルソナDB化 / WebUI・API化。

## 倫理境界(Track B の第一条・製品化時も不変)

SCEM は**個人の内面を断定しない**。LOD 3 出力は「ある出生年・共同体・制度環境に置かれた人が**どんな曝露構造を持ちやすいか**」の推定であって個人の決めつけではない。四線:**分類でなく理解 / 操作でなく翻訳 / 断定でなく来歴追跡 / 分断でなく相互理解**。= 人を分類する道具でなく**異なる意味世界の翻訳地図**(Paper 2 §6.4 と一致)。

---

# 共通

## 実装ステータス早見

| 層 | Track | 状態 | 実装 |
|---|---|---|---|
| 構造層(Core) | A | **実装済・純化済**(domain非依存・D項統合) | `src/core/` |
| Community層 | A | プロトタイプ | `src/culture/community_experiment.py` |
| Culture層 | A | 実装済 | `src/culture/` |
| CMR Layer | A | 実装済(グリッド・複数観測者) | `src/cmr/` |
| Exposure Adapters | A | 実装済(GSS・ESS) | `src/adapters/{gss,ess}/` |
| LOD / ペルソナ生成 | B | 実装済(CSP・SAT/UNSAT) | `src/cmr/lod_persona.py` |

**FIX スタンプ(1981年生まれ):** 指紋 PASSIVE 0.81 / ACTIVE 0.56 / REFRAME 0.55。干渉トップ=Windows95発売 × プリクラ普及(score 1.60)。被り判定 domain非依存=True、干渉 D項統合=True。

## 検証アーティファクト(再現性)

- `src/core/test_domainless.py` — domain冗長性の実測(指紋・バッチ不変、干渉9/10一致 → domain廃止を正当化)
- `src/culture/community_experiment.py` — 閉鎖度=離散 / 速度=連続 の非対称を実測
- `src/core/test_lag.py` — 情報-具現化ラグ味見(個人ラグをスコープ外とする根拠)
- `src/core/make_figures.py` / `src/cmr/make_paper2_figures.py` — 図
- `SI/reproduce_all.sh` / `SI/results_tables.md` — GSS/ESS 外部照合の完全再現・数値一覧

## 設計根拠(なぜこう設計したか・思想は最小)

- **domain を計算に入れない**:イベントを単一カテゴリに潰すのは「出生年という離散バケツを拒む」中心主張の**イベント側への自己適用**。作用ベクトルの cos だけで被りを判定し、domain は表示タグに格下げ(`test_domainless.py` で不変を実測)。
- **数理/解釈を分ける**:混ぜるとカテゴリ違反(解釈に N数・検定を当てる/数理に解釈を混ぜる)を生む。両者は代替不能。
- **4公理を課す**:LOD 0 を持たない LLM 出力は Projection Consistency が破綻し「上手いが空虚」になる。数理アンカーに縛ることで生成を観測に近づけ、捏造を構造的に拒否する。
- **LOD(3Dグラフィックス同型)**:用途を超えた解像度は冗長。社会学は LOD 0、マーケは LOD 1〜2、個人は LOD 3。
- (より広い存在設計理論・領域横断の同型論は実装に不要な思想として `docs/internal_notes.md` に分離。)

## Appendix: 用語対応表

| 用語 | 等価表現 |
|---|---|
| LOD 0 | exposure profile / 3軸指紋 / 曝露構造 / 数理アンカー |
| LOD 1〜3 | refine された解釈レイヤー / ペルソナ表現 |
| refine / project | 解釈分岐(制約追加)/ 解釈射影(要約) |
| 4公理 | SCEM Axioms / Honest Structuralism |
| CMR | Contextual Mode Resolver(`Event × Premise → ResolvedImpact`) |
| premise | 共同体前提(宗教×人種×地域×学歴 / 階級×EU距離×religiosity 等) |
| SAT / UNSAT | 制約充足 / 不充足 |
