// Correctness tests.
//
// The reduction rules are the part of the solver that can silently return a
// wrong answer: an unsafe rule still produces a valid independent set, just not
// a maximum one.  These tests therefore check the exact solver against brute
// force on small random graphs, and separately check that the dynamic graph
// restores itself exactly after an undo.
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <random>
#include <vector>

#include "../src/cascade.hpp"
#include "../src/dyngraph.hpp"
#include "../src/exact.hpp"
#include "../src/graph.hpp"

namespace {

int failures = 0;

void check(bool ok, const char* what, int seed) {
    if (!ok) {
        printf("  FAIL %s (seed %d)\n", what, seed);
        ++failures;
    }
}

Graph random_graph(int n, double p, std::mt19937& rng) {
    std::uniform_real_distribution<double> u(0.0, 1.0);
    std::vector<std::vector<int>> adj(n);
    for (int a = 0; a < n; ++a)
        for (int b = a + 1; b < n; ++b)
            if (u(rng) < p) { adj[a].push_back(b); adj[b].push_back(a); }
    Graph g;
    g.n = n;
    g.start.assign(n + 1, 0);
    long long total = 0;
    for (int v = 0; v < n; ++v) { g.start[v] = total; total += (long long)adj[v].size(); }
    g.start[n] = total;
    g.adj.resize(total);
    long long w = 0;
    for (int v = 0; v < n; ++v) for (int u2 : adj[v]) g.adj[w++] = u2;
    g.m = total / 2;
    return g;
}

// Exhaustive maximum independent set, for graphs of at most 24 vertices.
long long brute_force(const Graph& g) {
    std::vector<uint32_t> nbr(g.n, 0);
    for (int v = 0; v < g.n; ++v)
        for (long long i = g.start[v]; i < g.start[v + 1]; ++i) nbr[v] |= 1u << g.adj[i];
    long long best = 0;
    for (uint32_t mask = 0; mask < (1u << g.n); ++mask) {
        bool ok = true;
        for (int v = 0; v < g.n && ok; ++v)
            if ((mask >> v) & 1) { if (nbr[v] & mask) ok = false; }
        if (ok) best = std::max<long long>(best, __builtin_popcount(mask));
    }
    return best;
}

double no_time() { return 0.0; }

void test_exact_against_brute_force() {
    printf("exact solver vs brute force\n");
    std::function<double()> clock = no_time;
    for (int seed = 1; seed <= 300; ++seed) {
        std::mt19937 rng(seed);
        int n = 4 + (int)(rng() % 17);
        double p = 0.08 + 0.5 * (double)(rng() % 100) / 100.0;
        Graph g = random_graph(n, p, rng);
        ExactConfig cfg;
        ExactResult r = solve_exact(g, cfg, 1e18, clock);
        long long truth = brute_force(g);
        check(r.size == truth, "exact size matches brute force", seed);
        check(r.proved_optimal, "search completed", seed);
        // The returned set must actually be independent and of the stated size.
        long long size = 0;
        int bu, bv;
        std::vector<char> sol(r.solution.begin(), r.solution.end());
        sol.resize(g.n);
        check(is_independent_set(g, sol, size, bu, bv), "returned set is independent", seed);
        check(size == r.size, "returned set has the stated size", seed);
    }
}

void test_reductions_preserve_optimum() {
    printf("reductions preserve the optimum\n");
    std::function<double()> clock = no_time;
    for (int seed = 1; seed <= 200; ++seed) {
        std::mt19937 rng(1000 + seed);
        int n = 6 + (int)(rng() % 15);
        Graph g = random_graph(n, 0.1 + 0.25 * (double)(rng() % 100) / 100.0, rng);
        long long truth = brute_force(g);
        // Each rule is switched off in turn: every subset must still be exact.
        for (int off = 0; off < 5; ++off) {
            ExactConfig cfg;
            if (off == 0) cfg.red.fold2 = false;
            if (off == 1) cfg.red.twin = false;
            if (off == 2) cfg.red.domination = false;
            if (off == 3) cfg.red.unconfined = false;
            if (off == 4) cfg.red.degree_rules = false;
            ExactResult r = solve_exact(g, cfg, 1e18, clock);
            check(r.size == truth, "exact with a rule disabled", seed);
        }
    }
}

void test_dyngraph_undo() {
    printf("dynamic graph undo restores the graph\n");
    for (int seed = 1; seed <= 200; ++seed) {
        std::mt19937 rng(2000 + seed);
        int n = 8 + (int)(rng() % 25);
        Graph g = random_graph(n, 0.2, rng);
        DynGraph dg;
        dg.init(g, 64);
        check(dg.validate(), "initial state valid", seed);
        size_t root = dg.mark();
        std::vector<int> degrees(n);
        for (int v = 0; v < n; ++v) degrees[v] = dg.deg(v);
        int alive_before = dg.num_alive();

        for (int step = 0; step < 40; ++step) {
            int v = (int)(rng() % dg.capacity());
            if (!dg.alive(v)) continue;
            if (rng() % 4 == 0) {
                // Fold: a new vertex joined to a random live subset.
                std::vector<int> nbrs;
                for (int u = 0; u < dg.capacity(); ++u)
                    if (dg.alive(u) && u != v && rng() % 3 == 0) nbrs.push_back(u);
                dg.add_fold_vertex(nbrs);
            } else {
                dg.remove(v);
            }
            check(dg.validate(), "state valid mid-sequence", seed);
        }
        dg.undo_to(root);
        check(dg.validate(), "state valid after undo", seed);
        check(dg.num_alive() == alive_before, "vertex count restored", seed);
        bool degrees_ok = true;
        for (int v = 0; v < n; ++v) if (dg.deg(v) != degrees[v]) degrees_ok = false;
        check(degrees_ok, "degrees restored", seed);
    }
}

void test_heuristic_returns_valid_sets() {
    printf("heuristic returns valid independent sets\n");
    for (int seed = 1; seed <= 40; ++seed) {
        std::mt19937 rng(3000 + seed);
        int n = 30 + (int)(rng() % 400);
        Graph g = random_graph(n, 0.02 + 0.1 * (double)(rng() % 100) / 100.0, rng);
        CascadeConfig cfg;
        cfg.seed = seed;
        double t = 0.0;
        std::function<double()> clock = [&]() { return t += 1e-4; };
        Cascade solver(g, cfg);
        long long size = solver.run(0.05, clock);
        std::vector<char> sol(solver.best_solution().begin(), solver.best_solution().end());
        sol.resize(g.n);
        long long got = 0;
        int bu, bv;
        check(is_independent_set(g, sol, got, bu, bv), "heuristic set is independent", seed);
        check(got == size, "reported size matches the set", seed);
        int missed;
        check(is_maximal(g, sol, missed), "heuristic set is maximal", seed);
    }
}

}  // namespace

int main() {
    test_dyngraph_undo();
    test_exact_against_brute_force();
    test_reductions_preserve_optimum();
    test_heuristic_returns_valid_sets();
    if (failures == 0) {
        printf("all tests passed\n");
        return 0;
    }
    printf("%d failures\n", failures);
    return 1;
}
