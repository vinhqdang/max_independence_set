#!/usr/bin/env python3
"""Builds the long-budget (600 s) table for the paper, and the 60 s comparison
that goes with it.

The point of the long-budget run is not to find better solutions -- it is to
establish whether the 60-second budget used for the main study is doing the
comparison a disservice. So the table carries the size and the wall-clock time
at 600 s, and the script also prints, for each cell, what the same solver
reached at 60 s, which is what the surrounding prose needs to be checked
against.
"""
import argparse
import collections
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOLVERS = ["cascade", "redumis", "numvc", "fastvc"]
LABEL = {"cascade": r"\textsc{Cascade}", "redumis": "ReduMIS",
         "numvc": "NuMVC", "fastvc": "FastVC"}
INSTANCES = ["del20", "roadNet-CA", "web-BerkStan", "frb59-26-1"]


def load(path):
    out = collections.defaultdict(dict)
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                size = int(r["size"])
            except (ValueError, TypeError):
                size = None
            out[r["instance"]][r["solver"]] = (size, float(r["seconds"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--long", default=os.path.join(ROOT, "results", "cor_long600.csv"))
    ap.add_argument("--short", default=os.path.join(ROOT, "results", "cor_main60.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "paper", "tables", "longbudget.tex"))
    args = ap.parse_args()

    lng = load(args.long)
    sht = load(args.short)

    present = [i for i in INSTANCES if i in lng]
    best = {}
    for i in present:
        vals = [v[0] for v in lng[i].values() if v[0] is not None]
        best[i] = max(vals) if vals else None

    tex = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Solution size and wall-clock seconds at a 600-second budget, ten "
        r"times the budget of the main study. HIGHER IS BETTER for size, lower for time; "
        r"\textbf{bold} marks the best size on an instance. The comparison of interest is "
        r"with Table~\ref{tab:quality-geometric} and its companions, measured at 60 "
        r"seconds: outside the dense instance, the extra budget changes almost nothing.}",
        r"\label{tab:longbudget}",
        r"\begin{tabular}{l " + " ".join(["r@{\\,/\\,}l"] * len(present)) + r"}",
        r"\toprule",
        r"Solver & " + " & ".join(r"\multicolumn{2}{c}{\texttt{%s}}" % i.replace("_", r"\_")
                                  for i in present) + r" \\",
        r"& " + " & ".join([r"size & s"] * len(present)) + r" \\",
        r"\midrule",
    ]
    for s in SOLVERS:
        cells = []
        for i in present:
            v = lng[i].get(s)
            if v is None or v[0] is None:
                cells.append(r"\multicolumn{2}{c}{---}" if v is None
                             else r"\multicolumn{2}{c}{t/o}")
                continue
            size, secs = v
            txt = r"\textbf{%d}" % size if size == best[i] else "%d" % size
            cells.append("%s & %.0f" % (txt, secs))
        tex.append("%s & %s \\\\" % (LABEL[s], " & ".join(cells)))
    tex += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        f.write("\n".join(tex) + "\n")
    print("wrote %s" % args.out)

    # What the prose has to be checked against: 60 s versus 600 s, per cell.
    print("\n%-14s %-10s %12s %12s %10s" % ("instance", "solver", "60s", "600s", "gain"))
    for i in present:
        for s in SOLVERS:
            a = sht.get(i, {}).get(s)
            b = lng.get(i, {}).get(s)
            if not a or not b:
                continue
            av, bv = a[0], b[0]
            if av is None or bv is None:
                print("%-14s %-10s %12s %12s %10s"
                      % (i, s, av if av is not None else "t/o",
                         bv if bv is not None else "t/o", "-"))
                continue
            print("%-14s %-10s %12d %12d %+10d" % (i, s, av, bv, bv - av))


if __name__ == "__main__":
    main()
