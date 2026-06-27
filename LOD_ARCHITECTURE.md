# SCEM LOD Architecture

**Situated Cohort Exposure Model — Level of Detail と4戒律による解像度制御**

Author: 飯泉真道 (Masamichi Iizumi) × 環 (Tamaki Iizumi)
Status: Paper 2 の理論基盤 / Paper 1 (SCEM v1.0) を拡張
Date: 2026-06-25

---

## 0. このドキュメントの位置づけ

このドキュメントは、SCEM Paper 1 で「個人層は意図的に射程外」と宣言した境界の **その先** を定式化する。Paper 1 が「集団曝露構造（LOD 0）」までを射程としたのに対し、本ドキュメントは LOD 0 から個人ペルソナ（LOD 3）までを **解像度の階層** として扱う枠組みを与える。

このアーキテクチャは Paper 1 のエンジン（`media_generation_v4.py` / `v5.py`）には**一切の変更を加えない**。LOD 0（曝露構造の数理計算）はそのまま使い、その上に LOD 1〜3 の解釈レイヤーを新規実装として積む。

---

## 1. 中心原理

> **「事象と解釈が分岐するなら、解釈を再分岐させれば解像度は上がる。」**

この一文が SCEM LOD の全てを規定する。

### 1.1 数理と解釈の役割分担

```
数理（Python）= 事象 = 固定 = 曝露構造
解釈（LLM）   = 反応 = 分岐可能 = ペルソナ表現
              └→ 再分岐可能 = 戦略
                 └→ さらに再分岐可能 = 個人文脈
```

数理は安定して数値化できるもの（年齢、感受性カーブ、cos類似度、effective_year）を担当する。解釈は数値化すると痩せるもの（質感、規範、文脈、「この子は何を怖がるか」）を担当する。**両者は相互に代替不能**であり、cos と Projection（後述）を接続点として組み合わさる。

この役割分担を破ると以下が起きる：
- **解釈に数理の基準（N数・検定）を当てる** → Paper 1 の Appendix D が無効化される種類の誤り。マーケのペルソナ事例に「N=1で検定不能」と批判するのと同じカテゴリ違反。
- **数理に解釈を混ぜる** → Paper 1 で domain ラベルを cos計算に混ぜていた状態。冗長と二重計上を生む。

---

## 2. LOD の階層構造

3D グラフィックスの Level of Detail と同型の構造を持つ。カメラ距離（用途）が LOD を決め、LOD がスコープを決める。

### 2.1 各LODの定義

| LOD | 名称 | 内容 | 数理:解釈 | 担当 |
|-----|------|------|-----------|------|
| 0 | ExposureStructure | 曝露プロファイル（3軸指紋・主要事象・干渉・REFRAME発火） | 100:0 | Python（既存エンジン） |
| 1 | ResponseOrientation | 応答方向（Fight / Flight 等の二値分岐） | 50:50 | LLM |
| 2 | StrategyBranch | 戦略分岐（技術で攻める / 人脈で攻める / 大企業で守る / 公務員で守る 等） | 25:75 | LLM |
| 3 | PersonalContext | 個人文脈（具体的な職種、家族、地域、資産、学歴、関係資本） | 5:95 | LLM |

### 2.2 refine と project

LOD 間の遷移は2つの操作で記述される：

```
refine: LOD_n → LOD_{n+1}    （解釈を追加 = 情報を足す = 分岐）
project: LOD_{n+1} → LOD_n   （解釈を要約 = 情報を落とす = 射影）
```

定義式：
```
LOD₀ = ExposureStructure
LOD₁ = refine(LOD₀, response_orientation)
LOD₂ = refine(LOD₁, strategy_branch)
LOD₃ = refine(LOD₂, personal_context)
```

### 2.3 用途とLODの対応

- **社会学**（集団を見たい） → LOD 0で十分。3軸指紋・干渉・REFRAME発火。
- **マーケティング**（セグメントに使いたい） → LOD 1〜2。Fight/Flight × 戦略分岐。
  - これが Paper 1 Appendix D の正体。
- **カウンセリング・自己認識ツール**（個人まで降りたい） → LOD 3。全ディテール。

「遠いものに高LODを使うのはコストの無駄」という 3D グラフィックスの設計原理がそのまま効く。**用途を超えた LOD は冗長**。

### 2.4 連続性

LOD は離散的なスイッチではなく、3D グラフィックスと同じく **シームレスに切り替わる**。LOD 1.5（Fight/Flight の片方だけ戦略展開する）のような中間状態も許される。SCEM が「世代を連続プロファイルとして扱う」と主張していることと、構造的に同型。

---

## 3. 4戒律（SCEM Axioms）

