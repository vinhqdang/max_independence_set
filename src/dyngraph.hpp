// Dynamic graph with last-in-first-out undo.
//
// The graph shrinks as reductions and branching decisions are applied, and any
// prefix of that history can be rewound in time proportional to the work being
// undone.  This is what makes it affordable to revise a branching decision deep
// in a dive instead of restarting the dive from scratch.
//
// Layout.  Original edges live in a CSR-style array in which every entry knows
// the position of its twin (bpos_).  Deleting a vertex swaps its entry to the
// end of each neighbour's live range and shrinks that range, so a live
// neighbourhood is always a contiguous run and degrees are exact.  Undoing the
// deletion just grows the ranges back: nothing has to be swapped back, because
// later operations never move an entry that sits outside the live range.
//
// Edges created by folding cannot be stored in the static array, so they go
// into a per-vertex overflow list.  Those lists are append-only and filtered by
// the alive flag on traversal, which keeps undo trivial (a pop_back) at the cost
// of scanning a few dead entries.  Only vertices that take part in a fold ever
// get an overflow list.
#pragma once

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <vector>

#include "graph.hpp"

class DynGraph {
public:
    // fold_pool is the number of extra vertex ids reserved for fold vertices.
    void init(const Graph& g, int fold_pool) {
        n0_ = g.n;
        cap_ = g.n + fold_pool;
        bstart_.assign(cap_ + 1, 0);
        bend_.assign(cap_, 0);
        badj_ = g.adj;
        bpos_.assign(badj_.size(), 0);
        for (int v = 0; v <= g.n; ++v) bstart_[v] = g.start[v];
        for (int v = g.n; v <= cap_; ++v) bstart_[v] = (long long)badj_.size();
        for (int v = 0; v < g.n; ++v) bend_[v] = g.start[v + 1];
        for (int v = g.n; v < cap_; ++v) bend_[v] = (long long)badj_.size();

        // Twin positions: walk each adjacency list and match u -> v with v -> u.
        std::vector<long long> cursor(g.n);
        for (int v = 0; v < g.n; ++v) cursor[v] = g.start[v];
        for (int v = 0; v < g.n; ++v) {
            for (long long i = g.start[v]; i < g.start[v + 1]; ++i) {
                int u = g.adj[i];
                if (u < v) continue;  // handled when the smaller endpoint was processed
                long long j = cursor[u];
                while (j < g.start[u + 1] && g.adj[j] != v) ++j;
                assert(j < g.start[u + 1] && "graph is not symmetric");
                bpos_[i] = j;
                bpos_[j] = i;
                cursor[u] = j + 1;
            }
        }

        alive_.assign(cap_, 0);
        deg_.assign(cap_, 0);
        exslot_.assign(cap_, -1);
        exadj_.clear();  // init may be called repeatedly on a reused instance
        for (int v = 0; v < g.n; ++v) { alive_[v] = 1; deg_[v] = (int)g.degree(v); }
        nalive_ = g.n;
        next_fold_ = g.n;
        trail_.clear();
    }

    int capacity() const { return cap_; }
    int original_n() const { return n0_; }
    int num_alive() const { return nalive_; }
    bool alive(int v) const { return alive_[v] != 0; }
    int deg(int v) const { return deg_[v]; }
    bool is_fold_vertex(int v) const { return v >= n0_; }
    // Next unused fold id; used to spot vertices created by the last cascade.
    int next_fold() const { return next_fold_; }

    // Calls f(u) for every live neighbour u of v.
    template <class F>
    void for_each_nbr(int v, F&& f) const {
        for (long long i = bstart_[v]; i < bend_[v]; ++i) f(badj_[i]);
        int s = exslot_[v];
        if (s < 0) return;
        const std::vector<int>& e = exadj_[s];
        for (size_t k = 0; k < e.size(); ++k)
            if (alive_[e[k]]) f(e[k]);
    }

    // Collects the live neighbourhood of v into out (cleared first).
    void neighbours(int v, std::vector<int>& out) const {
        out.clear();
        for_each_nbr(v, [&](int u) { out.push_back(u); });
    }

    void remove(int v) {
        assert(alive_[v]);
        alive_[v] = 0;
        --nalive_;
        for (long long i = bstart_[v]; i < bend_[v]; ++i) {
            int u = badj_[i];
            long long j = bpos_[i];
            long long last = --bend_[u];
            swap_base(j, last);
            --deg_[u];
        }
        int s = exslot_[v];
        if (s >= 0) {
            const std::vector<int>& e = exadj_[s];
            for (size_t k = 0; k < e.size(); ++k)
                if (alive_[e[k]]) --deg_[e[k]];
        }
        trail_.push_back({OP_DEL, v});
    }

