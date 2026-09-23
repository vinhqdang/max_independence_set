# Submission record

## Computers & Operations Research, 23 September 2026

**Title.** Exact Large-Neighbourhood Search for the Maximum Independent Set
Problem on Massive Sparse Graphs

**Author.** Quang-Vinh Dang, British University Vietnam

**Submitted state.** Commit `d98dea5`. The manuscript builds from that commit
with `make` in `paper/`; a clean bundle of the 26 source files compiles
standalone with no errors and no undefined references, at 45 pages.

**Classifications.** 90C27 (combinatorial optimization), 90C59 (approximation
methods and heuristics), 90C35 (programming involving graphs or networks),
90C06 (large-scale problems), 90-08 (computational methods). 90C57 was
considered and rejected: it routes the paper to polyhedral reviewers, and the
paper reports no dual bound and uses a plain edge-formulation ILP baseline.

**Files submitted.** `paper/cascade-mis.tex`, `refs.bib`, `cascade-mis.bbl`,
`tables/*.tex` (17), `figures/` (`pipeline.tex`, `region.tex`, and
`profile.pdf`, `seeds.pdf`, `convergence.pdf`), plus `highlights.txt` and
`cover-letter.txt`.

## What the pre-submission review found and what was done about it

A five-seat review was run before submission; the reports are in `reviews/`,
and `reviews/06_editorial_decision.md` carries the adjudication. The theory
findings were fixed. The numerical findings were left in place by decision, so
they are listed here rather than lost.

### Fixed before submission

- The degree-2 folding proof appealed to the simplicial lemma in the one case
  its clique hypothesis excludes. Replaced with a direct exchange argument.
- The corollary relating regions to classical swaps claimed moves that no swap
  neighbourhood expresses. A region move releasing $j$ and writing back $k$ is a
  $(j,k)$-swap, so the claim was withdrawn and replaced with what the separation
  property actually buys.
- Monotonicity was stated only for a sub-solve run to optimality while the
  implementation bounds it. Added the acceptance condition $|T| \ge |F|$ and the
  maximality proposition that confines the repair scan.
- The cost proposition did not account for the walk that selects the freed set.
- The ablation referred to a "decision-space move" that no section defined.
- Journal conformance: Harvard citations, abstract cut to 246 words, corresponding
  author marked, appendix tables renumbered A.1/B.1, and the declarations the
  guide requires.

### Open, and untouched by decision

These are the items to expect from referees.

1. **Prior art not cited.** Borowitz, Grossmann & Schulz, *Optimal Neighborhood
   Exploration for Dynamic Independent Sets*, ALENEX 2025 (arXiv:2407.06912)
   publishes the same construction: "we add the $H$ tight nodes from
   $N(H)\setminus H$ to our subproblem", solved with KaMIS branch-and-reduce,
   capped by a subproblem-size parameter. It is by the authors of ReduMIS, the
   paper's own primary baseline. The defensible reframing is the construction
   moved from the dynamic setting to static LNS, with $|F|$ adapted online in
   place of a fixed cap.
2. **Tables are built from five of the seven solvers.** `make_tables.py:145`
   defaults to `heuristic.csv` and line 9 hardcodes a five-solver list, so NuMVC
   and FastVC are missing from the quality, aggregate and budget tables while the
   prose, the appendix and the figures use seven. Over all seven the mean gap is
   0.785% rather than the printed 0.414%, and FastVC has the lowest of any solver
   at 0.340%.
3. **The Wilcoxon test is not the one the paper describes.** The text says
   relative gaps; `stats_test.py:69` uses raw vertex counts. On gaps, FastVC goes
   to p = 0.441 and NuMVC to p = 0.155, so "ahead of five of six baselines"
   becomes three of six; a Holm correction alone reduces it to four.
4. **The stated mechanism is not supported.** Kernel fraction correlates
   -0.536 with the margin across the benchmark; the positive correlation on
   sparse instances comes entirely from the three self-generated Delaunay graphs.
5. **The only strict wins are on self-generated instances** whose names collide
   with the public DIMACS10 `delaunay_n*` graphs, which were available and unused.
   Running those is the single experiment that decides whether a positive claim
   exists.
6. **Ablated variants beat the shipped configuration on the winning family**:
   `del16` `nopert` 20656 against 20648, `del18` `nolp` 82666 against 82661.
7. Throughput figures (1800 moves/s, 543 us per move) appear in no shipped
   record; `main.cpp` prints the counters but `run_bench.py` discards them.
8. Exact solvers ran under unequal ceilings: VCSolver and PACE were killed at
   60 s while the method's exact mode was allowed 660 s.
9. `provenance.tex` attributes `soc-pokec-relationships` and `com-lj` to the
   instance generator; both are SNAP graphs.

## If a revision is invited

Fix 1 first, then run 5. Items 2 and 3 are mechanical and change what the paper
may claim, so they come before any rewriting of the empirical sections.
