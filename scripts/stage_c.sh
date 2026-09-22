#!/bin/bash
# Stage C of the study: the 600-second budget.
#
# Resumable by design. The container this runs in is recycled every ten to
# thirty minutes, so the script consults the results file and runs only the
# (instance, solver) pairs that are not already in it. Re-running it after a
# restart therefore costs nothing and repeats nothing.
#
# The pending pairs are attempted in a RANDOM order. A fixed order meant every
# restart retried the same pair, so one run that happened not to fit inside a
# container's lifetime blocked all the others behind it indefinitely --
# roadNet-CA/fastvc was attempted four times in a row with nothing else tried.
# Shuffling means each container cycle attempts a different pair, and the ones
# that fit get recorded instead of everything waiting on the one that does not.
set -u
cd "$(dirname "$0")/.."
export MIS_BASELINE_DIR=${MIS_BASELINE_DIR:-/tmp/claude-0/-home-user-max-independence-set/ab0fd628-37f5-5a8a-bda6-c8eaa0ba89dd/scratchpad}
OUT=results/cor_long600.csv
INSTANCES="del20 roadNet-CA web-BerkStan frb59-26-1"
SOLVERS="cascade redumis numvc fastvc"

pending=()
for i in $INSTANCES; do
  for s in $SOLVERS; do
    if [ -f "$OUT" ] && cut -d, -f1,5 "$OUT" | grep -qx "$i,$s"; then
      continue
    fi
    pending+=("$i $s")
  done
done

echo "pending pairs: ${#pending[@]}"
if [ "${#pending[@]}" -eq 0 ]; then
  echo "STAGE_C_DONE"
  exit 0
fi

while IFS= read -r pair; do
  set -- $pair
  i=$1; s=$2
  # Re-check: another cycle may have recorded it since the list was built.
  if cut -d, -f1,5 "$OUT" 2>/dev/null | grep -qx "$i,$s"; then
    echo "skip $i/$s (recorded meanwhile)"
    continue
  fi
  echo "=== run $i/$s ==="
  python3 scripts/run_bench.py --solvers "$s" --time-limit 600 \
          --instances "$i" --out "$OUT"
done < <(printf '%s\n' "${pending[@]}" | shuf)

echo "STAGE_C_DONE"
