# Reviewer 2 — Domain Expert Report

Manuscript: *Exact Large-Neighbourhood Search for the Maximum Independent Set Problem on Massive Sparse Graphs* (`paper/cascade-mis.tex`, 1201 lines) — Computers & Operations Research.

Reviewer profile: works on MIS/MVC kernelization, the KaMIS/ReduMIS lineage, branch-and-reduce, and MVC local search (NuMVC/FastVC/NuMWVC). Read the whole manuscript, `refs.bib`, all nine table files, `results/*.csv`, and the relevant parts of `src/`.

---

## 1. Overall assessment

The manuscript is unusually well written and unusually honest about its own weaknesses — Sections 6.11 (threats) and 6.7 (long budget) do more self-criticism than most accepted papers do. The engineering is real, the verification protocol (independent re-checking of every emitted set) is above the norm for this literature, and the BHOSLIB complement-form observation in Appendix A is a genuine public service.

Nevertheless I recommend **reject**, for two independent reasons, either of which would be sufficient.

**(1) The core contribution is prior art.** The "region move" — remove a set $F$ from the incumbent $S$, add every vertex whose solution-neighbours all lie in $F$, observe that the resulting subgraph is separated from $S \setminus R(F)$, then solve it exactly with a branch-and-reduce solver that applies the reduction rules inside the subproblem — is exactly the *optimal neighborhood exploration* of Borowitz, Großmann and Schulz (ALENEX 2025; arXiv:2407.06912). Their construction, their separation property $(N_G(H)\setminus H)\cap \mathcal{I} = \emptyset$, their use of KaMIS branch-and-reduce on $G[H]$, and their subproblem-size parameter are the same objects under different names. The manuscript does not cite it. Independently, the neighbourhood itself is the $(j,k)$-swap of Andrade, Resende and Werneck (2012) — which the manuscript *does* cite, but then misdescribes (see §2).

**(2) The paper contains two mutually contradictory sets of experimental results.** The five main quality tables, the aggregate table and the budget table were generated from a stale five-solver run (`results/heuristic.csv`) and contain **no NuMVC and no FastVC rows at all**, while the abstract, the body text, the Wilcoxon table, Table `whence`, the long-budget table, the replication table, the figures and the full appendix table were generated from the seven-solver run (`results/cor_main60.csv`). The result is direct self-contradiction inside one manuscript: Table 4 bolds `Cascade`'s 43 on `frb45-21-1` as the best value of the benchmark, while the appendix table on the same instance lists `fastvc 45` and `numvc 45`, and the body text on p. ~20 says "45 against our 43". I traced the cause: `scripts/make_tables.py` defaults to `--main heuristic.csv` while every other table script defaults to `cor_main60.csv`. This is mechanically fixable, but in its current state the reader cannot tell which numbers the paper is actually claiming, and the corrected aggregate materially damages the paper's story (see §6).

---

## 2. Novelty of the region move (with explicit prior-art comparison)

### 2.1 What is claimed

Section 3 defines, for independent $S$ and $F \subseteq S$,
$$R(F) = F \cup \{u \in V\setminus S : N(u)\cap S \subseteq F\},$$
proves (Thm 1a) that no edge joins $R(F)$ to $S\setminus R(F)$, (1b) that any independent $T \subseteq R(F)$ can be substituted, and (1c) that $S\cap R(F)=F$. The positioning paragraph claims three deltas: incumbent-defined rather than distance-defined region with a separation proof; reductions used *inside* the move; online adaptation of $|F|$. The intro and the corollary after Prop. 2 assert that "larger $F$ yields moves that no swap-based neighbourhood expresses".

### 2.2 Verdict: rediscovery, not refinement

**(a) $(j,k)$-swap / $k$-improvement.** Andrade, Resende and Werneck, *Fast local search for the maximum independent set problem*, J. Heuristics 18(4):525–547, 2012, explicitly generalise swaps to $(j,k)$-swaps: remove $j$ solution vertices, insert $k$. Lamm et al. (2017), the paper's own reference `lamm2017`, states this verbatim: "Andrade et al. [2] extended the notion of swaps to $(j,k)$-swaps". ARW give a linear-time $(1,2)$-swap routine *and* an $O(m\Delta)$ routine for the $(2,3)$-swap, i.e. they already work with $|F|=2$ and the set of vertices that become free. A region move with $|F|=j$ is, by construction, the best $(j,k)$-swap at that $F$ over all $k$. The manuscript's claim that "larger $F$ yields moves that no swap-based neighbourhood expresses" is therefore **false as stated**; the honest statement is "the best $(j,k)$-swap for all $k$ simultaneously, which ARW did not implement beyond $j=2$". The Figure 1 example does not rescue the claim: it is a $(2,3)$-swap, squarely inside ARW's own definition.

**(b) The separation observation is Theorem 1 of the same lineage.** The fact that the freed-plus-newly-free set cannot interact with the retained solution is the defining invariant of any $(j,k)$-swap and is stated as such in the ARW line. Thm 1(a)–(c) are three lines of set manipulation from the definition; (c) in particular is a tautology ($x\in S\cap R(F)$, $x\notin F$ $\Rightarrow$ $x \in V\setminus S$, contradiction). I do not think this rises to a theorem in a COR paper.

