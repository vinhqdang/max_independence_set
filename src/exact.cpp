#include "exact.hpp"

#include <algorithm>

#include "dyngraph.hpp"

namespace {

class Brancher {
public:
    Brancher(const Graph& g, const ExactConfig& cfg, double deadline,
             const std::function<double()>& elapsed)
        : cfg_(cfg), deadline_(deadline), elapsed_(elapsed), n0_(g.n) {
        dg_.init(g, std::max(256, g.n));
        red_.init(dg_, cfg.red);
        best_ = cfg.lower_bound;
        arena_.reserve(4 * (size_t)g.n + 64);
        cover_mark_.assign(dg_.capacity(), 0);
        nbr_mark_.assign(dg_.capacity(), 0);
        rng_ = cfg.seed ? cfg.seed : 0x9e3779b97f4a7c15ULL;
    }

    ExactResult run() {
        arena_.clear();
        for (int v = 0; v < n0_; ++v) arena_.push_back(v);
        size_t lo = 0, hi = arena_.size();
        int fold_mark = dg_.next_fold();
        red_.push_all();
        red_.reduce();
        size_t clo = push_live_range(lo, hi, fold_mark);
        bool complete = branch(clo, arena_.size());
        ExactResult r;
        r.size = best_;
        r.proved_optimal = complete && !out_of_budget_;
        r.nodes = nodes_;
        r.solution = best_sol_;
        r.solution.resize(n0_);
        return r;
    }

private:
    // Returns the highest-degree vertex of the node's live range, breaking ties
    // at random so that re-solving the same region can yield a different optimum
    // of equal size.
    int pick_branch_vertex(size_t lo, size_t hi) {
        int best = -1, bestd = -1, ties = 0;
        for (size_t i = lo; i < hi; ++i) {
            int v = arena_[i];
            int d = dg_.deg(v);
            if (d > bestd) { bestd = d; best = v; ties = 1; }
            else if (d == bestd && ++ties > 1 && (next_rand() % (uint32_t)ties) == 0) best = v;
        }
        return best;
    }

    uint32_t next_rand() {
        rng_ ^= rng_ << 13;
        rng_ ^= rng_ >> 7;
        rng_ ^= rng_ << 17;
        return (uint32_t)(rng_ >> 32);
    }

    // Builds the child's live range: the survivors of this node's range plus any
    // vertex the fold reductions have just created.  Each node owning an exact
    // copy is what keeps the bound sound -- a live vertex missing from the range
    // would not be covered by the clique cover, making the bound too small and
    // pruning away optimal solutions.
    size_t push_live_range(size_t lo, size_t hi, int fold_from) {
        size_t clo = arena_.size();
        for (size_t i = lo; i < hi; ++i)
            if (dg_.alive(arena_[i])) arena_.push_back(arena_[i]);
        for (int f = fold_from; f < dg_.next_fold(); ++f)
            if (dg_.alive(f)) arena_.push_back(f);
        return clo;
    }

    // Greedy clique cover: a clique holds at most one solution vertex, so the
    // number of cliques bounds the independent set in the residual graph.
    // Candidates are narrowed by marking rather than by pairwise adjacency
    // tests, which keeps a cover linear in the edges it touches.
    long long clique_cover_bound(size_t lo, size_t hi) {
        ++cover_stamp_;
        long long cliques = 0;
        for (size_t idx = lo; idx < hi; ++idx) {
            int v = arena_[idx];
            if (cover_mark_[v] == cover_stamp_) continue;
            ++cliques;
            cover_mark_[v] = cover_stamp_;
            cand_.clear();
            dg_.for_each_nbr(v, [&](int u) {
                if (cover_mark_[u] != cover_stamp_) cand_.push_back(u);
            });
            while (!cand_.empty()) {
                int u = cand_.front();
                cover_mark_[u] = cover_stamp_;
                ++nbr_stamp_;
                dg_.for_each_nbr(u, [&](int w) { nbr_mark_[w] = nbr_stamp_; });
                size_t w = 0;
                for (size_t i = 0; i < cand_.size(); ++i) {
                    int x = cand_[i];
                    if (x == u || cover_mark_[x] == cover_stamp_) continue;
                    if (nbr_mark_[x] == nbr_stamp_) cand_[w++] = x;
                }
                cand_.resize(w);
            }
        }
        return cliques;
    }

    void record_solution() {
        if (!cfg_.need_solution) return;
        sol_buf_.assign(dg_.capacity(), 0);
        red_.lift(sol_buf_);
        best_sol_ = sol_buf_;
    }

    // Solves the node whose live vertices are exactly arena_[lo, hi).
    // Returns false when the subtree was abandoned because of a budget.
    bool branch(size_t lo, size_t hi) {
        ++nodes_;
        if ((nodes_ & 0x3ff) == 0 && elapsed_() > deadline_) { out_of_budget_ = true; return false; }
        if (cfg_.node_budget >= 0 && nodes_ > cfg_.node_budget) { out_of_budget_ = true; return false; }

        if (dg_.num_alive() == 0) {
            if (red_.offset() > best_) { best_ = red_.offset(); record_solution(); }
            return true;
        }
        int v = pick_branch_vertex(lo, hi);
        if (v < 0) return true;
        if (red_.offset() + clique_cover_bound(lo, hi) <= best_) return true;

        bool complete = true;

        // Branch 1: v stays out of the solution.
        Reducer::State s = red_.state();
        int fold_mark = dg_.next_fold();
        red_.exclude(v);
        red_.reduce();
        size_t clo = push_live_range(lo, hi, fold_mark);
        if (!branch(clo, arena_.size())) complete = false;
        arena_.resize(clo);
        red_.restore(s);

        if (!out_of_budget_) {
            // Branch 2: v joins the solution.
            s = red_.state();
            fold_mark = dg_.next_fold();
            red_.include(v);
            red_.reduce();
            clo = push_live_range(lo, hi, fold_mark);
            if (!branch(clo, arena_.size())) complete = false;
            arena_.resize(clo);
            red_.restore(s);
        } else {
            complete = false;
        }
        return complete;
    }

    ExactConfig cfg_;
    double deadline_;
    std::function<double()> elapsed_;
    int n0_;
    DynGraph dg_;
    Reducer red_;
    long long best_ = 0;
    long long nodes_ = 0;
    bool out_of_budget_ = false;
    std::vector<char> best_sol_;
    std::vector<int> arena_, cand_;
    std::vector<char> sol_buf_;
    std::vector<int> cover_mark_, nbr_mark_;
    int cover_stamp_ = 0, nbr_stamp_ = 0;
    uint64_t rng_ = 0x9e3779b97f4a7c15ULL;
};

}  // namespace

ExactResult solve_exact(const Graph& g, const ExactConfig& cfg, double deadline,
                        const std::function<double()>& elapsed) {
    if (g.n == 0) {
        ExactResult r;
        r.proved_optimal = true;
        return r;
    }
    Brancher b(g, cfg, deadline, elapsed);
    return b.run();
}
