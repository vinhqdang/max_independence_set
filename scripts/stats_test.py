#!/usr/bin/env python3
"""Paired Wilcoxon signed-rank tests of Cascade against each baseline.

The test is run on per-instance *relative gaps*, gap = (best - value) / best,
where "best" is the best value any of the compared solvers reached on that
instance.  Raw vertex counts are not used: they let the largest instances
dominate the ranks.  p-values are Holm-corrected across the baselines.
Writes a LaTeX table when --tex is given.
"""
import argparse
import collections
import csv
import sys

from scipy.stats import wilcoxon

OURS = "cascade"
LABEL = {"redumis": "ReduMIS", "online_mis": "OnlineMIS", "nearlinear": "NearLinear",
         "lineartime": "LinearTime", "numvc": "NuMVC", "fastvc": "FastVC"}


def load(path):
    best = collections.defaultdict(dict)
    for r in csv.DictReader(open(path)):
        if not r["size"]:
            continue
        v = int(r["size"])
        d = best[r["instance"]]
        d[r["solver"]] = max(v, d.get(r["solver"], 0))
    return best


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def fmt(p):
    return "$<10^{-4}$" if p < 1e-4 else "%.4f" % p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--tex")
    ap.add_argument("--alpha", type=float, default=0.05)
    a = ap.parse_args()
    agg = load(a.csv)
    ref = {i: max(per.values()) for i, per in agg.items()}
    rows = []
    for s in LABEL:
        insts = [i for i in sorted(agg) if OURS in agg[i] and s in agg[i]]
        g0 = [(ref[i] - agg[i][OURS]) / ref[i] for i in insts]
        g1 = [(ref[i] - agg[i][s]) / ref[i] for i in insts]
        d = [x - y for x, y in zip(g0, g1)]
        win, tie, loss = sum(x < 0 for x in d), sum(x == 0 for x in d), sum(x > 0 for x in d)
        p = 1.0 if all(x == 0 for x in d) else wilcoxon(g0, g1, zero_method="zsplit").pvalue
        rows.append([s, len(insts), win, tie, loss, p, sum(d)])
    adj = holm([r[5] for r in rows])
    for r, q in zip(rows, adj):
        r.append(q)
    print("%-11s %5s %4s %4s %5s %10s %10s %s" % ("baseline", "pairs", "win", "tie", "loss", "p", "p_holm", "verdict"))
    tex = []
    for s, n, w, t, l, p, sd, q in rows:
        v = "--" if q >= a.alpha else (r"\textsc{Cascade}" if sd < 0 else LABEL[s])
        print("%-11s %5d %4d %4d %5d %10.5f %10.5f %s" % (s, n, w, t, l, p, q, v))
        tex.append("%s & %d & %d & %d & %d & %s & %s & %s \\\\" % (LABEL[s], n, w, t, l, fmt(p), fmt(q), v))
    if a.tex:
        open(a.tex, "w").write("\n".join([
            r"\begin{table}[htbp]", r"\centering",
            r"\caption{Paired Wilcoxon signed-rank test of \textsc{Cascade} against each baseline "
            r"over the instances both solved, at the 60\,s budget, computed on relative gaps "
            r"to the best of the seven solvers. $p_{\mathrm{Holm}}$ is Holm-adjusted over the six "
            r"comparisons; a verdict names the better solver when $p_{\mathrm{Holm}}<0.05$.}",
            r"\label{tab:wilcoxon}", r"\fittable{", r"\begin{tabular}{lrrrrrrr}", r"\toprule",
            r"Baseline & pairs & win & tie & loss & $p$ & $p_{\mathrm{Holm}}$ & verdict \\", r"\midrule"]
            + tex + [r"\bottomrule", r"\end{tabular}", r"}", r"\end{table}"]) + "\n")


if __name__ == "__main__":
    sys.exit(main())