**(c) Decisive prior art: optimal neighborhood exploration.** J. Borowitz, E. Großmann, C. Schulz, *Optimal Neighborhood Exploration for Dynamic Independent Sets*, ALENEX 2025, pp. 1–14 (arXiv:2407.06912, July 2024). Their construction: BFS to depth $d$ from a seed to get $H$; extend $H$ by all solution vertices adjacent to $H$; then add the "$H$-tight" vertices of $N(H)\setminus H$ — i.e. exactly the vertices all of whose solution-neighbours lie in $H$. They state the resulting property as $(N_G(H)\setminus H)\cap \mathcal{I}=\emptyset$ and observe that one may "exchange the independent set nodes of $\mathcal{I}\cap H$ in $G$ by any independent set of the node-induced subgraph". They then solve $G[H]$ with the KaMIS branch-and-reduce solver, which "applies a wide range of data reductions to the input instance exhaustively and afterwards runs a sophisticated branch-and-reduce algorithm" — i.e. **reductions applied inside the move**, the manuscript's claimed second delta. They expose a subproblem-size cap $\nu_{\max}$ and a depth $d$ as the size controls, and report that the default configuration "matches state-of-the-art performance for the cardinality independent set problem". This is the manuscript's contribution, published a year and a half before this submission, by the group whose solver is the manuscript's main baseline. It is neither cited nor compared against.

The remaining deltas after this comparison are: (i) $F$ is grown by BFS over *solution* vertices with a target count, rather than by a depth-$d$ BFS with a vertex cap — a parameterisation difference; (ii) $|F|$ is adapted online from the proved-optimal flag of the sub-solve rather than fixed — a genuine but small engineering idea; (iii) the sub-solver is the authors' own and is reused across moves rather than reconstructed. (ii) and (iii) are respectable engineering. They are not a COR-level algorithmic contribution, and the paper does not frame them as the contribution.

**(d) VLSN and LNS-with-exact-subproblem.** The generic pattern is Ahuja, Ergun, Orlin, Punnen, *A survey of very large-scale neighborhood search techniques*, Discrete Applied Mathematics 123(1–3):75–102, 2002 — specifically their category of neighbourhoods "induced by restrictions to subproblems that are solved exactly". Shaw's LNS (CP 1998) and Pisinger–Ropke are the destroy-and-repair ancestor. None are cited. For a COR submission this is a conspicuous gap: the journal's readership will recognise the pattern immediately and expect it named.

**(e) Local branching.** Fischetti and Lodi, *Local branching*, Math. Programming 98:23–47, 2003, define a neighbourhood by a Hamming-ball constraint around the incumbent and solve the sub-MIP exactly, with an explicitly proved non-degradation guarantee (the incumbent is feasible in the sub-MIP, exactly the role of Thm 1(c) here). Danna, Rothberg, Le Pape's RINS (Math. Prog. 102:71–90, 2005) is the other standard reference. The manuscript's "monotone because the incumbent restricted to the region is feasible for the sub-problem" is the local-branching argument. Not cited.

**(f) KaMIS-line LNS and block-exchange operators.** `lamm2017` (ReduMIS) already combines kernelization with an evolutionary algorithm whose combine operators exchange vertex blocks obtained from graph partitioning and separators, followed by ARW local search. The manuscript cites the paper but describes it only as "swap-based local search on the reduced graph" (Section 1), which understates it. The separator-based combine operator is closer to the region move than the manuscript admits: a separator-induced block exchange is also a provably admissible substitution of a solution fragment.

**(g) 2023–2025 KaMIS work.** Beyond ONE: CHILS (Großmann, Langedal, Schulz, *Concurrent Iterated Local Search for the MWIS Problem*, SEA 2025, LIPIcs 338, 22:1–22:20) and LearnAndReduce (arXiv:2412.14198, 2024) define the current frontier. METAMIS (Dong, Goldberg, Noe, Parotsidis, Resende, Spaen, ESA 2022; journal version *Networks*, 2025, doi:10.1002/net.22247) is the OR-community answer and is built precisely on a richer $(j,k)$-swap repertoire plus path-relinking. The manuscript's newest reference is from 2023.

**(h) Struction / increasing transformations.** `gellner2021` is cited and correctly described. The original struction (Ebenegger, Hammer, de Werra, 1984; Alexe, Hammer, Lozin, de Werra, 2003) is not, and the manuscript does not use struction inside the region — which would be the obvious way to make the claimed contribution non-trivial relative to ONE.

**Bottom line for §2.** $R(F)$ is a rediscovery. The paper must either (i) cite Borowitz–Großmann–Schulz, drop the theorem to a remark, and reposition entirely as an engineering study of *throughput* for this known move — which may be publishable, see §7 — or (ii) be withdrawn.

---

## 3. Correctness of the theory

I checked every proof line by line and cross-read them against `src/cascade.cpp` and `src/reductions.hpp`.

**Theorem 1 — correct but trivial.** (a), (b), (c) are all valid. (a) is a two-case check; (b) follows; (c) is definitional. No error. My objection is standing, not soundness.

**Corollary 2 (Monotonicity) — correct as stated, but the stated hypothesis is not what the algorithm does.** $|S'| = |S| - |F| + |T^\star| \ge |S|$ requires $T^\star$ *maximum*. Algorithm 1 line 10 calls `ExactMis(G[R])` described as "branch-and-reduce, bounded", i.e. it may time out. The manuscript never reconciles the two. The implementation does: `cascade.cpp:263` guards acceptance with `res.size >= incoming`, so a timed-out sub-solve is simply rejected and monotonicity survives. **This is correct in the code and unstated in the paper.** The abstract's unqualified "never degrades the incumbent" should be replaced by the actual invariant: *a move is applied only if the returned region solution is at least as large as the released fragment, so monotonicity holds regardless of whether the sub-solve proved optimality*. As written, a careful reader will (rightly) suspect a bug that is not there.

