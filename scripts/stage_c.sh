#!/bin/bash
# Stage C of the study: the 600-second budget.
#
# Resumable by design. The container this runs in can be recycled at any time,
# so the script consults the results file and runs only the (instance, solver)
# pairs that are not already in it. Re-running it after a restart therefore
# costs nothing and loses nothing.
set -u
cd "$(dirname "$0")/.."
export MIS_BASELINE_DIR=${MIS_BASELINE_DIR:-/tmp/claude-0/-home-user-max-independence-set/ab0fd628-37f5-5a8a-bda6-c8eaa0ba89dd/scratchpad}
OUT=results/cor_long600.csv
INSTANCES="del20 roadNet-CA web-BerkStan frb59-26-1"
SOLVERS="cascade redumis numvc fastvc"

for i in $INSTANCES; do
  for s in $SOLVERS; do
    if [ -f "$OUT" ] && cut -d, -f1,5 "$OUT" | grep -qx "$i,$s"; then
      echo "skip $i/$s (already recorded)"
      continue
    fi
    echo "=== run $i/$s ==="
    python3 scripts/run_bench.py --solvers "$s" --time-limit 600 \
            --instances "$i" --out "$OUT"
  done
done
echo "STAGE_C_DONE"
