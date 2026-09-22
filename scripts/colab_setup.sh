#!/bin/bash
# Provisions a Colab VM to reproduce the computational study: builds every
# solver from source, prepares the instances, and leaves the tree ready for
# scripts/run_bench.py.
#
# Usage:  bash colab_setup.sh   (writes progress to /content/setup.log)
set -eu
export DEBIAN_FRONTEND=noninteractive
ROOT=/content/mis
BASE=$ROOT/baselines
mkdir -p "$BASE"
cd "$ROOT" 2>/dev/null || { mkdir -p "$ROOT"; cd "$ROOT"; }

echo "== system packages =="
apt-get update -qq
apt-get install -y -qq --no-install-recommends cmake build-essential libargtable2-dev scons unzip >/dev/null
pip install --quiet scipy numpy highspy 2>/dev/null || true

echo "== our solver =="
if [ ! -d "$ROOT/max_independence_set" ]; then
  git clone --depth 1 https://github.com/vinhqdang/max_independence_set.git "$ROOT/max_independence_set"
fi
cd "$ROOT/max_independence_set"
git pull --ff-only || true
cmake -B build -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build build -j2 >/dev/null
./build/mis-tests | tail -1

echo "== KaMIS (ReduMIS, OnlineMIS) =="
cd "$BASE"
[ -d kamis ] || git clone --depth 1 https://github.com/KarlsruheMIS/KaMIS.git kamis
cd kamis && git submodule update --init --recursive >/dev/null 2>&1
mkdir -p build && cd build && cmake .. >/dev/null && make -j2 redumis online_mis >/dev/null

echo "== reducing-peeling (Chang et al.) =="
cd "$BASE"
[ -d Near-Maximum-Independent-Set ] || git clone --depth 1 https://github.com/LijunChang/Near-Maximum-Independent-Set.git
cd Near-Maximum-Independent-Set && mkdir -p .obj && make >/dev/null 2>&1

echo "== VCSolver (Akiba & Iwata) =="
cd "$BASE"
[ -d vertex_cover ] || git clone --depth 1 https://github.com/wata-orz/vertex_cover.git
cd vertex_cover && bash build.sh >/dev/null 2>&1 || true

echo "== PACE 2019 winner =="
cd "$BASE"
[ -d pace-2019 ] || git clone --depth 1 https://github.com/KarlsruheMIS/pace-2019.git
cd pace-2019
# The build files are Python 2; convert the print statements.
sed -i -E "s/^(\s*)print ('[^']*'[^#]*)$/\1print(\2)/" SConstruct SConscript
scons program=vc_solver variant=optimized -j2 >/dev/null 2>&1 || true

echo "== NuMVC and FastVC (LibMVC, carrying Cai's implementations) =="
cd "$BASE"
[ -d libmvc ] || git clone --depth 1 https://github.com/fmoessbauer/LibMVC.git libmvc
cd libmvc
for s in NuMVC FastVC; do
  g++ -O3 -std=c++14 -ILibMVC -DSOLVER=$s -o "$(echo $s | tr 'A-Z' 'a-z')" standalone/main.cpp
done

echo "== instances =="
mkdir -p /content/data/raw
cd /content/data/raw
for u in web-Stanford web-BerkStan as-skitter ca-AstroPh ca-CondMat email-Enron roadNet-CA roadNet-PA wiki-Talk; do
  [ -f "$u.txt.gz" ] || curl -sS -O --retry 3 "https://snap.stanford.edu/data/$u.txt.gz" || true
done
for u in com-amazon com-dblp com-youtube; do
  [ -f "$u.ungraph.txt.gz" ] || curl -sS -O --retry 3 \
    "https://snap.stanford.edu/data/bigdata/communities/$u.ungraph.txt.gz" || true
done
mkdir -p /content/data/bhoslib && cd /content/data/bhoslib
for i in frb30-15-1 frb35-17-1 frb40-19-1 frb45-21-1 frb50-23-1 frb53-24-1 frb59-26-1; do
  [ -d "$i" ] || { curl -sS -o $i.zip "https://nrvis.com/download/data/bhoslib/$i.zip" && unzip -oq $i.zip -d $i; } || true
done
cd "$ROOT/max_independence_set"
python3 tools/gen_instances.py --out /content/data/geometric --scales 16,18,20
python3 scripts/prepare_instances.py --raw /content/data/raw --geometric /content/data/geometric \
        --bhoslib /content/data/bhoslib --out /content/data/instances

echo "SETUP_COMPLETE"
