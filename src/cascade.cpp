#include "cascade.hpp"

#include <cmath>

#include "exact.hpp"

void Cascade::setup() {
    // Folding creates new vertices; the pool is sized generously relative to
    // the instance and the engine declines to fold once it runs out.
    int pool = std::max(1024, g_.n / 2);
    dg_.init(g_, pool);
    red_.init(dg_, cfg_.red);
    in_cand_.assign(dg_.capacity(), 0);
    cand_.clear();
    best_sol_.assign(dg_.capacity(), 0);
    ball_mark_.assign(g_.n + 1, 0);
    region_pos_.assign(g_.n + 1, 0);
    in_dirty_.assign(g_.n + 1, 0);
    hit_count_.assign(g_.n + 1, 0);
    tight_.assign(g_.n + 1, 0);
    free_target_ = cfg_.lns_start_free;
    slice_ = cfg_.lns_slice;
    node_budget_ = cfg_.lns_node_budget;
    dirty_.clear();
    dirty_head_ = 0;
    lns_target_ = cfg_.lns_start_target;
}

// Picks the decision vertex: the highest-degree vertex among a random sample.
// Sampling keeps the cost per decision constant and supplies the randomisation
// the local search needs; dead entries met on the way are compacted out.
int Cascade::pick_decision_vertex() {
    int best = -1, best_deg = -1;
    int tries = 0;
    int limit = cfg_.sample_size * 4;
    while (tries < limit && cand_size_ > 0) {
        int idx = (int)(rng_() % (uint64_t)cand_size_);
        int v = cand_[idx];
        if (!dg_.alive(v)) {
            std::swap(cand_[idx], cand_[cand_size_ - 1]);
            --cand_size_;
            continue;
        }
        ++tries;
        int d = dg_.deg(v);
        if (d > best_deg) { best_deg = d; best = v; }
        if (tries >= cfg_.sample_size) break;
    }
    if (best >= 0) return best;
    // Fall back to a linear scan when sampling keeps hitting dead entries.
    for (int i = 0; i < cand_size_;) {
        int v = cand_[i];
        if (!dg_.alive(v)) { std::swap(cand_[i], cand_[cand_size_ - 1]); --cand_size_; continue; }
        return v;
    }
    return -1;
}

void Cascade::apply(int v, bool include) {
    int fold_mark = dg_.next_fold();
    if (include) red_.include(v);
    else red_.exclude(v);
    red_.reduce();
    // Fold vertices created by this cascade become decision candidates too.
    for (int f = fold_mark; f < dg_.next_fold(); ++f) {
        if (!dg_.alive(f) || in_cand_[f]) continue;
        in_cand_[f] = 1;
        // The entry sitting at the boundary belongs to a vertex that is dead now
        // but comes back on undo, so it is moved aside rather than overwritten.
        if (cand_size_ < (int)cand_.size()) {
            cand_.push_back(cand_[cand_size_]);
            cand_[cand_size_] = f;
        } else {
            cand_.push_back(f);
        }
        ++cand_size_;
    }
}

long long Cascade::residual_greedy(std::vector<char>& in_sol) {
    if (dg_.num_alive() == 0) return 0;
    tmp_.clear();
    for (int v = 0; v < dg_.next_fold(); ++v)
        if (dg_.alive(v)) tmp_.push_back(v);
    std::sort(tmp_.begin(), tmp_.end(),
              [&](int a, int b) { return dg_.deg(a) < dg_.deg(b); });
    blocked_.assign(dg_.capacity(), 0);
    long long taken = 0;
    for (int v : tmp_) {
        if (blocked_[v]) continue;
        in_sol[v] = 1;
        ++taken;
        dg_.for_each_nbr(v, [&](int u) { blocked_[u] = 1; });
    }
    return taken;
}

long long Cascade::maximalize(std::vector<char>& in_sol) const {
    long long added = 0;
    for (int v = 0; v < g_.n; ++v) {
        if (in_sol[v]) continue;
        bool free_vertex = true;
        for (long long i = g_.start[v]; i < g_.start[v + 1] && free_vertex; ++i)
            if (in_sol[g_.adj[i]]) free_vertex = false;
        if (free_vertex) { in_sol[v] = 1; ++added; }
    }
    return added;
}

