// Exact maximum independent set by branch-and-reduce.
//
// Used in two roles: as a stand-alone exact solver (which also certifies the
// heuristic results on instances that are small enough), and as the engine that
// solves the large neighbourhoods explored by the local search.  The reduction
// suite is what makes the second role affordable: neighbourhoods of a few
// thousand vertices usually collapse to a kernel of a few dozen.
#pragma once

#include <cstdint>
#include <functional>
#include <vector>

#include "graph.hpp"
#include "reductions.hpp"

struct ExactResult {
    long long size = 0;
    bool proved_optimal = false;
    long long nodes = 0;
    std::vector<char> solution;  // indexed by vertex of the input graph
};

struct ExactConfig {
    ReduceConfig red;
    long long node_budget = -1;   // -1 for unlimited
    long long lower_bound = 0;    // prune against a solution already in hand
    bool need_solution = true;
    uint64_t seed = 0;  // randomises tie-breaking so repeated solves of the same
                        // region can return different optima of equal size
};

// Solves g exactly (or until the budget runs out).  elapsed() supplies the
// wall-clock reading used against deadline.
ExactResult solve_exact(const Graph& g, const ExactConfig& cfg, double deadline,
                        const std::function<double()>& elapsed);
