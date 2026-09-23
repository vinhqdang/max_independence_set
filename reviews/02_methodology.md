# Reviewer 1 — Methodology Report

*Computers & Operations Research — manuscript "Exact Large-Neighbourhood Search for the Maximum Independent Set Problem on Massive Sparse Graphs"*
*Reviewer role: empirical algorithmics — benchmarking protocol, statistical inference, reproducibility.*
*All claims below were checked by recomputation from `results/*.csv`, `paper/tables/*.tex` and `scripts/*`; every finding carries a pointer.*

---

## 1. Overall assessment

The paper is unusually honest in its prose. Section 5.13 ("Threats to validity", tex L1040–1130) states the narrowness of the positive result more bluntly than most referees would, Section 5.7 (L816–857) actively qualifies the paper's own headline, and Section 5.11 (L949–985) reports three negative ablation results. The theory (Theorem 1, L340–364) is correct and the contribution is real. I want to say that first, because the findings below are severe and they are *not* about intellectual dishonesty in the writing — they are about a broken results pipeline underneath it.

The decisive problem is this. **The manuscript describes a seven-solver study. The tables it ships are a five-solver study.** `paper/tables/quality_*.tex`, `paper/tables/aggregate.tex` and `paper/tables/budget.tex` contain only Cascade, ReduMIS, OnlineMIS, NearLinear and LinearTime. NuMVC and FastVC — two of the six baselines, and the two that the prose repeatedly names as the strongest competitors — are absent from every per-family quality table, from the aggregate table and from the budget table. The cause is visible in the generator: `scripts/make_tables.py:9-11` defines `SOLVERS` as a five-element list, and every bold face, every `#best` count and every `mean gap` in `aggregate.tex` is computed as a maximum over that five-element list (`make_tables.py:52-55`, `:71-79`). The data for all seven solvers is in `results/cor_main60.csv` and is correctly rendered in `paper/tables/appendix.tex` (189 rows = 27 × 7).

This is not cosmetic. Recomputing `aggregate.tex` over all seven solvers:

| Solver | #best (5-solver, as published) | #best (7-solver) | mean gap (published) | mean gap (7-solver) | max gap (published) | max gap (7-solver) |
|---|---|---|---|---|---|---|
| Cascade | 17 | **16** | 0.414% | **0.785%** | 2.857% | **4.444%** |
| ReduMIS | 23 | 19 | 0.113% | 0.501% | 2.575% | 4.444% |
| FastVC | *absent* | 11 | *absent* | **0.340%** | *absent* | 3.448% |
| NuMVC | *absent* | 8 | *absent* | 1.219% | *absent* | 6.956% |

Under the paper's own aggregate metric, computed over the solver set the paper says it uses, **FastVC has the lowest mean relative gap of any solver on this benchmark (0.340% vs Cascade's 0.785%)**. The published Table `aggregate` omits precisely the baseline that would take the top row. I do not believe this was deliberate — the prose elsewhere is scrupulous about FastVC, and the performance-profile figure does plot all seven (`scripts/make_figures.py:38`) — but the published aggregate table is not a fair summary of the study and cannot go to press.

A second cluster of problems is independent of the first and equally serious: the repository ships **two mutually inconsistent versions of the main result set and two of the seed study**, with no statement of which is authoritative; the Wilcoxon test is **not computed on the quantity the paper twice says it is computed on**, and the substitution changes the headline result; **no baseline revision is pinned** despite an explicit claim that one is; and **the two reducing-peeling baselines are unverified yet counted**, contradicting Section 5.1.

Recommendation: **major revision**, bordering on reject-and-resubmit. The algorithmic contribution survives. The computational study, as published, does not support the claims made from it and must be regenerated end to end.

---

## 2. Experimental design

**2.1 Family balance is poor and works against the claim.** 27 instances split 6 geometric / 2 road / 2 web / 10 social / 7 BHOSLIB (`tables/provenance.tex`). The single family in which the method is claimed to win — large-kernel geometric graphs — has six members, of which only the three Delaunay graphs are strict wins. The road and web families have two members each, which is too few to say anything; yet Section 5.3 (L672) draws a conclusion from them ("On web graphs Cascade is behind ReduMIS by 15 and 102 vertices"), and the Conclusions (L1155) elevate this to a stated limitation of the method. Two observations cannot carry that.

**2.2 The self-generated instances.** This is the structural weakness the authors themselves name (L1113–1130) and it is worse than stated. The three strict wins are `del16`, `del18`, `del20`. All three are produced by `tools/gen_instances.py` at seed 1 (`tables/provenance.tex`; Appendix A, L1183–1196). The generator produces exactly two families, Delaunay and RGG (`tools/gen_instances.py:13,23`). So:

- 100% of the paper's strict wins are on instances the authors generated;
- they are three draws from a *single* generator at a *single* seed — not three independent instances but three sizes of one construction;
- the paper correctly notes (L1050–1056) that these are not the DIMACS graphs of the same name, so no external result can be compared against them.

The claim "the margin grows with size" (L637) is therefore a claim about one generator family observed at three points, with n=1 seed per point. It is suggestive, not established. The honest framing in Section 5.13 does not repair this; a reader cannot falsify the central claim with public data.

**Remedy.** Generate ≥10 Delaunay and ≥10 RGG instances per size from *different* seeds and report the margin distribution. Add the DIMACS10 `delaunay_n*` graphs, which are public and are the graphs the literature actually uses — that makes the result checkable by third parties at essentially zero cost. Until then, the abstract's "strictly ahead of all of them on the three Delaunay instances by a margin that grows with size" (L68) should read "on three generated Delaunay instances of increasing size".

**2.3 Is 27 enough?** For the aggregate Wilcoxon, no — see §3. For the per-family claims, emphatically no: the road, web and geometric-RGG conclusions rest on 2, 2 and 3 instances respectively. The BHOSLIB family (7 instances) is the only one with adequate n, and it is the family where the method loses.

