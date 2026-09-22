#!/bin/bash
# Full computational study for the Computers & Operations Research submission.
# Run on an idle machine: every number is a wall-clock measurement.
set -u
cd "$(dirname "$0")/.."
export MIS_BASELINE_DIR=${MIS_BASELINE_DIR:-/tmp/claude-0/-home-user-max-independence-set/ab0fd628-37f5-5a8a-bda6-c8eaa0ba89dd/scratchpad}
OUT=results
mkdir -p "$OUT"

ALL=cascade,redumis,online_mis,numvc,fastvc,nearlinear,lineartime
STOCH=cascade,redumis,online_mis,numvc,fastvc
SUBSET=del16,del18,del20,rgg18,roadNet-PA,web-Stanford,web-BerkStan,frb40-19-1,frb53-24-1,frb59-26-1

echo "=== STAGE A: all solvers, all instances, 60s ==="
python3 scripts/run_bench.py --solvers "$ALL" --time-limit 60 --out "$OUT/cor_main60.csv"
echo "STAGE_A_DONE"

echo "=== STAGE B: 5 seeds on a subset, 60s (for the statistical test) ==="
python3 scripts/run_bench.py --solvers "$STOCH" --time-limit 60 --seeds 1,2,3,4,5 \
  --instances "$SUBSET" --out "$OUT/cor_seeds60.csv"
echo "STAGE_B_DONE"

echo "=== STAGE C: long budget, 600s ==="
python3 scripts/run_bench.py --solvers cascade,redumis,numvc,fastvc --time-limit 600 \
  --instances del20,roadNet-CA,web-BerkStan,frb59-26-1 --out "$OUT/cor_long600.csv"
echo "STAGE_C_DONE"
echo "ALL_DONE"