LOD の操作が満たすべき4つの公理。これは Paper 2 における Situated Cohort Exposure 拡張の **正当性条件** であり、同時に LLM 生成のバリデーション基準となる。

### 3.1 公理の定義

**Axiom 1: Anchor Preservation（固定点保存）**
> 低LODの事象・年齢・mode・weightは保存される。

LOD 0 で確定した数理（「就職氷河期23歳ACTIVE 0.75」）は、いかなる高LOD表現の中でも変更されない。これは「数理は不動の骨格」という役割分担の直接的帰結。

**違反例**: LOD 3 で「この人は就職氷河期の影響を受けていない」と LLM が生成する。LOD 0 の事象集合と矛盾。

**Axiom 2: Non-overwrite（非上書き）**
> 高LODの解釈は、数理結果を書き換えない。

LOD 1〜3 で追加される解釈（Fight 反応、技術で攻める、IT 起業家）は、LOD 0 の数値（PASSIVE 0.81）を変更してはならない。情報を **足す** ことは許される、**書き換える** ことは許されない。

**違反例**: 「Fight 型だから感受性カーブのピークが若年化する」のように、解釈で数理パラメータを変更する。

**Axiom 3: Projection Consistency（射影整合性）**
> 高LODを要約すると、低LODの構造に戻る。

`project(LOD₃ → LOD₀) = LOD₀` が成立しなければならない。生成されたペルソナを集計・要約したとき、元の曝露構造が**復元される**。これは LOD 3 が LOD 0 を **包含している** ことの操作的定義。

**違反例**: LOD 3 で「埼玉出身・大学進学なし」と生成されたが、LOD 0 では「大学進学（19歳, ACTIVE）」が高重みで含まれている。射影が破綻。

**Axiom 4: Provenance Traceability（由来追跡可能性）**
> すべての解釈枝は、どの事象・干渉・REFRAMEから派生したか追跡できる。

LOD 1〜3 の各解釈要素には、「これは LOD 0 のどの要素から導出されたか」という由来情報が付随する。これにより、後から「なぜこの解釈になったか」を辿れる。

**違反例**: 「この人は不安を抱えている」という解釈に、LOD 0 の何の事象が対応するか不明。

### 3.2 公理の2軸整理

| | 静的制約（構造） | 動的制約（過程） |
|---|---|---|
| **refine時（下→上）** | Axiom 2: Non-overwrite | Axiom 4: Provenance |
| **project時（上→下）** | Axiom 1: Anchor Preservation | Axiom 3: Projection Consistency |

上り下りどちらの方向にも2つずつ制約がかかる **対称構造**。これにより、LOD の往復が情報損失なく成立する（refine で足した解釈は project で落ちる、しかし元の LOD 0 は保存される＝レトラクション構造）。

---

## 4. CSP（制約充足問題）としての定式化

LOD によるペルソナ生成は **制約充足問題** として定式化される。これは LLM の出力を構造的に制御するための一般原理である。

### 4.1 CSP要素の対応

```
変数 (Variable)  = 各LODの解釈内容
ドメイン (Domain) = LLMが生成可能な全パターン集合（理論上無限）
制約 (Constraint) = 4戒律 + ユーザー指定の追加制約
```

### 4.2 制約の蓄積

LOD が上がるごとに制約が **増える** ：

```
LOD 0: constraint = {1981年生まれ, 主要事象集合, 3軸指紋}
LOD 1: constraint += {response=Fight}
LOD 2: constraint += {strategy=技術で攻める}
LOD 3: constraint += {profession=IT起業家, region=埼玉, family=独身, ...}
```

LOD が上がるほど解空間が狭まる。LOD 3 では「この人」にかなり絞られる。しかし **どのLODでも、LOD 0 の制約は保存されたまま** ＝ Anchor Preservation。

### 4.3 SAT / UNSAT 検出

CSPソルバーとしての SCEM は、生成されたペルソナを4戒律に対して検証する：

- **SAT**: 全制約を満たす → 有効なペルソナとして出力
- **UNSAT**: 制約間に矛盾 → リジェクト、再生成

UNSAT の検出は単なるエラー処理ではなく、**意味のある診断信号** である：

- **LLMの幻覚検出**: LLM がもっともらしいが LOD 0 と矛盾する生成をしたとき、Projection Consistency 違反として捕捉される。
- **自己認識のズレの可視化**: ユーザーが自己申告する LOD 1〜3 が、客観的な LOD 0 と矛盾するとき、「自分は Flight のつもりだけど構造的には Fight」のようなズレが浮き彫りになる。これはカウンセリング応用において、設計された機能となる。
- **制約の組み合わせ問題の発見**: ユーザーが指定した制約セット自体が矛盾しているとき、それを通知する。

