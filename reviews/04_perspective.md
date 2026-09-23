# Reviewer 3 — Perspective Report

*Seat: combinatorial optimisation / mathematical programming (MIP, LNS, matheuristics). Manuscript: `paper/cascade-mis.tex` (1201 lines, 42 pages), `paper/refs.bib` (28 entries), `results/*.csv`, `src/*.cpp`. Read-only; no file under `paper/` was modified.*

---

## 1. Overall assessment

The core object of this paper is genuinely nice, and I want to say that first. Definition (1) at line 336 together with Theorem 1 (lines 340–364) says: release a subset `F` of the incumbent, admit exactly those outside vertices whose entire incumbent-neighbourhood is inside `F`, and the induced region is edge-separated from `S \ R(F)`. That is a *certified-decomposable* neighbourhood — the sub-problem is not merely "small", it is genuinely independent of the rest of the solution, so re-optimising it is unconditionally admissible and monotone with no acceptance test, no repair, no tabu memory. The engineering that follows (reductions applied *inside* the move, payload-free LIFO undo, sub-solver reuse, ~1800 moves/s) is honest, well-measured work, and Section 5.13 (lines 1110–1125) is a more candid limitations statement than I usually see.

But I cannot recommend this for *Computers & Operations Research* in its present form, and my reasons are specific to this journal rather than generic.

1. **The paper reinvents a well-established mathematical-programming construct and cites none of the literature that owns it.** A neighbourhood defined by fixing all variables outside a support and re-solving the rest exactly *is* local branching / RINS / fix-and-optimise / POPMUSIC / CMSA. `refs.bib` contains not one of Fischetti & Lodi, Danna et al., Berthold, Fischetti & Monaci, Ahuja–Ergun–Orlin–Punnen, Shaw, Pisinger & Røpke, Taillard & Voß, Blum et al., Congram et al., or Glover. Line 214 literally asserts "Large-neighbourhood search with an exactly solved sub-problem is a standard metaheuristic pattern" **with no citation at all**. For COR this is not a bibliographic nicety; it is the difference between a contribution and a rediscovery. (§2)

2. **The five per-family quality tables, the aggregate table and the budget table were generated over five solvers, not seven.** `scripts/make_tables.py:9–11` hard-codes `SOLVERS` without `numvc` and `fastvc`. The data exist in `results/cor_main60.csv`. Consequence: on five instances the tables bold the wrong solver as "best", including `frb45-21-1` where **Cascade's 43 is bolded as best although NuMVC and FastVC both return 45** — a value the text itself concedes at line 676. And the aggregate table's headline (Cascade mean gap 0.414%) becomes **0.785%** when computed against the true seven-solver best, while **FastVC, omitted from the table, has the lowest mean relative gap of any solver on this benchmark at 0.340%**. This is a [CRITICAL] correctness-of-presentation defect. (§7, items 6–8)

3. **The paper's own causal story fails its own data.** The claimed regime is "advantage where the kernel stays large" (line 1120). I recomputed kernel fraction (from the `kernel=` notes on the NearLinear rows) against relative margin over the best baseline. Over the 20 sparse instances the Spearman correlation is +0.368, and it is carried entirely by the three Delaunay graphs: the second-largest kernel fraction in the whole sparse benchmark is `soc-pokec` at 0.53, **where Cascade loses by 0.062%**. Remove the three self-generated Delaunay instances and the mechanism has no support left. (§5)

4. **Unweighted-only, with a one-sentence hand-wave at MWIS** (lines 1141–1144) that is true of the *theorem* and false of the *method*. (§3)

5. **No "so what" is delivered.** Four applications are named at lines 97–109 and none reappears. A 0.08% margin on one self-generated family does not, on the evidence given, change any decision in scheduling, wireless scheduling, map labelling or entity resolution. (§4)

**Recommendation: Major revision.** The construct deserves publication; this framing of it does not. Everything I ask for is achievable without new theory.

---

## 2. The OR / mathematical-programming connection (and what is missing)

### 2.1 What the region move is, in MIP language

Write the natural node-packing model: maximise `Σ x_v` subject to `x_u + x_v ≤ 1` for all `uv ∈ E`, `x ∈ {0,1}^V`. Let `x̄` be the incumbent. The region move does exactly this:

- fix `x_v = x̄_v` for every `v ∉ R(F)`;
- solve the residual problem over `R(F)` to proven optimality;
- accept, always.

That is a **variable-fixing neighbourhood around an incumbent**, which is the defining pattern of a whole subfield of mathematical programming. Specifically:

