#!/usr/bin/env python3
"""Turns the raw benchmark CSV into per-instance and per-family comparison
tables, with our solver measured against the best baseline on each instance."""
import argparse
import csv
import collections

OURS = "cascade"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.csv)))
    best = collections.defaultdict(dict)  # instance -> solver -> size
    meta = {}
    for r in rows:
        if not r["size"]:
            continue
        inst, solver, size = r["instance"], r["solver"], int(r["size"])
        meta[inst] = (r["family"], int(r["n"]), int(r["m"]))
        if solver not in best[inst] or size > best[inst][solver]:
            best[inst][solver] = size

    solvers = sorted({r["solver"] for r in rows})
    others = [s for s in solvers if s != OURS]
    wins = losses = ties = 0
    fam_stat = collections.defaultdict(lambda: [0, 0, 0])

    header = ["instance", "family", "n", "m"] + solvers + ["best_other", "delta"]
    print(" | ".join(header))
    if args.markdown:
        print(" | ".join(["---"] * len(header)))
    for inst in sorted(best, key=lambda i: (meta[i][0], meta[i][1])):
        fam, n, m = meta[inst]
        line = [inst, fam, str(n), str(m)]
        for s in solvers:
            line.append(str(best[inst].get(s, "-")))
        bo = [best[inst][s] for s in others if s in best[inst]]
        bo_v = max(bo) if bo else None
        ours = best[inst].get(OURS)
        if ours is not None and bo_v is not None:
            d = ours - bo_v
            line += [str(bo_v), "%+d" % d]
            if d > 0: wins += 1; fam_stat[fam][0] += 1
            elif d < 0: losses += 1; fam_stat[fam][1] += 1
            else: ties += 1; fam_stat[fam][2] += 1
        else:
            line += ["-", "-"]
        print(" | ".join(line))

    print()
    print("%s vs best baseline: %d wins, %d ties, %d losses" % (OURS, wins, ties, losses))
    for fam in sorted(fam_stat):
        w, l, t = fam_stat[fam]
        print("  %-12s %d wins, %d ties, %d losses" % (fam, w, t, l))


if __name__ == "__main__":
    main()