**2.4 Missing coverage.** The long-budget study claims "four instances, one per family" (L822). There are five families; **social is absent** (`tables/longbudget.tex`: del20, roadNet-CA, web-BerkStan, frb59-26-1). Social is the family containing `soc-pokec`, the instance on which the paper admits kernelization is truncated at 18 s (L555) — exactly the instance where a 10× budget is most diagnostic. Similarly, the seed study covers 10 of 27 instances and includes **no social instance at all** (`results/cor_seeds60.csv`).

---

## 3. Statistical validity

**3.1 [CRITICAL] The Wilcoxon test is not computed on relative gaps.** Section 5.13 states flatly: "The Wilcoxon tests in Table~\ref{tab:wilcoxon} are computed over relative gaps" (L1119–1120); Section 5.4 sets the test up the same way, as the scale-robust alternative to counting wins (L706–711). It is not. `scripts/stats_test.py:69` calls `wilcoxon(ours, other, ...)` on **raw independent-set sizes**. I reproduced the published p-values exactly from raw sizes, and recomputed them on relative gaps:

| Baseline | published *p* | reproduced from raw sizes | recomputed on relative gaps | verdict changes? |
|---|---|---|---|---|
| ReduMIS | 0.1951 | 0.1951 ✓ | 0.1268 | no |
| **FastVC** | **0.0300** | 0.02998 ✓ | **0.4406** | **yes — significance lost** |
| **NuMVC** | **0.0008** | 0.00079 ✓ | **0.1549** | **yes — significance lost** |
| NearLinear | 0.0001 | 0.00014 ✓ | 0.00005 | no |
| OnlineMIS | <1e-4 | 9.7e-6 ✓ | 9.8e-6 | no |
| LinearTime | <1e-4 | 3.4e-5 ✓ | 2.0e-5 | no |

**The headline "significantly better than five of the six baselines" (abstract L75, Section 5.4 L713) becomes "three of six" the moment the stated test is actually run.** And the raw-size version is the wrong test on the paper's own reasoning: Section 5.4 opens by saying instance scale spans four orders of magnitude and that raw win-counting is therefore misleading (L706–709) — but a signed-rank test on raw size differences ranks a 46 054-vertex difference on `roadNet-CA` above a 2-vertex difference on `frb45-21-1`, which is precisely the scale-domination the section claims to avoid.

**3.2 [MAJOR] No multiple-comparison correction.** Six pairwise tests against a common reference (Table `wilcoxon`), plus four more in the seed study (L753–756), reported against an uncorrected α = 0.05 (`stats_test.py:37`). Bonferroni at α/6 = 0.0083: FastVC (p = 0.0300) **fails**. In the seed study at α/4 = 0.0125: FastVC (0.016) and NuMVC (0.023) **both fail**; only OnlineMIS (0.008) survives. Combined with §3.1, the defensible claim shrinks to: Cascade beats OnlineMIS and the two peeling heuristics, and is statistically indistinguishable from ReduMIS, NuMVC and FastVC.

**3.3 [MAJOR] Ties dominate and `zsplit` inflates n.** `stats_test.py:69` uses `zero_method="zsplit"`, which keeps zero-differences in the sample and splits their ranks. Against ReduMIS there are **14 ties in 26 pairs** (Table `wilcoxon`): only 12 pairs carry information, but the test is run at n = 26, which is why `zsplit` gives p = 0.195 where dropping zeros (`zero_method="wilcox"`) gives p = 0.525. The choice is not stated in the paper. The reader should be told that the ReduMIS comparison rests on 12 informative observations, not 26.

**3.4 [MAJOR] "No significant difference" is read as equivalence in places.** Section 5.4 (L723–726) reads the non-significant ReduMIS result correctly and carefully ("the two are equal on most of this benchmark ... that is exactly what a non-significant p-value ... should be taken to mean"). But the abstract (L75–76) reports it flatly as "finds no significant difference from ReduMIS", and Section 5.13 (L1125) uses it affirmatively: "against the one baseline that does not degrade there, ReduMIS, no test in this paper finds a significant difference". With 12 informative pairs and no power analysis, this is absence of evidence. A TOST equivalence test, or simply a reported minimum detectable effect, would let the authors make the claim they are actually reaching for.

**3.5 [MAJOR] Wilcoxon on one run per instance is the wrong unit of analysis.** Table `wilcoxon` is computed from `cor_main60.csv`, which contains a **single seed per (instance, solver)** for five randomised solvers. The test therefore treats one realisation of a stochastic process as the instance's value. The seed study shows this matters: `del16` Cascade ranges 20642–20647 over five seeds (`cor_seeds60.csv`), i.e. a spread of 5 vertices, while the paper's headline margin on that very instance is **+7 vertices** (L638). The margin is barely outside its own single-seed noise. Similarly on `del18` the best-of-5 margin over FastVC is +67, not the +77 the paper reports from seed 1.

**3.6 [MAJOR] No effect sizes anywhere.** No rank-biserial correlation, no matched-pairs Cliff's delta, no confidence intervals on any margin. For a paper whose wins are 0.03–0.09% of the objective, a p-value without an effect size and an interval is not interpretable. Table `aggregate` reports means with no dispersion at all.

