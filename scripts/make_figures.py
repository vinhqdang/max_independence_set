#!/usr/bin/env python3
"""Generates the figures for the manuscript.

Design notes. Colours are the validated categorical palette, assigned to solvers
in a fixed order and never cycled, so a solver keeps its colour across every
figure. Each series additionally carries its own line style and marker: the
paper is read in print and often in greyscale, so identity must survive the loss
of colour. Grid and axes are recessive; there is one y-axis per plot.
"""
import argparse
import collections
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# Fixed slot order from the validated categorical palette.
# Hatches give each solver a second, colour-independent identity, which is what
# the box plots rely on once the paper is printed in greyscale.
HATCH = {
    "cascade": "", "redumis": "///", "fastvc": "\\\\\\", "numvc": "...",
    "online_mis": "xxx", "nearlinear": "---", "lineartime": "|||",
}

STYLE = {
    "cascade":    ("#2a78d6", "-",  "o", r"\textsc{Cascade}"),
    "redumis":    ("#eb6834", "--", "s", "ReduMIS"),
    "fastvc":     ("#1baf7a", "-.", "^", "FastVC"),
    "numvc":      ("#eda100", ":",  "D", "NuMVC"),
    "online_mis": ("#e87ba4", "--", "v", "OnlineMIS"),
    "nearlinear": ("#008300", "-.", "x", "NearLinear"),
    "lineartime": ("#4a3aa7", ":",  "+", "LinearTime"),
}
ORDER = ["cascade", "redumis", "fastvc", "numvc", "online_mis", "nearlinear", "lineartime"]


def setup():
    plt.rcParams.update({
        "font.family": "serif", "font.size": 9, "axes.labelsize": 9,
        "axes.titlesize": 9, "legend.fontsize": 8, "xtick.labelsize": 8,
        "ytick.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
        "lines.linewidth": 1.4, "lines.markersize": 4, "figure.dpi": 200,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    })


def label(key):
    # \textsc only renders when the figure is typeset by LaTeX; keep plain text.
    return STYLE[key][3].replace(r"\textsc{", "").replace("}", "")


def load_results(path):
    best, meta = collections.defaultdict(dict), {}
    for r in csv.DictReader(open(path)):
        if not r["size"]:
            continue
        v = int(r["size"])
        best[r["instance"]][r["solver"]] = max(v, best[r["instance"]].get(r["solver"], 0))
        meta[r["instance"]] = r["family"]
    return best, meta


def performance_profile(path, out):
    """Dolan-Moré profile on solution quality.

    For each instance the ratio is best-found-by-anyone divided by the value the
    solver returned, so 1.0 means it matched the best and larger is worse. The
    curve is the fraction of instances within a factor tau, which reads as: how
    often is this solver within x% of the best anyone achieved.
    """
    best, _ = load_results(path)
    solvers = [s for s in ORDER if any(s in v for v in best.values())]
    insts = sorted(best)
    ratios = {s: [] for s in solvers}
    for i in insts:
        top = max(best[i].values())
        for s in solvers:
            v = best[i].get(s)
            ratios[s].append(top / v if v else np.inf)

    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    # Curves separate in the first few percent, so the axis stays zoomed; but it
    # must be wide enough that a solver which reached every instance is SEEN to
    # reach 1.0, otherwise truncation reads as failure. We therefore cover the
    # worst ratio of the majority of solvers and mark whoever is still cut off.
    worst = {s: max((r for r in ratios[s] if np.isfinite(r)), default=1.0)
             for s in solvers}
    hi = float(np.clip(np.percentile(list(worst.values()), 70), 1.04, 1.12))
    hi = round(hi + 0.002, 4)
    grid = np.linspace(1.0, hi, 400)
    truncated = []
    for s in solvers:
        r = np.array(ratios[s], dtype=float)
        frac = [(r <= t).sum() / len(r) for t in grid]
        c, ls, mk, _ = STYLE[s]
        ax.step(grid, frac, where="post", color=c, linestyle=ls, label=label(s))
        if worst[s] > hi:
            truncated.append(s)
            # An arrow at the axis edge says the curve continues off-plot.
            ax.annotate("", xy=(hi, frac[-1]), xytext=(hi - 0.006, frac[-1]),
                        arrowprops=dict(arrowstyle="->", color=c, lw=1.2))
    ax.set_xlabel(r"factor $\tau$ of the best value found by any solver")
    ax.set_ylabel("fraction of instances within $\\tau$")
    ax.set_xlim(1.0, hi)
    ax.set_ylim(0, 1.02)
    ax.legend(loc="lower right", frameon=False, ncol=2)
    fig.savefig(out)
    plt.close(fig)
    if truncated:
        print("  profile: curves continuing past the axis: %s"
              % ", ".join(truncated))
    return out


