#include <chrono>
#include <cstdio>
#include <cstring>
#include <string>

#include "cascade.hpp"
#include "exact.hpp"
#include "graph.hpp"

namespace {

double now_seconds(const std::chrono::steady_clock::time_point& t0) {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
}

void usage() {
    fprintf(stderr,
            "usage: cascade <graph> [options]\n"
            "  --output FILE       write the independent set (one 0/1 per vertex)\n"
            "  --time-limit SEC    wall-clock budget (default 60)\n"
            "  --seed N            random seed (default 1)\n"
            "  --sample N          candidates inspected per decision (default 32)\n"
            "  --include-prob P    probability of an include decision (default 0)\n"
            "  --kernel-only       stop after kernelization\n"
            "  --exact             prove optimality by branch-and-reduce\n"
            "  --no-lns            disable exact neighbourhood moves (ablation)\n"
            "  --no-perturb        disable perturbation and restarts (ablation)\n"
            "  --no-dive-moves     disable decision-space local search (ablation)\n"
            "  --no-reductions X   disable rules: fold2,twin,dom,unconf,degree\n");
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) { usage(); return 1; }
    std::string path = argv[1];
    std::string out;
    CascadeConfig cfg;
    // Diving re-reduces after every decision, so it drops the quadratic rules.
    cfg.dive_red.unconfined = false;
    cfg.dive_red.max_deg_domination = 8;
    cfg.dive_red.max_deg_clique = 4;
    bool kernel_only = false;
    bool exact = false;

    for (int i = 2; i < argc; ++i) {
        std::string a = argv[i];
        auto next = [&]() -> std::string {
            if (i + 1 >= argc) { usage(); exit(1); }
            return argv[++i];
        };
        if (a == "--output") out = next();
        else if (a == "--time-limit") cfg.time_limit = atof(next().c_str());
        else if (a == "--seed") cfg.seed = strtoull(next().c_str(), nullptr, 10);
        else if (a == "--sample") cfg.sample_size = atoi(next().c_str());
        else if (a == "--include-prob") cfg.include_prob = atof(next().c_str());
        else if (a == "--kernel-only") { kernel_only = true; cfg.kernel_only = true; }
        else if (a == "--no-lp") cfg.use_lp = false;
        else if (a == "--restart-idle") cfg.restart_idle_dives = atof(next().c_str());
        else if (a == "--kernel-share") cfg.kernel_share = atof(next().c_str());
        else if (a == "--exact") exact = true;
        else if (a == "--no-lns") cfg.use_lns = false;
        else if (a == "--no-perturb") cfg.use_perturbation = false;
        else if (a == "--no-dive-moves") cfg.use_dive_moves = false;
        else if (a == "--dive-moves") cfg.use_dive_moves = true;
        else if (a == "--lns-free") cfg.lns_start_free = atoi(next().c_str());
        else if (a == "--lns-budget") cfg.lns_node_budget = atoll(next().c_str());
        else if (a == "--lns-slice") cfg.lns_slice = atof(next().c_str());
        else if (a == "--no-reductions") {
            std::string v = next();
            if (v.find("fold2") != std::string::npos) cfg.red.fold2 = false;
            if (v.find("twin") != std::string::npos) cfg.red.twin = false;
            if (v.find("dom") != std::string::npos) cfg.red.domination = false;
            if (v.find("unconf") != std::string::npos) cfg.red.unconfined = false;
            if (v.find("degree") != std::string::npos) cfg.red.degree_rules = false;
        } else { usage(); return 1; }
    }

    auto t0 = std::chrono::steady_clock::now();
    Graph g;
    std::string err;
    if (!load_graph(path, g, err)) { fprintf(stderr, "error: %s\n", err.c_str()); return 1; }
    double read_time = now_seconds(t0);

    auto tstart = std::chrono::steady_clock::now();
    auto elapsed = [&]() { return now_seconds(tstart); };

    if (exact) {
        ExactConfig ec;
        ec.red = cfg.red;
        ec.seed_greedy = true;
        ExactResult r = solve_exact(g, ec, cfg.time_limit, elapsed);
        printf("instance=%s n=%d m=%lld size=%lld time=%.3f read_time=%.3f "
               "nodes=%lld proved_optimal=%d\n",
               path.c_str(), g.n, g.m, r.size, elapsed(), read_time, r.nodes,
               r.proved_optimal ? 1 : 0);
            if (!out.empty()) {
            FILE* f = fopen(out.c_str(), "wb");
            if (!f) { fprintf(stderr, "error: cannot write %s\n", out.c_str()); return 1; }
            std::string buf;
            buf.reserve(2 * g.n);
            for (int v = 0; v < g.n; ++v)
                { buf.push_back(v < (int)r.solution.size() && r.solution[v] ? '1' : '0'); buf.push_back('\n'); }
            fwrite(buf.data(), 1, buf.size(), f);
            fclose(f);
        }
        return 0;
    }

    Cascade solver(g, cfg);
    long long size = solver.run(cfg.time_limit, elapsed);
    double total = elapsed();

    const CascadeStats& st = solver.stats();
    printf("instance=%s n=%d m=%lld size=%lld time=%.3f read_time=%.3f "
           "kernel_n=%lld kernel_m=%lld kernel_offset=%lld kernel_time=%.3f "
           "lp_decided=%lld kernel_truncated=%d first_dive=%lld first_dive_time=%.3f "
           "lns_moves=%lld lns_impr=%lld lns_gain=%lld lns_plateau=%lld "
           "lns_free=%d restarts=%lld perturb=%lld sweeps=%lld\n",
           path.c_str(), g.n, g.m, size, total, read_time,
           st.kernel_n, st.kernel_m, st.kernel_offset, st.kernel_seconds,
           st.lp_decided, st.kernel_truncated, st.first_dive_value, st.first_dive_seconds,
           st.lns_moves, st.lns_improvements, st.lns_gain, st.lns_plateau,
           st.lns_expand, st.restarts, st.perturbations, st.lns_sweeps);

    if (!out.empty()) {
        FILE* f = fopen(out.c_str(), "wb");
        if (!f) { fprintf(stderr, "error: cannot write %s\n", out.c_str()); return 1; }
        const std::vector<char>& sol = solver.best_solution();
        std::string buf;
        buf.reserve(2 * g.n);
        for (int v = 0; v < g.n; ++v) { buf.push_back(sol[v] ? '1' : '0'); buf.push_back('\n'); }
        fwrite(buf.data(), 1, buf.size(), f);
        fclose(f);
    }
    return 0;
}