**3.7 Seed coverage, verified.** `results/cor_seeds60.csv`: 10 instances × 5 solvers × 5 seeds = 250 runs. Instances: del16, del18, del20, rgg18, roadNet-PA, web-Stanford, web-BerkStan, frb40-19-1, frb53-24-1, frb59-26-1. **No social instance; no rgg16/rgg20; no roadNet-CA.** NearLinear/LinearTime excluded (deterministic — legitimate). I reproduced all four seed-study p-values exactly (0.0156, 0.0234, 0.0078, 0.8125 vs the paper's 0.016, 0.023, 0.008, 0.81 at L753–755) ✓. The ablation (`results/ablation.csv`), the sensitivity study (`results/sensitivity.csv`), the long-budget study (`cor_long600.csv`) and the replication (`replication60.csv`) are **all single-seed**.

**3.8 [MAJOR] NuMVC and FastVC are never actually seeded.** `scripts/run_bench.py:137` invokes them as `[BIN[solver], dimacs, "0", str(int(tl))]` — graph, target size, cutoff. **No seed argument is passed**, at any seed setting. Yet `cor_seeds60.csv` records five rows for them labelled seed 1–5, and their values differ across those rows (e.g. `del16` FastVC: 20633/20635/20638/20642/20637). Those five runs differ because the binary self-seeds, not because the harness varied anything. Consequence: the `seed` column is meaningless for two of the five randomised solvers, and none of their runs is reproducible.

---

## 4. Budget, timing and fairness to baselines

**4.1 [MAJOR] The 60 s headline measures convergence rate on the instance that carries the result.** The reviewer's suspicion is confirmed by the authors' own data and, to their credit, half-admitted at L832–839. On `del20`: at 60 s Cascade − ReduMIS = 330 066 − 321 566 = **+8500**; at 600 s = 330 533 − 328 983 = **+1550**. ReduMIS gains 7417 vertices from the extra time; Cascade gains 467. So **94% of the flagship margin against ReduMIS is convergence rate, not solution quality**, and it decays with budget. The margin against the *best* baseline (FastVC) is indeed stable (+264 → +341), and the paper says so — but the number the reader remembers from Section 5.3 is +8500, stated four sentences before the qualification. The `del20` row is also the instance that produces essentially the entire +8651 net advantage over ReduMIS in Table `whence` (geometric net +8778; all other families negative).

**4.2 [MAJOR] 60 s is asserted, not justified.** Section 5.7 (L819–822) says the choice "needs defending" and then defends it with a 4-instance, 1-seed, 1-alternative-budget check that excludes the social family. That is not a defence; it is a spot check. No budget–quality curve is given for any solver over a range of budgets. Given §4.1, the reader cannot tell whether 60 s is a reasonable practitioner deadline or the point at which the gap to ReduMIS happens to be widest.

**4.3 [CRITICAL] Timing comparisons are not conducted under a common wall-clock allowance.** `scripts/run_bench.py` applies wildly different subprocess kill-times on top of the nominal budget:

| Solver | harness timeout | source |
|---|---|---|
| Cascade (all variants) | `tl + 600` = 660 s | `run_bench.py:174` |
| ReduMIS, OnlineMIS | `tl + 600` = 660 s | `:91` |
| NuMVC, FastVC | `tl + 900` = **960 s** | `:137` |
| HiGHS | `tl + 300` = 360 s | `:156` |
| **VCSolver, PACE 2019** | **`tl` = 60 s, hard** | `:107`, `:125` |

The two exact baselines in Table `exact` are killed at exactly the nominal budget while Cascade-exact is allowed eleven times it — and the table duly shows `cascade-exact` taking **83.2 s on `del18`** (`results/exact.csv`) against `vcsolver` and `pace` marked *t/o* at 60.066 s and 60.010 s. Section 5.10's second conclusion ("our exact solver is not competitive", L924) is unaffected, but the *t/o* entries for VCSolver and PACE are partly an artefact of a stricter kill, and this must be disclosed. The 960 s ceiling for NuMVC also explains the `com-lj` entry: `numvc,com-lj,,960.049,TIMEOUT` — NuMVC did not "fail", it was killed by the harness at 16× budget.

**4.4 [MAJOR] The budget table omits the solver the surrounding text is about.** Section 5.5 (L741–744) says "Table~\ref{tab:budget} should be read alongside these results. NuMVC checks its cutoff only between search steps, so under a 60 s budget it takes 204 s on average and exceeds 90 s on twelve of the 27 instances." I verified both numbers from `cor_main60.csv` (mean 204.3 s; 12 runs > 90 s) ✓ — but **NuMVC is not in Table `budget`**, nor is FastVC. The reader is directed to a table that does not contain the quantity discussed.

**4.5 [MAJOR] No baseline was tuned; Cascade was.** `run_bench.py:162-163` passes Cascade `--lns-free 4`, an explicitly chosen parameter value. ReduMIS gets `--kernelization=full` (`:91`) and nothing else; OnlineMIS gets no equivalent; NuMVC and FastVC get LibMVC defaults with no seed (§3.8); NearLinear/LinearTime get no arguments and no time limit at all (`:98`). No published best settings are cited for any baseline. Section 5.1 says baselines use "the authors' own build settings" (L588) — build settings are not parameter settings, and the paper never claims the latter. It should state plainly that baselines ran at defaults.

**4.6 [MINOR] Compiler flags are not as described.** Section 5.1 states "every solver compiled by GCC 13.3 at `-O3`" (L573). `CMakeLists.txt:9` builds Cascade with `-O3 -march=native -funroll-loops -DNDEBUG`. Whether the baselines received `-march=native` is unknown and unstated. `-march=native` also undermines the replication design, since it produces a different binary on the two machines.

**4.7 Budget adherence, verified.** Recomputed from `cor_main60.csv`: Cascade median 60.1 / mean 48.3 / max 75.0 s, 0 runs > 90 s; ReduMIS 60.2 / 69.7 / 660.2, 2 runs; NuMVC 85.9 / 204.3 / 960.0, 12 runs; FastVC 60.2 / 60.7 / 67.5, 0 runs. Table `budget` matches for the five solvers it lists ✓. Cascade overruns the budget on 9 of 27 instances (max 75.0 s on `com-lj`, +25%) — disclosed in Section 5.13 (L1032–1036) ✓.

---

## 5. Reproducibility

**5.1 [CRITICAL] Baseline revisions are not pinned, contrary to an explicit claim.** Section 5.1: "Baselines are built from their authors' published sources, **at the revision the provisioning script pins**" (L587–588). `scripts/colab_setup.sh` lines 31, 37, 42, 47, 55 clone KaMIS, Near-Maximum-Independent-Set, vertex_cover, pace-2019 and LibMVC with `git clone --depth 1 <url>` — the default branch HEAD, no tag, no commit, and `--depth 1` actively discards the history that would let a reader recover what was built. Nothing is pinned. This single line makes the baseline half of the study unreproducible by anyone, including the authors.

**5.2 [CRITICAL] Two inconsistent main result sets ship in the same repository, and the generator defaults to the wrong one.** `results/cor_main60.csv` (7 solvers, 189 runs) and `results/heuristic.csv` (5 solvers, 135 runs) disagree on **18 of their 135 shared (instance, solver) cells**. Examples: `del20`/cascade 330 066 vs 330 154; `del18`/cascade 82 656 vs 82 662; `frb40-19-1`/cascade **39 vs 40**; `soc-pokec`/cascade 788 866 vs 788 819; `roadNet-CA`/cascade 961 851 vs 961 850. `results/summary.md` is a third copy, agreeing with `heuristic.csv`. The paper's tables were produced from `cor_main60.csv`, but `make_tables.py:120` defaults to `--main heuristic.csv` — so running the shipped generator as shipped produces **different tables from the ones in the paper**. Neither file is dated, labelled, or mentioned in the manuscript.

**5.3 [CRITICAL] Two inconsistent seed studies.** `results/cor_seeds60.csv` (10 instances, 5 solvers) and `results/variance.csv` (12 instances, 3 solvers) disagree on **32 (instance, solver, seed) triples**, including sign-flipping cells: `frb40-19-1`/cascade/seed 2 = 40 vs 39; `frb59-26-1`/cascade/seed 3 = 56 vs 57; `del18`/cascade/seed 1 = 82 656 vs 82 662. The manuscript describes one seed study. A reader cannot tell which file backs Table `seeds`. (It is `cor_seeds60.csv` — I reproduced every published value and p-value from it.)

**5.4 [MAJOR] The entire throughput argument rests on numbers that exist nowhere in the data.** Section 4.2 (L526–559) gives: `del18` kernelization 1.16 s, dive 0.37 s, **107 238 region moves**, 543 µs/move; `web-Stanford` 0.69 s / 0.03 s / **96 842 moves** / 605 µs; queue-ordering comparison 0.84 vs 1.05 s, 4.87 vs 7.39 s, 13.98 vs 48.84 s; `soc-pokec` fixed-point kernelization **180.5 s**, truncation at 18.0 s. None of these appears in any shipped CSV. The `note` field for every Cascade row in `cor_main60.csv` is literally the constant string `maximal=yes` — no kernel size, no move count, no phase timing. Section 4.1 asserts "The kernel size measured for every instance is in the run records distributed with the source" (L476–477); it is not — kernel sizes are recorded only for NearLinear and LinearTime, parsed from *their* stdout (`run_bench.py:102`). The abstract's "about half a millisecond ... some 1800 of them per second" (L59–60) and Section 5.10's "at some 1800 moves per second" (L921) are therefore unverifiable from the artefact.

**5.5 [MAJOR] The provenance appendix misattributes two real-world graphs to the authors' own generator.** `tables/provenance.tex` marks `soc-pokec-relationships` and `com-lj` as `generated‡`, where ‡ is defined in the same caption as "produced by `tools/gen_instances.py` at seed 1". This directly contradicts Section 5.2 ("The first family is generated with a fixed seed ...; **the remainder are public**", L608–610) and Appendix A. The cause is `scripts/make_appendix_tables.py:23-35`: the `SNAP`/`SNAP_COMM` whitelists omit those two names, and `source()` falls through to "generated". As printed, the appendix tells a referee that **8 of 27 instances are self-generated, including the two largest social graphs**. Given that instance provenance is the paper's most exposed flank, this error is corrosive out of all proportion to its cause.

**5.6 [MAJOR] The reducing-peeling baselines are unverified and counted anyway.** Section 5.1: "values that fail this check, **or that a solver reports without emitting the set itself, are not counted**" (L580–583). In `cor_main60.csv` the `verified` column is `0` for **all 54 NearLinear and LinearTime rows** — `run_bench.py:105` returns `verified=False` by construction, with the comment "this number cannot be verified here". They are counted: in every quality table, in Table `aggregate` (where NearLinear scores `#best = 7`, including the bolded best value on `soc-pokec`), in the performance profile, and in **two of the six Wilcoxon comparisons**. Section 5.13 (L1043–1047) says they are "taken on trust", which contradicts Section 5.1. Two of the four surviving significant results are against solvers whose numbers the paper's own protocol says should not be counted.

**5.7 [MAJOR] The replication does not show what it claims.** Section 5.12 (L1008–1013): "on all 25 instances, the set of solvers attaining the best value on the replication machine intersects the set attaining it on the original machine. **No solver changes place with another.**" The first half is true but near-vacuous as a test — on `ca-AstroPh` six of seven solvers tie, so intersection is guaranteed. The second half is **false in the shipped data**. Comparing Cascade's rank in `cor_main60.csv` against `replication60.csv`:

| Instance | Cascade rank, main | Cascade rank, replication |
|---|---|---|
| `frb40-19-1` | 4 (39) | **1** (40) |
| `frb50-23-1` | 4 (48) | 3 (48) |
| `frb53-24-1` | 4 (50) | 3 (50) |
| `frb59-26-1` | 3 (56) | **4** (56) |

Best-value *sets* differ (not merely intersect) on 5 of 25 instances, including `roadNet-CA`, where ReduMIS drops out of the best set entirely. The correct statement is "no solver's rank changes outside the BHOSLIB family", which is weaker and is what the data supports.

**5.8 [MINOR] The replication platform is Google Colab VMs**, per `scripts/colab_setup.sh` and `scripts/colab_replicate.py`. Section 5.12 calls it "a second, unrelated platform" (L991) — shared-tenant cloud VMs with unknown co-tenancy are a poor control for a wall-clock study, and the paper should name the platform rather than describe it only by core count and RAM.

**5.9 What *is* adequate.** Hardware, OS, compiler version and budget are stated (L570–574); the data-availability statement gives a real repository that matches `git remote` ✓; `tools/gen_instances.py` is deterministic given the seed ✓; the BHOSLIB complement issue is handled correctly and documented twice (L611–619, L1170–1181) — this is a genuine service to the field, since a study that gets it wrong reports confidently wrong numbers. No `refs.bib` problems observed.

---

## 6. Numerical audit

Every row recomputed from the CSVs. `M` = `results/cor_main60.csv`.

| # | Claim as written | Location | Value in data | Verdict |
|---|---|---|---|---|
| 1 | "best value of all seven solvers on every geometric instance" | abstract L66, §5.3 L636 | rgg16 16086 = ReduMIS; del16/18/20 strict; rgg18/20 tie ReduMIS | ✓ |
| 2 | "+7 on del16, +77 on del18 and +264 on del20" vs strongest baseline | §5.3 L638–639 | 20647−20640(ReduMIS)=7; 82656−82579(FastVC)=77; 330066−329802(FastVC)=264 | ✓ |
| 3 | "against ReduMIS alone ... +7, +271 and +8500" | §5.3 L641 | 7; 82656−82385=271; 330066−321566=8500 | ✓ |
| 4 | "0.03%, 0.09% and 0.08%" relative margins | §5.3 L649 | 0.0339%, 0.0932%, 0.0800% | ✓ |
| 5 | abstract "0.08% over the strongest baseline at one million vertices" | abstract L68 | 264/329802 = 0.0800% | ✓ |
| 6 | abstract "behind ... by at most 0.06% on five large sparse graphs" | abstract L71–72 | worst is soc-pokec 486/789352 = **0.0616%** | ✓ (rounds down; state as 0.062%) |
| 7 | abstract "three / thirteen / eleven" split | abstract L70–73 | over 7 solvers: 3 ahead, 13 tie, 11 behind | ✓ |
| 8 | Table `aggregate` Cascade `#best` = 17 vs prose "matches the best value on 16 of the 27" | `aggregate.tex`; §5.4 L729 | 7-solver: **16**; 5-solver: 17 | ✗ table and prose contradict; table is the 5-solver artefact |
| 9 | "a two-vertex shortfall is a 4.4% relative gap, **the largest we record anywhere**" | §5.3 L679–680 | 2/45 = 4.444% ✓, but Table `aggregate` prints Cascade max gap = **2.857%** | ✗ internal contradiction (same cause as #8) |
| 10 | "0.06% behind FastVC, the best value there" (soc-pokec) | §5.3 L667 | 788866 vs 789352 = 0.0616%; FastVC is best ✓ | ✓ — but FastVC absent from Table `quality-social`, which bolds NearLinear 789161 |
| 11 | "the solver returns **788 868** within its budget" (soc-pokec) | §4.2 L556 | `cor_main60` = **788 866**; `heuristic.csv` = 788 819 | ✗ matches no shipped record |
| 12 | "behind ReduMIS by 15 and 102 vertices, which is 0.009% and 0.025%" | §5.3 L672–673 | 163390−163375=15 (0.0092%); 408482−408380=102 (0.0250%) | ✓ |
| 13 | "45 against our 43 on frb45-21-1, 58 against our 56 on frb59-26-1" | §5.3 L677–678 | 45/43 ✓; 58/56 ✓ | ✓ |
| 14 | "ahead by 8778 ... behind by 127 ... net +8651" (vs ReduMIS) | §5.4 L720–721 | +8778 / −127 / +8651 | ✓ (`whence.tex` ✓) |
| 15 | Table `whence` "All: 27 instances, 3/14/9" | `whence.tex` | 3+14+9 = **26**; ReduMIS failed on one | ✗ label should read 26 compared (27 listed) |
| 16 | "NuMVC ... takes 204 s on average and exceeds 90 s on twelve of the 27" | §5.5 L742–743 | mean 204.3 s; 12 runs > 90 s | ✓ — but not in Table `budget` |
| 17 | "ReduMIS returned nothing on soc-pokec within eleven minutes" / "NuMVC ... on com-lj within sixteen" | §5.3 L668–670 | 660.20 s = 11.0 min ✓; 960.05 s = 16.0 min ✓ | ✓ — 960 s is the *harness* kill (`run_bench.py:137`), not NuMVC's own limit |
| 18 | "near-linear kernelization leaves 9780 of them" (com-lj) | §5.3 L664 | `note=kernel=9780` | ✓ |
| 19 | "1550 ... ReduMIS gains 7417 ... NuMVC 6227 ... 467 ... 390" | §5.7 L833–835 | 330533−328983=1550; 7417; 6227; 467; 390 | ✓ all five |
| 20 | "264 vertices at 60 seconds, 341 at 600" | §5.7 L845 | 330533−330192 = 341 | ✓ |
| 21 | "ReduMIS reaches its final value on web-BerkStan in 67 s and roadNet-CA in 69" | §5.7 L850–851 | `longbudget.tex` 67 / 69 | ✓ |
| 22 | seed p-values 0.016 / 0.023 / 0.008 / 0.81 | §5.6 L753–755 | 0.0156 / 0.0234 / 0.0078 / 0.8125 from `cor_seeds60.csv` | ✓ (uncorrected) |
| 23 | "spread is at most 0.024%" on geometric/road/web | §5.6 L760 | max = del16 0.0242% | ✓ |
| 24 | "on two instances all five seeds return the same value" | §5.6 L761 | zero-spread instances are rgg18 **and frb59-26-1** — only one is geometric/road/web | ✗ misleading in context |
| 25 | "2.5% on frb40-19-1 and 2.0% on frb53-24-1"; "OnlineMIS spreads 5.1% and 3.9%" | §5.6 L763–766 | 2.500 / 1.961; 5.13 / 3.92 | ✓ |
| 26 | "NuMVC reaches it after 0.2 s and FastVC after 0.8, where we need 6.6" | §5.6 L799–801 | `traces.csv`: 0.233 / 0.826 / 6.589 | ✓ |
| 27 | "All three solvers finish on the same value of **40**" (frb40-19-1) | §5.6 L799 | trace final 40, but Table `quality-bhoslib` gives Cascade **39** | ✗ figure and headline table disagree |
| 28 | "between 6 and 586 points here" / "up to 33 000" | Fig. caption L810–812 | 6 … 586 ✓; 33 032 ✓ | ✓ |
| 29 | "improves six times in sixty seconds" (web-Stanford) | §5.6 L795 | 6 points, all within **0.887–3.414 s** | ✓ count, misleading phrasing |
| 30 | "removing it costs 1.2% on del18 and 1.4% on del16 ... 32.5% on frb40-19-1 ... summed loss 1577" | §5.11 L962–966 | 1022/82661=1.236%; 279/20648=1.351%; 13/40=32.5%; Σ=1577 | ✓ all four |
| 31 | "changes the summed total by +2" / "by +8" | §5.11 L978–981 | +2 ✓ / +8 ✓ | ✓ |
| 32 | "returns exactly ... 81 639, 533 385 and 163 369" | §5.11 L971–972 | `ablation.tex` ✓ | ✓ |
| 33 | "82 592 at 50, 82 639 at 100, 82 659 at the default 200, then 82 655 at both 400 and 800"; "0.081%" | §5.9 L883–885 | `sensitivity.tex` ✓; 67/82659 = 0.081% ✓ | ✓ |
| 34 | "every value of kernel_share ... and lns_slice ... returns the same 163 375" | §5.9 L877–879 | ✓ | ✓ |
| 35 | "a factor of 25 to 40 over HiGHS, three to five over VCSolver, 1.1 to 1.4 over the PACE portfolio" | §5.10 L917–919 | HiGHS 24.7–39.3×; VCSolver 3.4–5.1×; PACE 1.14–**1.44**× | ~ ranges slightly overstated at both ends |
| 36 | "exceeds the 60-second budget on most others, taking up to 360 s" | §5.10 L936 | `exact.csv` HiGHS max 360.16 s | ✓ — but 360 s is the harness ceiling (`run_bench.py:156`), i.e. HiGHS was silently given 6× budget |
| 37 | "on frb45-21-1 through frb53-24-1 it returns a single vertex, on rgg18 none at all" | §5.10 L937–938 | 1/1/1 ✓; 0 ✓ | ✓ |
| 38 | "22 253 vertices against the 22 255" while claiming optimality | §5.10 L939–941 | `highs,email-Enron,22253,...,maximal=no proved_optimal` | ✓ (creditably reported) |
| 39 | "46 054 vertices on roadNet-CA, 18 645 on del20" (vs NuMVC) | §5.13 L1084–1085 | 961851−915797=46054; 330066−311421=18645 | ✓ |
| 40 | "differ by five vertices out of 20 647 on del16, which is 0.024%" | §5.13 L1105–1106 | 5/20647 = 0.0242% ✓ | ✓ |
| 41 | abstract "1800 moves/s"; "half a millisecond per move" | abstract L59–60 | 107238/58.5 = 1834/s, 545 µs — **but no move count exists in any shipped record** | unverifiable |
| 42 | "kernelizes the whole graph in 1.16 s" (del18) vs "kernelization takes 0.84 s ... on web-Stanford" and "0.69 s" (web-Stanford) | §4.2 L529, L539, L530 | web-Stanford kernelization is given as **0.69 s** and **0.84 s** 10 lines apart | ✗ unexplained 22% discrepancy |
| 43 | "every reported solution is independent **and maximal**" | §4.2 L562–563 | `exact.csv` contains `maximal=no` rows still marked `verified=1` (del16, web-Stanford, email-Enron/HiGHS) | ✗ maximality is not enforced |

Verdict counts: 30 verified exactly, 8 refuted or internally contradictory, 3 unverifiable from the shipped artefact, 2 imprecise.

---

## 7. Ablation and parameter sensitivity

**7.1 The ablation can falsify the central claim, and to the authors' credit it partly does.** `no-lns` is the right control and it is decisive (−1577 vertices summed; −1022 on `del18`). Three of the four variants return *negative* results and are reported as such (§5.11 L968–985), including the striking admission that `cascade-dive` — the move the authors designed first — "contributes nothing whatever". This is the best-executed part of the study.

**7.2 [MAJOR] But it is n = 1 per cell, and the noise floor exceeds three of the four effects.** Seven instances × five configurations × **one seed** (`results/ablation.csv`, 35 rows). The `no-pert` effect is +2 vertices summed and `no-lp` is +8; the ablation's own `full` column disagrees with the main table by up to 6 vertices on `del18` (82 661 vs 82 656), and the sensitivity study's *default* configuration returns 82 655 / 82 655 / 82 656 / 82 659 for the same settings in its four blocks. In other words the measurement noise on `del18` is ±4 vertices and the claimed `no-lp` effect is +5. The paper says the right thing ("both within noise", L976) but then draws a directional conclusion anyway ("a reader looking to reimplement ... should start with the region move and add the rest only if measurement justifies it", L983–985) that these runs cannot support in either direction. Also note `no-pert` on `del16` returns 20 656, **eight vertices better than the full solver** — larger than the +7 headline margin on that instance.

**7.3 [MAJOR] The sensitivity grid covers 4 of at least 8 tunables.** Table `sensitivity` varies `kernel_share`, `lns_start_free`, `lns_slice`, `restart_idle_dives`. `src/main.cpp:53-71` exposes at least eight behavioural knobs: `--sample`, `--include-prob`, `--restart-idle`, `--kernel-share`, `--lns-free`, `--lns-budget`, `--lns-slice`, plus the `--no-*` switches. **`lns_node_budget` is untested** and is the parameter that decides whether a sub-solve reaches proven optimality — which is the signal driving the online *k* adaptation that the paper lists as contribution (2) (L149–152). The one parameter the adaptive mechanism depends on is the one not varied.

**7.4 [MAJOR] One-at-a-time, single-seed, three instances.** 60 runs, no seed replication, no interaction terms. On `frb40-19-1` the default configuration returns 40, 39, 39, 40 across the four blocks — pure noise — and the paper correctly says "A single run per setting cannot separate a parameter effect from that noise" (L894–895). It should then not report per-block spread figures to three decimals (`0.001`, `0.013`, `0.008`) that are an order of magnitude below the default configuration's own run-to-run variation.

**7.5 [MAJOR] Tuning-on-test contamination.** The sensitivity instances are `del18`, `frb40-19-1`, `web-Stanford` — **all three are in the 27-instance headline benchmark**, and `del18` is one of the three instances on which the paper's central claim rests. `run_bench.py:163` hard-codes `--lns-free 4` for every main run. There is no held-out tuning set and no statement of how the defaults were arrived at. Compounding this, the grid shows the default is **not the best value in its own grid**: on `del18`, `lns_start_free=16` returns 82 659 against the default's 82 655, and `restart_idle_dives=200` returns 82 659 in its block while the other three blocks return 82 655–82 656 at the same nominal defaults. Whatever tuning happened, it happened on the test instances, and the paper's claim of "an online rule ... that needs no per-instance tuning" (L149–150) is about *k* only, not about the six other dials.

---

## 8. Specific issues

1. **[CRITICAL] NuMVC and FastVC are missing from every main table.** `paper/tables/quality_{geometric,road,social,web,bhoslib}.tex`, `aggregate.tex`, `budget.tex`; cause at `scripts/make_tables.py:9-11`. The prose calls FastVC the strongest baseline on `del18`/`del20` (L639–640) and quotes NuMVC's timing behaviour against Table `budget` (L741–744); neither is in the table cited. *Remedy:* extend `SOLVERS` to all seven, regenerate all six tables, and re-derive every bolded value, `#best` count and gap.

2. **[CRITICAL] The aggregate table's numbers change materially once the missing baselines are restored.** Cascade `#best` 17 → 16, mean gap 0.414% → 0.785%, max gap 2.857% → 4.444%; FastVC enters at mean gap **0.340%**, the best in the table. *Remedy:* republish Table `aggregate` over seven solvers and rewrite §5.4 accordingly — including acknowledging that on this metric FastVC leads.

3. **[CRITICAL] The Wilcoxon test is computed on raw sizes, not relative gaps as stated.** `scripts/stats_test.py:69` vs §5.13 L1119–1120. On relative gaps, FastVC p = 0.441 and NuMVC p = 0.155. *Remedy:* run the test on the stated quantity and rewrite the abstract's "ahead of five of the six baselines" (L75) to "three of six"; or keep raw sizes and delete the claim that the test is scale-robust.

4. **[CRITICAL] Baseline revisions are not pinned.** `scripts/colab_setup.sh:31,37,42,47,55` use `git clone --depth 1` of HEAD, against the claim at L587–588. *Remedy:* pin explicit commit SHAs for all five baseline repositories, record them in a table, and correct §5.1.

5. **[CRITICAL] Exact solvers run under unequal wall-clock ceilings.** VCSolver and PACE are killed at exactly 60 s (`run_bench.py:107,125`) while Cascade-exact gets 660 s (`:174`) and visibly uses 83.2 s on `del18`; HiGHS gets 360 s (`:156`) and uses it. *Remedy:* re-run Table `exact` with one ceiling for all four, or state the ceilings in the caption and mark every affected cell.

6. **[MAJOR] Two conflicting main result files and two conflicting seed files ship together.** `cor_main60.csv` vs `heuristic.csv` (18/135 cells differ); `cor_seeds60.csv` vs `variance.csv` (32 triples differ); `make_tables.py:120` defaults to the file the paper did **not** use. *Remedy:* delete or clearly archive the superseded files, name the authoritative one in §5.1 and the data-availability statement, and fix the generator default.

7. **[MAJOR] `provenance.tex` labels `soc-pokec-relationships` and `com-lj` as generated by the authors' own tool.** Cause: `scripts/make_appendix_tables.py:23-25`. Contradicts §5.2 L608–610 and Appendix A. *Remedy:* add both to the SNAP list and regenerate; given the paper's exposure on instance provenance, also state the SNAP snapshot date.

8. **[MAJOR] Unverified values are counted despite an explicit protocol to the contrary.** All 54 NearLinear/LinearTime rows carry `verified=0` (`run_bench.py:105`), yet appear in every quality table, in `aggregate.tex` (NearLinear `#best`=7), in the profile, and in two of six Wilcoxon comparisons. §5.1 L580–583 vs §5.13 L1043–1047. *Remedy:* either report them in a clearly separated, non-tested block, or patch Chang et al.'s code to emit the set (a few lines) and verify them.

9. **[MAJOR] No multiple-comparison correction on 6 + 4 tests.** Table `wilcoxon`; §5.6 L753–755. Under Bonferroni, FastVC fails in the main test and both FastVC and NuMVC fail in the seed study. *Remedy:* report Holm-adjusted p-values alongside raw ones, and state the family of tests.

10. **[MAJOR] "No solver changes place with another" is contradicted by `replication60.csv`.** §5.12 L1011–1012; Cascade's rank moves on four BHOSLIB instances (4→1 on `frb40-19-1`, 3→4 on `frb59-26-1`) and best-value sets differ on 5 of 25 instances. *Remedy:* replace with "no rank change outside BHOSLIB", and report Kendall's τ between the two machines' rankings per instance.

11. **[MAJOR] The throughput and kernelization numbers in §4.2 are absent from the shipped run records**, contrary to L476–477 and L557–558. *Remedy:* emit kernel size, kernelization seconds, dive seconds and move count per run into the CSV; these are one `fprintf` each and they are load-bearing for the abstract.

12. **[MAJOR] Single seed per instance throughout the main study, ablation, sensitivity, long-budget and replication.** The `del16` headline margin (+7) is inside the solver's own five-seed range (20642–20647). *Remedy:* run ≥5 seeds for all randomised solvers on all 27 instances and report median with IQR; at minimum, run the ablation and sensitivity grids at ≥5 seeds.

13. **[MAJOR] NuMVC and FastVC are never given a seed** (`run_bench.py:137` passes graph/target/cutoff only), yet are recorded under seed labels 1–5. *Remedy:* pass LibMVC's seed argument and re-run, or state that these two solvers' runs are unseeded and unreproducible.

14. **[MAJOR] The long-budget study omits the social family** although §5.7 L822 says "one per family". `soc-pokec` — the truncated-kernelization instance — is exactly the one a 600 s budget would illuminate. *Remedy:* add `soc-pokec` (or `com-lj`) to `longbudget`.

15. **[MAJOR] Tuning instances are test instances.** `del18`, `frb40-19-1`, `web-Stanford` all appear in the headline benchmark; `--lns-free 4` is hard-coded at `run_bench.py:163`. *Remedy:* tune on a disjoint set of generated instances (trivially available from `gen_instances.py` at other seeds) and state the protocol.

16. **[MAJOR] `lns_node_budget` is untested** although it governs the proven-optimality signal driving contribution (2). *Remedy:* add it to Table `sensitivity`.

17. **[MINOR] §5.3 "the largest [relative gap] we record anywhere" is 4.4%, but Table `aggregate` prints 2.857%.** L679–680 vs `aggregate.tex`. Resolves itself once issue 1 is fixed.

18. **[MINOR] Table `whence` "All" row says 27 instances but the counts sum to 26.** `whence.tex`. *Remedy:* label the row "26 compared (27 listed)".

19. **[MINOR] §5.6 claims Cascade and all baselines "finish on the same value of 40" on `frb40-19-1`, but Table `quality-bhoslib` gives 39.** The convergence traces come from a different build (acknowledged at L1094–1100). *Remedy:* regenerate Figure `convergence` from the same build and seed as the main tables, or annotate the figure.

20. **[MINOR] `web-Stanford` kernelization is quoted as 0.69 s and 0.84 s ten lines apart** (L530 vs L539). *Remedy:* reconcile or state that they are different builds.

21. **[MINOR] Compiler flags understated.** §5.1 says `-O3`; `CMakeLists.txt:9` is `-O3 -march=native -funroll-loops -DNDEBUG`. *Remedy:* state the true flags and whether baselines were built with `-march=native`; note that `-march=native` weakens the cross-machine replication.

22. **[MINOR] Maximality is claimed to be verified but is not enforced.** §4.2 L562–563; `exact.csv` has `maximal=no` rows with `verified=1`. *Remedy:* reword to "independent, and maximality is recorded", or enforce it.

23. **[MINOR] §5.6 "on two instances all five seeds return the same value"** — within the geometric/road/web set named in that sentence there is only one (`rgg18`); the second is `frb59-26-1`, from the family the sentence contrasts against. *Remedy:* reword.

24. **[MINOR] Effect-size ratios in §5.10 are slightly overstated at both ends** ("25 to 40" for 24.7–39.3; "three to five" for 3.4–5.1; "1.1 to 1.4" for 1.14–1.44). *Remedy:* quote the computed range.

25. **[MINOR] Leftover drafting artefact:** `%% TODO: tighten once the final experiments are in.` at tex L48, immediately above the abstract.

---

## 9. Recommendation with justification

**Major revision** — with the explicit warning that if the regenerated seven-solver tables do not restore a defensible aggregate advantage, the paper's framing must change rather than its numbers.

For:
- Theorem 1 and Corollary 1 (L340–371) are correct, and the region/swap relationship (L417–422) is a genuine and clean observation.
- The ablation is well designed: `no-lns` is a real control, it is decisive, and three of four results are negative and reported as such.
- The BHOSLIB complement issue (L611–619, L1170–1181) is handled correctly and documented; this alone is worth publishing.
- The paper repeatedly qualifies its own headline (§5.7 L836–847, §5.13 L1113–1130) in ways a referee would otherwise have to force.

Against:
- The published tables understate the competition by omitting two baselines, and restoring them roughly doubles Cascade's mean gap and puts FastVC first on that metric (issues 1–2).
- The principal statistical claim does not survive running the test the paper says it runs (issue 3), and survives multiple-comparison correction only against three baselines (issue 9).
- The artefact cannot be re-executed: no pinned baseline revisions, two conflicting copies of the main results, a generator whose default points at the superseded file, and a provenance table that misattributes two SNAP graphs to the authors' own tool (issues 4, 6, 7).
- The strict wins are three sizes of one self-generated construction at one seed, with margins (0.03–0.09%) of the same order as the single-seed noise on the same instances (§2.2, §3.5).

These are all fixable, and most are fixable by re-running scripts that already exist. But the volume of them means the current submission's tables cannot be taken as evidence for its abstract. I would want to see the regenerated seven-solver tables, the gap-based Wilcoxon with Holm correction, multi-seed main results, pinned baselines, and a held-out tuning protocol before recommending acceptance. An expanded Delaunay/RGG sample (10 seeds per size) plus the public DIMACS10 `delaunay_n*` graphs would move the central claim from suggestive to established, and the machinery to produce it is already in the repository.

---

## 10. Confidence and what I could not check

**High confidence** in everything recomputed from `results/*.csv` and `paper/tables/*.tex` — all 43 audit rows in §6, all Wilcoxon recomputations in §3.1, the 5-vs-7-solver aggregate in §1, the seed-study p-values, the replication rank changes, and the file-level conflicts in §5.2–5.3. These are arithmetic on shipped data and I re-derived each independently.

**High confidence** in the code-level findings (unpinned clones, unequal harness timeouts, unseeded LibMVC, the 5-element `SOLVERS` list, the SNAP whitelist), all read directly from the scripts at the cited line numbers.

**Could not check:**
- Whether the numbers *in the CSVs* reflect the runs described — I have no way to re-execute the benchmark. The audit establishes internal consistency between prose, tables and CSVs, not that the CSVs are truthful.
- The §4.2 throughput figures (1.16 s, 107 238 moves, 543 µs, 180.5 s, the queue-ordering comparison) — these appear in no shipped record and I could not corroborate or refute them.
- The correctness of the C++ implementation, the reduction rules, the dynamic-graph undo, or the clique-cover bound. I read `run_bench.py` and `CMakeLists.txt` but did not audit `src/cascade.cpp`, `src/reductions.hpp` or `src/exact.hpp` for correctness — that is outside a methodology review and I defer to the reviewer covering it. The bug described at L519–523 (a shared live-list dropping a folded vertex, causing the clique-cover bound to prune optimal solutions *while reporting optimality proven*) is candidly disclosed and is exactly the class of bug that would silently corrupt the exact sub-solve; I could not verify that the fix is complete.
- Whether the baselines were built correctly on either machine, or whether ReduMIS/OnlineMIS honour `--time_limit` as assumed.
- The mathematical proofs beyond a reading pass (Theorem 1 and Lemmas 1–3 appear sound to me, but proof-checking is another reviewer's scope).
- Figure `profile`, `seeds` and `convergence` are shipped as PDFs only; I verified the claims made *about* them from `traces.csv` and `cor_seeds60.csv` but did not inspect the rendered plots.
