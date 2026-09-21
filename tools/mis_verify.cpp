// Independent verification of a solution file against the original graph.
//
// Accepts:
//   * one vertex id per line (0-based by default, --one-based for 1-based)
//   * a 0/1 vector with exactly n lines (the KaMIS --output format)
//   * PACE .vc cover files ("s vc n k" header, 1-based cover vertices)
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "../src/graph.hpp"

int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: mis-verify <graph> <solution> [--one-based] [--cover]\n");
        return 1;
    }
    bool one_based = false, is_cover = false;
    for (int i = 3; i < argc; ++i) {
        if (!strcmp(argv[i], "--one-based")) one_based = true;
        else if (!strcmp(argv[i], "--cover")) is_cover = true;
    }
    Graph g;
    std::string err;
    if (!load_graph(argv[1], g, err)) { fprintf(stderr, "error: %s\n", err.c_str()); return 2; }

    FILE* f = fopen(argv[2], "rb");
    if (!f) { fprintf(stderr, "error: cannot open %s\n", argv[2]); return 2; }
    std::vector<long long> vals;
    std::vector<char> line(1 << 16);
    bool pace_header = false;
    while (fgets(line.data(), (int)line.size(), f)) {
        char* p = line.data();
        while (*p == ' ' || *p == '\t') ++p;
        if (*p == '#' || *p == '%' || *p == 'c') continue;
        if (*p == 's') { pace_header = true; continue; }  // "s vc n k"
        if (*p == '\0' || *p == '\n' || *p == '\r') continue;
        vals.push_back(atoll(p));
    }
    fclose(f);
    if (pace_header) { one_based = true; is_cover = true; }

    std::vector<char> in_set(g.n, 0);
    bool as_vector = ((long long)vals.size() == g.n);
    if (as_vector) {
        for (long long v : vals) if (v != 0 && v != 1) { as_vector = false; break; }
    }
    if (as_vector && !is_cover) {
        for (int v = 0; v < g.n; ++v) in_set[v] = (char)vals[v];
    } else {
        std::vector<char> listed(g.n, 0);
        for (long long v : vals) {
            long long idx = one_based ? v - 1 : v;
            if (idx < 0 || idx >= g.n) { fprintf(stderr, "error: vertex %lld out of range\n", v); return 2; }
            listed[idx] = 1;
        }
        for (int v = 0; v < g.n; ++v) in_set[v] = is_cover ? (char)!listed[v] : listed[v];
    }

    long long size = 0;
    int bu = -1, bv = -1;
    if (!is_independent_set(g, in_set, size, bu, bv)) {
        printf("INVALID conflict_edge=(%d,%d)\n", bu, bv);
        return 3;
    }
    int missed = -1;
    bool maximal = is_maximal(g, in_set, missed);
    printf("VALID size=%lld maximal=%s%s\n", size, maximal ? "yes" : "no",
           maximal ? "" : (" missing_vertex=" + std::to_string(missed)).c_str());
    return 0;
}
