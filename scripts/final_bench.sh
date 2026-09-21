#!/bin/bash
# Full evaluation. Run on an otherwise idle machine: every number below is a
# wall-clock measurement and concurrent load invalidates it.
set -u
cd "$(dirname "$0")/.."
OUT=${1:-results}
TL=${2:-60}
mkdir -p "$OUT"

echo "== heuristic comparison (${TL}s budget, 3 seeds) =="
python3 scripts/run_bench.py \
  --solvers cascade,redumis,online_mis,nearlinear,lineartime \
  --time-limit "$TL" --seeds 1,2,3 --out "$OUT/heuristic.csv"

echo "== exact solvers (${TL}s budget) on instances they can attempt =="
python3 scripts/run_bench.py \
  --solvers cascade-exact,vcsolver,pace,highs \
  --time-limit "$TL" --max-n 300000 --out "$OUT/exact.csv"

echo "== ablation: which component earns its place =="
python3 scripts/run_bench.py --solvers cascade --time-limit "$TL" \
  --instances del16,del18,rgg16,web-Stanford,roadNet-PA,frb40-19-1,frb59-26-1 \
  --out "$OUT/ablation_full.csv"

python3 scripts/summarize.py "$OUT/heuristic.csv" --markdown > "$OUT/summary.md"
cat "$OUT/summary.md"
