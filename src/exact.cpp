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
        alive_.reserve(g.n);
        cover_mark_.assign(dg_.capacity(), 0);
        nbr_mark_.assign(dg_.capacity(), 0);
        rng_ = cfg.seed ? cfg.seed : 0x9e3779b97f4a7c15ULL;
    }

    ExactResult run() {
        alive_.clear();
        for (int v = 0; v < n0_; ++v) alive_.push_back(v);
        alive_size_ = n0_;
        int fold_mark = dg_.next_fold();
        red_.push_all();
        red_.reduce();
        absorb_new_folds(fold_mark);
        bool complete = branch();
        ExactResult r;
        r.size = best_;
        r.proved_optimal = complete && !out_of_budget_;
        r.nodes = nodes_;
        r.solution = best_sol_;
        r.solution.resize(n0_);
        return r;
    }

private:
    // Drops dead entries from the live list and returns the highest-degree
    // survivor.  The list is only ever permuted and truncated, so restoring the
    // saved length after a branch brings back exactly the vertices that the
    // branch removed.
    int compact_alive() {
        int best = -1, bestd = -1, ties = 0;
        for (int i = 0; i < alive_size_;) {
            int v = alive_[i];
            if (!dg_.alive(v)) {
                std::swap(alive_[i], alive_[alive_size_ - 1]);
                --alive_size_;
                continue;
            }
            int d = dg_.deg(v);
            if (d > bestd) { bestd = d; best = v; ties = 1; }
            else if (d == bestd && ++ties > 1 && (next_rand() % (uint32_t)ties) == 0) best = v;
            ++i;
        }
        return best;
    }

    uint32_t next_rand() {
        rng_ ^= rng_ << 13;
        rng_ ^= rng_ >> 7;
        rng_ ^= rng_ << 17;
        return (uint32_t)(rng_ >> 32);
    }

    void absorb_new_folds(int from) {
        for (int f = from; f < dg_.next_fold(); ++f) {
            if (!dg_.alive(f)) continue;
            if (alive_size_ == (int)alive_.size()) alive_.push_back(f);
            else alive_[alive_size_] = f;
            ++alive_size_;
        }
    }

    // Greedy clique cover: a clique holds at most one solution vertex, so the
    // number of cliques bounds the independent set in the residual graph.
    // Candidates are narrowed by marking rather than by pairwise adjacency
    // tests, which keeps a cover linear in the edges it touches.
    long long clique_cover_bound() {
        ++cover_stamp_;
        long long cliques = 0;
        for (int idx = 0; idx < alive_size_; ++idx) {
            int v = alive_[idx];
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

    // Returns false when the subtree was abandoned because of a budget.
    bool branch() {
        ++nodes_;
        if ((nodes_ & 0x3ff) == 0 && elapsed_() > deadline_) { out_of_budget_ = true; return false; }
        if (cfg_.node_budget >= 0 && nodes_ > cfg_.node_budget) { out_of_budget_ = true; return false; }

        if (dg_.num_alive() == 0) {
            if (red_.offset() > best_) { best_ = red_.offset(); record_solution(); }
            return true;
        }
        int v = compact_alive();
        if (v < 0) return true;
        if (red_.offset() + clique_cover_bound() <= best_) return true;

        bool complete = true;
        int saved_alive = alive_size_;

        // Branch 1: v stays out of the solution.
        Reducer::State s = red_.state();
        int fold_mark = dg_.next_fold();
        red_.exclude(v);
        red_.reduce();
        absorb_new_folds(fold_mark);
        if (!branch()) complete = false;
        red_.restore(s);
        alive_size_ = saved_alive;

        if (!out_of_budget_) {
            // Branch 2: v joins the solution.
            s = red_.state();
            fold_mark = dg_.next_fold();
            red_.include(v);
            red_.reduce();
            absorb_new_folds(fold_mark);
            if (!branch()) complete = false;
            red_.restore(s);
            alive_size_ = saved_alive;
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
    std::vector<int> alive_, cand_;
    int alive_size_ = 0;
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
