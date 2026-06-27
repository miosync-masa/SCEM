#!/usr/bin/env bash
# reproduce_all.sh — SCEM Paper 2 §5.5 外部照合(GSS+ESS)の完全再現。
#
# 取得 → slim → 分析 → 図表 を一括実行。コードは正本 src/ を呼ぶ(SI で複製しない)。
# 生データは NORC(GSS)/ Sikt(ESS)から DOI 経由で取得・再配布しない(.gitignore)。
#
# 前提:
#   - Python 3.12 / numpy pandas pyarrow matplotlib(requirements.txt)。scipy/statsmodels 不要。
#   - GSS: ネット接続(NORC から ~45MB zip を DL)。
#   - ESS: 環境変数 ESS_USER_ID(https://ess.sikt.no/en/api で取得。認証でなく利用統計用)。
#          未設定なら ESS をスキップ(GSS は実行)。
#   - CMR グリッド入力(data/*_grid.jsonl, Claude/Gemini observer)はリポジトリに committed。
#
# 使い方:
#   export ESS_USER_ID="<your-ESS-user-id>"   # ESS を回すなら
#   bash SI/reproduce_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."          # repo root
echo "== repo root: $(pwd) =="
PY=python3

run() { echo; echo ">>> $*"; "$@"; }

echo "######################## GSS (US) ########################"
echo "NORC GSS data: by running gss_acquire you agree to NORC/GSS terms of use."
run $PY src/gss_acquire.py                                   # → data/gss/gss_slim.parquet (.gitignore)
run $PY src/merge_paper2_data.py --country us --variant grid # → interpretations_us_grid.jsonl 等
run $PY src/merge_paper2_data.py --country uk --variant grid
run $PY src/cmr_matrix.py  --country us --variant grid
run $PY src/cmr_matrix.py  --country uk --variant grid
run $PY src/cmr_compare.py --country us --variant grid
run $PY src/cmr_compare.py --country uk --variant grid
run $PY src/gss_core_contrast.py     # SSM コア対比 (Coastal 91% / Bible Belt 6→66%)
run $PY src/gss_interaction.py       # b′ 交互作用 (p=0.157, period頑健)
run $PY src/gss_valuepack.py         # 徳用パックの割れ + 変化点>線形 (移民×Coastal +41.5)
run $PY src/gss_overlay.py           # overlay 10/12, ACTIVE→transition 8/8, 銃=装置ミスマッチ
run $PY src/make_paper2_figures.py   # Paper2 §5 CMR 図 (fig_p2_*)

if [ "${ESS_USER_ID:-}" = "" ]; then
  echo
  echo "######################## ESS スキップ ########################"
  echo "ESS_USER_ID 未設定 → ESS をスキップ。回すには:"
  echo "  export ESS_USER_ID=<your-ESS-user-id>  (https://ess.sikt.no/en/api)"
  echo "  bash SI/reproduce_all.sh"
else
  echo
  echo "######################## ESS (UK/Europe) ########################"
  echo "ESS data: by running ess_acquire you agree to ESS/Sikt terms of use."
  run $PY src/ess_acquire.py            # ESS7-11 API parquet → ess_slim.parquet (.gitignore)
  run $PY src/ess_core_validation.py    # 水準ゲート (Secular 90% / Religious 66%, US並置)
  run $PY src/ess_valuepack.py          # clusters + euftf + 移民 (EVENT_STRUCTURE)
  run $PY src/ess_southern_country.py   # Southern 5国 b′ 正勾配一貫
  run $PY src/ess_effective_year.py     # effective_year→移行段階 (ρ 0.54/0.67)
  run $PY src/ess_overlay.py            # overlay UK (euftf↔Brexit 3/3)
fi

echo
echo "== 完了。出力: data/{gss,ess}_results/*.csv|json / figures/*.png =="
echo "== 各数字の対応は SI/README.md §1 三対応マッピング表を参照 =="
echo "== 強度: 予測対応・suggestive・modest(確証と書かない)。検証の問いは SI/README.md §0 =="
