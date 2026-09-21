// Reduction engine operating on the dynamic graph.
//
// Every rule here is *safe*: applying it preserves at least one maximum
// independent set of the current graph, and the recorded reconstruction turns
// an optimum of the reduced graph into an optimum of the graph before the rule
// fired.  That property is what lets the search treat a completed dive as
// "exactly optimal given the branching decisions".
#pragma once

#include <cstdint>
#include <vector>

#include "dyngraph.hpp"

struct ReduceConfig {
    bool degree_rules = true;   // degree 0/1 and simplicial vertices
    bool fold2 = true;          // degree-2 vertex folding
    bool domination = true;
    bool unconfined = true;
    bool twin = true;
    int max_deg_clique = 8;     // simplicial test is quadratic in the degree
    int max_deg_domination = 24;
    int max_deg_unconfined = 64;   // the test is quadratic in the degree
    int unconfined_max_set = 8;
    long long work_budget = -1; // -1 for unlimited; counted in scanned edges
};

class Reducer {
public:
    // Reconstruction records, replayed in reverse to lift a solution.
    enum RKind : uint8_t { R_IN, R_OUT, R_FOLD2, R_TWIN };
    struct Rec {
        RKind kind;
        int a, b, c, d, e, f;
    };

    struct State {
        size_t trail;
        size_t recs;
        long long offset;
    };

    void init(DynGraph& g, const ReduceConfig& cfg) {
        g_ = &g;
        cfg_ = cfg;
        int cap = g.capacity();
        inq_.assign(cap, 0);
        mark_.assign(cap, 0);
        mark2_.assign(cap, 0);
        stamp_ = 0;
        stamp2_ = 0;
        queue_.clear();
        recs_.clear();
        offset_ = 0;
        work_ = 0;
    }

    long long offset() const { return offset_; }
    long long work() const { return work_; }
    const std::vector<Rec>& records() const { return recs_; }

    State state() const { return {g_->mark(), recs_.size(), offset_}; }

    void restore(const State& s) {
        g_->undo_to(s.trail);
        recs_.resize(s.recs);
        offset_ = s.offset;
        // Queue contents are advisory; drop them so no stale vertex is examined.
        for (int v : queue_) inq_[v] = 0;
        queue_.clear();
    }

    void push(int v) {
        if (!g_->alive(v) || inq_[v]) return;
        inq_[v] = 1;
        queue_.push_back(v);
    }

    void push_all() {
        for (int v = 0; v < g_->capacity(); ++v) push(v);
    }

    // Puts v into the solution and deletes N[v].
    void include(int v) {
        recs_.push_back({R_IN, v, 0, 0, 0, 0, 0});
        ++offset_;
        g_->neighbours(v, buf_);
        for (int u : buf_) recs_.push_back({R_OUT, u, 0, 0, 0, 0, 0});
        for (int u : buf_) kill(u);
        kill(v);
    }

    // Deletes v without putting it into the solution.
    void exclude(int v) {
        recs_.push_back({R_OUT, v, 0, 0, 0, 0, 0});
        kill(v);
    }

    // Applies rules until no rule fires or the work budget is exhausted.
    // Returns the number of vertices removed.
    int reduce() {
        int before = g_->num_alive();
        while (!queue_.empty()) {
            if (cfg_.work_budget >= 0 && work_ > cfg_.work_budget) break;
            int v = queue_.back();
            queue_.pop_back();
            inq_[v] = 0;
            if (!g_->alive(v)) continue;
            apply_rules(v);
        }
        return before - g_->num_alive();
    }

    // Reconstructs a solution on the original vertices.  in_sol must already
    // hold the decision for every vertex still alive; it is filled in for the
    // rest.  Returns the size of the resulting independent set.
    long long lift(std::vector<char>& in_sol) const {
        for (size_t i = recs_.size(); i-- > 0;) {
            const Rec& r = recs_[i];
            switch (r.kind) {
                case R_IN: in_sol[r.a] = 1; break;
                case R_OUT: in_sol[r.a] = 0; break;
                case R_FOLD2:
                    // a=v, b=u, c=w, d=fold vertex
                    if (r.d >= 0 && in_sol[r.d]) {
                        in_sol[r.b] = 1; in_sol[r.c] = 1; in_sol[r.a] = 0;
                    } else {
                        in_sol[r.a] = 1; in_sol[r.b] = 0; in_sol[r.c] = 0;
                    }
                    break;
                case R_TWIN:
                    // a=u, b=v (the twins), c,d,e = their shared neighbourhood,
                    // f = fold vertex
                    if (r.f >= 0 && in_sol[r.f]) {
                        in_sol[r.c] = 1; in_sol[r.d] = 1; in_sol[r.e] = 1;
                        in_sol[r.a] = 0; in_sol[r.b] = 0;
                    } else {
                        in_sol[r.a] = 1; in_sol[r.b] = 1;
                        in_sol[r.c] = 0; in_sol[r.d] = 0; in_sol[r.e] = 0;
                    }
                    break;
            }
        }
        long long size = 0;
        for (int v = 0; v < g_->original_n(); ++v) size += in_sol[v] ? 1 : 0;
        return size;
    }

private:
    void kill(int v) {
        if (!g_->alive(v)) return;
        g_->for_each_nbr(v, [&](int u) { push(u); });
        work_ += g_->deg(v);
        g_->remove(v);
    }

