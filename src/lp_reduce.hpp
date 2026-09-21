// Nemhauser-Trotter (LP) reduction.
//
// The vertex-cover LP is half-integral, and an optimal half-integral solution
// is read off a maximum matching in the bipartite double cover: split every
// vertex v into a_v and b_v, join a_u to b_v for each edge {u,v}, take a minimum
// vertex cover C of that bipartite graph, and set x_v = |C n {a_v, b_v}| / 2.
//
// Persistency then says some maximum independent set contains every vertex with
// x_v = 0 and avoids every vertex with x_v = 1, so both can be decided outright.
// Only the x_v = 1/2 vertices survive into the kernel.
//
// This is the one rule here that looks at the whole graph rather than a local
// neighbourhood, which is why it fires where the local rules have stalled.
#pragma once

#include <algorithm>
#include <vector>

#include "dyngraph.hpp"
#include "reductions.hpp"

class LPReduction {
public:
    // Applies the reduction to the live subgraph.  Returns the number of
    // vertices decided.
    int apply(DynGraph& g, Reducer& red) {
        live_.clear();
        pos_.assign(g.capacity(), -1);
        for (int v = 0; v < g.next_fold(); ++v)
            if (g.alive(v)) { pos_[v] = (int)live_.size(); live_.push_back(v); }
        int n = (int)live_.size();
        if (n == 0) return 0;

        // Bipartite adjacency: left copy of each vertex, right copies of its
        // neighbours.
        adj_start_.assign(n + 1, 0);
        long long total = 0;
        for (int i = 0; i < n; ++i) { adj_start_[i] = total; total += g.deg(live_[i]); }
        adj_start_[n] = total;
        adj_.resize(total);
        long long w = 0;
        for (int i = 0; i < n; ++i)
            g.for_each_nbr(live_[i], [&](int u) { adj_[w++] = pos_[u]; });

        match_l_.assign(n, -1);
        match_r_.assign(n, -1);
        dist_.assign(n + 1, 0);
        hopcroft_karp(n);

        // Koenig: Z is everything reachable from an unmatched left vertex along
        // alternating paths.  The minimum cover is (L \ Z) u (R n Z).
        std::vector<char> zl(n, 0), zr(n, 0);
        queue_.clear();
        for (int i = 0; i < n; ++i)
            if (match_l_[i] < 0) { zl[i] = 1; queue_.push_back(i); }
        for (size_t qi = 0; qi < queue_.size(); ++qi) {
            int u = queue_[qi];
            for (long long e = adj_start_[u]; e < adj_start_[u + 1]; ++e) {
                int v = adj_[e];
                if (zr[v] || match_l_[u] == v) continue;  // only non-matching edges forward
                zr[v] = 1;
                int back = match_r_[v];
                if (back >= 0 && !zl[back]) { zl[back] = 1; queue_.push_back(back); }
            }
        }

        // x_v = 0 -> take it; x_v = 1 -> drop it; x_v = 1/2 -> keep for the kernel.
        take_.clear();
        drop_.clear();
        for (int i = 0; i < n; ++i) {
            int cover = (zl[i] ? 0 : 1) + (zr[i] ? 1 : 0);
            if (cover == 0) take_.push_back(live_[i]);
            else if (cover == 2) drop_.push_back(live_[i]);
        }
        int decided = 0;
        for (int v : take_)
            if (g.alive(v)) { red.include(v); ++decided; }
        for (int v : drop_)
            if (g.alive(v)) { red.exclude(v); ++decided; }
        return decided;
    }

private:
    static const int kInf = 1 << 30;

    bool bfs(int n) {
        queue_.clear();
        for (int u = 0; u < n; ++u) {
            if (match_l_[u] < 0) { dist_[u] = 0; queue_.push_back(u); }
            else dist_[u] = kInf;
        }
        dist_[n] = kInf;
        for (size_t qi = 0; qi < queue_.size(); ++qi) {
            int u = queue_[qi];
            if (dist_[u] >= dist_[n]) continue;
            for (long long e = adj_start_[u]; e < adj_start_[u + 1]; ++e) {
                int w2 = match_r_[adj_[e]];
                int next = w2 < 0 ? n : w2;
                if (dist_[next] != kInf) continue;
                dist_[next] = dist_[u] + 1;
                if (next != n) queue_.push_back(next);
            }
        }
        return dist_[n] != kInf;
    }

    bool dfs(int u, int n) {
        for (long long e = adj_start_[u]; e < adj_start_[u + 1]; ++e) {
            int v = adj_[e];
            int w2 = match_r_[v];
            int next = w2 < 0 ? n : w2;
            if (dist_[next] != dist_[u] + 1) continue;
            if (next == n || dfs(next, n)) {
                match_l_[u] = v;
                match_r_[v] = u;
                return true;
            }
        }
        dist_[u] = kInf;
        return false;
    }

    void hopcroft_karp(int n) {
        while (bfs(n))
            for (int u = 0; u < n; ++u)
                if (match_l_[u] < 0) dfs(u, n);
    }

    std::vector<int> live_, pos_, adj_, match_l_, match_r_, dist_, queue_, take_, drop_;
    std::vector<long long> adj_start_;
};
