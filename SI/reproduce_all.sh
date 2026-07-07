#!/usr/bin/env bash
# reproduce_all.sh — complete reproduction of SCEM Paper 2 §5.5 external cross-check (GSS+ESS).
#
# Runs acquire → slim → analyze → figures in one shot. Code calls the canonical src/ (not duplicated in SI).
# Raw data is acquired via DOI from NORC (GSS) / Sikt (ESS) and is not redistributed (.gitignore).
#
# Requirements:
#   - Python 3.12 / numpy pandas pyarrow matplotlib (requirements.txt). No scipy/statsmodels.
#   - GSS: network connection (downloads a ~45MB zip from NORC).
#   - ESS: env var ESS_USER_ID (obtain at https://ess.sikt.no/en/api; for usage statistics, not authentication).
#          If unset, ESS is skipped (GSS still runs).
#   - The CMR grid inputs (data/*_grid.jsonl, Claude/Gemini observers) are committed to the repo.
#
# Usage:
#   export ESS_USER_ID="<your-ESS-user-id>"   # if you want to run ESS
#   bash SI/reproduce_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."          # repo root
echo "== repo root: $(pwd) =="
PY=python3

run() { echo; echo ">>> $*"; "$@"; }

echo "######################## GSS (US) ########################"
echo "NORC GSS data: by running gss_acquire you agree to NORC/GSS terms of use."
run $PY src/adapters/gss/gss_acquire.py                                   # → data/gss/gss_slim.parquet (.gitignore)
run $PY src/cmr/merge_paper2_data.py --country us --variant grid # → interpretations_us_grid.jsonl etc.
run $PY src/cmr/merge_paper2_data.py --country uk --variant grid
run $PY src/cmr/cmr_matrix.py  --country us --variant grid
run $PY src/cmr/cmr_matrix.py  --country uk --variant grid
run $PY src/cmr/cmr_compare.py --country us --variant grid
run $PY src/cmr/cmr_compare.py --country uk --variant grid
run $PY src/adapters/gss/gss_core_contrast.py     # SSM core contrast (Coastal 91% / Bible Belt 6→66%)
run $PY src/adapters/gss/gss_interaction.py       # b′ interaction (p=0.157, period-robust)
run $PY src/adapters/gss/gss_valuepack.py         # value-pack divergence + changepoint > linear (immigration×Coastal +41.5)
run $PY src/adapters/gss/gss_overlay.py           # overlay 10/12, ACTIVE→transition 8/8, guns = instrument mismatch
run $PY figures/generate_figures.py fig1 fig2 fig3 fig6   # submission figures: mode matrices, fingerprints, GSS SSM trajectories, schematic (Fig 4-5 need ESS, generated below)

if [ "${ESS_USER_ID:-}" = "" ]; then
  echo
  echo "######################## ESS skipped ########################"
  echo "ESS_USER_ID unset → skipping ESS. To run it:"
  echo "  export ESS_USER_ID=<your-ESS-user-id>  (https://ess.sikt.no/en/api)"
  echo "  bash SI/reproduce_all.sh"
else
  echo
  echo "######################## ESS (UK/Europe) ########################"
  echo "ESS data: by running ess_acquire you agree to ESS/Sikt terms of use."
  run $PY src/adapters/ess/ess_acquire.py            # ESS7-11 API parquet → ess_slim.parquet (.gitignore)
  run $PY src/adapters/ess/ess_core_validation.py    # level gate (Secular 90% / Religious 66%, US juxtaposed)
  run $PY src/adapters/ess/ess_valuepack.py          # clusters + euftf + immigration (EVENT_STRUCTURE)
  run $PY src/adapters/ess/ess_southern_country.py   # Southern 5 countries: consistent positive b′ slope
  run $PY src/adapters/ess/ess_effective_year.py     # effective_year → transition stage (ρ 0.54/0.67)
  run $PY src/adapters/ess/ess_overlay.py            # overlay UK (euftf↔Brexit 3/3)
  run $PY figures/generate_figures.py fig4 fig5      # submission figures: ESS cluster decomposition + institution-year vs changepoint
fi

echo
echo "== Done. Outputs: data/{gss,ess}_results/*.csv|json / figures/*.png =="
echo "== For the mapping of each number, see SI/README.md §1 (three-way mapping table) =="
echo "== Strength: prediction-consistent, suggestive, modest (never 'confirmation'). The validation question is in SI/README.md §0 =="