**Edge cases.**
- $F=\emptyset$: $R(\emptyset)=\{u\notin S: N(u)\cap S=\emptyset\}$, which is empty for maximal $S$. Benign; the code returns early (`build_region` returns false on empty `freed_`). Not discussed.
- $R(F)$ disconnected: harmless, and the sub-solver will decompose it; not discussed, and it would be worth saying that the region is typically disconnected, since that is *why* the sub-solves are cheap.
- **Maximality after a move is never discussed.** It can be shown that $S'$ stays maximal when $S$ is maximal and $T$ is maximal in $G[R(F)]$: for $u\notin S\cup R(F)$ there is $w\in N(u)\cap S$ with $w\notin F$, hence $w \in S\setminus R(F)$, which is retained. The code nevertheless runs a repair loop (`cascade.cpp:277–283`) taking every neighbour $u$ of the region with `tight_[u]==0`. That loop is needed only because a *timed-out* $T$ may be non-maximal inside the region. This should be in the paper; as it stands the reader cannot tell whether the repair loop is a patch for a hole in Theorem 1.
- **Folded vertices and lifting.** The reductions are applied to the freshly-built induced subgraph `sub` (`cascade.cpp:231–245`), not to the global dynamic graph, so degree-2 fold, twin-fold and unconfined are evaluated on $G[R(F)]$ with correct degrees. This is the right thing and matches the theory. Acceptance requires `res.solution.size() == sub.n`, i.e. the sub-solver must have lifted fold vertices all the way back to the original region indexing. Correct, but the paper's one sentence on lifting ("replays those records in reverse") is not enough given that the authors themselves report a past bug of exactly this shape — the shared-live-list bug in Section 4.2 where the clique-cover bound missed a fold vertex and "pruned optimal solutions while still reporting that optimality had been proven". If that class of bug occurred once, the paper owes the reader the regression test, not a paragraph.

**Proposition 3 (Cost of a move) — the stated bound is wrong for the implemented construction.** The proposition bounds region construction by $O(\sum_{v\in F}\deg v)$. But `build_region` (`cascade.cpp:403–426`) obtains $F$ itself by a BFS from the seed over *all* vertices, capped at `visit_cap = max(64, free_target*64)` visited vertices, expanding the full adjacency of each. On `wiki-Talk` ($\Delta = 100{,}029$) or `web-BerkStan` ($\Delta = 84{,}230$) a single hub in that BFS costs more than the whole of the claimed bound. The proposition should either bound the BFS explicitly or state that it bounds only the second phase. This matters because the throughput argument (Section 4.2) is the paper's real contribution.

**Lemma 6 (Degree-2 folding) — the proof invokes a lemma whose hypothesis it violates.** The $(\le)$ direction opens: "By Lemma~\ref{lem:simplicial} applied to the case $|N(v)|=2$ we may assume $S$ contains $v$, or contains both $u$ and $w$". Lemma 3 (simplicial) requires $N(v)$ to induce a *clique*; here $uw\notin E$ by hypothesis, so Lemma 3 does not apply. The needed argument is self-contained and one line (if $S\cap\{u,v,w\}=\emptyset$ then $S\cup\{v\}$ contradicts maximality; if $S$ contains exactly one of $u,w$, exchange it for $v$) — but as printed the proof is invalid. Please fix.

**Corollary (Relation to classical swaps)** carries no `\label` and is unreferenced; and its concluding clause ("larger $F$ yields moves no swap-based neighbourhood expresses") is the false novelty claim of §2.

**Missing: any complexity statement about the neighbourhood.** Solving $G[R(F)]$ exactly is NP-hard; finding a best $(j,k)$-swap is hard for $j\ge 2$ (Komusiewicz and Morawietz, *Finding 3-Swap-Optimal Independent Sets and Dominating Sets Is Hard*, ACM Trans. Comput. Theory, 2024/25). A VLSN paper in COR is expected to say what the neighbourhood's search complexity is; this one does not.

---

## 4. Reduction rules and their attribution

Table 1 and Lemmas 3–6 are, with the exceptions below, correct.

1. **Degree-0 / degree-1 / simplicial** — stated correctly; degree-1 is indeed the $|N(v)|=1$ case of simplicial. Lemma 3's proof is correct. No citation given; the rule is folklore, so acceptable.
2. **Degree-2 fold** — the transformation and offset are correct (Lemma 6); the proof is broken, see §3. Standard attribution is Chen–Kanj–Jia (2001) / Beigel; the table gives none while giving citations for two other rows, which reads as an implicit claim.
3. **Twin** — "$N(u)=N(v)$, $|N(u)|=3$: take both, or fold". The disjunction is correct in outline (take $u,v$ and delete $N(u)$ if $N(u)$ contains an edge; otherwise fold $u,v,N(u)$ into one vertex) but the table does not say which case is which, so as printed the rule is not reproducible from the paper. Attribution missing — this is Xiao and Nagamochi, and it enters practice through Akiba–Iwata (`akiba2016`, cited elsewhere).
4. **Domination** — correctly stated; Lemma 5's proof is correct. Attribution missing.
5. **Unconfined** — attributed to `xiao2017` only. The confining-set machinery is Xiao and Nagamochi **2013** (`xiao2013`, already in the bibliography and cited in the related-work prose). The table should cite both, and should note that the implemented test is a one-sided sound heuristic, not a decision procedure for unconfinedness.
6. **Nemhauser–Trotter LP** — correctly stated and correctly attributed; the sentence deriving it from a maximum matching in the bipartite double cover via König is correct.

**A more serious problem than any attribution: the implemented rules are capped, so what the paper calls a "kernel" is not one.** Section 2 defines "a graph on which no rule fires is called a kernel", and Section 4 reports "kernel sizes" and compares them to the literature. But `reductions.hpp:23–26` sets `max_deg_clique = 8` (the simplicial test is skipped above degree 8), `max_deg_domination = 24`, `unconfined_work = 20000` edges per test and `unconfined_max_set = 8`; `main.cpp:42–43` tightens these further for the dive (`4` and `8`). On top of that, Section 4.2 truncates kernelization at a `kernel_share` fraction of the budget (18.0 s on `soc-pokec`). The consequence is that the paper's reported kernel sizes are *upper bounds* on the true kernel under the stated rule set, and are not comparable with kernel sizes in `hespe2019` or `akiba2016`. None of the degree caps appear anywhere in the manuscript. This should be a table of implemented rule parameters in Section 2 or 4, and the word "kernel" should be qualified throughout.