void Cascade::archive() {
    if (value_ <= archive_value_) return;
    archive_value_ = value_;
    archive_sol_ = best_sol_;
    improved_ = true;
}

// Throws away the current incumbent and dives again from the kernel with fresh
// randomness.  The archive keeps the best solution, so a restart can only cost
// time, never quality.  This is the diversification that a single descent plus
// perturbation cannot provide on adversarial instances.
void Cascade::restart(double deadline, const std::function<double()>& elapsed) {
    ++stats_.restarts;
    archive();
    red_.restore(root_state_);
    cand_size_ = root_cand_;
    decisions_.clear();
    cfg_.include_prob = 0.05;  // a little randomness in the dive itself
    dive(deadline, elapsed);

    std::vector<char> in_sol(dg_.capacity(), 0);
    residual_greedy(in_sol);
    long long size = red_.lift(in_sol);
    size += maximalize(in_sol);
    best_sol_.swap(in_sol);
    value_ = size;
    best_value_ = std::max(best_value_, size);
    rebuild_tight();
    refill_dirty();
    free_target_ = cfg_.lns_start_free;
    slice_ = cfg_.lns_slice;
    node_budget_ = cfg_.lns_node_budget;
    perturb_strength_ = 1;
    perturb_failures_ = 0;
    plateau_ = false;
    archive();
}

long long Cascade::snapshot_solution() {
    std::vector<char> in_sol(dg_.capacity(), 0);
    residual_greedy(in_sol);
    long long size = red_.lift(in_sol);
    size += maximalize(in_sol);
    if (size > best_value_) {
        best_value_ = size;
        value_ = size;
        best_sol_ = in_sol;
        // The incumbent was replaced wholesale, so the tightness counters the
        // neighbourhood search relies on must be recomputed.
        value_ = size;
        rebuild_tight();
        if (!dirty_.empty()) refill_dirty();
    }
    archive();
    return size;
}

// Picks a ball of vertices around a random seed, frees every incumbent vertex
// inside it, and re-solves that region exactly.  Vertices of the ball that are
// blocked by an incumbent vertex outside the ball are dropped, which makes the
// region independent of its surroundings: the region optimum can never be worse
// than what the incumbent already has there, so the move never loses ground.
void Cascade::mark_dirty(int v) {
    if (in_dirty_[v]) return;
    in_dirty_[v] = 1;
    dirty_.push_back(v);
}

void Cascade::refill_dirty() {
    dirty_.clear();
    dirty_head_ = 0;
    for (int v : seeds_) { dirty_.push_back(v); in_dirty_[v] = 1; }
    // A shuffled sweep keeps successive regions from overlapping heavily.
    for (int i = (int)dirty_.size() - 1; i > 0; --i)
        std::swap(dirty_[i], dirty_[rng_() % (uint64_t)(i + 1)]);
    ++stats_.lns_sweeps;
}

