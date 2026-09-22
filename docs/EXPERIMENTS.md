# Experimental evaluation

## Setup

All solvers run on the same machine (4 cores, single-threaded runs), get the
same 60 second wall-clock budget, and read the same graphs converted to each
solver's native input format.  Every solution is checked by `mis-verify`, which
re-reads the original graph and confirms the returned set is independent; sizes
that could not be verified this way are not counted.  Wall-clock time is
measured by the harness around the whole process, so reading and kernelization
are included.

Baselines are built from their authors' published code:

| Solver | Reference |
| --- | --- |
| ReduMIS | Lamm, Sanders, Schulz, Strash, Werneck, *J. Heuristics* 23(4), 2017 |
| OnlineMIS | Dahlum, Lamm, Sanders, Schulz, Strash, Werneck, *SEA 2016* |
| NearLinear, LinearTime | Chang, Li, Zhang, *SIGMOD 2017* |
| VCSolver (branch-and-reduce) | Akiba, Iwata, *Theoret. Comput. Sci.* 609, 2016 |
| WeGotYouCovered | Hespe, Lamm, Schulz, Strash, PACE 2019 winner, *CSC 2020* |
| HiGHS | integer programming reference |

ReduMIS is run with `--kernelization=full`.

## Instances

27 instances in five families: Delaunay triangulations and random geometric
graphs (generated, seeded, `tools/gen_instances.py`), road networks, social and
web graphs from SNAP, and BHOSLIB `frb` instances.

One note on the BHOSLIB instances.  They are distributed in *clique* form, and
the copies on Network Repository are the dense clique graphs: `frb30-15-1` there
has 450 vertices and 83,198 edges.  A maximum independent set of that file has
size 15 — the domain size of the underlying Model-RB construction — and every
solver tested returns exactly 15 on it.  The MIS instance is its complement
(450 vertices, 17,827 edges, independence number 30), and that is what is used
here.  Benchmarking the distributed file directly would have every solver agree
on a confidently wrong answer.

## Result: solution quality at 60 seconds

Best value per solver; bold marks the best value on the row.

| instance | family | n | m | **CASCADE** | ReduMIS | OnlineMIS | NearLinear | LinearTime | vs best |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `rgg16` | geometric | 65,501 | 260,438 | **16086** | **16086** | 16082 | 16035 | 15321 | +0 |
| `del16` | geometric | 65,536 | 196,583 | **20650** | 20640 | 20634 | 20284 | 20213 | +10 |
| `rgg18` | geometric | 262,011 | 1,046,301 | **64278** | **64278** | 63939 | 64094 | 61282 | +0 |
| `del18` | geometric | 262,144 | 786,401 | **82662** | 82385 | 82031 | 81211 | 80881 | +277 |
| `rgg20` | geometric | 1,048,171 | 4,188,702 | **256994** | **256994** | 242831 | 256277 | 244769 | +0 |
| `del20` | geometric | 1,048,576 | 3,145,692 | **330154** | 321566 | 311006 | 324619 | 323438 | +5535 |
| `roadNet-PA` | road | 1,088,092 | 1,541,898 | 533627 | **533628** | 516394 | 531184 | 530910 | -1 |
| `roadNet-CA` | road | 1,965,206 | 2,766,607 | 961850 | **961851** | 924579 | 957199 | 956573 | -1 |
| `ca-AstroPh` | social | 18,772 | 198,050 | **6760** | **6760** | **6760** | **6760** | 6759 | +0 |
| `ca-CondMat` | social | 23,133 | 93,439 | **9612** | **9612** | 9601 | **9612** | 9611 | +0 |
| `email-Enron` | social | 36,692 | 183,831 | **22255** | **22255** | 22227 | **22255** | **22255** | +0 |
| `com-dblp` | social | 317,080 | 1,049,866 | **152131** | **152131** | 152061 | **152131** | 152129 | +0 |
| `com-amazon` | social | 334,863 | 925,872 | **174632** | **174632** | 172685 | 174627 | 174612 | +0 |
| `com-youtube` | social | 1,134,890 | 2,987,624 | **857945** | **857945** | 857680 | **857945** | 857944 | +0 |
| `soc-pokec-relationships` | social | 1,632,803 | 22,301,964 | 788819 | -- | 777605 | **789161** | 789003 | -342 |
| `as-skitter` | social | 1,696,415 | 11,095,298 | 1170579 | **1170580** | 1152300 | 1170541 | 1170410 | -1 |
| `wiki-Talk` | social | 2,394,385 | 4,659,565 | **2338222** | **2338222** | 2338207 | **2338222** | **2338222** | +0 |
| `com-lj` | social | 3,997,962 | 34,681,189 | **2085626** | **2085626** | 2066610 | 2085604 | 2085353 | +0 |
| `web-Stanford` | web | 281,903 | 1,992,636 | 163375 | **163390** | 162588 | 163198 | 163121 | -15 |
| `web-BerkStan` | web | 685,230 | 6,649,470 | 408382 | **408482** | 406304 | 408054 | 407716 | -100 |
| `frb30-15-1` | bhoslib | 450 | 17,827 | **30** | **30** | 29 | 24 | 22 | +0 |
| `frb35-17-1` | bhoslib | 595 | 27,856 | 34 | **35** | 33 | 27 | 25 | -1 |
| `frb40-19-1` | bhoslib | 760 | 41,314 | **40** | **40** | 39 | 27 | 29 | +0 |
| `frb45-21-1` | bhoslib | 945 | 59,186 | **43** | **43** | 42 | 33 | 32 | +0 |
| `frb50-23-1` | bhoslib | 1,150 | 80,072 | 48 | **49** | 48 | 35 | 33 | -1 |
| `frb53-24-1` | bhoslib | 1,272 | 94,227 | 50 | **51** | 49 | 38 | 40 | -1 |
| `frb59-26-1` | bhoslib | 1,534 | 126,555 | 56 | **57** | 56 | 43 | 43 | -1 |

