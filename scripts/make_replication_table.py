#!/usr/bin/env python3
"""Builds the hardware-replication table for the paper.

Compares results/replication60.csv (the second platform) against
results/cor_main60.csv (the platform the main tables were measured on), over
the instances that are fully present in both.

Two things are worth reporting and the table carries both. First, whether the
*ranking* survives the change of machine, which is what a reader relies on when
they read the main tables. Second, how far each solver's own value moved, which
separates a solver whose answer is reproducible from one whose answer is not.
"""
import argparse
import collections
import csv
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ORDER = ["cascade", "redumis", "online_mis", "numvc", "fastvc",
         "nearlinear", "lineartime"]
LABEL = {"cascade": r"\textsc{Cascade}", "redumis": "ReduMIS",
         "online_mis": "OnlineMIS", "numvc": "NuMVC", "fastvc": "FastVC",
         "nearlinear": "NearLinear", "lineartime": "LinearTime"}
FAMILIES = ["geometric", "road", "web", "social", "bhoslib"]


def load(path):
    sizes = collections.defaultdict(dict)
    family = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            family[r["instance"]] = r["family"]
            try:
                sizes[r["instance"]][r["solver"]] = int(r["size"])
            except (ValueError, TypeError):
                sizes[r["instance"]][r["solver"]] = None
    return sizes, family


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", default=os.path.join(ROOT, "results", "cor_main60.csv"))
    ap.add_argument("--replication", default=os.path.join(ROOT, "results", "replication60.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "paper", "tables", "replication.tex"))
    args = ap.parse_args()

    main_s, fam = load(args.main)
    rep_s, _ = load(args.replication)
    shared = sorted(i for i in rep_s if i in main_s and len(rep_s[i]) >= len(ORDER))

    # Does the set of best solvers on an instance survive the change of machine?
    agree, differs = 0, []
    for i in shared:
        mv = {s: v for s, v in main_s[i].items() if v}
        rv = {s: v for s, v in rep_s[i].items() if v}
        if not mv or not rv:
            continue
        mw = {s for s, v in mv.items() if v == max(mv.values())}
        rw = {s for s, v in rv.items() if v == max(rv.values())}
        if mw & rw:
            agree += 1
        else:
            differs.append((i, sorted(mw), sorted(rw)))

    def diffs(solver, family=None):
        out = []
        for i in shared:
            if family and fam.get(i) != family:
                continue
            a, b = main_s[i].get(solver), rep_s[i].get(solver)
            if a and b:
                out.append(100.0 * abs(b - a) / a)
        return out

    rows = []
    for s in ORDER:
        cells = []
        for f in FAMILIES:
            d = diffs(s, f)
            cells.append("%.3f" % statistics.mean(d) if d else "---")
        alld = diffs(s)
        ident = sum(1 for x in alld if x == 0)
        rows.append((LABEL[s], cells, ident, len(alld), max(alld) if alld else 0.0))

    tex = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Replication on a second platform. Each cell is the mean, over the "
        r"instances of that family, of $100\,|s_2-s_1|/s_1$ where $s_1$ is the size the "
        r"solver returned on the machine used for the main tables and $s_2$ the size it "
        r"returned on the replication machine. LOWER IS BETTER: zero means the solver "
        r"returned the same value on both machines. \emph{Same} counts the instances on "
        r"which it did so exactly, out of %d.}" % len(shared),
        r"\label{tab:replication}",
        r"\begin{tabular}{l " + "r " * len(FAMILIES) + r"r r}", r"\toprule",
        r"Solver & " + " & ".join(f.capitalize() for f in FAMILIES)
        + r" & Same & Max \\",
        r"\midrule",
    ]
    for label, cells, ident, n, mx in rows:
        tex.append("%s & %s & %d/%d & %.2f \\\\" % (label, " & ".join(cells), ident, n, mx))
    tex += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        f.write("\n".join(tex) + "\n")

    print("instances compared: %d" % len(shared))
    print("best-solver set overlaps on %d of %d" % (agree, len(shared)))
    for d in differs:
        print("  ranking differs on %s: %s vs %s" % d)
    print("wrote %s" % args.out)


if __name__ == "__main__":
    main()