    // Creates a fold vertex adjacent to every (live) vertex in nbrs.
    // Returns -1 when the fold pool is exhausted.
    int add_fold_vertex(const std::vector<int>& nbrs) {
        if (next_fold_ >= cap_) return -1;
        int f = next_fold_++;
        alive_[f] = 1;
        deg_[f] = 0;
        ++nalive_;
        trail_.push_back({OP_NEWFOLD, f});
        for (int u : nbrs) {
            if (!alive_[u]) continue;
            append(f, u);
            append(u, f);
        }
        return f;
    }

    size_t mark() const { return trail_.size(); }

    void undo_to(size_t level) {
        while (trail_.size() > level) {
            Op op = trail_.back();
            trail_.pop_back();
            switch (op.kind) {
                case OP_DEL: {
                    int v = op.v;
                    alive_[v] = 1;
                    ++nalive_;
                    for (long long i = bstart_[v]; i < bend_[v]; ++i) {
                        int u = badj_[i];
                        ++bend_[u];
                        ++deg_[u];
                    }
                    int s = exslot_[v];
                    if (s >= 0) {
                        const std::vector<int>& e = exadj_[s];
                        for (size_t k = 0; k < e.size(); ++k)
                            if (alive_[e[k]]) ++deg_[e[k]];
                    }
                    break;
                }
                case OP_APPEND: {
                    // Both endpoints were live when the edge was appended and
                    // are live again now, so the degree update is unconditional.
                    --deg_[op.v];
                    exadj_[exslot_[op.v]].pop_back();
                    break;
                }
                case OP_NEWFOLD: {
                    int f = op.v;
                    alive_[f] = 0;
                    --nalive_;
                    --next_fold_;
                    break;
                }
            }
        }
    }

    // Rebuilds the live subgraph as a static graph, together with the mapping
    // from new ids back to dynamic ids.
    void extract(Graph& out, std::vector<int>& id_map) const {
        id_map.clear();
        std::vector<int> pos(cap_, -1);
        for (int v = 0; v < cap_; ++v)
            if (alive_[v]) { pos[v] = (int)id_map.size(); id_map.push_back(v); }
        int n = (int)id_map.size();
        out.n = n;
        out.start.assign(n + 1, 0);
        long long total = 0;
        for (int i = 0; i < n; ++i) { out.start[i] = total; total += deg_[id_map[i]]; }
        out.start[n] = total;
        out.adj.assign(total, 0);
        long long w = 0;
        for (int i = 0; i < n; ++i) {
            for_each_nbr(id_map[i], [&](int u) { out.adj[w++] = pos[u]; });
            std::sort(out.adj.begin() + out.start[i], out.adj.begin() + out.start[i + 1]);
        }
        out.m = total / 2;
    }

    // Debug helper: recomputes degrees and checks structural invariants.
    bool validate() const {
        int live = 0;
        for (int v = 0; v < cap_; ++v) {
            if (!alive_[v]) continue;
            ++live;
            int d = 0;
            for_each_nbr(v, [&](int u) {
                if (!alive_[u]) return;  // for_each_nbr already filters
                ++d;
            });
            if (d != deg_[v]) return false;
            for (long long i = bstart_[v]; i < bend_[v]; ++i) {
                if (!alive_[badj_[i]]) return false;         // live range must be live
                if (bpos_[bpos_[i]] != i) return false;      // twin links consistent
                if (badj_[bpos_[i]] != v) return false;
            }
        }
        return live == nalive_;
    }

private:
    enum OpKind : uint8_t { OP_DEL, OP_APPEND, OP_NEWFOLD };
    struct Op {
        OpKind kind;
        int v;
    };

    void swap_base(long long a, long long b) {
        if (a == b) return;
        std::swap(badj_[a], badj_[b]);
        std::swap(bpos_[a], bpos_[b]);
        bpos_[bpos_[a]] = a;
        bpos_[bpos_[b]] = b;
    }

    int slot(int v) {
        if (exslot_[v] < 0) {
            exslot_[v] = (int)exadj_.size();
            exadj_.emplace_back();
        }
        return exslot_[v];
    }

    void append(int v, int u) {
        exadj_[slot(v)].push_back(u);
        ++deg_[v];
        trail_.push_back({OP_APPEND, v});
    }

    int n0_ = 0, cap_ = 0, nalive_ = 0, next_fold_ = 0;
    std::vector<long long> bstart_, bend_, bpos_;
    std::vector<int> badj_;
    std::vector<int> deg_;
    std::vector<char> alive_;
    std::vector<int> exslot_;
    std::vector<std::vector<int>> exadj_;
    std::vector<Op> trail_;
};
