#!/usr/bin/env python3
"""Adaptation figure from results/adapt/*.txt (solver --lns-log windows of 500 moves)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def load(n):
    return np.genfromtxt(f"results/adapt/{n}.txt", names=True)

fig, ax = plt.subplots(1, 3, figsize=(9.2, 3.5))
runs = [("del18", "del18, $k_0=4$", "#1f77b4", "-"), ("del18_k1", "del18, $k_0=1$", "#1f77b4", "--"),
        ("del18_k1024", "del18, $k_0=1024$", "#1f77b4", ":"), ("roadNet-PA", "roadNet-PA", "#d62728", "-"),
        ("web-Stanford", "web-Stanford", "#2ca02c", "-")]
for n, lab, c, ls in runs:
    d = load(n); ax[0].plot(d["t"], d["k"], color=c, ls=ls, lw=1.4, label=lab)
ax[0].set_yscale("log"); ax[0].set_xlabel("time (s)"); ax[0].set_ylabel("released vertices $k$")
ax[0].set_title("(a) the online rule forgets $k_0$", fontsize=9); ax[0].legend(fontsize=7, frameon=False)
d = load("del18")
ax[1].plot(d["t"], d["region"], color="#1f77b4", lw=1.4, label="region $|R|$ before reduction")
ax[1].plot(d["t"], d["root"], color="#ff7f0e", lw=1.4, label="live after root reduction")
ax[1].set_yscale("log"); ax[1].set_xlabel("time (s)"); ax[1].set_ylabel("vertices (mean per move)")
ax[1].set_title("(b) reductions shrink each region (del18)", fontsize=9); ax[1].legend(fontsize=7, frameon=False)
for n, lab, c, ls in runs[:1] + runs[3:]:
    d = load(n); ax[2].plot(d["t"], d["gain"], color=c, ls=ls, lw=1.4, label=lab)
ax[2].set_yscale("log"); ax[2].set_xlabel("time (s)"); ax[2].set_ylabel("cumulative gain from region moves")
ax[2].set_title("(c) where the gain arrives", fontsize=9); ax[2].legend(fontsize=7, frameon=False)
for a in ax: a.tick_params(labelsize=8); a.grid(alpha=0.25, lw=0.4)
fig.tight_layout()
fig.savefig("paper/figures/adapt.pdf")