| Construct | Reference | Relation to the region move |
|---|---|---|
| **Local branching** | Fischetti & Lodi, *Math. Prog.* 98:23–47, 2003 | Defines a neighbourhood by a Hamming-distance constraint around `x̄` and solves it with the MIP solver itself. The region move is the *asymmetric, support-restricted* version: it bounds the number of 1s **removed** (`|F| = k`) and leaves additions free — precisely Fischetti & Lodi's asymmetric local-branching constraint `Σ_{v: x̄_v=1}(1 − x_v) ≤ k` for binary problems with a one-sided structure. This is the closest ancestor and it is uncited. |
| **RINS** | Danna, Rothberg, Le Pape, *Math. Prog.* 102:71–90, 2005 | Fix the variables on which incumbent and relaxation agree; re-solve the rest as a sub-MIP. Same fix-and-re-solve skeleton. |
| **RENS** | Berthold, *Math. Prog. Computation* 6:33–54, 2014 | Sub-MIP restricted to the rounding neighbourhood of the LP solution. Directly relevant because the paper's LP rule (Nemhauser–Trotter, line 264) is exactly the half-integral relaxation RENS would round. |
| **Proximity search** | Fischetti & Monaci, *J. Heuristics* 20:709–731, 2014 | Replaces the objective by a proximity term to `x̄` and re-solves. |
| **VLSN** | Ahuja, Ergun, Orlin, Punnen, *Discrete Appl. Math.* 123:75–102, 2002 | The survey that names the class "neighbourhoods too large to enumerate, searched by an exact algorithm". The paper's contribution is a VLSN and should say so. |
| **LNS** | Shaw, *CP* 1998; Pisinger & Røpke, *Handbook of Metaheuristics*, 2010 | Destroy-and-repair with an exact repair. The paper's title uses "large-neighbourhood search" and cites neither. |
| **POPMUSIC** | Taillard & Voß, in *Essays and Surveys in Metaheuristics*, 2002 | This is the uncomfortable one. POPMUSIC: decompose the incumbent into parts; maintain a **worklist of unoptimised seed parts**; build a sub-problem from a seed and its `r` nearest parts; solve it exactly; **if it improves, push the touched parts back on the worklist**; stop when the list empties. Compare Algorithm 1, lines 452–462, which is the same loop verbatim. A COR reader will recognise it immediately. |
| **CMSA** | Blum, Pinacho, López-Ibáñez, Lozano, ***Computers & Operations Research* 68:75–88, 2016** | Construct–Merge–Solve–Adapt: build a reduced sub-instance and solve it exactly inside a heuristic loop. Published in this journal. |
| **Fix-and-optimise** | Helber & Sahling, *Int. J. Prod. Econ.* 123:247–256, 2010 | The lot-sizing community's name for the identical operator. |
| **Kernel search** | Angelelli, Mansini, Speranza, ***Computers & Operations Research* 37:2017–2026, 2010** | Must be cited if only to disambiguate: this paper uses "kernel" in the parameterized-complexity sense throughout, and a COR reader's first association with "kernel" + "restricted sub-problem solved exactly" is Kernel Search. The clash needs one sentence. |
| **Dynasearch** | Congram, Potts, van de Velde, *INFORMS J. Computing* 14:52–67, 2002 | The canonical precedent for *"independent compound moves can be combined because they do not interact."* Theorem 1(a)–(b) is a node-packing analogue of the dynasearch independence condition. |
| **Ejection chains** | Glover, *Discrete Appl. Math.* 65:223–253, 1996 | Release a set, let the vacancy propagate, re-fill. The `R(F)` construction is an ejection *tree* of depth one. |
| **VNS** | Hansen & Mladenović, *EJOR* 130:449–467, 2001; Røpke & Pisinger, *Transp. Sci.* 40:455–472, 2006 | The paper's contribution 2 — "an online rule for the neighbourhood size" (lines 149–152, 479–486) — is a shaking-radius schedule / adaptive LNS. Halve on failure, double on stagnation is a textbook multiplicative-increase/multiplicative-decrease schedule. It is fine to use it; it is not fine to claim it as a contribution without citing the literature that established it. |

### 2.2 Why this matters *for COR specifically*

COR's readership is mathematical programming and metaheuristics. A submission whose central operator is "fix outside the support, re-solve exactly" and whose bibliography contains **zero** MIP-neighbourhood references will read, to this readership, as a graph-algorithm-engineering paper that has not looked over the fence. The "Positioning" paragraph (lines 214–227) makes three novelty claims:

- *"the region is defined from the incumbent rather than from graph distance, and is provably separated from it, so the move is unconditionally admissible and monotone"* — **claim 1 is the only one I accept as novel**, and even then "defined from the incumbent" is precisely what local branching and RINS do. What is genuinely new is the *provable separation*: local branching gives a bound on how far you move, not a guarantee that the sub-problem is independent. That guarantee is the paper's real contribution and it should be stated **in contrast to** local branching, not in a vacuum.
- *"the data reduction rules are used inside the move"* — this is presolve-inside-the-sub-MIP, which every modern sub-MIP heuristic does. What is new is that the *problem-specific* MIS reductions are strong enough to make it a 500 µs operation. Say that.
- *"the neighbourhood size is not a parameter but a quantity inferred at run time"* — adaptive LNS (Røpke & Pisinger 2006). Not novel.

**What I want in the revision.** A "Relation to neighbourhood search in mathematical programming" subsection (about one page), which (a) writes the region move as a variable-fixing restriction of the node-packing MIP, (b) states the asymmetric local-branching constraint it corresponds to, (c) states precisely what the separation theorem buys that local branching does not — *the sub-problem's optimum is the global optimum restricted to that support, so no acceptance criterion is needed and the move is monotone by construction*, which local branching does **not** give — and (d) cites the table above. Done properly this *strengthens* the paper: "we exhibit a combinatorial structure under which the local-branching neighbourhood is exactly decomposable" is a far better COR contribution than "we propose a neighbourhood".

### 2.3 A second, smaller MP gap: the IP baseline is a straw man

Section 5.10 (lines 901–947) runs HiGHS on the edge formulation (`tools/ilp_baseline.py` confirms: one variable per vertex, one constraint per edge, no clique constraints, no warm start, no cuts) and concludes at line 933 that *"the integer-programming route is not a usable baseline at this scale"*. No MP reviewer will accept that. The edge formulation has an LP bound of `n/2` and is known to be the weakest possible model. Missing:

- **Padberg, *Math. Prog.* 5:199–215, 1973** — clique and odd-hole facets of the set-packing polytope. Replacing edge constraints by a clique-cover partition is a two-line change and typically cuts the root gap by an order of magnitude.
- **Nemhauser & Sigismondi, *J. Oper. Res. Soc.* 43:443–457, 1992** — node packing by cutting planes.
- **Rebennack, Reinelt, Pardalos, *Int. Trans. Oper. Res.* 19:161–199, 2012** — the branch-and-cut tutorial for maximum stable set; and Rebennack et al., *J. Comb. Optim.* 21:434–457, 2011.
- **Balas & Yu, *SIAM J. Comput.* 15:1054–1068, 1986**; **Warrier, Wilhelm, Warren, Hicks, *Networks* 46:198–209, 2005** (branch-and-price).
- **Wu & Hao, *EJOR* 242:693–709, 2015** — the maximum-clique algorithm review. Its absence from a COR MIS paper is conspicuous.

Also at lines 940–944 the paper observes HiGHS reporting optimality at 22 253 when 22 255 is proven optimal, and concludes *"we therefore treat its optimality claims as unreliable"*. That inference is not safe. The far more likely explanation is on the authors' side: `ilp_baseline.py` extracts the solution with `x > 0.5` from `getSolution()` without checking the model status path or integrality tolerances, and `read_edges` renumbers only the vertices that appear in an edge, silently dropping isolated vertices — which the appendix (lines 1160–1166) says are deliberately retained everywhere else. Two isolated/degree-anomalous vertices going missing is exactly a two-vertex shortfall. Either debug it or withdraw the accusation; publicly impugning a named open-source solver on this evidence is not acceptable.

**Minimum acceptable fix for §5.10:** re-run with a clique-cover formulation, feed the Cascade incumbent as a MIP start, and report the *dual bound*. The dual bound is what the paper actually needs and never reports — with it, the 0.08% margin on `del20` could be contextualised as a fraction of the remaining optimality gap, which would be a genuinely useful statement.

---

## 3. Generalisability beyond unweighted MIS

### 3.1 What the theory actually gives

Theorem 1(a) and 1(b) are purely structural — they mention neither cardinality nor weight — so they hold verbatim for any objective. Theorem 1(c) and Corollary 2 need `w(F) ≤ w(T*)`, which follows because `F` is feasible in `G[R(F)]`. So **yes, the theory carries to MWIS, and more generally to any separable-objective packing problem.** The conclusion's claim (lines 1141–1144) is correct *as far as the theorem goes*.

The trouble is that the theorem is not what makes the method work. Line 138 is explicit: *"What makes this affordable is the reduction rules themselves."* And the reduction rules do **not** carry over verbatim:

| Rule (Table 1, lines 253–266) | Weighted status |
|---|---|
| Degree-0 | carries |
| Degree-1 | needs `w(v) ≥ w(u)`; otherwise fails |
| Simplicial | needs `w(v) ≥ max_{u ∈ N(v)} w(u)`; the general weighted case requires the much weaker "simplicial with weight" variant |
| Degree-2 fold | the weighted fold introduces a *weighted* meta-vertex and only applies under weight inequalities (Lamm et al. 2019; Xiao et al. 2021) |
| Twin | substantially restricted |
| Domination | needs `w(u) ≥ w(v)` |
| Unconfined | **no accepted weighted analogue**; this is well known in the MWIS literature |
| LP / Nemhauser–Trotter | the weighted LP is half-integral, but the persistency argument and the bipartite-matching implementation both change |

Empirically, weighted kernels are *much* larger than unweighted ones on the same graphs — which the MWIS papers the authors already cite (`lamm2019`, `xiaowww2021`, `grossmann2023`) report. Since the whole cost model ("collapse a region of thousands of vertices to a kernel of a few dozen", line 59) depends on the reductions being ferocious, a weaker weighted rule set could easily make the move an order of magnitude more expensive and destroy the 1800 moves/s that the paper says is the point (line 60). **The claim "carry over verbatim" (line 1141) is therefore misleading and must be reworded.**

Also: `src/graph.cpp:123–129` *rejects weighted METIS files outright*. The implementation has no weighted path at all. The conclusion should not imply otherwise.

### 3.2 The other targets

- **MWIS.** This is where the applied interest is, and where the strongest competitors now live. The paper should at minimum cite and discuss **Dong, Goldberg, Noe, Parotsidis, Resende, Spaen, "A local search algorithm for large maximum weight independent set problems" (ESA 2022 / *Math. Prog. Computation*)** — Amazon's METAMIS, developed for a real industrial MWIS workload, and built around exactly the kind of local-search-with-structure this paper proposes; and **Nogueira, Pinheiro, Subramanian, *Optimization Letters* 12:567–583, 2018** (hybrid ILS for MWIS) and **Nogueira & Pinheiro, *Computers & Operations Research* 90:232–248, 2018**. Not citing the COR-published MWIS heuristic literature in a COR submission is a problem in itself.
- **Maximum clique.** The region move does **not** transfer usefully. The complement of a sparse graph is dense, and the paper's own analysis (lines 677–682) shows the move degenerates on dense graphs. Say this explicitly rather than leaving the equivalence at line 92 to imply otherwise.
- **Set packing / node packing with general constraints.** This is the interesting one and it is free. For set packing, `R(F)` generalises immediately: release `F` columns, admit every column whose conflicts all lie in `F`. Separation holds by the identical argument. This is the generalisation that would make the paper matter to a COR audience — and it connects straight back to §2, because the general statement is *"for a binary program whose constraint matrix is a conflict structure, the asymmetric local-branching neighbourhood of radius k is exactly decomposable."*
- **Interval/conflict scheduling, frequency assignment, map labelling.** Same structure. One paragraph each would do.

