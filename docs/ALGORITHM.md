# CASCADE: exact neighbourhood search for maximum independent set

## The gap this fills

Every strong solver for massive sparse graphs is built the same way: reduce the
graph with safe rules, then search whatever survives.  They differ only in what
happens after kernelization stalls.

* **Reduce-and-peel** (Chang, Li & Zhang, SIGMOD 2017) takes one greedy dive —
  delete the maximum-degree vertex, re-reduce, repeat — and never revisits a
  decision.
* **ReduMIS / OnlineMIS** (Lamm et al., J. Heuristics 2017; Dahlum et al., SEA
  2016) run (1,2)-swap local search on the kernel.  The local search is
  reduction-blind: it searches raw vertex space, one or two vertices at a time.
* **Branch-and-reduce** (Akiba & Iwata, TCS 2016) explores decisions
  exhaustively with reductions at every node.  Complete, but exponential once
  the kernel stays large.

The residual kernel is where all of them are weak, and it is large on exactly
the families the literature identifies: meshes and Delaunay triangulations,
dense web and social cores, and adversarial Model-RB instances.

CASCADE attacks the residual kernel with moves that are **solved exactly rather
than sampled**, using the reduction machinery as the engine that makes big exact
moves affordable.

## The move

Let `S` be the incumbent independent set and let `F ⊆ S` be a set of vertices we
free.  Define

    R(F) = F ∪ { u ∉ S : every neighbour of u that lies in S lies in F }.

**Claim.** `S \ R(F)` is independent, no vertex of `R(F)` is adjacent to a
vertex of `S \ R(F)`, and therefore for any independent set `T` of the induced
subgraph `G[R(F)]`, the set `(S \ R(F)) ∪ T` is independent.

*Proof.* `S \ R(F)` is a subset of `S`, hence independent.  Take `v ∈ R(F)` and
`w ∈ S \ R(F)` and suppose they are adjacent.  If `v ∈ F` then `v ∈ S`, so `v`
and `w` are two adjacent vertices of `S`, contradicting independence.  Otherwise
`v ∉ S`, and `w` is a neighbour of `v` lying in `S`, so by the definition of
`R(F)` we get `w ∈ F ⊆ R(F)`, contradicting `w ∉ R(F)`.  Hence there is no such
edge, and any independent `T ⊆ R(F)` can be combined with `S \ R(F)`. ∎

Two consequences make this the right move:

* **It never loses ground.**  `S ∩ R(F)` is itself an independent set of
  `G[R(F)]`, so a maximum independent set of `G[R(F)]` has size at least
  `|S ∩ R(F)|`.  Replacing the region by its optimum can only keep or increase
  the total.
* **It subsumes classical swaps.**  With `|F| = 1` the region is exactly what an
  ARW (1,2)-swap examines; solving it exactly finds the best (1,k)-swap for any
  `k` at once.  Growing `|F|` gives moves that no swap-based local search can
  express.

The move is applied as: build `R(F)`, extract the induced subgraph, solve it by
branch-and-reduce, write the result back.  Vertices left free by the rewrite
(a neighbour outside the region whose only incumbent neighbours were freed) are
taken immediately, which keeps the incumbent maximal.

## Why the regions are solvable

A region of a few thousand vertices would be hopeless for plain branch-and-bound
inside an inner loop.  It is not hopeless after reductions: degree-0/1,
simplicial, degree-2 folding, twin, domination and unconfined rules collapse a
typical region to a kernel of a few dozen vertices, so the sub-solve finishes in
microseconds.  **The reduction suite is not a preprocessing step here — it is
what makes the move affordable**, and the ablation switch `--no-lns` versus the
full solver measures exactly that.

## Self-tuning region size

`|F|` is not a tuning parameter, because the right value differs by three orders
of magnitude across families.  It adapts from two signals:

* a region that could not be solved to proven optimality within its budget, or
  that exceeded the size cap, **halves** `|F|`;
* `lns_stale_grow` consecutive regions solved to optimality **without** finding
  anything **doubles** `|F|`.

On Delaunay meshes this settles at tens of freed vertices; on dense Model-RB
instances it settles at one or two, where the neighbourhood degenerates to a
classical swap.  No per-family configuration is needed.

A worklist drives the sweep: only vertices whose neighbourhood changed are
re-examined, so a sweep converges to a solution that is optimal for *every*
region of the current size before the size grows.

## Escaping a local optimum

Two mechanisms:

* **Plateau moves.**  A region optimum of equal size that differs from the
  incumbent is accepted once a full sweep has stopped finding real gains.
  Random tie-breaking in the sub-solver's branching makes repeated solves of the
  same region return different optima, so the search drifts along the plateau
  instead of stalling.  This was worth roughly 0.1% on Delaunay instances — the
  difference between trailing ReduMIS and beating it.
* **Perturbation.**  A random vertex is forced into the incumbent, its incumbent
  neighbours are evicted, and neighbourhood moves repair the damage.  Every
  change goes through a change log, so a perturbation that ends up worse is
  rolled back by rewriting only the touched vertices — never the whole solution,
  which matters at millions of vertices.

## The reduction engine

Reductions and branching decisions both mutate a dynamic graph that supports
undo in time proportional to the work being undone.

* Original edges live in a CSR array where each entry knows the position of its
  twin.  Deleting a vertex swaps its entry to the end of each neighbour's live
  range and shrinks the range; degrees stay exact and a live neighbourhood stays
  contiguous.  Undo just grows the ranges back — nothing needs swapping back,
  because later operations never move an entry outside the live range.
* Edges created by folding cannot live in the static array, so they go into
  per-vertex overflow lists that are append-only and filtered on traversal.
  Undo is a `pop_back`.  Only vertices involved in a fold ever allocate one.

Every rule records how to reconstruct a solution, and lifting replays the
records in reverse.  A fold of a degree-2 vertex `v` with non-adjacent
neighbours `u, w` records `(v, u, w, f)`: if the fold vertex `f` ends up in the
solution then `u` and `w` are taken, otherwise `v` is.

The Nemhauser–Trotter LP reduction runs during kernelization.  It is the one
rule that looks at the whole graph rather than a local neighbourhood, which is
why it fires where the local rules have stalled: it cut web-Stanford's kernel
from 39 060 to 9 549 vertices.  It is read off a maximum matching in the
bipartite double cover via König's theorem, and alternates with the local rules
until neither moves.

## Exactness

The same engine runs as a stand-alone exact solver (`--exact`): branch-and-reduce
with a greedy clique-cover bound, which is also what solves the regions.

One subtlety cost real correctness during development and is worth recording.
Each search node must hold an **exact** list of its live vertices.  An earlier
version shared one list across the recursion and could drop a vertex when a fold
created a new one; the clique cover then failed to cover that vertex, the bound
came out too small, and optimal solutions were pruned — while the solver still
reported "proved optimal".  Each node now owns its live range, built by
filtering the parent's.  `tests/test_correctness.cpp` checks the exact solver
against brute force on 300 random graphs, with each reduction rule disabled in
turn, which is what catches this class of bug.
