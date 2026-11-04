#!/usr/bin/env python3
"""Draws one region move on a small Delaunay graph, using the construction of
the paper (breadth-first walk for F, tight vertices, reductions, exact solve).
Output: paper/figures/move_example.pdf"""
import itertools
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import Delaunay

N, SEED = 90, 7


def graph(n, seed):
    pts = np.random.default_rng(seed).random((n, 2))
    adj = [set() for _ in range(n)]
    for s in Delaunay(pts).simplices:
        for a, b in itertools.combinations(s, 2):
            adj[a].add(b); adj[b].add(a)
    return pts, adj


def greedy(adj, rng):
    order = list(range(len(adj))); rng.shuffle(order)
    S, blocked = set(), set()
    for v in order:
        if v not in blocked:
            S.add(v); blocked |= adj[v] | {v}
    return S


def region(adj, S, seed_v, k):
    ball, seen, F = [seed_v], {seed_v}, []
    i = 0
    while i < len(ball) and len(F) < k:
        v = ball[i]; i += 1
        if v in S: F.append(v)
        for u in sorted(adj[v]):
            if u not in seen: seen.add(u); ball.append(u)
    Fs = set(F)
    tight = {u for f in F for u in adj[f] if u not in S and adj[u] & S <= Fs}
    return Fs, tight


def reduce_region(adj, R):
    """degree-0/1 and domination, to a fixed point; returns surviving vertices."""
    live = set(R); changed = True
    while changed:
        changed = False
        for v in sorted(live):
            nb = adj[v] & live
            if len(nb) <= 1:
                live -= {v} | nb; changed = True; break
            if any((adj[u] & live) | {u} <= (nb | {v}) for u in nb):
                live.discard(v); changed = True; break
    return live


def mis(adj, V):
    V = sorted(V)
    best = []
    def rec(cand, cur):
        nonlocal best
        if not cand:
            if len(cur) > len(best): best = cur[:]
            return
        if len(cur) + len(cand) <= len(best): return
        v = max(cand, key=lambda x: len(adj[x] & cand))
        rec(cand - adj[v] - {v}, cur + [v])
        rec(cand - {v}, cur)
    rec(set(V), [])
    return set(best)


def main():
    pts, adj = graph(N, 3)
    rng = random.Random(SEED)
    for trial in range(2000):
        S = greedy(adj, rng)
        for v in range(N):
            for k in (3, 4, 5):
                F, tight = region(adj, S, v, k)
                R = F | tight
                if not (16 <= len(R) <= 30) or len(F) < k: continue
                P = pts[sorted(R)]
                if not (0.25 < pts[v][0] < 0.75 and 0.25 < pts[v][1] < 0.75) or np.ptp(P, axis=0).max() > 0.38: continue
                live = reduce_region(adj, R)
                T = mis(adj, R)
                if len(T) - len(F) >= 1 and 3 <= len(live) < len(R) - 5:
                    return draw(pts, adj, S, F, tight, R, live, T, v)
    sys.exit("no example found")


def draw(pts, adj, S, F, tight, R, live, T, v):
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.9))
    edges = {(a, b) for a in range(len(adj)) for b in adj[a] if a < b}
    gray, dark, orange, blue, green = "#c9c9c9", "#222222", "#e8871e", "#3b7dd8", "#2ca02c"
    def base(ax, title):
        for a, b in edges:
            ax.plot(*zip(pts[a], pts[b]), color="#e3e3e3", lw=0.6, zorder=1)
        ax.set_title(title, fontsize=9); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.set_aspect("equal")
    def pts_of(vs): return pts[sorted(vs)] if vs else np.zeros((0, 2))
    allv = set(range(len(adj)))
    # (i) incumbent and the seed
    ax = axs[0]; base(ax, "(i) incumbent $S$ (black); seed $v$ (ring)")
    ax.scatter(*pts_of(allv - S).T, s=14, c="white", edgecolors=gray, linewidths=0.6, zorder=2)
    ax.scatter(*pts_of(S).T, s=26, c=dark, zorder=3)
    ax.scatter(*pts[[v]].T, s=150, facecolors="none", edgecolors=orange, linewidths=1.6, zorder=4)
    # (ii) released set and region
    ax = axs[1]; base(ax, "(ii) release $F$, collect the region $R(F)$")
    for a in R:
        for b in adj[a]:
            if b in R and a < b: ax.plot(*zip(pts[a], pts[b]), color="#777", lw=1.0, zorder=2)
    rest = allv - R
    ax.scatter(*pts_of(rest - S).T, s=12, c="white", edgecolors=gray, linewidths=0.5, zorder=2)
    ax.scatter(*pts_of(S - F).T, s=22, c=dark, zorder=3)
    ax.scatter(*pts_of(tight).T, s=40, c=blue, edgecolors="k", linewidths=0.4, zorder=4)
    ax.scatter(*pts_of(F).T, s=55, c=orange, edgecolors="k", linewidths=0.4, zorder=5)
    # (iii) after reduction and exact solve
    ax = axs[2]; base(ax, "(iii) reduce the region, solve it, write back")
    for a in R:
        for b in adj[a]:
            if b in R and a < b: ax.plot(*zip(pts[a], pts[b]), color="#aaa", lw=0.8, zorder=2)
    ax.scatter(*pts_of(rest - S).T, s=12, c="white", edgecolors=gray, linewidths=0.5, zorder=2)
    ax.scatter(*pts_of(S - F).T, s=22, c=dark, zorder=3)
    ax.scatter(*pts_of(R - live - T).T, s=34, c="white", edgecolors="#999", linewidths=0.8, zorder=4)
    ax.scatter(*pts_of(live - T).T, s=40, c="#f2c94c", edgecolors="k", linewidths=0.4, zorder=4)
    ax.scatter(*pts_of(T).T, s=60, c=green, edgecolors="k", linewidths=0.5, zorder=5)
    from matplotlib.lines import Line2D
    L = [Line2D([], [], marker="o", ls="", color=orange, label=f"released $F$ ($|F|={len(F)}$)"),
         Line2D([], [], marker="o", ls="", color=blue, label="tight vertices (all solution neighbours in $F$)"),
         Line2D([], [], marker="o", ls="", color="#f2c94c", label=f"survive reduction ($|R|={len(R)}\\to{len(live)}$ live)"),
         Line2D([], [], marker="o", ls="", color=green, label=f"new solution $T$ ($|T|={len(T)}$, gain ${len(T)-len(F)}$)")]
    fig.legend(handles=L, loc="lower center", ncol=2, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.1, 1, 0.95))
    fig.savefig("paper/figures/move_example.pdf")
    print("F", len(F), "tight", len(tight), "R", len(R), "live", len(live), "T", len(T))


if __name__ == "__main__":
    main()
