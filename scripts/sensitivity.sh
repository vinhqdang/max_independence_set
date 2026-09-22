#!/bin/bash
# Parameter sensitivity: vary one tunable at a time around its default.
#
# The method has six tunables, and a reviewer is entitled to ask whether the
# reported numbers sit on a plateau or on a knife edge. This varies each
# exposed parameter one at a time, holding the rest at their defaults, on three
# instances chosen to span the families where the parameters plausibly matter.
#
# Resumable by design, like the long-budget stage: the container is recycled
# every few tens of minutes, so the script reads the results file and runs only
# the (instance, parameter, value) triples not already recorded. The pending
# list is shuffled so that one slow triple cannot block the rest.
set -u
cd "$(dirname "$0")/.."
OUT=results/sensitivity.csv
BIN=build/cascade
TL=60
INSTANCES="del18 web-Stanford frb40-19-1"

# name:flag:default:values
GRID="
kernel_share:--kernel-share:0.3:0.1 0.2 0.3 0.5 0.7
lns_start_free:--lns-free:4:1 2 4 8 16
restart_idle_dives:--restart-idle:200:50 100 200 400 800
lns_slice:--lns-slice:0.05:0.01 0.02 0.05 0.1 0.2
"

if [ ! -f "$OUT" ]; then
  echo "instance,parameter,flag,value,is_default,size,seconds" > "$OUT"
fi

pending=()
for i in $INSTANCES; do
  while IFS= read -r spec; do
    [ -z "$spec" ] && continue
    name=${spec%%:*}; rest=${spec#*:}
    flag=${rest%%:*}; rest=${rest#*:}
    def=${rest%%:*}; values=${rest#*:}
    for v in $values; do
      grep -q "^$i,$name,$flag,$v," "$OUT" && continue
      pending+=("$i $name $flag $def $v")
    done
  done <<< "$GRID"
done

echo "pending runs: ${#pending[@]}"
[ "${#pending[@]}" -eq 0 ] && { echo "SENSITIVITY_DONE"; exit 0; }

while IFS= read -r row; do
  set -- $row
  i=$1; name=$2; flag=$3; def=$4; v=$5
  grep -q "^$i,$name,$flag,$v," "$OUT" && continue
  p=/home/user/data/instances/$i.txt
  [ -f "$p" ] || continue
  echo "=== $i $name=$v (default $def) ==="
  out=$(timeout $((TL + 240)) "$BIN" "$p" --time-limit $TL --seed 1 "$flag" "$v" 2>/dev/null)
  size=$(echo "$out" | grep -o 'size=[0-9]*' | head -1 | cut -d= -f2)
  secs=$(echo "$out" | grep -o 'time=[0-9.]*' | head -1 | cut -d= -f2)
  isdef=0; [ "$v" = "$def" ] && isdef=1
  if [ -n "$size" ]; then
    echo "$i,$name,$flag,$v,$isdef,$size,$secs" >> "$OUT"
    echo "    size=$size time=$secs"
  else
    echo "    NO RESULT (timeout or crash)"
  fi
done < <(printf '%s\n' "${pending[@]}" | shuf)

echo "SENSITIVITY_DONE"
