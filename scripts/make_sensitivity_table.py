#!/usr/bin/env python3
"""Builds the parameter-sensitivity table.

Rows are (parameter, value), columns are instances, cells are the solution size.
The default value of each parameter is marked, and the spread across the range
is given so it can be read against the seed-to-seed spread reported elsewhere:
a parameter whose whole range moves the answer by less than seed noise is a
plateau, and one that moves it by more is a real sensitivity.
"""
import argparse
import collections
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PARAM_LABEL = {
    "kernel_share": r"\texttt{kernel\_share}",
    "lns_start_free": r"\texttt{lns\_start\_free}",
    "restart_idle_dives": r"\texttt{restart\_idle\_dives}",
    "lns_slice": r"\texttt{lns\_slice}",
}
ORDER = ["kernel_share", "lns_start_free", "lns_slice", "restart_idle_dives"]


def fmt(v):
    return ("%g" % v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(ROOT, "results", "sensitivity.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "paper", "tables", "sensitivity.tex"))
    args = ap.parse_args()

    size = collections.defaultdict(dict)       # (param, value) -> instance -> size
    default = {}
    instances = []
    with open(args.csv) as f:
        for r in csv.DictReader(f):
            v = float(r["value"])
            size[(r["parameter"], v)][r["instance"]] = int(r["size"])
            if r["is_default"] == "1":
                default[r["parameter"]] = v
            if r["instance"] not in instances:
                instances.append(r["instance"])
    instances.sort()

    tex = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Parameter sensitivity. Each block varies one parameter over its "
        r"range with the others held at their defaults; $\star$ marks the default. "
        r"Cells are the size returned at a 60-second budget, HIGHER IS BETTER. "
        r"The \emph{spread} line under each block is $100\,(\max-\min)/\max$ over that "
        r"block, per instance, to be read against the seed-to-seed spread of "
        r"Section~\ref{sec:experiments}: $0.024\%$ on the geometric family and up to "
        r"$2.5\%$ on BHOSLIB.}",
        r"\label{tab:sensitivity}",
        r"\begin{tabular}{l r " + "r " * len(instances) + r"}", r"\toprule",
        r"Parameter & Value & " + " & ".join(r"\texttt{%s}" % i.replace("_", r"\_")
                                             for i in instances)
        + r" \\",
        r"\midrule",
    ]
    for pi, p in enumerate(ORDER):
        vals = sorted(v for (pp, v) in size if pp == p)
        if not vals:
            continue
        # The spread is reported PER INSTANCE. A single figure taken across
        # instances would always be the BHOSLIB one, and quoting that against a
        # parameter that is flat on the two sparse instances reads as a
        # sensitivity the data does not show.
        spreads = []
        for inst in instances:
            col = [size[(p, v)].get(inst) for v in vals]
            col = [c for c in col if c is not None]
            spreads.append(100.0 * (max(col) - min(col)) / max(col) if col else 0.0)
        for k, v in enumerate(vals):
            cells = []
            for inst in instances:
                s = size[(p, v)].get(inst)
                cells.append("%d" % s if s is not None else "---")
            mark = r"$\star$" if default.get(p) == v else ""
            name = PARAM_LABEL.get(p, p) if k == 0 else ""
            tex.append("%s & %s%s & %s \\\\"
                       % (name, fmt(v), mark, " & ".join(cells)))
        tex.append(r"\cmidrule(lr){3-%d}" % (2 + len(instances)))
        tex.append(r"& \emph{spread \%%} & %s \\\\"
                   % " & ".join(r"\emph{%.3f}" % x for x in spreads))
        if pi < len(ORDER) - 1:
            tex.append(r"\midrule")
    tex += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        f.write("\n".join(tex) + "\n")
    print("wrote %s" % args.out)

    # The reading the prose has to be checked against.
    print("\n%-20s %-14s %8s %8s %8s" % ("parameter", "instance", "default", "best", "spread%"))
    for p in ORDER:
        vals = sorted(v for (pp, v) in size if pp == p)
        for inst in instances:
            col = {v: size[(p, v)].get(inst) for v in vals}
            col = {v: c for v, c in col.items() if c is not None}
            if not col:
                continue
            best_v = max(col, key=lambda v: col[v])
            sp = 100.0 * (max(col.values()) - min(col.values())) / max(col.values())
            print("%-20s %-14s %8s %8s %8.3f"
                  % (p, inst, col.get(default.get(p)), "%d@%g" % (col[best_v], best_v), sp))


if __name__ == "__main__":
    main()