long long Cascade::lns_move(double deadline, const std::function<double()>& elapsed) {
    if (g_.n == 0) return 0;
    if (dirty_head_ >= dirty_.size()) {
        // No gain anywhere at this neighbourhood size: free more vertices per
        // region, and let plateau moves run so the next sweep starts from a
        // different optimum of the same size.
        if (stats_.lns_gain == gain_at_sweep_start_) {
            plateau_ = true;
            if (free_target_ < cfg_.lns_max_free)
                free_target_ = std::min(cfg_.lns_max_free, free_target_ + free_target_ / 4 + 1);
            // A sweep that converged also means there is room to spend more on
            // each region.  Instances too large for a sweep to ever finish keep
            // the cheap setting and simply make more moves instead.
            slice_ = std::min(cfg_.lns_max_slice, slice_ * 2.0);
            node_budget_ = std::min(cfg_.lns_max_node_budget, node_budget_ * 4);
        } else {
            plateau_ = false;
        }
        stats_.lns_expand = free_target_;
        gain_at_sweep_start_ = stats_.lns_gain;
        refill_dirty();
    }
    int seed = dirty_[dirty_head_++];
    in_dirty_[seed] = 0;
    ++stats_.lns_moves;

    if (!build_region(seed)) return 0;

    for (size_t i = 0; i < region_.size(); ++i) region_pos_[region_[i]] = (int)i;
    ++ball_stamp_;
    for (int v : region_) ball_mark_[v] = ball_stamp_;

    Graph& sub = sub_;  // reused across moves so the buffers keep their capacity
    sub.n = (int)region_.size();
    sub.start.assign(sub.n + 1, 0);
    sub.adj.clear();
    long long w = 0;
    for (size_t i = 0; i < region_.size(); ++i) {
        sub.start[i] = w;
        int v = region_[i];
        for (long long e = g_.start[v]; e < g_.start[v + 1]; ++e) {
            int u = g_.adj[e];
            if (ball_mark_[u] == ball_stamp_) { sub.adj.push_back(region_pos_[u]); ++w; }
        }
        std::sort(sub.adj.begin() + sub.start[i], sub.adj.end());
    }
    sub.start[sub.n] = w;
    sub.m = w / 2;

    long long incoming = 0;
    for (int v : region_) incoming += best_sol_[v] ? 1 : 0;

    ExactConfig ec;
    ec.red = cfg_.red;
    ec.node_budget = node_budget_;
    ec.lower_bound = incoming - 1;  // an equal-size region solution is still recorded
    ec.seed = rng_();
    double slice = std::min(deadline, elapsed() + slice_);
    ExactResult res = region_solver_.solve(sub, ec, slice, elapsed);
    if (res.proved_optimal) ++stats_.lns_proved;
    stats_.lns_nodes += res.nodes;
    stats_.lns_region_vertices += (long long)region_.size();

    long long gain = 0;
    if ((int)res.solution.size() == sub.n && res.size >= incoming) {
        gain = res.size - incoming;
        bool changed = false;
        for (size_t i = 0; i < region_.size(); ++i)
            if (best_sol_[region_[i]] != res.solution[i]) { changed = true; break; }
        // A region optimum of equal size is still worth taking: moving along the
        // plateau is what opens up improvements elsewhere.  Plateau moves only
        // run once a full sweep has stopped finding real gains.
        if (gain > 0 || (changed && plateau_)) {
            for (size_t i = 0; i < region_.size(); ++i)
                set_sol(region_[i], res.solution[i]);
            if (gain > 0) { ++stats_.lns_improvements; stats_.lns_gain += gain; }
            else ++stats_.lns_plateau;
            // Freeing vertices can leave a neighbour outside the region with no
            // solution neighbour at all; take those immediately.
            touched_.clear();
            for (int v : region_)
                for (long long e = g_.start[v]; e < g_.start[v + 1]; ++e) {
                    int u = g_.adj[e];
                    if (!best_sol_[u] && tight_[u] == 0) { set_sol(u, 1); ++gain; }
                    mark_dirty(u);
                }
            for (int v : region_) mark_dirty(v);
        }
    }
    // Adapt how much is freed per region: shrink when a region turns out to be
    // too hard to solve exactly, grow when a whole sweep finds nothing.  On a
    // mesh this settles at tens of freed vertices, on a dense graph at one or
    // two, without either case being configured by hand.
    if (!res.proved_optimal || (int)region_.size() > cfg_.lns_region_cap) {
        free_target_ = std::max(1, free_target_ / 2);
        stale_ = 0;
        mark_dirty(seed);
    } else if (gain > 0) {
        stale_ = 0;
    } else if (++stale_ > cfg_.lns_stale_grow) {
        // Regions of this size are being solved to optimality without finding
        // anything; the only way forward is to free more per region.
        free_target_ = std::min(cfg_.lns_max_free, free_target_ * 2);
        stale_ = 0;
    }
    stats_.lns_expand = free_target_;
    stats_.lns_target = lns_target_;
    stats_.lns_slice = slice_;
    return gain;
}

void Cascade::set_sol(int v, char value) {
    if (best_sol_[v] == value) return;
    if (logging_) log_.emplace_back(v, best_sol_[v]);
    best_sol_[v] = value;
    int delta = value ? 1 : -1;
    for (long long e = g_.start[v]; e < g_.start[v + 1]; ++e) tight_[g_.adj[e]] += delta;
}

void Cascade::revert_log() {
    bool saved = logging_;
    logging_ = false;
    for (size_t i = log_.size(); i-- > 0;) set_sol(log_[i].first, log_[i].second);
    log_.clear();
    logging_ = saved;
}