### 4.4 制約による解の質の向上

LLM の問題は「何でも生成できすぎる」ことにある。制約が無いと幻覚・矛盾・もっともらしい嘘が出る。

SCEM LOD は **LOD 0 という数理的アンカー** を提供することで、LLM の自由度を絞り、生成の質を上げる。制約を積めば積むほど、LLM の生成は **観測** に近づく（「次どうする？」ではなく「あ、この人はこう反応するわ」）。

---

## 5. Paper 1 との接続

### 5.1 Paper 1 の射程の再記述

Paper 1 の SCEM は、本ドキュメントの用語で言うと：

- **本文（§3〜§5）**: LOD 0（構造層）の完全な定式化
- **§5.3（Culture層）**: LOD 1 の一部実装（嗜好分岐の仮説生成）
- **Appendix D（Community事例）**: LOD 1〜2 のマーケ応用事例

Paper 1 が「個人層は意図的に射程外」と宣言したのは、**LOD 3 を扱わないと宣言した** ことと同義である。これは「やれない」ではなく「やらない」という設計境界。

### 5.2 Paper 2 へ送る範囲

- LOD 2〜3 の体系的実装
- 4戒律の形式的証明（特に Projection Consistency のレトラクション性）
- Community 層の数値化（閉鎖度離散アーキタイプ × 速度連続オフセット）
- Prolific による実証（LOD 0 → 3 のペルソナ一致率検証）

---

## 6. 実装プロトタイプの仕様

別ファイル `lod_persona.py` として実装する。Paper 1 のエンジンには触らない。

### 6.1 入出力

```python
入力: LODConstraints
  - lod0_exposure: dict (媒体: media_generation_v5.build_exposure_profile)
  - lod1_response: "Fight" | "Flight" | None
  - lod2_strategy: str | None
  - lod3_context: dict | None

出力: dict
  - status: "SAT" | "UNSAT"
  - persona: { summary, narrative, provenance }
  - attempts: int
```

### 6.2 検証フロー

```
1. constraints から LLM プロンプトを構築（4戒律を明示）
2. LLM 呼び出し（OpenAI、culture_axis.py と同じフォールバック方式）
3. 生成されたペルソナを project(LOD 0) で射影
4. 射影結果と元の lod0_exposure を比較
   - 一致 → SAT、返却
   - 不一致 → UNSAT、再試行（max_retries まで）
5. max_retries 超過 → UNSAT として理由付きで返却
```

### 6.3 Projection Consistency の実装方針

`project` の MVP 実装は、生成されたペルソナの `provenance` フィールドから LOD 0 要素を抽出し、それが元の曝露構造の主要事象集合と十分に一致するかを判定する。

- 厳密な一致は要求しない（解釈は自由度がある）
- ただし **核となる事象**（上位重み事象、REFRAME発火ペア、主要干渉ノード）の **大半**が provenance に現れている必要がある
- 一致率の閾値は MVP で 70% 程度から始めて、実験的に調整

### 6.4 何が「実装されない」か（重要）

このプロトタイプは Paper 2 への素材であり、以下は **意図的に MVP 範囲外**:

- 完全な CSP ソルバー（バックトラッキング、制約伝播の最適化）
- LOD 0 ↔ 3 の双方向変換の数学的厳密性
- 大規模なペルソナデータベース化
- WebUI / API化

これらは MVP の動作確認後に必要に応じて拡張する。今は **「LOD 制約を積み上げてペルソナ生成 → Projection Consistency で検証」のループが動くこと**が目標。

---

## Appendix: 用語対応表

| 本ドキュメントの用語 | 等価な表現 |
|---|---|
| LOD 0 | exposure profile / 3軸指紋 / 曝露構造 / 数理アンカー |
| LOD 1〜3 | refine された解釈レイヤー / ペルソナ表現 |
| refine | 解釈分岐 / 制約追加 |
| project | 解釈射影 / 制約除去 / 要約 |
| 4戒律 | SCEM Axioms / Honest Structuralism 戒律 |
| Projection Consistency | ホログラフィック原理（AdS/CFT類比） |
| SAT/UNSAT | 制約充足/不充足 |

---

## References（内部）

- `paper1_media_generation.md` — Paper 1 本文
- `media_generation_v4.py` / `v5.py` — LOD 0 計算エンジン
- `events_patched.jsonl` — 156件社会事象データベース
- `culture_axis.py` / `generate_picks.py` — LOD 1 既存実装（文化層）
- `community_experiment.py` — LOD 1〜2 の Community 事例実験
- Hindsight memory bank — 2026-06-24/25 セッション知見