CASCADE is ahead on all three Delaunay instances, level on the random geometric
graphs, the road networks and most social graphs, and behind by a small margin
on the web graphs, `soc-pokec` and part of the BHOSLIB family.  The margin on
Delaunay grows with size: +10 on `del16`, +277 on `del18`, +5535 on `del20`
(1.7%).  These are the instances where the literature reports that reductions
stall, and they are exactly where exact neighbourhood moves have the most to
work with.

Several of the single-vertex gaps are run-to-run noise rather than a real
difference, which the seed study below separates out.

## Result: three seeds

Best and mean over seeds 1-3, same 60 second budget.

| instance | family | **CASCADE** best/mean | ReduMIS best/mean | OnlineMIS best/mean |
|---|---|---:|---:|---:|
| `del16` | geometric | 20648 / 20646.0 | 20640 / 20640.0 | 20636 / 20634.7 |
| `rgg18` | geometric | 64278 / 64278.0 | 64278 / 64278.0 | 63956 / 63948.7 |
| `del18` | geometric | 82662 / 82659.3 | 82402 / 82383.0 | 82099 / 82071.3 |
| `roadNet-PA` | road | 533628 / 533627.7 | 533628 / 533627.7 | 516666 / 516542.7 |
| `web-Stanford` | web | 163375 / 163373.3 | 163390 / 163390.0 | 162585 / 162580.3 |
| `frb30-15-1` | bhoslib | 30 / 30.0 | 30 / 30.0 | 29 / 29.0 |
| `frb35-17-1` | bhoslib | 35 / 34.3 | 35 / 34.7 | 33 / 33.0 |
| `frb40-19-1` | bhoslib | 39 / 39.0 | 40 / 40.0 | 39 / 38.7 |
| `frb45-21-1` | bhoslib | 43 / 43.0 | 44 / 43.7 | 43 / 42.3 |
| `frb50-23-1` | bhoslib | 49 / 48.3 | 49 / 48.3 | 48 / 48.0 |
| `frb53-24-1` | bhoslib | 51 / 50.3 | 51 / 51.0 | 51 / 50.0 |
| `frb59-26-1` | bhoslib | 57 / 56.3 | 57 / 57.0 | 56 / 55.7 |

With three seeds `roadNet-PA` and four of the seven BHOSLIB instances come level,
`frb30-15-1` and `frb35-17-1` reach the known optima of 30 and 35, and
`frb53-24-1` and `frb59-26-1` reach 51 and 57, matching ReduMIS.  Two BHOSLIB
instances remain one vertex behind ReduMIS, and `web-Stanford` remains 15
behind.  The mean column also shows CASCADE is the more stable of the two on the
geometric instances: on `del18` its worst seed beats ReduMIS's best.

## Result: exact solving

`--exact` runs the same engine as a branch-and-reduce solver.  Bold marks a
proven optimum with the time to prove it.

| instance | family | n | **CASCADE --exact** | WeGotYouCovered | VCSolver | HiGHS |
|---|---|---:|---:|---:|---:|---:|
| `ca-AstroPh` | social | 18,772 | **6760** (0.10s) | **6760** (0.12s) | **6760** (0.34s) | **6760** (3.97s) |
| `ca-CondMat` | social | 23,133 | **9612** (0.05s) | **9612** (0.06s) | **9612** (0.23s) | **9612** (1.29s) |
| `email-Enron` | social | 36,692 | **22255** (0.08s) | **22255** (0.12s) | **22255** (0.41s) | **22253** (1.98s) |
| `rgg16` | geometric | 65,501 | 16086 | **16086** (0.36s) | **16086** (0.71s) | 16086 |
| `del16` | geometric | 65,536 | 20474 | timeout | timeout | 9679 |
| `rgg18` | geometric | 262,011 | 64271 | **64278** (2.17s) | **64278** (2.29s) | 0 |
| `del18` | geometric | 262,144 | 73928 | timeout | timeout | -- |
| `web-Stanford` | web | 281,903 | 163376 | timeout | timeout | -- |
| `frb30-15-1` | bhoslib | 450 | 25 | **30** (1.82s) | timeout | 28 |
| `frb35-17-1` | bhoslib | 595 | 28 | **35** (2.47s) | timeout | 30 |
| `frb40-19-1` | bhoslib | 760 | 30 | **40** (3.58s) | timeout | 2 |
| `frb45-21-1` | bhoslib | 945 | 34 | timeout | timeout | 1 |
| `frb50-23-1` | bhoslib | 1,150 | 35 | timeout | timeout | 1 |
| `frb53-24-1` | bhoslib | 1,272 | 37 | timeout | timeout | 1 |
| `frb59-26-1` | bhoslib | 1,534 | 42 | timeout | timeout | 30 |