### 3.3 Verdict on narrowness

Unweighted-only is a **stated limitation, not a fatal one** — *provided* the paper states it honestly. Right now it does the opposite: it claims transfer in one sentence and provides no experiment, no weighted rule discussion, and no code path. I would accept either (a) an honest scoping statement plus the set-packing generalisation worked out on paper, or (b) an MWIS experiment on the standard instances used by `lamm2019`/`grossmann2023`. (a) is enough for major revision; (b) would make it a much better paper.

---

## 4. Practical significance: the "so what" test

### 4.1 The applications never come back

Lines 97–109 name scheduling, wireless interference, map labelling / computer vision, and entity resolution. Every one of the 27 benchmark instances is a Delaunay triangulation, a random geometric graph, a road network, a SNAP social/web graph, or a Model-RB adversarial instance. **Not one is an instance of any named application.** The motivation paragraph is decoration.

Would any of them care about 0.08%? On the evidence in the paper: almost certainly not.

- **Wireless scheduling** is re-solved on a millisecond-to-second timescale; the operative metric is time-to-good-solution, and Table 11 (`longbudget`) shows Cascade needs 601 s on `del20` to beat FastVC's 604 s result by 0.1%.
- **Entity resolution / de-duplication** cares about *which* records survive and about precision/recall downstream, not about 0.08% more survivors.
- **Map labelling** is scored by human legibility; 0.08% more labels is invisible.
- **Scheduling** would be weighted anyway (see §3).

### 4.2 The regime statement exists but is buried and partly wrong

Lines 1120–1123 give a genuine regime rule: *"the region move gives a consistent advantage on graphs whose kernel stays large, it costs nothing on graphs that reduce away, and it is the wrong tool on dense graphs."* This is the most useful sentence in the paper and it is in §5.13 Threats to Validity, on page ~38, rather than in the abstract or the conclusion. Move it.

Two things are wrong with it as stated:

1. **"costs nothing on graphs that reduce away" is false on the time axis.** Lines 846–853 report that ReduMIS reaches its final value on `web-BerkStan` in 67 s and on `roadNet-CA` in 69 s, matching or beating what Cascade returns after **600 s**. That is not "costs nothing" — that is a 9× time cost for a ≤0.025% quality loss. For a practitioner this is the decisive number and the paper states it only as an aside. Rewrite as: *"on graphs that reduce away it costs up to an order of magnitude in time to reach the same value."*
2. **"advantage on graphs whose kernel stays large" is not supported by the paper's own data** — see §5 below.

### 4.3 There is no operational decision rule

A practitioner cannot act on "use it when the kernel stays large" because they do not know the kernel fraction until they have run kernelization — at which point they could equally run ReduMIS. Except: they *can*. Near-linear kernelization (already a baseline) returns a kernel in 0.2 s median (Table 10, `budget`), and `results/cor_main60.csv` records the kernel size for every instance. So the paper has everything needed for a genuinely actionable rule:

> Run near-linear kernelization (≈ 0.2 s). If `|K|/n` exceeds τ, run Cascade; otherwise run ReduMIS and stop when it converges.

Fitting τ on this benchmark and validating it on held-out instances would be a real practical contribution and would cost the authors one afternoon. As it stands, §4's answer is: **no, an applied reader cannot act on this paper.**

### 4.4 Where the practical value actually is, and the paper undersells it

The result I would put in the abstract is not 0.08%. It is **robustness**: Cascade returned a verified solution on all 27 instances; ReduMIS failed on `soc-pokec` (660 s, no solution — `cor_main60.csv`), NuMVC failed on `com-lj`, NuMVC's mean wall time under a 60 s budget is 204 s, and ReduMIS's max is 660 s (Table 10). Cascade's max is 75.0 s with zero runs over 1.5× budget. *"A reduction-based solver that always answers inside a wall-clock deadline"* is a claim an applied user would act on immediately, and it is far better supported than 0.08%. Note also that the `del20` comparison against ReduMIS is made against a ReduMIS run that took **258 s** under a 60 s budget — i.e. the headline is if anything conservative. Say so.

---

## 5. Alternative explanations for the geometric win

### 5.1 The confound set

The three strict wins are `del16`, `del18`, `del20`. Those instances are simultaneously:

- (C1) **large-kernel** (kernel/n ≈ 0.93);
- (C2) **planar** (a Delaunay triangulation of points in the plane is planar);
- (C3) **bounded degree with low degree variance** (avg 6.0, Δ = 20–22 per Table A.1);
- (C4) **generated by the authors** (`tools/gen_instances.py`, seed 1) and not byte-identical to any published instance (lines 1067–1073, 1178–1185);
- (C5) **near-regular and locally uniform** — a triangulation has a rigid local structure that random graphs do not.

The paper advances only (C1) as the explanation (lines 655–659, 1120). It offers no evidence that discriminates it from (C2)–(C5), and the argument is post-hoc: the mechanism was inferred *after* observing where the wins were.

### 5.2 The paper's own data contradicts (C1)

I extracted kernel fractions from the `kernel=` notes on the NearLinear rows of `results/cor_main60.csv` and correlated them with Cascade's relative margin over the best of the six baselines:

- Over all 21 instances with a recorded kernel: **Spearman ρ = −0.536** (wrong sign; driven by BHOSLIB, where kernel/n = 1.00 and Cascade loses).
- Over the 20 **sparse** instances (BHOSLIB excluded, which is the paper's own scoping): **Spearman ρ = +0.368**.

But look at the ordering:

| instance | kernel/n | rel. margin |
|---|---|---|
| del16 / del20 / del18 | 0.93 | **+0.034% / +0.080% / +0.093%** |
| **soc-pokec** | **0.53** | **−0.062%** |
| roadNet-CA / -PA | 0.30 / 0.28 | 0.000% / −0.000% |
| rgg16/18/20 | 0.15 | 0.000% |
| web-Stanford / -BerkStan | 0.09 / 0.08 | −0.009% / −0.025% |
| everything else | ≤ 0.01 | 0.000% |

The +0.368 is produced **entirely by the three Delaunay instances**. The *second*-largest kernel fraction in the sparse benchmark, `soc-pokec` at 0.53, is a **loss**. Delete the three self-generated Delaunay graphs and the "large kernel ⇒ advantage" hypothesis has zero support and one counterexample.

So: the mechanism has **n = 1 family**, and that family is the one the authors generated. This is the single most serious scientific weakness in the paper, more serious than the narrowness the authors themselves confess at line 1110 — because they confess the narrowness of the *result* while continuing to assert the *mechanism* as established.

### 5.3 Could it be tuning?

Partly, and the paper cannot rule it out. `restart_idle_dives` is reported (lines 884–891) as the one sensitive parameter, and it was tuned on `del18` — a member of the winning family. The baselines were run at their authors' defaults. Tuning one solver's most sensitive parameter on the family where it wins, against untuned baselines, on instances you generated, is a configuration that a referee has to flag. The effect size reported (0.081% on `del18`) is **the same order as the entire winning margin (0.093%)**. That is not a footnote; it is a plausible complete explanation.

### 5.4 The experiments that would distinguish these

In rough order of value per unit of effort:

1. **[Decisive, and cheap] Run the public DIMACS10 `delaunay_n16`…`delaunay_n20` instances.** They exist, they are archived, they are the same family, and they are *not* generated by the authors. This removes (C4) entirely and costs one benchmark run. That the paper instead generates its own Delaunay graphs, and then confesses at lines 1069–1073 that its numbers are therefore incomparable with prior work, is a self-inflicted wound. **I regard this as mandatory.**
2. **[Decisive for (C2) vs (C1)] Random regular graphs, `d = 3, 4, 6`, at n = 2^16, 2^18, 2^20.** Sparse, bounded degree, near-100% kernel, **non-planar**, non-geometric, with a published generator. If the margin survives, (C1) is the mechanism and (C2)/(C5) are out. If it vanishes, the story is geometric structure, not kernel size.
3. **[Decisive for (C1) as stated] Sparse Erdős–Rényi `G(n, m)` at average degree 6, n = 10^6.** Large kernel, unbounded-ish degree, no geometry. Same test, different direction.
4. **[Addresses (C3)/(C5)] 2D and 3D FEM meshes from the Walshaw / DIMACS10 collections** (`144`, `m14b`, `auto`, `luxembourg_osm`). Planar-ish, bounded degree, large kernel, publicly archived, and actually used by practitioners.
5. **[Addresses tuning] Re-tune the one sensitive parameter on a held-out family** (or use a fixed protocol such as irace on instances disjoint from the test set) and report the margin under the held-out setting. Alternatively, run the baselines under a comparable tuning budget.
6. **[Addresses the mechanism directly] Plot relative margin against kernel/n across a designed sweep.** The authors already have this data for 21 instances; with (1)–(4) added they would have 40+, and a monotone trend would turn a post-hoc story into evidence. Right now the sweep is missing and, as computed above, the existing 20 points do not carry it.
7. **[Instrumentation] Report the realised distribution of `|F|` and `|R(F)|` per family, and the fraction of moves that improve.** The claim is that Delaunay is where "a move that restructures tens of vertices at once has the most to work with" (line 659). That is directly measurable and never measured. If the improving-move rate on Delaunay is 10× that on `soc-pokec` at comparable kernel fractions, the mechanism claim becomes empirical.

---

## 6. Framing, structure and honesty of the narrative

### 6.1 Structure

42 pages with 6 sections and a 12-subsection Section 5 (Setup, Instances, Solution quality, Aggregate, Seed study, Convergence, Long budget, Sensitivity, Exact solvers, Ablation, Replication, Threats). The *content* of those twelve is good — I would not cut the replication study or the threats section, and the sensitivity study is better than most. But the reader has no map. Concretely:

- Sections 5.3–5.8 tell the story three times (per-family tables → aggregate → profile → seed → convergence → long budget) before the reader learns in 5.13 what the defensible claim actually is.
- **Move the regime statement (lines 1120–1123) to the end of §1 and to the abstract.** Tell the reader in the first page what the method is for.
- Merge 5.4 (aggregate) and the performance profile; they are the same comparison twice, and the paper spends two paragraphs (lines 690–703, 726–740) apologising for the profile's scale sensitivity. Either fix the metric (use absolute margins plus a rank test) or drop the profile.
- Merge 5.6 (convergence) and 5.7 (long budget). They answer one question.
- §4.2 "Data structures and throughput" (lines 501–563) is 60 lines of excellent engineering detail, of which the counting-sort queue-ordering result (lines 538–551: 3.5× on 4M vertices) is arguably a more transferable finding than the region move. It is buried. Promote it or move it to an appendix — it should not sit in the middle unmarked.

### 6.2 The abstract

**363 words.** COR's guidance is far shorter. It also spends its first three sentences on the state of the art before reaching the contribution, and then packs in `+0.08%`, `three/thirteen/eleven`, `0.06%`, `one or two vertices`, a Wilcoxon result and an ablation. It is *honest* — strikingly so, and I want to credit that; very few abstracts volunteer "behind on eleven". But it is not *readable*, and an abstract that no one finishes does not communicate the honesty it contains. Cut to ~200 words: what the neighbourhood is, what the separation theorem gives, the regime in which it helps, the regime in which it does not, and the robustness result.

**Line 48 contains `%% TODO: tighten once the final experiments are in.`** In a submitted manuscript. That must go, and its presence suggests the abstract was never revisited against the final numbers — consistent with the 16/17 discrepancy noted in §7.

### 6.3 Honesty

Mostly excellent, with three exceptions.

*Credit where due.* §5.13 (lines 1110–1125) is genuinely unusual: the authors state that their strict wins are on three instances of one family that they generated themselves, that the Wilcoxon significances come mostly from baselines degrading rather than from Cascade improving, and that no test separates them from ReduMIS. §5.7 (lines 828–840) volunteers that the +8500 headline collapses to +1550 at 10× budget. §5.11 (lines 963–983) reports three negative ablation results and calls the authors' own first design "worthless". §5.13's build-confound paragraph (lines 1093–1108) measures a confound the authors could simply have not mentioned. This is the standard I would like to see more often.

*Exception 1 — the tables do not match the text.* See §7 items 6–8. The text repeatedly says "seven solvers" while the tables show five, and the bolding is wrong on five instances. Whatever the cause, the effect is that a reader checking the text against the tables is misled in the authors' favour on exactly the instances where they lose.

*Exception 2 — the conclusion underclaims the robustness result and overclaims the MWIS transfer.* Lines 1128–1144 mention neither the "always answers inside the deadline" property (the best applied result in the paper) nor the queue-ordering speedup, and assert a weighted transfer that the code explicitly refuses to support.

*Exception 3 — the mechanism is asserted as settled.* Line 1120's "consistent advantage on graphs whose kernel stays large" is presented as an established regime; §5.2 above shows the paper's own data does not support it beyond one family.

---

## 7. Specific issues

**1. [CRITICAL] No mathematical-programming neighbourhood-search literature is cited at all.** `paper/refs.bib` (28 entries) contains none of local branching, RINS, RENS, proximity search, VLSN, LNS, POPMUSIC, CMSA, fix-and-optimise, kernel search, dynasearch, ejection chains, ALNS. Line 214 asserts the pattern is "standard" with **no citation**. *Remedy:* add the subsection described in §2.3 and the references tabulated in §2.1. For COR this is not optional.

**2. [CRITICAL] The five per-family quality tables, the aggregate table and the budget table were generated over five of the seven solvers.** Root cause: `scripts/make_tables.py:9–11` hard-codes `SOLVERS` omitting `numvc` and `fastvc`, although `results/cor_main60.csv` contains 27 rows for each. *Remedy:* regenerate all tables with all seven solvers.

**3. [CRITICAL] Consequent mis-bolding of "best value" on five instances.** Recomputed from `cor_main60.csv`:

| instance | tabulated best | true best | true winner | Cascade |
|---|---|---|---|---|
| `frb45-21-1` | 43 (**Cascade bolded**) | 45 | NuMVC, FastVC | 43 |
| `frb50-23-1` | 49 | 50 | NuMVC | 48 |
| `frb53-24-1` | 51 | 52 | NuMVC | 50 |
| `frb59-26-1` | 57 | 58 | NuMVC | 56 |
| `soc-pokec` | 789 161 (NearLinear bolded) | 789 352 | FastVC | 788 866 |

Table 5 (`quality_bhoslib`) therefore bolds Cascade as co-best on `frb45-21-1` while line 676 of the text says Cascade is *two vertices behind* there. Table 3 (`quality_social`) bolds NearLinear on `soc-pokec` while line 667 says FastVC holds the best value. *Remedy:* as item 2.

**4. [CRITICAL] The aggregate table's headline numbers are computed against a five-solver "best" and are materially wrong.** Table 6 reports Cascade mean gap 0.414%, ReduMIS 0.113%. Against the true seven-solver best: **Cascade 0.785%, ReduMIS 0.501%, and FastVC — absent from the table — 0.340%**, i.e. FastVC has the lowest mean relative gap of any solver on this benchmark. `#best` also changes (Cascade 17 → 16, matching the 16 quoted at line 730 and the 3+13 of the abstract, so the abstract and §5.4 are right and the table is wrong). *Remedy:* regenerate; and add one paragraph reconciling the two views honestly — Cascade attains the best value on more instances (16 vs 11) while FastVC has the smaller mean relative gap, because Cascade's losses concentrate on the small-optimum BHOSLIB instances where a two-vertex loss is 4.4%. Both facts belong in the paper.

**5. [MAJOR] The mechanism claim is not supported by the paper's own data.** Line 1120's "consistent advantage on graphs whose kernel stays large": over 20 sparse instances the kernel-fraction/margin Spearman is +0.368, carried entirely by the three self-generated Delaunay graphs, and the next-highest kernel fraction (`soc-pokec`, 0.53) is a loss. *Remedy:* the experiments in §5.4, at minimum items 1 and 2; and until then, restate the mechanism as a hypothesis.

**6. [MAJOR] The only strict wins are on instances the authors generated, and a public version of the same family exists.** Lines 1113–1115 and 1178–1185. DIMACS10 ships `delaunay_n10`–`delaunay_n24`. *Remedy:* run them. The paper's own caveat that its numbers are incomparable with prior work (lines 1069–1073) is then unnecessary, and the strongest objection to the paper disappears.

**7. [MAJOR] The weighted-transfer claim is overstated and contradicted by the implementation.** Line 1141: "carry over verbatim". True of Theorem 1; false of the reduction rules (degree-1, simplicial, fold, twin, domination all acquire weight conditions; *unconfined has no accepted weighted analogue*), which is where the paper says the affordability comes from (line 138). `src/graph.cpp:123–129` rejects weighted input outright. *Remedy:* rewrite as "Theorem 1 carries over; the reduction rules that make the move affordable do not, and whether the sub-solve stays sub-millisecond under the weaker weighted rule set is an open question" — and cite `lamm2019`, `xiaowww2021`, `grossmann2023` for that specific point, plus Dong et al. (METAMIS) and the COR-published MWIS heuristics of Nogueira et al.

**8. [MAJOR] The IP baseline uses the weakest available formulation and then generalises from it.** `tools/ilp_baseline.py`: edge formulation, no clique cover, no warm start, no cuts, and `read_edges` drops isolated vertices (contradicting the normalisation stated at lines 1160–1166). Line 933 then concludes the IP route "is not usable at this scale". *Remedy:* clique-cover formulation, MIP start from the incumbent, report the dual bound; cite Padberg 1973, Nemhauser & Sigismondi 1992, Rebennack et al. 2011/2012.

**9. [MAJOR] The HiGHS "unreliable optimality" accusation (lines 940–944) is more likely a bug in the authors' harness.** See §2.3. *Remedy:* investigate the isolated-vertex drop; if confirmed, withdraw the claim.

**10. [MAJOR] No compute or energy reporting.** Grepping the manuscript for `energy|carbon|CO2|joule|watt|CPU hour|core hour` returns **nothing**. A study of this size (27 instances × 7 solvers × {60 s, 600 s} + 5 seeds × 10 instances + 4 ablations × 7 + a 25-instance replication + a sensitivity sweep) is on the order of several hundred core-hours. COR increasingly expects this. *Remedy:* one paragraph in §5.1 with total core-hours and the platform; optionally an estimate in kWh/CO2e.

**11. [MAJOR] The applications in §1 are never revisited.** Lines 97–109. *Remedy:* either run one instance from a named application (an entity-resolution conflict graph or a map-labelling instance would be easy to obtain) or reframe §1 to motivate by graph class rather than by application.

**12. [MAJOR] `soc-pokec-relationships` and `com-lj` are labelled "generated‡" in Table A.1** (`paper/tables/provenance.tex`), i.e. produced by `tools/gen_instances.py` at seed 1, while lines 606–608 and 1178–1185 say only the geometric family is generated and the CSV family field calls both `social`. Given that "the only wins are on self-generated instances" is already the paper's most exposed flank, a provenance table that appears to say two more large instances are also self-generated is a serious problem. *Remedy:* fix the table (presumably a fall-through default in the generator script), and state in §5.2 exactly which files were downloaded and from which archive snapshot.

**13. [MINOR/MAJOR] Three different values are reported for the same runs.** `del18`: 82 656 (Table 2), 82 661 (Table 12, ablation "full"), 82 662 (`results/summary.md`). `frb40-19-1`: 39 (Table 5 and `cor_main60.csv`), 40 (Table 12 "full", `summary.md`, and line 798 "All three solvers finish on the same value of 40"). `del16`: 20 647 / 20 648 / 20 650. Lines 957–959 explain the ablation runs are separate, which covers the ablation table, but not `summary.md` or line 798. *Remedy:* state which CSV is authoritative for the paper and regenerate everything from it; note that line 798's claim rests on a value the main table contradicts.

**14. [MINOR] The "decision-space move" ablated in Table 12 is never defined.** Line 955 says "the decision-space move described in Section~\ref{sec:move}"; Section 3 (lines 331–422) contains no such description. It is one of the paper's more interesting negative results (lines 967–975) and the reader cannot evaluate it. *Remedy:* define it, in two sentences, in §3.

**15. [MINOR] `%% TODO: tighten once the final experiments are in.`** — `cascade-mis.tex:48`, inside the abstract.

**16. [MINOR] Abstract is 363 words** and opens on prior work. *Remedy:* ~200 words; lead with the separation property and the regime statement (see §6.2).

**17. [MINOR] The adaptive-`k` rule is claimed as contribution 2** (lines 149–152) without reference to adaptive LNS or VNS shaking schedules. *Remedy:* cite Røpke & Pisinger 2006 and Hansen & Mladenović 2001, and reframe the contribution as "the *signal* used to adapt — proven optimality of the sub-solve — is problem-specific and parameter-free", which is a defensible narrower claim.

**18. [MINOR] The `del20` ReduMIS comparison is made against an over-budget run.** `cor_main60.csv` records ReduMIS at 258.2 s on `del20` under a 60 s budget (Cascade 61.1 s). This is *favourable* to the authors and should be stated: the +8500 is measured against a baseline that took 4× the budget. Table 10 shows ReduMIS max 660.2 s and 2 runs over 1.5× budget, but the text (line 741) criticises only NuMVC for overrunning.

**19. [MINOR] "costs nothing on graphs that reduce away" (line 1121) is false on the time axis** — lines 846–853 give ReduMIS 67 s / 69 s against Cascade's 600 s for the same or better value. *Remedy:* restate as a time cost.

**20. [MINOR] Section 5 has 12 subsections with no roadmap.** See §6.1 for the specific merges I would make.

**21. [MINOR] "kernel" is used in the parameterized-complexity sense throughout** and will collide with Kernel Search (Angelelli et al., *COR* 2010) for this readership. *Remedy:* one disambiguating sentence in §2.

**22. [MINOR/positive] The BHOSLIB complement issue (lines 617–630, 1167–1177) is a genuine service to the community** and should be flagged more prominently — it belongs in the abstract or the introduction, not only in §5.2 and an appendix. Several published comparisons are likely affected.

---

## 8. Recommendation with justification

**Major revision.**

*Why not reject.* Theorem 1 is a real result: an exactly decomposable neighbourhood, with a clean proof, for a problem where such structure is not obvious. The implementation work is serious (the LIFO undo, the sub-solver reuse, the counting-sort reduction queue) and the throughput numbers — 1800 moves/s, 543 µs per move on a 262k-vertex graph — are the kind of number that makes a method usable rather than merely definable. The experimental protocol is better than most: independent verification of every solution, a hardware replication, a measured build confound, a genuine sensitivity study, and three reported negative ablations. And §5.13 is more honest about its own narrowness than the great majority of submissions I see.

*Why not accept.* For *this journal*, the paper as written would be a rediscovery announcement. A neighbourhood defined by fixing everything outside a support and re-solving exactly is the central object of a twenty-year mathematical-programming literature, and the manuscript cites none of it — including two directly relevant papers published in *Computers & Operations Research* itself (Blum et al. 2016 on CMSA; Angelelli et al. 2010 on kernel search). Separately, the tables do not agree with the text on which solver won, in a direction that flatters the authors on exactly the instances where they lose; the mechanism the paper proposes is contradicted by the paper's own kernel-fraction data once the three self-generated Delaunay instances are removed; and the practical claim rests on a 0.08% margin on a family the authors generated when a public version of that same family exists.

*What a revision must contain.*

1. A "Relation to MIP neighbourhood search" subsection positioning the region move against local branching / RINS / VLSN / POPMUSIC / CMSA, and stating precisely what the separation theorem buys that local branching does not. **(item 1)**
2. All tables regenerated over all seven solvers, with the aggregate figures corrected and the Cascade-vs-FastVC divergence between `#best` and mean gap discussed. **(items 2–4)**
3. The public DIMACS10 Delaunay instances, so that the strict wins are not confined to self-generated data. **(item 6)**
4. At least one non-planar large-kernel family (random regular or sparse ER) to separate kernel size from geometry. **(item 5)**
5. An honest MWIS statement — theorem transfers, rules do not — plus the MWIS literature including the COR-published work. **(item 7)**
6. The regime statement moved to the abstract/introduction, restated to include the time cost. **(items 19, 20)**
7. The IP baseline redone on a clique-cover formulation with a MIP start and a reported dual bound, and the HiGHS accusation resolved. **(items 8, 9)**
8. Compute reporting, provenance fix, numerical consistency, and the TODO removed. **(items 10, 12, 13, 15)**

Items 1, 2, 3, 5, 6, 8 are non-negotiable. Item 4 could be deferred to a "future work" statement if the authors explicitly downgrade the mechanism claim to a hypothesis. If items 3 and 4 come back negative — the margin does not survive on public Delaunay graphs or on non-planar large-kernel graphs — the paper is still publishable, but as a paper about an exactly decomposable neighbourhood with a robustness result and a negative empirical finding, which is a different and shorter paper.

---

## 9. Confidence and limits

**High confidence:**
- The bibliographic gap. Verified by direct grep over `paper/refs.bib` and the manuscript: zero occurrences of `local branching`, `RINS`, `proximity`, `matheuristic`, `VLSN`, `very large`, `column generation`, `set packing`, `cutting plane`, `polyhedr`, `facet`. Line 214 is uncited. The named references are ones I can state from memory with their venues; the authors should verify exact page numbers.
- The five-vs-seven-solver table defect. Verified at source: `scripts/make_tables.py:9–11`, cross-checked against `results/cor_main60.csv`, and the five mis-bolded instances recomputed.
- The corrected aggregate figures (Cascade 0.785%, ReduMIS 0.501%, FastVC 0.340%). Recomputed from `cor_main60.csv` using the gap definition in the Table 6 caption.
- The kernel-fraction correlation (ρ = +0.368 sparse, −0.536 overall). Recomputed from the `kernel=` notes in `cor_main60.csv`.
- That the implementation is unweighted-only (`src/graph.cpp:123–129`) and that the IP model is the plain edge formulation (`tools/ilp_baseline.py`).

**Medium confidence:**
- That the Delaunay win is a kernel-fraction effect rather than a planarity or generator effect. I have shown the paper does not distinguish these; I have *not* shown which is true.
- That a weighted rule set would degrade the move's affordability. This follows from what is known about weighted reductions, but I have not measured it.
- That the HiGHS discrepancy is the authors' isolated-vertex handling. This is the likeliest explanation given `read_edges`, not a verified diagnosis.

**Limits of this review:**
- I did not audit the proofs of Theorem 1, Corollary 2 or Proposition 3 line by line beyond checking that the arguments are structurally sound; another seat covers correctness.
- I did not verify the Wilcoxon computations in `scripts/stats_test.py`, the seed study, or the replication tables in detail. I note only that the Wilcoxon table *does* include NuMVC and FastVC while the quality tables do not, which is itself an inconsistency worth the statistics seat's attention.
- I could not check whether the DIMACS10 Delaunay instances are still reachable, nor whether `https://github.com/vinhqdang/max_independence_set` (line 1148) is public; the repository as supplied is BSD-3-Clause with a build script and a verifier, which is good practice.
- My literature claims are made from memory of the field. Every reference in §2 is one I am confident exists and is correctly attributed; exact page and volume numbers should be checked against the sources before the authors cite them.
- I reviewed only the LaTeX source, the bibliography, the generated tables, the result CSVs and the solver sources. I did not read the compiled PDF's figures.
