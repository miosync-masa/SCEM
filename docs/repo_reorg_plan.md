# Repository 整理 計画書(src/ 層化 → Paper2 §8.1 対応)

**版:** 1.0(2026-06-27)/ **親:** spec 0.3 §9-1 / Paper2 §8.1(Core / CMR / Exposure Adapters)
**握り(2026-06-27):** **深いサブパッケージ(§8.1準拠)** / **data/ は今回触らない**(別タスク)。
**目的:** src/ の34フラットファイルを、論文 §8.1 の層構成に物理対応させる。再現性(SI/reproduce_all)を1ミリも壊さない。
**状態:** 計画確定・**未実行**。本書どおり実行すれば文脈死んでも完遂できる精度で記述。

---

## 1. 目標ツリー(全ファイルの移動先)

```
src/
  _paths.py                  # 【新規】ROOT/DATA/FIGURES 一元化 + sys.path bootstrap
  core/                      # = §8.1 SCEM Core(Paper 1 構造層)
    __init__.py
    media_generation_v4.py   media_generation_v5.py   event_loader.py
    make_figures.py          build_html.py            test_domainless.py   test_lag.py
  culture/                   # Paper 1 Culture/Community 層
    __init__.py
    culture_axis.py   generate_picks.py   compare_picks.py   culture_interactive.py
    community_experiment.py   lod2_cluster.py
  cmr/                       # = §8.1 CMR Layer(Paper 2)
    __init__.py
    merge_paper2_data.py   cmr_matrix.py   cmr_compare.py
    generate_claude_observer.py   recover_gemini_jsonl.py   lod_persona.py   make_paper2_figures.py
  adapters/                  # = §8.1 Exposure Adapters
    __init__.py
    gss/  __init__.py  gss_acquire.py gss_segments.py gss_core_contrast.py gss_interaction.py gss_valuepack.py gss_overlay.py
    ess/  __init__.py  ess_acquire.py ess_segments.py ess_core_validation.py ess_valuepack.py ess_southern_country.py ess_effective_year.py ess_overlay.py
  tools/                     # 補助ツール
    __init__.py
    build_paper_html.py
```

依存の向き(下向きのみ・健全):**cmr → core** / **adapters → data(コード import なし)** / adapters 内は同パッケージ intra-import。

---

## 2. 配線を通す機構(壊さないための設計)

### 2.1 `src/_paths.py`(新規・パス一元化)
```python
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent   # _paths.py は src/ 直下 → parent.parent = repo root
DATA = ROOT / "data"
FIGURES = ROOT / "figures"
```
→ 全スクリプトの `DATA = Path(__file__).resolve().parent.parent / "data"`(ネスト深度依存で壊れる)を
   `from _paths import DATA, ROOT, FIGURES` に置換。**深度非依存**になる。

### 2.2 各スクリプト冒頭の bootstrap(深度非依存・スクリプト実行対応)
```python
import sys, pathlib
sys.path.insert(0, str(next(p for p in pathlib.Path(__file__).resolve().parents if p.name == "src")))
from _paths import DATA, ROOT, FIGURES          # パス
from core import media_generation_v4 as v4      # 絶対 import(例)
```
- **絶対 import に統一**(`from core import …` / `from cmr import cmr_matrix` / `from adapters.ess import ess_segments` /
  `from adapters.ess.ess_core_validation import wls_slope, changepoint, wmean_ci`)。
- 相対 import(`from . import`)は**使わない**(`python3 src/.../x.py` のスクリプト実行で __main__ になり壊れるため)。
- 名前空間パッケージ(Python3)で `__init__.py` 無くても動くが、**明示のため空 `__init__.py` を置く**。

### 2.3 実行規約(現行の `python3 <path>` を維持)
- `python3 src/adapters/gss/gss_core_contrast.py` のように**ファイルパス実行を維持**(bootstrap が src を path に載せる)。
- `python -m` 方式は採らない(SI/reproduce_all の文字列変更を最小化)。

---

## 3. import 改修マップ(誰が誰を呼ぶか)