On the instances that reductions dissolve, CASCADE proves optimality fastest of
the four.  Beyond those it is clearly outclassed: WeGotYouCovered proves
`rgg16`, `rgg18` and the three smallest BHOSLIB instances that CASCADE cannot,
because it calls a dedicated maximum-clique solver (MoMC) on the complement, and
a greedy clique-cover bound is no substitute on dense instances.  The honest
summary is that the exact mode is useful as a certificate tool on easy instances
and as the engine behind the neighbourhood moves, not as a competitive stand-
alone exact solver.

It does certify two useful facts about the heuristic: the proven optima for
`rgg16` (16,086) and `rgg18` (64,278) are exactly the values CASCADE's heuristic
reaches, as are the optima for `ca-AstroPh`, `ca-CondMat` and `email-Enron`.

## Ablation: which component earns its place

Each column disables one component; the number in brackets is the change from
the full solver.

| instance | full | no region moves | no perturbation/restarts | no LP reduction | decision-space moves instead |
|---|---:|---:|---:|---:|---:|
| `del16` | 20648 | 20369 (-279) | 20656 (+8) | 20652 (+4) | 20383 (-265) |
| `del18` | 82661 | 81639 (-1022) | 82657 (-4) | 82666 (+5) | 81639 (-1022) |
| `rgg16` | 16086 | 16085 (-1) | 16086 (+0) | 16086 (+0) | 16086 (+0) |
| `roadNet-PA` | 533627 | 533385 (-242) | 533627 (+0) | 533627 (+0) | 533385 (-242) |
| `web-Stanford` | 163375 | 163369 (-6) | 163375 (+0) | 163373 (-2) | 163369 (-6) |
| `frb40-19-1` | 40 | 27 (-13) | 38 (-2) | 40 (+0) | 34 (-6) |
| `frb59-26-1` | 56 | 42 (-14) | 56 (+0) | 57 (+1) | 49 (-7) |

The exact region move is the component that matters, and it is what the
comparison above is measuring: removing it costs 1022 vertices on `del18`, 242
on `roadNet-PA` and 13-14 on the BHOSLIB instances — more than the entire margin
over the baselines in every case.  Without it the solver falls back to what
reduce-and-peel already does.

The decision-space moves in the last column were the original design: search
over the sequence of branching decisions, rewinding and re-diving.  They are
worth almost nothing next to the region moves (identical to disabling the region
moves entirely on `del18` and `roadNet-PA`), which is why they are off by
default and survive only as an ablation switch.

Perturbation and restarts pay for themselves only where diving is cheap: +2 on
`frb40-19-1`, nothing or slightly negative elsewhere.  The LP reduction is
roughly neutral for final quality on this set; its value is in kernel size and
kernelization speed (`web-Stanford` 39,060 -> 9,549 vertices) rather than in the
last few vertices of the answer.

## Reproducing

```sh
python3 tools/gen_instances.py --out data/geometric --scales 16,18,20
python3 scripts/prepare_instances.py
bash scripts/final_bench.sh results 60
```

Raw per-run records are in `results/*.csv`: one row per solver, instance and
seed, with the wall-clock time and the verifier's verdict.

## Threats to validity

* Single machine, four cores, one run per seed; wall-clock timings include
  reading and kernelization, which is why some rows exceed the 60 second budget
  (kernelization is bounded by a share of the budget but is not interruptible
  mid-rule).
* ReduMIS failed to produce any solution on `soc-pokec` within 11 minutes, so
  that row compares against NearLinear instead.
* The Delaunay and random geometric instances are generated here rather than
  taken from a public archive, so they are reproducible from the seed in
  `tools/gen_instances.py` but are not the identical files used in the papers
  that report on `del*` and `rgg*` instances.
* Solution sizes are only counted when `mis-verify` re-reads the original graph
  and confirms independence.  The reference implementation of NearLinear and
  LinearTime prints a size without emitting the set, so its numbers are taken on
  trust and marked unverified in the raw CSV.