---

## 5. Literature coverage and missing references

`refs.bib` has 24 entries, the newest from 2023. For a 2026 COR submission on MIS this is a 2017-era view of the field with a 2021–2023 appendix. The following are missing; the first three are, in my judgement, disqualifying omissions.

**Disqualifying**

1. J. Borowitz, E. Großmann, C. Schulz. *Optimal Neighborhood Exploration for Dynamic Independent Sets*. In Proc. SIAM Symposium on Algorithm Engineering and Experiments (ALENEX 2025), SIAM, 2025, pp. 1–14. arXiv:2407.06912. — **The contribution of this manuscript.**
2. Y. Dong, A. V. Goldberg, A. Noe, N. Parotsidis, M. G. C. Resende, Q. Spaen. *A Local Search Algorithm for Large Maximum Weight Independent Set Problems*. In 30th Annual European Symposium on Algorithms (ESA 2022), LIPIcs 244, 45:1–45:16. Journal version: *A metaheuristic algorithm for large maximum weight independent set problems*, Networks, 2025, doi:10.1002/net.22247. — METAMIS; the OR-community $(j,k)$-swap solver, and the obvious comparator for a COR paper.
3. R. K. Ahuja, Ö. Ergun, J. B. Orlin, A. P. Punnen. *A survey of very large-scale neighborhood search techniques*. Discrete Applied Mathematics 123(1–3):75–102, 2002. doi:10.1016/S0166-218X(01)00338-9 — the taxonomy the paper's method belongs to, in the journal's own tradition.

**Should be cited**

4. E. Großmann, K. Langedal, C. Schulz. *Concurrent Iterated Local Search for the Maximum Weight Independent Set Problem*. SEA 2025, LIPIcs 338, 22:1–22:20. doi:10.4230/LIPIcs.SEA.2025.22 — CHILS.
5. E. Großmann, K. Langedal, C. Schulz. *Accelerating Reductions Using Graph Neural Networks and a New Concurrent Local Search for the Maximum Weight Independent Set Problem*. arXiv:2412.14198, 2024. — LearnAndReduce.
6. E. Großmann, S. Lamm, C. Schulz, D. Strash et al. *A Comprehensive Survey of Data Reduction Rules for the Maximum Weighted Independent Set Problem*. arXiv:2412.09303, 2024. — would replace half of Section 2's prose and fix the attributions.
7. M. Fischetti, A. Lodi. *Local branching*. Mathematical Programming 98:23–47, 2003. doi:10.1007/s10107-003-0395-5.
8. E. Danna, E. Rothberg, C. Le Pape. *Exploring relaxation induced neighborhoods to improve MIP solutions*. Mathematical Programming 102(1):71–90, 2005. doi:10.1007/s10107-004-0518-7.
9. P. Shaw. *Using constraint programming and local search methods to solve vehicle routing problems*. CP 1998, LNCS 1520, 417–431. (Or D. Pisinger, S. Ropke, *Large neighborhood search*, in Handbook of Metaheuristics, 2nd ed., Springer, 2010, 399–419.)
10. J. Gu, W. Zheng, Y. Cai, P. Peng. *Towards Computing a Near-Maximum Weighted Independent Set on Massive Graphs*. KDD 2021, 467–477. doi:10.1145/3447548.3467232 — HtWIS.
11. Y. Jin, J.-K. Hao. *General swap-based multiple neighborhood tabu search for the maximum independent set problem*. Engineering Applications of Artificial Intelligence 37:20–33, 2015. doi:10.1016/j.engappai.2014.08.007 — directly on generalised swap neighbourhoods for MIS, and on exactly the BHOSLIB instances used here.
12. C. Komusiewicz, N. Morawietz. *Finding 3-Swap-Optimal Independent Sets and Dominating Sets Is Hard*. ACM Transactions on Computation Theory, 2024/25. doi:10.1145/3700642 — the hardness of the neighbourhood being searched.
13. R. Li, S. Hu, J. Gao, Y. Zhou, Y. Wang, M. Yin. *NuMWVC: A novel local search for minimum weighted vertex cover problem*. Journal of the Operational Research Society 71(9):1498–1509, 2020. — the successor of the NuMVC line, which the paper stops at 2017.
14. M. Böther, O. Kißig, M. Taraz, S. Cohen, K. Seidel, T. Friedrich. *What's Wrong with Deep Learning in Tree Search for Combinatorial Optimization*. ICLR 2022, arXiv:2201.10494. — with Z. Li, Q. Chen, V. Koltun (NeurIPS 2018) and S. Ahn, Y. Seo, J. Shin (ICML 2020), this settles the learning-augmented question the paper never raises.
15. K. Xu, W. Li. *Exact phase transitions in random constraint satisfaction problems*. JAIR 12:93–103, 2000. — Model RB, and the source of the *known optima* of the `frb` instances. `xu2007` alone does not support the claim that the `frb` optima are known.
16. D. A. Bader, H. Meyerhenke, P. Sanders, D. Wagner (eds.). *Graph Partitioning and Graph Clustering: 10th DIMACS Implementation Challenge*. AMS Contemporary Mathematics 588, 2013. — the source of the real `delaunay_n16/18/20` instances whose names the paper reuses (see §6).
17. C. Ebenegger, P. L. Hammer, D. de Werra. *Pseudo-Boolean functions and stability of graphs*. Annals of Discrete Mathematics 19:83–98, 1984. — the original struction, behind `gellner2021`.

