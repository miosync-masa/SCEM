# Situated Cohort Exposure Model — Architecture v6 (FIXED)

**Status: FIXED (2026-06-24).** これは正典(single source of truth)。以降のコード・論文はこの仕様に従う。仕様変更はバージョンを上げる(v7)こと。

**対象:** 集団の曝露構造(collective exposure structure)。**個人の内面・個人ラグは対象外**(下記スコープ外)。

略称: **SCEM**。Paper 1 の和名「年齢同期型メディア世代論」は、本モデル(SCEM)の世代論的提示である。

---

## 層構成

### 1. 構造層 — 事象 × 着弾年齢 × 作用モード  〔実装済: `media_generation_v4.py` / `v5.py` / `event_loader.py`〕

- **3作用モード** PASSIVE / ACTIVE / REFRAME。生の合計で同列にせず、**3軸**として別々に保持する(`mode_density`, `report_3axis`)。
  - PASSIVE: 受動着弾(刷り込み)。$w = s\cdot\lambda$
  - ACTIVE: 能動分岐(意思決定強制)。$w = s\cdot(0.30+0.70\alpha)\cdot\lambda$
  - REFRAME: 参照点書き換え(差分発火)。$w = s\cdot(0.50+0.50\alpha)\cdot\lambda$
- **感受性カーブ** 非対称ガウス、**個別 peak 優先ハイブリッド**(個別 `sensitivity_peak_age` があれば使用、無ければ領域×モードのフォールバック33本)。
  $g(a)=\max(\phi,\ \exp[-(a-\mu)^2/2\sigma(a)^2])$、$\sigma=\sigma_L\,(a\le\mu)\ /\ \sigma_R\,(a>\mu)$。
- **REFRAME 発火** 同一 `reframe_group` 内のアンカー→トリガーで、`reference_value` の**対数比**で差分発火。
  $\delta=\min(1,\ \log(\max/\min)/\log 2)$、$\text{fire}=w_a(0.35+0.65\,w_t)\,\delta$。
- **干渉** 同一認知バンドへの同時着弾のみ。**作用直交性** $D=1.6-1.05\min(\cos,1)$ で増幅(cos=0→1.6 / cos=1→0.55)。
  $\text{score}=\frac{w_a+w_b}{2}\cdot D\cdot(0.5+0.5\,p)$、$p=1-\min(\delta a/W,1)$。
- **被り判定** `effect_vector` の**コサインのみ**で4段階(duplicate/sibling/interference/independent)。**domain は計算に非関与**。
- **イベントは単一カテゴリに潰さない**=連続作用ベクトル $\mathbf{v}_e$。**domain は人間用の表示タグ**にすぎず、いかなる計算にも入らない(中心的主張「離散バケツを拒む」のイベント側への自己適用)。

### 2. Community層 — Situated(環境)の変調  〔プロトタイプ: `community_experiment.py`〕

- **閉鎖度** = **離散アーキタイプ**(開放 / 中間 / 閉鎖)。**塊(クラスタ)を作る**。Code を内包する(選択肢空間の生成ロジックを持つ)。
  - 実測根拠: 閉鎖度固定(速度可変)のペルソナ平均cos=0.90 > 速度固定(閉鎖度可変)=0.86。閉鎖型は速度に依らず一点へ収束(内部cos=0.93)。→ 離散タイプとして扱うのが妥当。
- **伝播速度** = **連続 offset**。`effective_year` を地域で変調(速0 / 中+1 / 遅+2年 等)。**塊を作らない**(同一閉鎖度内をなめらかにずらすだけ)。
  - 実装は既存エンジンのまま(`effective_year` を伝播型事象=diffusion/media/infrastructure/lifestyle系にだけ加算)。
- **閉鎖度が個人の具現化遅延を生む**(が、**個人ラグ自体は測らない** — 集団の曝露構造として扱う)。

### 3. Culture層 — 嗜好分岐(仮説生成器、マーケ応用)  〔実装済: `culture_axis.py` / `generate_picks.py` / `compare_picks.py`〕

- **4軸 pickリスト**(音楽 / スポーツ / 文学 / 映画)を世代別に **LLM 生成**。
- 構造プロファイル + 嗜好で**文化サブクラスタ**を生成。
- 位置づけは**仮説生成器**(hypothesis generator)。実在分布の測定ではない(実証は Paper 2)。

### 4. グラウンディング — プロンプト調整(アーキテクチャ非依存)

- **LLM 側の地域特性解像度を磨く** ← **唯一の残調整**。アーキテクチャは変えない、プロンプト品質の問題。

---

## スコープ外(意図的境界)

これらは**やらない**と決めた境界。「対象=集団の曝露構造」を保つために除外する。

- **個人層**(self-efficacy、個人の能力・意志)
- **個人の情報-具現化ラグ**(`test_lag.py` で味見 → 集団普及ラグは仮説と逆向き(現代ほど小)かつ右側打ち切り汚染。個人の「知る vs なる」ギャップは本プロキシでは測れないため境界外とする)
- **地域間具現化波及の動的モデル**(=キャズム / トゥーマッチ。普及の地域間ダイナミクスは扱わない)

---

## 実装ステータス早見

| 層 | 状態 | ファイル |
|---|---|---|
| 構造層 | **実装済・純化済**(domain非依存・D項統合) | `media_generation_v4.py`, `v5.py`, `event_loader.py` |
| Community層 | プロトタイプ(判断材料実験) | `community_experiment.py` |
| Culture層 | 実装済 | `culture_axis.py`, `generate_picks.py`, `compare_picks.py` |
| グラウンディング | プロンプトレベル | (各 SYSTEM プロンプト) |

**FIX スタンプ(2026-06-24, 1981年生まれ):** 指紋 PASSIVE 0.81 / ACTIVE 0.56 / REFRAME 0.55。干渉トップ = Windows95発売 × プリクラ普及 (score 1.60)。被り判定 domain非依存=True、干渉 D項統合=True。

---

## 検証アーティファクト(再現性)

- `test_domainless.py` — domain冗長性の実測(指紋・バッチ不変、干渉9/10一致 → domain廃止を正当化)
- `community_experiment.py` + `_cache.json` — 閉鎖度=離散 / 速度=連続 の非対称を実測
- `test_lag.py` — 情報-具現化ラグ味見(個人ラグをスコープ外とする根拠)
- `make_figures.py` — Fig2(3軸密度推移)/ Fig3(文化選択肢断絶)