    void apply_rules(int v) {
        if (cfg_.degree_rules && rule_simplicial(v)) return;
        if (cfg_.fold2 && rule_fold2(v)) return;
        if (cfg_.twin && rule_twin(v)) return;
        if (cfg_.domination && rule_domination(v)) return;
        if (cfg_.unconfined && rule_unconfined(v)) return;
    }

    // Degree 0/1 and, more generally, a vertex whose neighbourhood is a clique:
    // such a vertex belongs to some maximum independent set.
    bool rule_simplicial(int v) {
        int d = g_->deg(v);
        if (d == 0) { include(v); return true; }
        if (d == 1) { include(v); return true; }
        if (d > cfg_.max_deg_clique) return false;
        g_->neighbours(v, nbuf_);
        ++stamp_;
        for (int u : nbuf_) mark_[u] = stamp_;
        for (int u : nbuf_) {
            int seen = 0;
            work_ += g_->deg(u);
            g_->for_each_nbr(u, [&](int w) { if (mark_[w] == stamp_) ++seen; });
            if (seen != d - 1) return false;
        }
        include(v);
        return true;
    }

    // Degree-2 folding: v with non-adjacent neighbours u, w is replaced by a
    // single vertex joined to N(u) u N(w); the optimum drops by exactly one.
    bool rule_fold2(int v) {
        if (g_->deg(v) != 2) return false;
        g_->neighbours(v, nbuf_);
        int u = nbuf_[0], w = nbuf_[1];
        if (adjacent(u, w)) return false;  // handled by the simplicial rule
        ++stamp_;
        mark_[v] = mark_[u] = mark_[w] = stamp_;
        fold_nbrs_.clear();
        ++stamp2_;
        for (int x : {u, w}) {
            work_ += g_->deg(x);
            g_->for_each_nbr(x, [&](int y) {
                if (mark_[y] == stamp_ || mark2_[y] == stamp2_) return;
                mark2_[y] = stamp2_;
                fold_nbrs_.push_back(y);
            });
        }
        // The fold vertex is created first: if the pool is exhausted nothing
        // has been deleted yet and the rule can simply decline to fire.
        int f = g_->add_fold_vertex(fold_nbrs_);
        if (f < 0) return false;
        kill(v); kill(u); kill(w);
        ++offset_;
        recs_.push_back({R_FOLD2, v, u, w, f, 0, 0});
        push(f);
        for (int y : fold_nbrs_) push(y);
        return true;
    }

    // Twin reduction for two non-adjacent degree-3 vertices with identical
    // neighbourhoods.
    bool rule_twin(int v) {
        if (g_->deg(v) != 3) return false;
        g_->neighbours(v, nbuf_);
        int p = nbuf_[0], q = nbuf_[1], r = nbuf_[2];
        ++stamp_;
        mark_[p] = mark_[q] = mark_[r] = stamp_;
        int u = -1;
        work_ += g_->deg(p);
        g_->for_each_nbr(p, [&](int x) {
            if (u >= 0 || x == v || g_->deg(x) != 3) return;
            int seen = 0;
            g_->for_each_nbr(x, [&](int y) { if (mark_[y] == stamp_) ++seen; });
            if (seen == 3) u = x;
        });
        if (u < 0) return false;
        bool edge_inside = adjacent(p, q) || adjacent(p, r) || adjacent(q, r);
        if (edge_inside) {
            // u and v can both be taken; their whole neighbourhood is dropped.
            recs_.push_back({R_IN, u, 0, 0, 0, 0, 0});
            recs_.push_back({R_IN, v, 0, 0, 0, 0, 0});
            recs_.push_back({R_OUT, p, 0, 0, 0, 0, 0});
            recs_.push_back({R_OUT, q, 0, 0, 0, 0, 0});
            recs_.push_back({R_OUT, r, 0, 0, 0, 0, 0});
            offset_ += 2;
            kill(p); kill(q); kill(r); kill(u); kill(v);
            return true;
        }
        ++stamp_;
        mark_[p] = mark_[q] = mark_[r] = mark_[u] = mark_[v] = stamp_;
        fold_nbrs_.clear();
        ++stamp2_;
        for (int x : {p, q, r}) {
            work_ += g_->deg(x);
            g_->for_each_nbr(x, [&](int y) {
                if (mark_[y] == stamp_ || mark2_[y] == stamp2_) return;
                mark2_[y] = stamp2_;
                fold_nbrs_.push_back(y);
            });
        }
        int f = g_->add_fold_vertex(fold_nbrs_);
        if (f < 0) return false;
        kill(p); kill(q); kill(r); kill(u); kill(v);
        offset_ += 2;
        recs_.push_back({R_TWIN, u, v, p, q, r, f});
        push(f);
        for (int y : fold_nbrs_) push(y);
        return true;
    }