**References cited for claims they do not support**

- `xu2007` is cited in Section 6.2 for the BHOSLIB collection "generated from Model RB". Model RB is Xu & Li (2000); Xu et al. (2007) is about easy generation of hard satisfiable CSP instances. More importantly, the *known-optimum* claims in Sections 6.3 and 6.9 rest on the forced-satisfiable construction, which `xu2007` does not establish for these specific graphs. Add ref. 15 and the BHOSLIB benchmark page.
- Section 1 describes `lamm2017` (ReduMIS) as running "swap-based local search on the reduced graph". ReduMIS is a memetic algorithm with separator- and partition-based combine operators on top of iterated ARW local search; the description understates the baseline, and it does so in exactly the direction that makes the region move look more novel.

**Are the baselines current?** No. ReduMIS (2017), OnlineMIS (2016), NuMVC (2013), FastVC (2017), reducing-peeling and near-linear kernelization (2017). For unweighted MIS the frontier in 2025–26 includes ONE/ALENEX 2025 (which reports *exceeding* ReduMIS quality when the subproblem cap is raised — i.e. on precisely the axis this paper claims), and the CHILS/LearnAndReduce line for the weighted case. Omitting ONE is disqualifying for two reasons at once: it is the prior art, and it is the one baseline that would test whether this implementation of the idea beats the published implementation of the same idea.

---

## 6. Benchmark conventions and comparability to published numbers

**BHOSLIB complement form — handled correctly, and the appendix note is a real contribution.** I checked the arithmetic. `frb30-15-1` in clique form has 450 vertices and 83,198 edges; $\binom{450}{2}-83{,}198 = 17{,}827$, which is the manuscript's complement edge count, and $\alpha = 30$. Likewise `frb59-26-1`: $\binom{1534}{2} - 126{,}555 = 1{,}049{,}256$, the published clique-form edge count. `frb35-17-1`, `frb40-19-1`, `frb45-21-1`, `frb50-23-1`, `frb53-24-1` all check out. The observation that the Network Repository copies are the clique form and that $\alpha$ of that form is the domain size is correct and worth publishing.

**But the known optima are not reported, and the paper's "largest gap" is understated.** For `frb`$XX$-$YY$-$Z$ the optimum is $XX$ by construction. So the benchmark's true reference values are 30, 35, 40, 45, 50, 53, 59. Against those, `Cascade` returns 30, 34, 39, 43, 48, 50, 56 — gaps of 0, 1, 1, 2, 2, **3**, **3**. The worst relative gap to a *known optimum* is $3/53 = 5.66\%$, not the $4.4\%$ the paper reports against best-found. And *no* solver in the study reaches the optimum on `frb50-23-1` (best 50 — actually attained by NuMVC), `frb53-24-1` (best 52 vs 53) or `frb59-26-1` at 60 s (best 58 vs 59). The paper acknowledges the optimum only for `frb30-15-1` and, in Section 6.9, for `frb35`/`frb40`. **Remedy:** add an "optimum" column to Table 4 and state the gap to it; a BHOSLIB table without the known $\alpha$ is not readable by this community.