// Forces a random vertex into the incumbent, evicts the neighbours that block
// it, repairs the damage with neighbourhood moves, and keeps the result only if
// it is no worse.  This is what lets the search escape a solution that is
// optimal for every neighbourhood it can afford to solve.
void Cascade::perturb(double deadline, const std::function<double()>& elapsed) {
    if (g_.n == 0) return;
    ++stats_.perturbations;
    long long before = value_;
    log_.clear();
    logging_ = true;

    // The kick gets stronger the longer the search goes without a gain, and
    // resets as soon as one is found.
    for (int f = 0; f < perturb_strength_; ++f) {
        // Kicks are aimed at the same set the sweep seeds from; perturbing a
        // vertex the reductions already settled cannot help.
        int v = seeds_.empty() ? (int)(rng_() % (uint64_t)g_.n)
                               : seeds_[rng_() % (uint64_t)seeds_.size()];
        if (best_sol_[v]) continue;
        for (long long e = g_.start[v]; e < g_.start[v + 1]; ++e) {
            int u = g_.adj[e];
            if (best_sol_[u]) { set_sol(u, 0); --value_; }
        }
        set_sol(v, 1);
        ++value_;
        mark_dirty(v);
        for (long long e = g_.start[v]; e < g_.start[v + 1]; ++e) {
            int u = g_.adj[e];
            mark_dirty(u);
            // Vertices that the eviction freed can be taken straight away.
            for (long long e2 = g_.start[u]; e2 < g_.start[u + 1]; ++e2) {
                int x = g_.adj[e2];
                if (!best_sol_[x] && tight_[x] == 0) { set_sol(x, 1); ++value_; mark_dirty(x); }
            }
        }
    }
    for (int i = 0; i < cfg_.perturb_rounds && elapsed() < deadline; ++i)
        value_ += lns_move(deadline, elapsed);

    if (value_ >= before) {
        log_.clear();
        ++stats_.perturb_accepted;
    } else {
        revert_log();
        value_ = before;
    }
    logging_ = false;
    if (value_ > best_value_) best_value_ = value_;

    if (stats_.lns_gain != gain_at_perturb_) {
        gain_at_perturb_ = stats_.lns_gain;
        perturb_failures_ = 0;
        perturb_strength_ = 1;
    } else if (++perturb_failures_ > 32 && perturb_strength_ < cfg_.perturb_max_strength) {
        perturb_failures_ = 0;
        perturb_strength_ = std::min(cfg_.perturb_max_strength, perturb_strength_ * 2);
    }
    // Once the kick is at full strength the counter keeps running, so a search
    // that is well and truly stuck eventually restarts instead of spinning.
    stats_.perturb_strength = perturb_strength_;
}

void Cascade::rebuild_tight() {
    tight_.assign(g_.n + 1, 0);
    for (int v = 0; v < g_.n; ++v)
        if (best_sol_[v])
            for (long long e = g_.start[v]; e < g_.start[v + 1]; ++e) ++tight_[g_.adj[e]];
}

// Builds the region to be re-optimised.  Freeing a set F of incumbent vertices
// makes exactly those vertices addable whose every incumbent neighbour lies in
// F, so F together with that set is a region no outside vertex can interact
// with: re-solving it exactly is always safe and never loses ground.
//
// F is collected by a breadth-first walk from the seed, which keeps the freed
// vertices close together (where the interesting interactions are) and works
// the same way on a mesh and on a dense graph.  With |F| = 1 the region is what
// an ARW-style (1,2)-swap examines; growing |F| subsumes swaps of any arity.
bool Cascade::build_region(int seed) {
    freed_.clear();
    ++ball_stamp_;
    int visit_cap = std::max(64, free_target_ * 64);
    ball_.clear();
    ball_.push_back(seed);
    ball_mark_[seed] = ball_stamp_;
    for (size_t i = 0; i < ball_.size() && (int)freed_.size() < free_target_; ++i) {
        int v = ball_[i];
        if (best_sol_[v]) freed_.push_back(v);
        if ((int)ball_.size() >= visit_cap) continue;
        for (long long e = g_.start[v]; e < g_.start[v + 1]; ++e) {
            int u = g_.adj[e];
            if (ball_mark_[u] == ball_stamp_) continue;
            ball_mark_[u] = ball_stamp_;
            ball_.push_back(u);
        }
    }
    if (freed_.empty()) return false;

    // Mark exactly the freed set, then collect the vertices it unlocks.
    ++ball_stamp_;
    for (int v : freed_) ball_mark_[v] = ball_stamp_;
    region_.assign(freed_.begin(), freed_.end());
    hits_.clear();
    for (int v : freed_) {
        for (long long e = g_.start[v]; e < g_.start[v + 1]; ++e) {
            int u = g_.adj[e];
            if (best_sol_[u] || ball_mark_[u] == ball_stamp_) continue;
            if (++hit_count_[u] == 1) hits_.push_back(u);
        }
    }
    for (int u : hits_) {
        if (hit_count_[u] == tight_[u]) { ball_mark_[u] = ball_stamp_; region_.push_back(u); }
        hit_count_[u] = 0;
    }
    return region_.size() >= 2;
}

