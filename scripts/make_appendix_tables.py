#!/usr/bin/env python3
"""Builds the two appendix longtables: instance provenance and full per-instance
results.

Both were originally produced by throwaway scripts, which left the paper with
two tables nobody could regenerate. They are built here from the catalogue and
the results file so that a change to either propagates.

Neither table can be wrapped in a resizebox, because a longtable spans pages, so
both are kept inside the text width by carrying only the columns they need: the
provenance table abbreviates the source and puts the file names in a footnote,
and the results table drops the vertex and edge counts, which the provenance
table already gives once per instance rather than once per solver.
"""
import argparse
import collections
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SNAP = ["web-Stanford", "web-BerkStan", "as-skitter", "ca-AstroPh", "ca-CondMat",
        "email-Enron", "roadNet-CA", "roadNet-PA", "wiki-Talk"]
SNAP_COMM = ["com-amazon", "com-dblp", "com-youtube"]
FAMILY_ORDER = ["geometric", "road", "web", "social", "collaboration",
                "communication", "bhoslib"]


def source(name):
    if name in SNAP or name in SNAP_COMM:
        return "SNAP"
    if name.startswith("frb"):
        return r"NetRep$^{\dagger}$"
    return r"generated$^{\ddagger}$"


def provenance(catalogue, out):
    cat = json.load(open(catalogue))
    rows = sorted(cat.items(),
                  key=lambda kv: (FAMILY_ORDER.index(kv[1]["family"])
                                  if kv[1]["family"] in FAMILY_ORDER else 99,
                                  kv[1]["n"]))
    head = r"Instance & Family & $n$ & $m$ & $\bar{d}$ & $\Delta$ & Source \\"
    tex = [
        r"\footnotesize",
        # Seven columns at the default column separation overrun the text width
        # by about the width of one column's padding; tightening it fits the
        # table without another step down in type size.
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{longtable}{l l r r r r l}",
        r"\caption{Provenance and basic statistics of the %d benchmark instances. "
        r"$\bar{d}$ is the average degree and $\Delta$ the maximum degree. Sources: "
        r"SNAP is \texttt{snap.stanford.edu/data}, where each instance is the file of "
        r"its own name; $^{\dagger}$ Network Repository \texttt{bhoslib}, used in "
        r"complement as Section~\ref{sec:experiments} explains; $^{\ddagger}$ produced "
        r"by \texttt{tools/gen\_instances.py} at seed 1.}\label{tab:provenance}\\" % len(rows),
        r"\toprule", head, r"\midrule", r"\endfirsthead",
        r"\multicolumn{7}{l}{\itshape Table~\ref{tab:provenance}, continued}\\",
        r"\toprule", head, r"\midrule", r"\endhead",
        r"\midrule \multicolumn{7}{r}{\itshape continued on next page}\\", r"\endfoot",
        r"\bottomrule", r"\endlastfoot",
    ]
    for name, d in rows:
        tex.append(r"\texttt{%s} & %s & %s & %s & %.1f & %s & %s \\" % (
            name.replace("_", r"\_"), d["family"], format(d["n"], ","),
            format(d["m"], ","), d["avg_deg"], format(d["max_deg"], ","),
            source(name)))
    tex += [r"\end{longtable}", r"\setlength{\tabcolsep}{6pt}", r"\normalsize"]
    open(out, "w").write("\n".join(tex) + "\n")
    return len(rows)


def per_instance(results, out):
    rows = []
    with open(results) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    rows.sort(key=lambda r: (r["instance"], r["solver"]))
    head = r"Instance & Solver & Size & Seconds \\"
    tex = [
        r"\footnotesize",
        r"\begin{longtable}{l l r r}",
        r"\caption{Complete per-instance results at the 60\,s budget. A dash means the "
        r"solver returned no solution within the cutoff. Vertex and edge counts are in "
        r"Table~\ref{tab:provenance}.}\label{tab:appendix}\\",
        r"\toprule", head, r"\midrule", r"\endfirsthead",
        r"\multicolumn{4}{l}{\itshape Table~\ref{tab:appendix}, continued}\\",
        r"\toprule", head, r"\midrule", r"\endhead",
        r"\midrule \multicolumn{4}{r}{\itshape continued on next page}\\", r"\endfoot",
        r"\bottomrule", r"\endlastfoot",
    ]
    for r in rows:
        size = r["size"] if r["size"] else "---"
        tex.append(r"\texttt{%s} & %s & %s & %.1f \\" % (
            r["instance"].replace("_", r"\_"), r["solver"].replace("_", r"\_"),
            size, float(r["seconds"])))
    tex += [r"\end{longtable}", r"\normalsize"]
    open(out, "w").write("\n".join(tex) + "\n")
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", default="/home/user/data/instances/catalogue.json")
    ap.add_argument("--results", default=os.path.join(ROOT, "results", "cor_main60.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "paper", "tables"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    n = provenance(args.catalogue, os.path.join(args.out, "provenance.tex"))
    m = per_instance(args.results, os.path.join(args.out, "appendix.tex"))
    print("provenance: %d instances" % n)
    print("appendix: %d rows" % m)


if __name__ == "__main__":
    main()
