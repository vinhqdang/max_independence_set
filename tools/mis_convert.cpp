// Converts a graph into the input formats required by the baseline solvers.
//
//   metis  : KaMIS (redumis, online_mis)
//   chang  : binary directory format of Chang et al.'s reducing-peeling code
//   pace   : PACE 2019 format, read by the WeGotYouCovered vc_solver
//   dimacs : DIMACS edge format
#include <cstdio>
#include <cstring>
#include <string>
#include <sys/stat.h>
#include <vector>

#include "../src/graph.hpp"

namespace {

bool write_chang(const std::string& dir, const Graph& g, std::string& err) {
    mkdir(dir.c_str(), 0755);
    FILE* f = fopen((dir + "/b_degree.bin").c_str(), "wb");
    if (!f) { err = "cannot write b_degree.bin"; return false; }
    int int_size = (int)sizeof(int);
    unsigned int n = (unsigned int)g.n;
    unsigned int m = (unsigned int)(2 * g.m);  // the reader expects the degree sum
    fwrite(&int_size, sizeof(int), 1, f);
    fwrite(&n, sizeof(unsigned int), 1, f);
    fwrite(&m, sizeof(unsigned int), 1, f);
    std::vector<unsigned int> deg(g.n);
    for (int v = 0; v < g.n; ++v) deg[v] = (unsigned int)g.degree(v);
    fwrite(deg.data(), sizeof(unsigned int), g.n, f);
    fclose(f);

    f = fopen((dir + "/b_adj.bin").c_str(), "wb");
    if (!f) { err = "cannot write b_adj.bin"; return false; }
    fwrite(g.adj.data(), sizeof(int), g.adj.size(), f);
    fclose(f);
    return true;
}

bool write_pace(const std::string& path, const Graph& g, std::string& err) {
    FILE* f = fopen(path.c_str(), "wb");
    if (!f) { err = "cannot write " + path; return false; }
    std::string out;
    out.reserve(1 << 22);
    char buf[64];
    snprintf(buf, sizeof buf, "p td %d %lld\n", g.n, g.m);
    out += buf;
    for (int v = 0; v < g.n; ++v)
        for (long long i = g.start[v]; i < g.start[v + 1]; ++i) {
            if (g.adj[i] <= v) continue;
            int len = snprintf(buf, sizeof buf, "%d %d\n", v + 1, g.adj[i] + 1);
            out.append(buf, len);
            if (out.size() > (1u << 22)) { fwrite(out.data(), 1, out.size(), f); out.clear(); }
        }
    fwrite(out.data(), 1, out.size(), f);
    fclose(f);
    return true;
}

// Plain 0-based edge list; used to hand solvers a graph whose vertex ids match
// the ones the verifier works with.
bool write_edgelist(const std::string& path, const Graph& g, std::string& err) {
    FILE* f = fopen(path.c_str(), "wb");
    if (!f) { err = "cannot write " + path; return false; }
    std::string out;
    out.reserve(1 << 22);
    char buf[32];
    for (int v = 0; v < g.n; ++v)
        for (long long i = g.start[v]; i < g.start[v + 1]; ++i)
            if (g.adj[i] > v) {
                int len = snprintf(buf, sizeof buf, "%d %d\n", v, g.adj[i]);
                out.append(buf, len);
                if (out.size() > (1u << 22)) { fwrite(out.data(), 1, out.size(), f); out.clear(); }
            }
    fwrite(out.data(), 1, out.size(), f);
    fclose(f);
    return true;
}

bool write_dimacs(const std::string& path, const Graph& g, std::string& err) {
    FILE* f = fopen(path.c_str(), "wb");
    if (!f) { err = "cannot write " + path; return false; }
    fprintf(f, "p edge %d %lld\n", g.n, g.m);
    for (int v = 0; v < g.n; ++v)
        for (long long i = g.start[v]; i < g.start[v + 1]; ++i)
            if (g.adj[i] > v) fprintf(f, "e %d %d\n", v + 1, g.adj[i] + 1);
    fclose(f);
    return true;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr,
                "usage: mis-convert <input> [--complement] [--metis F] [--chang DIR] [--pace F]\n"
                "                   [--dimacs F] [--edgelist F] [--stats]\n");
        return 1;
    }
    Graph g;
    std::string err;
    if (!load_graph(argv[1], g, err)) { fprintf(stderr, "error: %s\n", err.c_str()); return 1; }

    bool stats = false;
    // DIMACS/BHOSLIB clique instances are stated in clique form; the maximum
    // independent set lives in the complement.
    for (int i = 2; i < argc; ++i) {
        if (std::string(argv[i]) == "--complement") { g = complement(g); break; }
    }
    for (int i = 2; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--stats") { stats = true; continue; }
        if (a == "--complement") continue;
        if (i + 1 >= argc) { fprintf(stderr, "error: %s needs an argument\n", a.c_str()); return 1; }
        std::string v = argv[++i];
        bool ok = true;
        if (a == "--metis") ok = write_metis(v, g, err);
        else if (a == "--chang") ok = write_chang(v, g, err);
        else if (a == "--pace") ok = write_pace(v, g, err);
        else if (a == "--dimacs") ok = write_dimacs(v, g, err);
        else if (a == "--edgelist") ok = write_edgelist(v, g, err);
        else { fprintf(stderr, "error: unknown option %s\n", a.c_str()); return 1; }
        if (!ok) { fprintf(stderr, "error: %s\n", err.c_str()); return 1; }
    }
    if (stats) {
        long long maxdeg = 0, isolated = 0;
        for (int v = 0; v < g.n; ++v) {
            maxdeg = std::max(maxdeg, g.degree(v));
            if (g.degree(v) == 0) ++isolated;
        }
        printf("n=%d m=%lld avg_deg=%.3f max_deg=%lld isolated=%lld\n", g.n, g.m,
               g.n ? 2.0 * (double)g.m / g.n : 0.0, maxdeg, isolated);
    }
    return 0;
}
