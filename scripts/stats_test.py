#!/usr/bin/env python3
"""Paired statistical comparison of our solver against each baseline.

Reviewers in the operations research literature expect a paired test rather than
a win/loss tally, because instances differ enormously in scale. We use the
Wilcoxon signed-rank test on per-instance values, which makes no normality
assumption and is the standard choice for this kind of comparison.
"""
import argparse
import collections
import csv
import sys

from scipy.stats import wilcoxon

OURS = "cascade"


def load(path, aggregate):
    runs = collections.defaultdict(lambda: collections.defaultdict(list))
    meta = {}
    for r in csv.DictReader(open(path)):
        if not r["size"]:
            continue
        runs[r["instance"]][r["solver"]].append(int(r["size"]))
        meta[r["instance"]] = r["family"]
    agg = collections.defaultdict(dict)
    for inst, per in runs.items():
        for solver, vals in per.items():
            agg[inst][solver] = max(vals) if aggregate == "best" else sum(vals) / len(vals)
    return agg, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--aggregate", choices=["best", "mean"], default="best")
    ap.add_argument("--alpha", type=float, default=0.05)
    args = ap.parse_args()

    agg, meta = {}, {}
    for path in args.csv:
        a, m = load(path, args.aggregate)
        for k, v in a.items():
            agg.setdefault(k, {}).update(v)
        meta.update(m)

    solvers = sorted({s for per in agg.values() for s in per} - {OURS})
    print("Paired Wilcoxon signed-rank test, %s over seeds, alpha=%g" %
          (args.aggregate, args.alpha))
    print("%-14s %7s %5s %5s %5s %12s %10s %s"
          % ("baseline", "n_pairs", "win", "tie", "loss", "p-value", "verdict", "sum(diff)"))
    print("-" * 88)
    for s in solvers:
        pairs = [(agg[i][OURS], agg[i][s]) for i in sorted(agg)
                 if OURS in agg[i] and s in agg[i]]
        if len(pairs) < 3:
            print("%-14s %7d  (too few paired instances)" % (s, len(pairs)))
            continue
        ours = [a for a, _ in pairs]
        other = [b for _, b in pairs]
        diff = [a - b for a, b in pairs]
        win = sum(d > 0 for d in diff)
        tie = sum(d == 0 for d in diff)
        loss = sum(d < 0 for d in diff)
        if all(d == 0 for d in diff):
            p, verdict = float("nan"), "identical"
        else:
            p = wilcoxon(ours, other, zero_method="zsplit").pvalue
            if p >= args.alpha:
                verdict = "no diff"
            else:
                verdict = "CASCADE" if sum(diff) > 0 else s
        print("%-14s %7d %5d %5d %5d %12.5g %10s %+d"
              % (s, len(pairs), win, tie, loss, p, verdict, sum(diff)))

    print("\nPer family (CASCADE minus baseline, summed over instances):")
    fams = sorted({meta[i] for i in agg})
    print("%-14s %s" % ("baseline", "  ".join("%12s" % f for f in fams)))
    for s in solvers:
        cells = []
        for f in fams:
            d = sum(agg[i][OURS] - agg[i][s] for i in agg
                    if meta[i] == f and OURS in agg[i] and s in agg[i])
            cells.append("%12s" % ("%+d" % d))
        print("%-14s %s" % (s, "  ".join(cells)))


if __name__ == "__main__":
    sys.exit(main())