**SNAP graphs: the paper is below *proven optima* and does not say so.** Lamm et al. 2017 (`lamm2017`, the paper's own reference), Table 8, lists as exactly solved: `web-Stanford` $\alpha = 163{,}390$ and `as-Skitter-big` $\alpha = 1{,}170{,}580$, both marked as among the hardest instances solved exactly by the branch-and-reduce algorithm. `Cascade` returns 163,375 and 1,170,576. So on `web-Stanford` the paper is 15 vertices short of a *proven optimum* that its own baseline attains in 31.3 s (appendix table), and on `as-skitter` 4 short. Likewise `roadNet-PA` 533,628 and `roadNet-CA` 961,851 are the values ReduMIS reaches here and the values published in the KaMIS line; `Cascade` misses `roadNet-PA` by one. The manuscript describes these as being "behind the strongest baseline" and says of the web graphs "we have not identified a structural reason for this". The correct framing is much sharper: **on four SNAP instances the method fails to reach a known or near-certain optimum that a 2016 branch-and-reduce solver proves.** This should be stated, with citations, and it removes the interpretation that these are merely baseline-vs-baseline differences.

**Delaunay instances: the only strict wins are on self-generated graphs whose names collide with public ones.** `del16/18/20` are produced by `tools/gen_instances.py` at seed 1. The paper says so (Section 6.11 and Appendix A) and says the values are not comparable with earlier papers — commendable. But the consequence is severe: the *entire* strict-win claim of the paper rests on three instances that exist nowhere else. The DIMACS10 `delaunay_n16`, `delaunay_n18`, `delaunay_n20` graphs are public, have published KaMIS numbers, and would have cost nothing to download. Using them instead is not optional for a paper whose headline is "best on the Delaunay family".

**Provenance table errors.** Table A.1 lists `soc-pokec-relationships` and `com-lj` with source "generated$^{\ddagger}$" (i.e. `tools/gen_instances.py` at seed 1). They are SNAP graphs, and the $n$/$m$ printed (1,632,803 / 22,301,964 and 3,997,962 / 34,681,189) are the SNAP values. This is a table-generation bug in a table whose stated purpose is "so that the benchmark set can be rebuilt exactly". Separately, `as-skitter` is an autonomous-systems topology, not a social network. And the generated RGG sizes contradict the stated normalisation policy: `rgg16` has $n=65{,}501 < 2^{16}$, `rgg18` $262{,}011 < 2^{18}$, `rgg20` $1{,}048{,}171 < 2^{20}$, yet Appendix A says "Isolated vertices are retained rather than dropped". Something is being dropped; say what.

**The corrected aggregate is worse for the paper than the printed one.** Recomputing Table 6 from the seven-solver file `results/cor_main60.csv`:

| Solver | #best | #solved | mean gap | max gap |
|---|---|---|---|---|
| Cascade | 16 | 27 | **0.785%** | 4.444% |
| ReduMIS | 19 | 26 | 0.501% | 4.444% |
| FastVC | 11 | 27 | **0.340%** | 3.448% |
| NuMVC | 8 | 26 | 1.219% | 6.956% |
| OnlineMIS | 1 | 27 | 2.156% | 6.667% |
| NearLinear | 6 | 27 | 7.113% | 32.500% |
| LinearTime | 2 | 27 | 8.019% | 34.000% |

The printed Table 6 says Cascade 17 / 0.414% / 2.857% — computed over five solvers. Under the correct seven-solver aggregate, **`Cascade` has the worst mean gap of the three strong solvers**, and FastVC — which the Wilcoxon test declares `Cascade` beats at $p=0.030$ — has the lowest mean gap on the benchmark. Both statements can be true simultaneously (Wilcoxon is on signed ranks of paired gaps, FastVC's losses are many-but-small and its wins few-but-large), but a paper cannot print only the framing that favours it. The corrected table must appear, and Section 6.5's discussion must be rewritten around it. Similarly, Table 8 (budget) omits the NuMVC row whose content — mean 204.3 s, max 960.0 s, 12 of 27 runs over 90 s — the body text quotes; I verified those three numbers from `cor_main60.csv`. Finally, `#best = 16` in the corrected table matches the body text ("matches the best value on 16 of the 27") and contradicts the printed 17.

---

## 7. What the field learns

Strictly best on 3 of 27 (all three author-generated, one family), tied on 13, behind on 11. Against the one strong baseline, no significant difference. Against a baseline the paper does not run (ONE, ALENEX 2025), the comparison is unknown and is the comparison that matters.

What the field could legitimately take away, if the paper were reframed:

- **The throughput numbers are the real result.** 107,238 region moves in 58 s on `del18` ($543\,\mu$s each), 96,842 on `web-Stanford` ($605\,\mu$s), with a reduce-and-solve sub-problem inside every one of them, is a genuinely new datum. ONE reports a subproblem-size/quality trade-off but, to my reading, nothing at this move rate. A paper whose thesis was "the known optimal-neighbourhood move becomes a *different algorithm* when you can run it 1800 times a second, and here is the data-structure work that gets you there" would be worth publishing — in a venue like ALENEX/JEA, and plausibly in COR if the OR framing (VLSN, local branching) were supplied.
- **The payload-free LIFO undo on a twin-indexed compressed adjacency array**, with per-vertex overflow lists for fold edges, is a clean and reusable piece of engineering, and the honest account of the shared-live-list bug is the kind of thing this literature under-reports.
- **The degree-ordered reduction queue** result — kernelization $1.25\times$ faster at 282k vertices and $3.5\times$ at 4M, from a counting sort — is a small, checkable, transferable finding.
- **The online adaptation of $|F|$** from the proved-optimal flag is a better answer than ONE's fixed $\nu_{\max}$/$d$, *if* it is benchmarked against ONE's fixed setting. Right now it is benchmarked against nothing.
- **The negative results are valuable and should be kept**: the decision-space move contributing literally nothing on three of seven instances, perturbation and the LP reduction both inside noise, and the `del20` gap to ReduMIS collapsing from 8500 to 1550 at $10\times$ budget. The last of these in particular is the sort of correction most papers bury.

What the field does *not* learn: that the region move is new (it is not), or that it is better than the state of the art (no test in the paper separates it from ReduMIS, and the current state of the art is not in the paper).

---

## 8. Specific issues

1. **[CRITICAL] The core contribution is unattributed prior art.** Sections 1, 1.1 ("Positioning"), 3. `R(F)`, Theorem 1(a), the substitution argument, the use of reductions inside the sub-solve, and the size parameter are the *optimal neighborhood exploration* of Borowitz, Großmann and Schulz, ALENEX 2025 (arXiv:2407.06912). **Remedy:** cite it, restate Theorem 1 as a restatement of their separation property, run it as a baseline on all 27 instances, and reposition the contribution as throughput engineering plus online $|F|$ adaptation, or withdraw.

2. **[CRITICAL] The manuscript contains two contradictory result sets.** Tables 2–6 and 8 (`tables/quality_*.tex`, `aggregate.tex`, `budget.tex`) omit NuMVC and FastVC entirely; the abstract, body text, Tables 7, 9–13 and the appendix table include them. Direct contradiction: Table 4 bolds `Cascade` 43 on `frb45-21-1` as the benchmark best while Table A.2 lists `fastvc 45`, `numvc 45` and the text says "45 against our 43". Cause: `scripts/make_tables.py` defaults to `--main heuristic.csv` (5 solvers, dated 2026-09-21) while every other table script defaults to `cor_main60.csv` (7 solvers, 2026-09-22). **Remedy:** regenerate all tables from `cor_main60.csv` and rewrite Section 6.5 around the corrected aggregate (§6 above).

3. **[CRITICAL] The corrected aggregate contradicts the paper's framing.** Corrected: Cascade mean gap 0.785%, worst of the three strong solvers; FastVC 0.340%; ReduMIS 0.501%; Cascade #best 16 vs ReduMIS 19. Printed: 0.414% / 2.857% / #best 17. **Remedy:** print the corrected table and address the FastVC mean-gap result explicitly rather than leaning on the Wilcoxon verdict alone.

4. **[CRITICAL] "Larger $F$ yields moves that no swap-based neighbourhood expresses" is false.** Abstract, Section 1, and the corollary after Proposition 3. A region move with $|F|=j$ is the best $(j,k)$-swap over all $k$; $(j,k)$-swaps are ARW's own generalisation (`lamm2017` states this explicitly). **Remedy:** replace with "finds the best $(j,k)$-swap for all $k$ at once, which ARW define but implement only for $j\le 2$".

5. **[MAJOR] The monotonicity claim does not match the algorithm.** Corollary 2 assumes a maximum $T^\star$; Algorithm 1 line 10 calls a *bounded* sub-solver. The code is correct (`cascade.cpp:263`, acceptance guarded by `res.size >= incoming`) but the paper never states the guard. **Remedy:** state the invariant as "a move is applied only if $|T|\ge|F|$", and note that this preserves monotonicity under time-out.

6. **[MAJOR] Lemma 6's proof invokes Lemma 3 where Lemma 3's hypothesis fails.** Section 2, $(\le)$ direction: $N(v)=\{u,w\}$ with $uw\notin E$ is precisely *not* a clique. **Remedy:** replace with the two-line self-contained exchange argument.

7. **[MAJOR] Reported "kernels" are not kernels under the stated rule set.** `reductions.hpp:23–26` caps the simplicial test at degree 8, domination at degree 24, and the unconfined test at 20,000 scanned edges / 8 set-expansion rounds; `main.cpp:42–43` tightens to 4 and 8 for the dive; and `kernel_share` truncates kernelization by wall clock. Section 2 defines a kernel as a graph on which no rule fires, and Section 4.1 reports kernel sizes as if comparable with `hespe2019`. **Remedy:** table the implemented caps, and relabel "kernel" as "reduced graph" where the rules were capped or truncated.

8. **[MAJOR] BHOSLIB known optima are not reported.** Table 4 and Section 6.3. The optima are 30/35/40/45/50/53/59; the worst gap to a known optimum is $3/53=5.66\%$, not the $4.4\%$ claimed as "the largest we record anywhere"; and no solver reaches the optimum on `frb50`, `frb53` or `frb59` at 60 s. **Remedy:** add an optimum column and report gaps against it.

9. **[MAJOR] Shortfalls against *proven* optima on SNAP graphs are not acknowledged.** `web-Stanford` $\alpha=163{,}390$ and `as-Skitter-big` $\alpha=1{,}170{,}580$ are listed as exactly solved in Table 8 of `lamm2017`, the paper's own reference. `Cascade` returns 163,375 and 1,170,576. **Remedy:** say so, with the citation, in Section 6.3 and in the Conclusions (which currently say only that "we have not identified a structural reason" for the web-graph deficit).

10. **[MAJOR] The only strict wins are on instances that exist nowhere else.** Sections 6.2, 6.3, 6.11, Appendix A. `del16/18/20` are generated at seed 1 and are not the DIMACS10 `delaunay_n*` graphs whose names they reuse. **Remedy:** rerun the geometric family on the public DIMACS10 Delaunay graphs. If the margin survives there, the paper's central empirical claim becomes checkable by others; if it does not, the paper has no strict win.

11. **[MAJOR] Proposition 3 does not bound what the implementation does.** The $O(\sum_{v\in F}\deg v)$ bound excludes the seed BFS in `build_region` (`cascade.cpp:410–420`), which expands up to `max(64, 64|F|)` full adjacency lists and can touch a $\Delta=100{,}029$ hub on `wiki-Talk`. **Remedy:** state the BFS cost, or restrict the proposition to phase two.

12. **[MAJOR] The ablation references a move that the paper never defines.** Section 6.9: "\textsc{dive} replaces the region move with the decision-space move described in Section~\ref{sec:move}". Section 3 describes no decision-space move. The table row is labelled "decision-space moves" and is discussed at length. **Remedy:** define it, or drop it.

13. **[MAJOR] Provenance table lists two SNAP graphs as generated.** Table A.1: `soc-pokec-relationships` and `com-lj` carry the $^{\ddagger}$ "produced by `tools/gen_instances.py` at seed 1" marker while showing SNAP's $n$ and $m$. **Remedy:** fix the source column.

14. **[MINOR] The "common 60-second budget" of the abstract is not common.** Verified from `cor_main60.csv`: NuMVC median 85.9 s, mean 204.3 s, max 960.0 s, 12 of 27 runs over 90 s; ReduMIS max 660.2 s; `Cascade` max 75.0 s. The body discloses this (Section 6.5) but the abstract does not. **Remedy:** qualify the abstract.

15. **[MINOR] Maximality of $S'$ is never discussed**, and the repair loop at `cascade.cpp:277–283` is therefore unexplained. **Remedy:** one sentence: $S'$ is maximal when $T$ is maximal in $G[R(F)]$; the repair handles the timed-out case.

16. **[MINOR] Missing hardness statement for the neighbourhood.** Add Komusiewicz–Morawietz (ACM ToCT 2024/25) and state that searching $R(F)$ exactly is NP-hard, which is what makes the reduce-inside step necessary rather than merely convenient.

17. **[MINOR] "No acceptance criterion, tabu list or repair step is required" (Section 1.1) overstates.** The implementation has plateau acceptance, perturbation with a rollback log, restarts with an archive, and a post-move maximality repair. **Remedy:** restrict the claim to the move itself.

18. **[MINOR] Generated RGG vertex counts contradict the stated normalisation.** $n = 65{,}501 / 262{,}011 / 1{,}048{,}171$ against $2^{16}/2^{18}/2^{20}$, while Appendix A states isolated vertices are retained. **Remedy:** explain what is dropped.

19. **[MINOR] Table A.2 lists identical values 162,453 for both `numvc` and `online_mis` on `web-Stanford`.** Possibly a coincidence, possibly a collection error. Worth a check.

20. **[MINOR] A `%% TODO: tighten once the final experiments are in.` comment survives at line 48**, immediately above the abstract. Remove before resubmission.

21. **[MINOR] Attribution gaps in Table 1:** degree-2 fold (Chen–Kanj–Jia), twin (Xiao–Nagamochi via Akiba–Iwata) and domination carry no citation while unconfined and LP do; the twin row does not say which condition selects "take both" versus "fold"; unconfined cites `xiao2017` but not `xiao2013`, where confining sets originate.

22. **[MINOR] `xu2007` cannot support the known-optimum claims for the `frb` instances.** Add Xu & Li, JAIR 12:93–103, 2000, and the BHOSLIB page.

23. **[MINOR] `lamm2017` is described as "swap-based local search on the reduced graph"** (Section 1), understating a memetic algorithm with separator- and partition-based combine operators — in the direction that flatters the paper's novelty claim.

24. **[MINOR] `cai2017fastvc` has no DOI** in `refs.bib`, unlike every other article entry.

---

## 9. Recommendation with justification

**Reject.**

The determining factor is issue 1. The neighbourhood, the separation property, the exact sub-solve with reductions applied inside it, and the subproblem-size control were published in ALENEX 2025 by the group that wrote the paper's principal baseline. A COR submission whose stated primary contribution ("a neighbourhood with a proof of separation and monotonicity ... together with the observation that it strictly generalises the swap neighbourhoods used by existing local search") is a rediscovery of a known construction — and whose generalisation claim is additionally false with respect to ARW's own $(j,k)$-swaps — cannot be accepted on that contribution. This is not a citation-hygiene complaint that a revision letter fixes; the paper's contribution list would have to be rewritten from the first item down.

Issues 2 and 3 are independently serious. As submitted, the paper's main tables and its text describe different experiments, and the version of the aggregate that the text is based on is materially less favourable than the version that is printed. I do not read this as misconduct — the mechanism is a stale default in one of six table scripts, and every other artefact in the repository is consistent with the honest reading — but a reviewer cannot recommend acceptance of tables that contradict the appendix of the same paper.

Issue 10 caps what a corrected version could claim: three strict wins, all on instances the authors generated, on a family for which public equivalents (DIMACS10 `delaunay_n*`) exist and were not used.

**What would make a resubmission viable, most likely at ALENEX/JEA or, with an OR framing, at COR:**
(i) cite Borowitz–Großmann–Schulz and run ONE as a baseline on all 27 instances; (ii) reposition around throughput — the 1800 moves/s figure, the LIFO undo, the sub-solver reuse, the degree-ordered queue — and against ONE's fixed $\nu_{\max}$, so the contribution becomes "the same move, two orders of magnitude more often, and here is what that buys"; (iii) rerun the geometric family on public DIMACS10 instances; (iv) regenerate every table from one results file; (v) report BHOSLIB optima and the SNAP proven optima; (vi) add METAMIS/CHILS and the VLSN/local-branching framing; (vii) fix Lemma 6 and Proposition 3 and state the acceptance guard. The engineering and the experimental discipline in this manuscript are good enough that such a paper would be worth reading. This one is not the paper it thinks it is.

---

## 10. Confidence and limits

**High confidence:**
- The prior-art identification (issue 1). I read the ALENEX 2025 paper's construction directly and it matches clause for clause. I did not obtain the full PDF text, only a structured extraction of the definitions section plus the abstract, so I have not compared their Lemma statement to Theorem 1 word for word — but the construction, the separation property and the exact-solve-with-reductions are unambiguous.
- Issues 2, 3, 13: verified by recomputing the aggregate, the win/tie/loss counts and the timing statistics directly from `results/cor_main60.csv` and comparing with the committed `.tex` tables, and by reading the default arguments in `scripts/make_tables.py` against those in the other five table scripts.
- Issues 5, 6, 7, 11, 15: verified against `src/cascade.cpp` and `src/reductions.hpp` at the line numbers cited.
- The BHOSLIB complement arithmetic and the `frb` optima.
- `web-Stanford` = 163,390 and `as-Skitter-big` = 1,170,580 as proven optima: read from Table 8 of `lamm2017` (arXiv:1509.00764), where both are marked as among the hardest instances solved exactly.

**Moderate confidence:**
- That `as-Skitter-big` in the KaMIS papers is byte-identical to SNAP `as-skitter` as the authors normalise it. The vertex/edge counts are consistent, but the KaMIS "-big" suffix denotes a specific preprocessing and I did not verify it. If it differs, issue 9 still stands for `web-Stanford`.
- That METAMIS's $(j,k)$-swap machinery covers the region move specifically, as opposed to bounded-arity swaps. METAMIS is MWIS-focused and my reading of it is from secondary sources in this session; I cite it as context, not as the decisive prior art. The decisive prior art is ONE.
- The claim that no public collection of large-kernel families exists (Section 6.11). The DIMACS10 mesh/Delaunay family is precisely such a collection and is public; I did not verify kernel sizes for it.

**Limits of this review:**
- I did not compile the manuscript, run the solver, or re-run any baseline. All numerical checks are recomputations from the committed CSVs against the committed tables.
- I did not read `figures/*.tex` or the generated figures, so Figures 2–5 are unreviewed beyond their captions.
- I did not audit `exact.hpp`'s branch-and-reduce beyond confirming which reductions it enables and that lifting returns a full-length solution vector; the clique-cover bound and the fold handling in the sub-solver are the components most likely to harbour the class of bug the authors themselves report, and a rigorous review would require a correctness harness I did not build.
- Per instruction I read no other file under `reviews/`, so this report is independent of the other panellists'.