| ファイル | 現 import | 改修後(絶対) |
|---|---|---|
| cmr/cmr_compare | media_generation_v4/v5, cmr_matrix | `from core import media_generation_v4 as v4, media_generation_v5 as v5` / `from cmr import cmr_matrix as CM` |
| cmr/make_paper2_figures | cmr_matrix | `from cmr import cmr_matrix as CM` |
| cmr/lod_persona | media_generation_v4/v5 | `from core import media_generation_v4 as v4, media_generation_v5 as v5` |
| cmr/cmr_matrix, merge_paper2_data, generate_claude_observer, recover_gemini_jsonl | (なし/data のみ) | DATA を `_paths` から |
| adapters/gss/gss_core_contrast,interaction,valuepack,overlay | gss_segments(+ gss_interaction を valuepack が) | `from adapters.gss import gss_segments as G` / `from adapters.gss.gss_interaction import …` |
| adapters/ess/ess_core_validation | ess_segments | `from adapters.ess import ess_segments as S` |
| adapters/ess/ess_valuepack, ess_southern_country, ess_effective_year, ess_overlay | ess_segments, ess_core_validation(, ess_valuepack) | `from adapters.ess import ess_segments as S` / `from adapters.ess.ess_core_validation import …` / `from adapters.ess.ess_valuepack import …` |
| culture/lod2_cluster, community_experiment | (sys.path 自挿入 + media_generation 等) | bootstrap + 絶対 import |

> 補足:lod_persona の `arch -arm64 python3.12`(OpenAI)実行は不変。Paper 1 の v4/v5・events_patched.jsonl は**無改変**(import のみ)。

---

## 4. SI / ドキュメントの追従更新(再現性を守る)

- **`SI/README.md` 三対応表**:`src/gss_core_contrast.py` → `src/adapters/gss/gss_core_contrast.py` 等、全コマンドのパスを新ツリーへ。
- **`SI/reproduce_all.sh`**:`src/X.py` → 新パス(`src/adapters/gss/...`, `src/cmr/...`, `src/adapters/ess/...`)。
- **`README.md` リポジトリ構成**:src/ ツリーを §1 の層化に差し替え。
- **`docs/exposure_adapters_spec.md`**:Adapter 実装が src/adapters/ に対応した旨を1行。

---

## 5. 検証プロトコル(マージ前ゲート・必須)

1. **ブランチで作業**(`reorg/src-layering`)。worktree でも可。
2. 移動 + 改修後、**再現関連スクリプトを実行**(GSS は slim 既存で可、ESS は ESS_USER_ID あれば):
   `merge → cmr_matrix/compare → gss_core_contrast/interaction/valuepack/overlay → make_paper2_figures`、
   ESS は `ess_core_validation/valuepack/southern_country/effective_year/overlay`。
3. **`git status data/*_results figures` が空(差分ゼロ)= バイト一致**を確認 → 再現性保持の証明。差分が出たら改修ミス。
4. `python3 -c "import"` 相当で各スクリプトの import 解決を確認(構文/パス)。
5. **User ID 非混入**(`grep -rn <id> src SI docs`)・生データ ignore を再確認。
6. 全緑なら main へ。

---

## 6. 実行順(チェックリスト)

```
[ ] 1. ブランチ作成
[ ] 2. src/_paths.py 作成 / 各パッケージに空 __init__.py
[ ] 3. git mv で 34ファイルを目標ツリーへ(履歴保持)
[ ] 4. 各スクリプト改修: bootstrap 追加 / DATA→_paths / import を絶対化(§3表)
[ ] 5. SI/README.md・SI/reproduce_all.sh・README.md・exposure_adapters_spec.md のパス更新(§4)
[ ] 6. 検証プロトコル(§5): 再実行 → data/*_results・figures バイト一致 / import 解決 / UID非混入
[ ] 7. commit & push
```

---

## 7. 非対象(今回やらない・明示)

- **data/ の37ベタ置きファイル整理**(別タスク。スクリプトのファイル名直書きを触ると別の再検証が必要)。
- docs/ の再編(現状で許容範囲)。
- Repository 全体の Zenodo アーカイブ化(SI 確定後)。

> リスク管理:本作業は import/path を広範に触るが、**§5 検証(data/*_results バイト一致)が安全網**。
> 差分ゼロ = 「構造を変えたが結果は不変」を機械的に証明できる。2セッション前の src/ 集約と同種・同安全度。