def seed_boxplot(path, out):
    """Spread over seeds, as a percentage of each instance's best value, so that
    instances of very different scale can share one axis."""
    runs = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in csv.DictReader(open(path)):
        if r["size"]:
            runs[r["instance"]][r["solver"]].append(int(r["size"]))
    insts = sorted(runs)
    solvers = [s for s in ORDER if any(s in runs[i] for i in insts)]
    data, positions, colors, hatches = [], [], [], []
    width = 0.8 / max(1, len(solvers))
    for xi, i in enumerate(insts):
        top = max(max(v) for v in runs[i].values())
        for si, s in enumerate(solvers):
            vals = runs[i].get(s)
            if not vals:
                continue
            data.append([100.0 * (v - top) / top for v in vals])
            positions.append(xi + (si - (len(solvers) - 1) / 2) * width)
            colors.append(STYLE[s][0])
            hatches.append(HATCH.get(s, ""))
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    bp = ax.boxplot(data, positions=positions, widths=width * 0.85,
                    patch_artist=True, medianprops=dict(color="#0b0b0b", linewidth=1.0),
                    flierprops=dict(marker=".", markersize=2, alpha=0.6))
    for patch, c, h in zip(bp["boxes"], colors, hatches):
        patch.set_facecolor(c)
        patch.set_alpha(0.55)
        patch.set_linewidth(0.6)
        patch.set_edgecolor("#2b2b2b")
        patch.set_hatch(h)
    ax.set_xticks(range(len(insts)))
    ax.set_xticklabels(insts, rotation=20, ha="center")
    ax.tick_params(axis="x", pad=6)
    ax.set_ylabel("gap to best on the instance (\\%)")
    # The legend goes above the axes: inside it would sit on top of the boxes.
    handles = [mpatches.Patch(facecolor=STYLE[s][0], alpha=0.55, hatch=HATCH.get(s, ""),
                              edgecolor="#2b2b2b", linewidth=0.6, label=label(s))
               for s in solvers]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.01),
              frameon=False, ncol=len(solvers), borderaxespad=0)
    fig.savefig(out)
    plt.close(fig)
    return out


def convergence(path, out, instances):
    """Solution quality against wall-clock time, one panel per instance."""
    series = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in csv.DictReader(open(path)):
        series[r["instance"]][r["solver"]].append((float(r["seconds"]), int(r["size"])))
    shown = [i for i in instances if i in series]
    if not shown:
        return None
    fig, axes = plt.subplots(1, len(shown), figsize=(2.3 * len(shown), 2.4), squeeze=False)
    for ax, inst in zip(axes[0], shown):
        for s in ORDER:
            pts = sorted(series[inst].get(s, []))
            if not pts:
                continue
            t = [p[0] for p in pts]
            v = [p[1] for p in pts]
            c, ls, mk, _ = STYLE[s]
            ax.plot(t, v, color=c, linestyle=ls, label=label(s))
        ax.set_title(inst)
        ax.set_xlabel("seconds")
        ax.set_xscale("symlog", linthresh=1.0)
    axes[0][0].set_ylabel("independent set size")
    axes[0][-1].legend(loc="lower right", frameon=False)
    fig.savefig(out)
    plt.close(fig)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="paper/figures")
    ap.add_argument("--main", default="cor_main60.csv")
    ap.add_argument("--seeds", default="cor_seeds60.csv")
    ap.add_argument("--traces", default="traces.csv")
    ap.add_argument("--convergence-instances", default="del20,web-BerkStan,frb59-26-1")
    args = ap.parse_args()

    setup()
    os.makedirs(args.out, exist_ok=True)
    made = []
    main_csv = os.path.join(args.results, args.main)
    if os.path.exists(main_csv):
        made.append(performance_profile(main_csv, os.path.join(args.out, "profile.pdf")))
    seeds_csv = os.path.join(args.results, args.seeds)
    if os.path.exists(seeds_csv):
        made.append(seed_boxplot(seeds_csv, os.path.join(args.out, "seeds.pdf")))
    tr = os.path.join(args.results, args.traces)
    if os.path.exists(tr):
        m = convergence(tr, os.path.join(args.out, "convergence.pdf"),
                        args.convergence_instances.split(","))
        if m:
            made.append(m)
    for m in made:
        print("wrote", m)


if __name__ == "__main__":
    main()