long long Cascade::dive(double deadline, const std::function<double()>& elapsed) {
    while (dg_.num_alive() > 0) {
        if (elapsed() > deadline) break;
        int v = pick_decision_vertex();
        if (v < 0) break;
        bool include = cfg_.include_prob > 0.0 &&
                       (double)(rng_() % 1000000u) / 1e6 < cfg_.include_prob;
        decisions_.push_back({v, include, red_.state(), cand_size_});
        apply(v, include);
    }
    ++stats_.dives;
    stats_.decisions_total += (long long)decisions_.size();
    return red_.offset();
}

long long Cascade::run(double deadline, const std::function<double()>& elapsed) {
    setup();

    // Phase 1: exhaustive kernelization of the whole graph.
    double t0 = elapsed();
    double kernel_deadline = cfg_.kernel_only ? 1e18 : t0 + cfg_.kernel_share * deadline;
    red_.set_stop([&]() { return elapsed() > kernel_deadline; });
    red_.push_all();
    red_.reduce();
    long long live_edges = 0;
    for (int v = 0; v < dg_.next_fold(); ++v)
        if (dg_.alive(v)) live_edges += dg_.deg(v);
    live_edges /= 2;
    if (cfg_.use_lp && live_edges <= cfg_.lp_max_edges && elapsed() < kernel_deadline) {
        // The LP reduction looks at the whole graph, so it fires where the local
        // rules have stalled; each round it decides vertices can in turn unlock
        // more local rules, so the two alternate until neither moves.
        LPReduction lp;
        double lp_deadline = t0 + std::max(1.0, cfg_.lp_budget_share * deadline);
        for (int round = 0; round < 4; ++round) {
            int decided = lp.apply(dg_, red_);
            stats_.lp_decided += decided;
            if (decided == 0) break;
            red_.push_all();
            red_.reduce();
            if (elapsed() > lp_deadline) break;
        }
    }
    stats_.kernel_seconds = elapsed() - t0;
    stats_.kernel_truncated = elapsed() > kernel_deadline ? 1 : 0;
    // The search itself only has to respect the overall deadline.
    red_.set_stop([&]() { return elapsed() > deadline; });
    red_.set_config(cfg_.dive_red);
    stats_.kernel_offset = red_.offset();
    stats_.kernel_n = dg_.num_alive();
    long long km = 0;
    for (int v = 0; v < dg_.capacity(); ++v)
        if (dg_.alive(v)) km += dg_.deg(v);
    stats_.kernel_m = km / 2;

    if (cfg_.kernel_only) return 0;

    // Everything the reductions decided is part of some maximum independent
    // set, so an improvement has to touch a vertex that survived into the
    // kernel.  Seeding the sweep from those vertices and their neighbours is
    // what keeps a 4M-vertex instance with a 2000-vertex kernel from spending
    // its whole budget re-examining settled ground.
    seeds_.clear();
    std::vector<char> is_seed(g_.n, 0);
    for (int v = 0; v < g_.n; ++v) {
        if (!dg_.alive(v)) continue;
        if (!is_seed[v]) { is_seed[v] = 1; seeds_.push_back(v); }
        for (long long e = g_.start[v]; e < g_.start[v + 1]; ++e)
            if (!is_seed[g_.adj[e]]) { is_seed[g_.adj[e]] = 1; seeds_.push_back(g_.adj[e]); }
    }
    if (seeds_.empty())
        for (int v = 0; v < g_.n; ++v) seeds_.push_back(v);

    for (int v = 0; v < dg_.capacity(); ++v) {
        if (!dg_.alive(v)) continue;
        in_cand_[v] = 1;
        cand_.push_back(v);
    }
    cand_size_ = (int)cand_.size();
    root_state_ = red_.state();
    root_cand_ = cand_size_;

    // Phase 2: first dive (this alone reproduces reduce-and-peel).
    decisions_.clear();
    double d0 = elapsed();
    long long cur = dive(deadline, elapsed);
    snapshot_solution();  // establishes an incumbent even if the dive was cut short
    stats_.first_dive_seconds = elapsed() - d0;
    stats_.first_dive_value = best_value_;
    value_ = best_value_;
    last_improve_ = elapsed();
    rebuild_tight();
    archive();

    if (decisions_.empty()) { archive(); return archive_value_; }  // reductions solved it

    // Phase 3: local search over dives.  A move rewinds to a level, changes the
    // decision there, and re-dives; the cost is the suffix, not the instance.
    std::vector<Decision> saved;
    while (elapsed() < deadline) {
        if (cfg_.use_lns) {
            // Most of the budget goes to exact neighbourhood moves; they act
            // directly on the incumbent and never make it worse.
            int rounds = cfg_.use_dive_moves ? 8 : 64;
            for (int i = 0; i < rounds && elapsed() < deadline; ++i) {
                value_ += lns_move(deadline, elapsed);
                if (value_ > best_value_) best_value_ = value_;
            }
            if (cfg_.use_perturbation && elapsed() < deadline) {
                perturb(deadline, elapsed);
                if (improved_) { improved_ = false; last_improve_ = elapsed(); }
                bool stuck_on_kicks = perturb_strength_ >= cfg_.perturb_max_strength &&
                                      perturb_failures_ >= cfg_.restart_after;
                double idle_limit = std::max(0.02, cfg_.restart_idle_dives *
                                                    stats_.first_dive_seconds);
                bool stuck_on_time = elapsed() - last_improve_ > idle_limit;
                if ((stuck_on_kicks || stuck_on_time) && elapsed() < deadline) {
                    restart(deadline, elapsed);
                    last_improve_ = elapsed();
                }
            }
        }
        if (!cfg_.use_dive_moves || decisions_.empty()) continue;
        ++stats_.iterations;
        int k = (int)decisions_.size();
        // How far back to rewind is drawn log-uniformly, so most moves revise
        // only the last few decisions and are correspondingly cheap, while the
        // occasional deep move can restructure the whole dive.
        double u = (double)(rng_() % 1000000u) / 1e6;
        int back = (int)std::floor(std::exp(u * std::log((double)k + 1.0)));
        if (back < 1) back = 1;
        if (back > k) back = k;
        int level = k - back;

        saved.assign(decisions_.begin() + level, decisions_.end());
        Decision& d = decisions_[level];
        // Half the moves flip the decision at that level, the other half keep it
        // and simply re-dive with fresh randomness below it.
        bool flip = (rng_() & 1) != 0;
        int flip_vertex = d.vertex;
        bool flip_include = flip ? !d.include : d.include;

        red_.restore(d.state);
        cand_size_ = d.cand_size;
        decisions_.resize(level);

        decisions_.push_back({flip_vertex, flip_include, red_.state(), cand_size_});
        apply(flip_vertex, flip_include);
        long long val = dive(deadline, elapsed);

        if (val >= cur) {
            cur = val;
            ++stats_.moves_accepted;
            if (val > best_value_) snapshot_solution();
        } else {
            // Reject: rewind and replay the decisions that were in place.
            red_.restore(saved.front().state);
            cand_size_ = saved.front().cand_size;
            decisions_.resize(level);
            for (const Decision& old : saved) {
                decisions_.push_back({old.vertex, old.include, red_.state(), cand_size_});
                apply(old.vertex, old.include);
            }
            // Reductions are deterministic, so the replay restores the state
            // exactly; the value is unchanged.
        }
    }
    archive();
    return archive_value_;
}