    // If some neighbour u of v satisfies N[u] subset of N[v], then v is in no
    // "better" solution than u and can be discarded.
    bool rule_domination(int v) {
        int dv = g_->deg(v);
        if (dv == 0 || dv > cfg_.max_deg_domination) return false;
        g_->neighbours(v, nbuf_);
        ++stamp_;
        mark_[v] = stamp_;
        for (int u : nbuf_) mark_[u] = stamp_;
        for (int u : nbuf_) {
            if (g_->deg(u) > dv) continue;
            bool contained = true;
            work_ += g_->deg(u);
            g_->for_each_nbr(u, [&](int y) { if (mark_[y] != stamp_) contained = false; });
            if (contained) { exclude(v); return true; }
        }
        return false;
    }

    // Unconfined vertices (Xiao & Nagamochi): if the test succeeds, v lies
    // outside some maximum independent set and can be discarded.
    bool rule_unconfined(int v) {
        if (g_->deg(v) == 0 || g_->deg(v) > cfg_.max_deg_unconfined) return false;
        s_set_.clear();
        s_set_.push_back(v);
        ++stamp_;   // membership in S
        ++stamp2_;  // membership in N[S]
        mark_[v] = stamp_;
        mark2_[v] = stamp2_;
        g_->for_each_nbr(v, [&](int u) { mark2_[u] = stamp2_; });

        for (int iter = 0; iter < cfg_.unconfined_max_set; ++iter) {
            int best_u = -1, best_out = 1 << 30, best_w = -1;
            for (size_t si = 0; si < s_set_.size(); ++si) {
                int s = s_set_[si];
                work_ += g_->deg(s);
                g_->for_each_nbr(s, [&](int u) {
                    if (mark_[u] == stamp_) return;         // u is in S
                    if (best_out == 0) return;
                    int in_s = 0, outside = 0, witness = -1;
                    g_->for_each_nbr(u, [&](int y) {
                        if (mark_[y] == stamp_) ++in_s;
                        else if (mark2_[y] != stamp2_) { ++outside; witness = y; }
                    });
                    work_ += g_->deg(u);
                    if (in_s != 1) return;
                    if (outside < best_out) { best_out = outside; best_u = u; best_w = witness; }
                });
            }
            if (best_u < 0) return false;
            if (best_out == 0) { exclude(v); return true; }
            if (best_out > 1) return false;
            // Extend S by the single vertex outside N[S].
            s_set_.push_back(best_w);
            mark_[best_w] = stamp_;
            mark2_[best_w] = stamp2_;
            g_->for_each_nbr(best_w, [&](int y) { mark2_[y] = stamp2_; });
        }
        return false;
    }

    bool adjacent(int a, int b) {
        if (g_->deg(a) > g_->deg(b)) std::swap(a, b);
        bool found = false;
        work_ += g_->deg(a);
        g_->for_each_nbr(a, [&](int x) { if (x == b) found = true; });
        return found;
    }

    DynGraph* g_ = nullptr;
    ReduceConfig cfg_;
    std::vector<Rec> recs_;
    long long offset_ = 0;
    long long work_ = 0;
    std::vector<int> queue_, buf_, nbuf_, fold_nbrs_, s_set_;
    std::vector<char> inq_;
    std::vector<int> mark_, mark2_;
    int stamp_ = 0, stamp2_ = 0;
};
