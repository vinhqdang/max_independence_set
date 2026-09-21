// CASCADE: local search in the space of branching decisions.
//
// A *dive* is a sequence of decisions (include / exclude a vertex); after each
// decision the reduction engine runs to fixpoint.  When the graph is empty the
// dive yields an independent set that is exactly optimal *conditioned on* its
// decisions, because every other vertex was resolved by a safe rule.  Reduce-
// and-peel is the special case "always exclude the maximum-degree vertex, never
// revise".  CASCADE keeps the dive on an undoable trail and searches over dives:
// it rewinds to a chosen level and re-dives differently, at a cost proportional
// to the suffix rather than the whole instance.
#pragma once

#include <algorithm>
#include <cstdint>
#include <functional>
#include <random>
#include <vector>

#include "dyngraph.hpp"
#include "graph.hpp"
#include "lp_reduce.hpp"
#include "reductions.hpp"

struct CascadeConfig {
    double time_limit = 60.0;
    uint64_t seed = 1;
    int sample_size = 32;       // candidates inspected per decision (BMS style)
    double include_prob = 0.0;  // probability of an include decision while diving
    bool use_lns = true;        // exact large-neighbourhood moves
    int lns_start_free = 4;     // incumbent vertices freed per region; self-tuning
    int lns_max_free = 4096;
    int lns_region_cap = 3000;  // regions larger than this are too slow to solve
    int lns_stale_grow = 512;   // fruitless proved moves before regions grow
    bool use_dive_moves = false; // decision-space local search (ablation)
    int lns_start_target = 64;  // neighbourhood size; doubled after each sweep
    int lns_max_target = 20000;
    long long lns_node_budget = 20000;
    bool kernel_only = false;   // stop after kernelization
    bool use_lp = true;         // Nemhauser-Trotter reduction during kernelization
    // The LP reduction has to run to completion to stay sound: a partial
    // matching still yields a valid cover, but not a minimum one, and
    // persistency only holds for an optimal LP solution.  It is therefore
    // gated by size and by a share of the budget rather than interrupted.
    long long lp_max_edges = 60000000;
    double lp_budget_share = 0.25;
    bool use_perturbation = true;
    int perturb_rounds = 24;    // neighbourhood moves granted per perturbation
    int perturb_max_strength = 32;
    // Fruitless perturbations at full strength before the search restarts from a
    // fresh randomised dive, keeping the best solution found so far.
    long long restart_after = 200;
    double lns_slice = 0.05;    // seconds allowed per neighbourhood solve
    double lns_max_slice = 1.0;
    long long lns_max_node_budget = 1000000;
    ReduceConfig red;
};

struct CascadeStats {
    long long iterations = 0;
    long long lns_moves = 0;
    long long lns_improvements = 0;
    long long lns_gain = 0;
    long long lns_proved = 0;
    long long lns_sweeps = 0;
    long long lns_plateau = 0;
    int lns_expand = 0;
    double lns_slice = 0.0;
    long long perturbations = 0;
    long long perturb_accepted = 0;
    int perturb_strength = 1;
    long long restarts = 0;
    long long lns_nodes = 0;
    long long lns_region_vertices = 0;
    int lns_target = 0;
    long long kernel_n = 0;
    long long kernel_m = 0;
    long long kernel_offset = 0;
    long long lp_decided = 0;
    long long dives = 0;
    long long moves_accepted = 0;
    long long decisions_total = 0;
    double kernel_seconds = 0.0;
    double first_dive_seconds = 0.0;
    long long first_dive_value = 0;
};

class Cascade {
public:
    Cascade(const Graph& g, const CascadeConfig& cfg) : g_(g), cfg_(cfg), rng_(cfg.seed) {}

    const CascadeStats& stats() const { return stats_; }
    long long best_value() const { return archive_value_; }
    const std::vector<char>& best_solution() const { return archive_sol_; }

    // Runs kernelization followed by decision-space local search until the
    // deadline.  Returns the size of the best independent set found.
    long long run(double deadline_seconds, const std::function<double()>& elapsed);

private:
    struct Decision {
        int vertex;
        bool include;
        Reducer::State state;
        int cand_size;
    };

    void setup();
    int pick_decision_vertex();
    void apply(int v, bool include);
    long long dive(double deadline, const std::function<double()>& elapsed);
    long long residual_greedy(std::vector<char>& in_sol);
    // Adds every vertex that no longer conflicts; a dive can leave gaps because
    // exclude decisions are guesses, not safe reductions.
    long long maximalize(std::vector<char>& in_sol) const;
    long long snapshot_solution();
    // One exact large-neighbourhood move on the incumbent.  Returns the gain.
    long long lns_move(double deadline, const std::function<double()>& elapsed);

    const Graph& g_;
    CascadeConfig cfg_;
    std::mt19937_64 rng_;
    DynGraph dg_;
    Reducer red_;
    CascadeStats stats_;

    std::vector<int> cand_;
    std::vector<char> in_cand_;
    int cand_size_ = 0;

    std::vector<Decision> decisions_;
    std::vector<char> best_sol_;      // the working incumbent
    long long best_value_ = 0;
    std::vector<char> archive_sol_;   // best seen across restarts
    long long archive_value_ = 0;
    Reducer::State root_state_{};
    int root_cand_ = 0;
    void archive();
    void restart(double deadline, const std::function<double()>& elapsed);
    std::vector<int> tmp_;
    std::vector<char> blocked_;

    // Large-neighbourhood search scratch space.
    int lns_target_ = 0;
    std::vector<int> ball_, region_, ball_mark_, region_pos_;
    int ball_stamp_ = 0;
    // Worklist of seeds still worth examining at the current radius.
    std::vector<int> dirty_;
    // tight_[v] counts how many neighbours of v are in the incumbent; a vertex
    // can only be added once every one of them has been freed.
    std::vector<int> tight_, hits_, touched_, freed_, hit_count_;
    int free_target_ = 4;
    double slice_ = 0.05;
    long long node_budget_ = 20000;
    long long value_ = 0;
    long long stale_ = 0;
    int perturb_strength_ = 1;
    long long gain_at_perturb_ = 0;
    long long perturb_failures_ = 0;
    bool logging_ = false;
    std::vector<std::pair<int, char>> log_;
    void set_sol(int v, char value);
    // A perturbation forces a vertex into the incumbent, evicts its neighbours
    // and re-optimises locally; if that ends up worse the change log rolls it
    // back, so only the touched vertices are ever rewritten.
    void perturb(double deadline, const std::function<double()>& elapsed);
    void revert_log();
    void rebuild_tight();
    bool build_region(int seed);
    std::vector<char> in_dirty_;
    size_t dirty_head_ = 0;
    bool plateau_ = false;
    long long gain_at_sweep_start_ = 0;
    void mark_dirty(int v);
    void refill_dirty();
};
