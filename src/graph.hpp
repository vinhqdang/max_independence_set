// Static CSR graph plus readers for the common benchmark formats.
#pragma once

#include <cstdint>
#include <string>
#include <vector>

struct Graph {
    int n = 0;                     // number of vertices
    long long m = 0;               // number of undirected edges
    std::vector<long long> start;  // size n + 1, CSR offsets
    std::vector<int> adj;          // size 2 * m

    long long degree(int v) const { return start[v + 1] - start[v]; }
    const int* nbr_begin(int v) const { return adj.data() + start[v]; }
    const int* nbr_end(int v) const { return adj.data() + start[v + 1]; }
    bool has_edge(int u, int v) const;
};

// Reads METIS (.graph), edge list (.txt/.edges/.el), Matrix Market (.mtx) and
// DIMACS (.clq/.col/.gr) files.  Self loops are dropped, parallel edges merged,
// and vertex ids are compacted to 0..n-1.  Returns false and fills err on
// failure.
bool load_graph(const std::string& path, Graph& g, std::string& err);

// Writes the graph in METIS format (used to hand instances to external solvers).
bool write_metis(const std::string& path, const Graph& g, std::string& err);

// Builds the complement graph.  Only safe for small n (used for DIMACS clique
// instances that are stated in complement form).
Graph complement(const Graph& g);

// Verification helpers.
bool is_independent_set(const Graph& g, const std::vector<char>& in_set, long long& size, int& bad_u, int& bad_v);
bool is_maximal(const Graph& g, const std::vector<char>& in_set, int& missed);
