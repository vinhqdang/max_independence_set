# CASCADE — maximum independent set on massive sparse graphs

CASCADE computes large independent sets (equivalently, small vertex covers) on
sparse graphs with millions of vertices, and proves optimality on instances that
are small enough for its exact mode.

The solver is built around one idea: **improvement moves should be solved
exactly, not sampled.**  Freeing a set `F` of vertices from the current solution
makes exactly those vertices addable whose every solution neighbour lies in `F`.
That region cannot interact with anything outside it, so re-solving it optimally
is always safe and never loses ground.  A full reduction suite (degree-0/1,
simplicial, degree-2 folding, twin, domination, unconfined) collapses each region
before branching, which is what makes regions of thousands of vertices solvable
in microseconds — and lets a single move restructure a whole neighbourhood where
a classical (1,2)-swap moves one or two vertices.

The size of `F` tunes itself: it shrinks when a region turns out to be too hard
to solve exactly, and grows when regions of the current size are being solved to
optimality without finding anything.  The same binary therefore settles on
neighbourhoods of tens of vertices on a mesh and one or two on a dense
adversarial instance, with no per-family configuration.

## Build

```sh
cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j
```

Produces `build/cascade` (solver), `build/mis-convert` (format conversion) and
`build/mis-verify` (independent verification of any solver's output).

## Run

```sh
build/cascade graph.txt --time-limit 60 --output solution.txt
build/mis-verify graph.txt solution.txt
```

Input may be an edge list, METIS (`.graph`), Matrix Market (`.mtx`) or DIMACS
(`.clq`).  The solution file holds one `0`/`1` per vertex.

Useful options:

| Option | Meaning |
| --- | --- |
| `--time-limit SEC` | wall-clock budget (default 60) |
| `--seed N` | random seed |
| `--lns-free N` | initial number of incumbent vertices freed per region |
| `--kernel-only` | stop after kernelization and report the kernel |
| `--no-lns`, `--dive-moves` | ablation switches |

## Results

Against the published solvers under a common 60 second budget, on 27 instances
across five families, with every solution independently verified
(`docs/EXPERIMENTS.md` has the full tables and the caveats):

| family | outcome |
| --- | --- |
| Delaunay triangulations | ahead on all three, by +10, +277 and +5535 (1.7% on `del20`) |
| random geometric | level with ReduMIS; `rgg16` and `rgg18` are provably optimal |
| road networks | level |
| social | level on 8 of 10; behind on `as-skitter` by 1 and `soc-pokec` by 342 |
| web | behind by 15 and 100 |
| BHOSLIB `frb` | level on 5 of 7 over three seeds, behind by 1 on the other two |

The margin comes from the neighbourhood move: removing it costs 1022 vertices on
`del18` and 242 on `roadNet-PA`, more than the entire margin over the baselines.

## Evaluation

`scripts/` holds the benchmark pipeline: instance preparation, a runner that
gives every solver the same wall-clock budget and verifies each returned set
independently, and a summariser.  Baselines are built from their authors'
published code (KaMIS ReduMIS and OnlineMIS, the reducing-peeling solver of
Chang et al., Akiba & Iwata's branch-and-reduce, the PACE 2019 winner) plus a
HiGHS integer-programming reference.

```sh
python3 tools/gen_instances.py --out data/geometric --scales 16,18,20
python3 scripts/prepare_instances.py
python3 scripts/run_bench.py --solvers cascade,redumis,online_mis,nearlinear --time-limit 60
python3 scripts/summarize.py results/raw.csv
```

## Layout

```
src/dyngraph.hpp    dynamic graph with last-in-first-out undo
src/reductions.hpp  safe reduction rules and solution lifting
src/exact.hpp       branch-and-reduce; solves regions and small instances
src/cascade.hpp     kernelization, diving, and the neighbourhood search
tools/              format conversion, verification, instance generation
scripts/            benchmark pipeline
```
