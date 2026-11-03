# CASCADE: region-move local search for maximum independent set

CASCADE computes large independent sets (equivalently, small vertex covers) on
sparse graphs with millions of vertices.  After kernelization and a greedy dive it
repeatedly releases a set `F` of incumbent vertices, collects every outside vertex
whose incumbent neighbours all lie in `F`, and re-solves that region with a
branch-and-reduce engine.  Nothing outside the region touches the incumbent inside
it, so a region solution of size at least `|F|` can be written back without any
check against the rest of the graph.

The region construction is the one used by Borowitz, Grossmann and Schulz,
*Optimal Neighborhood Exploration for Dynamic Independent Sets* (ALENEX 2025), for
dynamic graphs.  CASCADE applies it to static graphs, runs reductions inside each
move, and adapts `|F|` online: it halves when a sub-solve is cut off and doubles
after a run of proved, fruitless regions.

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
| `--no-lns`, `--dive-moves`, `--lns-heuristic`, `--lns-no-reduce` | ablation switches (heuristic repair; no reductions inside regions) |

## Results

Under a 60 s budget on 27 instances in five families, against six solvers from
2012-2019 (`paper/`, `results/`):

* strictly ahead of the best of the other six on 3 instances (all Delaunay graphs
  from one generator seed), tied on 13, behind on 11;
* mean relative gap 0.785%, third of seven (FastVC 0.340%, ReduMIS 0.501%);
* Wilcoxon on relative gaps, Holm-corrected: ahead of OnlineMIS, NearLinear and
  LinearTime; no significant difference from ReduMIS, NuMVC or FastVC;
* behind on dense BHOSLIB instances and slightly behind on web graphs.

More recent solvers (for example InfVC, IJCAI 2025) were not run.

## Evaluation

`scripts/` holds the benchmark pipeline: instance preparation, a runner that
gives every solver the same wall-clock budget and verifies each returned set
independently, and a summariser.  Baselines are built from their authors'
published code (KaMIS ReduMIS and OnlineMIS, the reducing-peeling solver of
Chang et al., NuMVC and FastVC, Akiba & Iwata's branch-and-reduce, the PACE 2019
winner) plus a HiGHS integer-programming reference.

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
