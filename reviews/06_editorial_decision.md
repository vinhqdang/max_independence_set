# Editorial Decision Letter

**Manuscript:** Exact Large-Neighbourhood Search for the Maximum Independent Set
Problem on Massive Sparse Graphs
**Venue:** Computers & Operations Research
**Panel:** five role-separated seats, each committing without sight of the others,
plus an editorial synthesis. Every finding repeated below was re-verified by the
editor against the raw data, the generator scripts or the primary literature.

## Decision: **Reject**, with a clear route back

The seats split 3-1-1: Major Revision (Journal-Fit, "bordering reject"),
Major Revision (Methodology, "bordering reject-and-resubmit"), Major Revision
(Devil's Advocate, conditional on one experiment), Reject (Domain). The editor
adjudicates to Reject, on one ground that no revision of this manuscript can
repair: **the central construction is published prior art.** Everything else in
this letter is fixable and much of it is fixable cheaply.

---

## 1. The decisive finding: the region move is not new

The Domain seat identified, and the editor confirmed against the source PDF:

> J. Borowitz, E. Grossmann, C. Schulz. *Optimal Neighborhood Exploration for
> Dynamic Independent Sets.* ALENEX 2025 (arXiv:2407.06912, July 2024).

Their construction, quoted verbatim:

> "Let $u \in V \setminus I$ and $A \subset I$. We say $u$ is **tight** to $A$ if
> $A = N(u) \cap I$. The definition is motivated by the fact that $u$ can always
> join $I$ if we remove $A$ from it."

> "...it is possible that the improved independent set in $G$ is not maximal even
> if the solution in $G[H]$ has been optimal. **We fix this by adding nodes in
> $N_G(H) \setminus H$ for which all adjacent independent set nodes are in $H$**,
> i.e. we add the $H$ tight nodes from $N(H) \setminus H$ to our subproblem."

This is $R(F) = F \cup \{u \notin S : N(u) \cap S \subseteq F\}$, with the same
motivation the manuscript gives for Theorem 1. They solve the subproblem with
KaMIS branch-and-reduce, which "applies a wide range of data reductions to the
input instance exhaustively" — the manuscript's second claimed delta, reductions
inside the move. They cap subproblem size with a parameter $\nu_{max}$.

The work is by the group that wrote ReduMIS, the manuscript's own primary
baseline. It is not cited. The manuscript's newest reference is 2023.

**What survives.** ONE is a *fully dynamic* algorithm, triggered on edge
insertion. This manuscript applies the construction as a *static* LNS operator
and adapts $|F|$ online against observed sub-solve optimality, where ONE uses a
fixed $\nu_{max}$. That is a real but secondary difference. It cannot be
presented as "we propose a neighbourhood that is solved exactly rather than
sampled" (abstract), and Theorem 1 cannot be presented as new.

Separately, the claim that larger $F$ "yields moves that no swap-based
neighbourhood expresses" is false: a region move with $|F| = j$ is the best
$(j,k)$-swap over all $k$. The manuscript's own citation `lamm2017` states that
Andrade et al. introduced $(j,k)$-swaps.

## 2. The results pipeline is broken, independently of novelty

Four of the five seats found this independently; the editor reproduced it.

`scripts/make_tables.py:145` defaults to `--main heuristic.csv` while every
other generator defaults to `cor_main60.csv`; and `make_tables.py:9-11`
hardcodes a five-solver list. **NuMVC and FastVC therefore appear in none of the
five quality tables, the aggregate table, or the budget table** — while the
prose, the abstract, the Wilcoxon table, the appendix and the figures all use
seven.

Recomputed over all seven solvers:

| | as printed | true |
|---|---|---|
| Cascade mean gap | 0.414% | **0.785%** |
| Cascade max gap | 2.857% | **4.444%** |
| Cascade #best | 17 | **16** |
| ReduMIS mean gap | 0.113% | **0.501%** |
| FastVC mean gap | *absent* | **0.340% — best of any solver** |

The aggregate table's caption defines the gap against "best found by any
algorithm". That is false: it is the best of five. On its own headline
statistic the method is third of seven, and the omitted table is the one that
would put a baseline on top. Consequences include bolding Cascade's 43 on
`frb45-21-1` as best when NuMVC and FastVC both returned 45 — which the
surrounding text itself concedes.

## 3. The statistical claim does not survive its own stated method

The abstract and the threats section both say the Wilcoxon test is computed
"over relative gaps". `scripts/stats_test.py:69` runs it on **raw vertex
counts**, so the signed-rank statistic is dominated by the largest instances —
precisely the bias the aggregate-comparison section says the test is there to
remove.

| baseline | p, raw sizes (as published) | Holm-corrected | p, relative gaps |
|---|---|---|---|
| OnlineMIS | 0.00001 | sig | sig |
| LinearTime | 0.00003 | sig | sig |
| NearLinear | 0.00014 | sig | sig |
| NuMVC | 0.00079 | sig | **0.155 — n.s.** |
| FastVC | 0.030 | **0.060 — n.s.** | **0.441 — n.s.** |
| ReduMIS | 0.195 | n.s. | n.s. |

"Significantly ahead of five of the six baselines, including both solvers from
the vertex cover local search line" holds only uncorrected and only on raw
sizes. Under the paper's *stated* test it is three of six, and neither survivor
is from the vertex-cover line. Two of the three survivors carry `verified=0` on
all 54 of their runs, against an abstract claiming every reported solution was
independently verified.

## 4. The stated mechanism is not supported by the paper's own data

The claimed regime is "graphs whose kernel stays large". Spearman correlation
between kernel fraction and relative margin is **-0.536** across the benchmark;
the positive correlation on sparse instances is carried entirely by the three
self-generated Delaunay graphs. `soc-pokec`, the second-largest kernel fraction
in the benchmark, is a loss. BHOSLIB has 100% kernel and loses 6 of 7. The
variable that actually separates the three wins is planarity with bounded
degree, which is never mentioned.

## 5. The positive result, stated accurately

All three strict wins are on Delaunay graphs generated by the authors' own tool,
whose names collide with the public DIMACS10 `delaunay_n*` graphs that were
available and unused. The margins are +7, +77, +264 (0.034%, 0.093%, 0.080%).

Two further facts the editor verified:

- **Ablated variants beat the shipped configuration on the winning family.**
  `ablation.csv`: on `del16`, `cascade-nopert` returns 20656 against the full
  method's 20648; on `del18`, `cascade-nolp` returns 82666 against 82661. These
  deltas are the size of the headline margins. Reported nowhere.
- **Same-seed, same-configuration runs vary by as much as the margin.** `del16`
  seed 1 appears as 20647, 20647, 20648, 20648, 20650, 20654 across six result
  files — a spread of 7, equal to the reported `del16` margin.

## 6. Venue

Of 28 references, one is in an OR journal. There are zero citations to local
branching, RINS, RENS, proximity search, VLSN, LNS, POPMUSIC, CMSA or kernel
search — two of which (CMSA; kernel search) are COR's own papers — while the
introduction asserts that LNS with an exactly solved sub-problem is "a standard
metaheuristic pattern" with no citation at all. The applications paragraph, the
sole claim to OR relevance, contains no citations. NuMVC and FastVC are
attributed to "the operations research literature"; both are JAIR/IJCAI.

As submitted, JEA or ALENEX is the better fit than COR.

---

## Adjudication of the Devil's Advocate CRITICAL findings

Per panel rules each is recorded with its disposition.

| # | DA finding | Disposition |
|---|---|---|
| 1 | Main tables omit NuMVC/FastVC | **Upheld** — reproduced; root cause located at `make_tables.py:145` |
| 2 | Wilcoxon not computed on relative gaps | **Upheld** — reproduced both ways |
| 3 | `del16` win inside same-seed noise | **Partly upheld.** The cross-file spread of 7 at seed 1 is real and does undermine the margin's precision. But the DA's inference that the win is not robust is *rejected*: across 5 seeds Cascade's minimum (20642) equals FastVC's maximum, so Cascade is never worse on a paired seed. The editor substitutes a stronger finding: an ablated variant beats the shipped configuration on this instance. |
| 4 | Throughput numbers have no supporting artefact | **Upheld** — every `cascade` row carries the constant `note=maximal=yes`; no CSV records moves or timings |
| 5 | "One per family" for the 600 s study, but five families | **Upheld** — social is omitted, and contains the worst sparse loss |
| 6 | Paper loses its own headline aggregate | **Upheld** |
| 7 | Mechanism falsified by the paper's own kernel data | **Upheld**, and independently reached by the Perspective seat |
| 8 | Provenance table labels `soc-pokec`/`com-lj` as generated | **Upheld** — `make_appendix_tables.py:23-25` whitelist gap |
| 9 | "No acceptance criterion or repair step required" contradicted by Algorithm 1 | **Upheld** |
| 10 | 6 of the 13 ties are values a kernelization baseline reaches in <0.7 s | **Upheld** — editor confirms 5 of 16 top values are reached by 5+ of 7 solvers |
| 11 | Unequal wall-clock ceilings for exact solvers | **Upheld** — `run_bench.py`: VCSolver/PACE killed at 60 s, Cascade allowed 660 s |
| 12 | `del20` absent from ablation, sensitivity and convergence | **Upheld** |

## Credit where the panel was unanimous

All five seats independently noted that the manuscript's self-criticism exceeds
the field's norm, and the editor agrees. The long-budget section volunteers that
the headline margin collapses from 8500 to 1550. Three ablations are reported as
having contributed nothing. The BHOSLIB clique-versus-complement warning is a
genuine service to the community. The Devil's Advocate further found that
`heuristic.csv` contains an *earlier* run in which the method scored better on 6
of 8 differing instances, and the authors reported the later, worse run — the
opposite of run selection, and it deserves to be said plainly.

The engineering is also real: 107,238 moves in 58 s with a reduce-and-solve
inside each, payload-free LIFO undo on a twin-indexed adjacency array, and a
degree-ordered reduction queue worth 3.5x at 4M vertices. It is currently
unmeasurable from the released artefacts, which is a fixable defect, not a
fatal one.

---

## Revision roadmap

**Before anything else — correctness of the record**

1. Point `make_tables.py` at `cor_main60.csv` and restore all seven solvers.
   Regenerate every table and reconcile the prose against them.
2. Recompute the Wilcoxon on relative gaps as stated, apply a Holm correction
   across the six comparisons, and rewrite every claim that depends on it.
3. Fix the provenance whitelist so `soc-pokec` and `com-lj` are attributed to
   SNAP.
4. Resolve `cor_main60.csv` vs `heuristic.csv` and `cor_seeds60.csv` vs
   `variance.csv`; state which is authoritative and delete or archive the other.
5. Remove the `%% TODO` at line 48.

**Then — the scientific question**

6. Cite Borowitz, Grossmann & Schulz (ALENEX 2025) and reposition the
   contribution against it. The honest framing is: *the ONE neighbourhood,
   transferred from the dynamic setting to static LNS, with online adaptation of
   the freed-set size in place of a fixed cap, engineered to run two orders of
   magnitude more often.* That is a legitimate contribution. It is not "we
   propose a neighbourhood that is solved exactly rather than sampled".
7. Run the public DIMACS10 `delaunay_n16..n20`. This is cheap and it is the
   single experiment that decides whether a positive claim exists at all. Add
   random $d$-regular graphs ($d=3,4,6$) to separate kernel size from
   planarity — the mechanism claim currently has $n=1$ family.
8. Print the move counters `main.cpp` already computes, and record them, so
   section 4.2 becomes checkable.
9. Equalise the exact-solver time limits and re-run that comparison.
10. Explain, or withdraw, the ablated variants that beat the shipped
    configuration on the winning family.
11. Retune on held-out instances; `del18`, `frb40-19-1` and `web-Stanford` are
    all in the headline benchmark.

**Then — venue**

12. Either engage the OR neighbourhood-search literature properly (local
    branching, RINS, VLSN, POPMUSIC, CMSA, kernel search) and generalise to set
    packing, which transfers for free — or submit to ALENEX/JEA, where the paper
    as reframed would be a good fit.
