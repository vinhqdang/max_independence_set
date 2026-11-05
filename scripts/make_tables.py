#!/usr/bin/env python3
"""Generates the LaTeX result tables from the raw benchmark CSVs, so every
number in the paper is traceable to a recorded run."""
import argparse
import collections
import csv
import os

SOLVERS = [("cascade", r"\textsc{Cascade}"), ("redumis", "ReduMIS"),
           ("online_mis", "OnlineMIS"), ("nearlinear", "NearLinear"),
           ("lineartime", "LinearTime"), ("numvc", "NuMVC"), ("fastvc", "FastVC")]
FAMILY_TITLE = {"geometric": "Geometric (Delaunay and random geometric)",
                "road": "Road networks", "social": "Social networks",
                "web": "Web graphs", "bhoslib": "BHOSLIB \\texttt{frb}"}
FAMILY_ORDER = ["geometric", "road", "social", "web", "bhoslib"]


def load(path):
    best, meta = collections.defaultdict(dict), {}
    for r in csv.DictReader(open(path)):
        if not r["size"]:
            continue
        v = int(r["size"])
        best[r["solver"]][r["instance"]] = max(v, best[r["solver"]].get(r["instance"], 0))
        meta[r["instance"]] = (r["family"], int(r["n"]), int(r["m"]))
    return best, meta


def esc(name):
    return "\\texttt{%s}" % name.replace("_", r"\_")


def quality_tables(best, meta, out_dir):
    """One table per family; instances are rows and solvers are columns, so the
    width is fixed by the seven solvers rather than by the family size."""
    for fam in FAMILY_ORDER:
        insts = sorted([i for i in meta if meta[i][0] == fam], key=lambda i: meta[i][1])
        if not insts:
            continue
        lines = [r"\begin{table}[htbp]", r"\centering",
                 r"\caption{%s: size of the independent set found within the "
                 r"60\,s budget (larger is better). Best value per instance in bold.}"
                 % FAMILY_TITLE[fam],
                 r"\label{tab:quality-%s}" % fam,
                 r"\small",
                 r"\fittable{\begin{tabular}{l" + "r" * len(SOLVERS) + "}", r"\toprule",
                 "Instance & " + " & ".join(lab for _, lab in SOLVERS) + r" \\", r"\midrule"]
        for i in insts:
            top = max(best[k].get(i, 0) for k, _ in SOLVERS)
            cells = []
            for key, _ in SOLVERS:
                v = best[key].get(i)
                if v is None:
                    cells.append("--")
                else:
                    cells.append(r"\textbf{%d}" % v if v == top else str(v))
            lines.append(esc(i) + " & " + " & ".join(cells) + r" \\")
        lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]
        open(os.path.join(out_dir, "quality_%s.tex" % fam), "w").write("\n".join(lines) + "\n")


def quality_all(best, meta, out_dir):
    """Single compact table with every instance, for the page-limited main text."""
    insts = []
    for fam in FAMILY_ORDER:
        insts += sorted([i for i in meta if meta[i][0] == fam], key=lambda i: meta[i][1])
    lines = [r"\begin{table}[htbp]", r"\centering",
             r"\caption{Size of the independent set found within the 60\,s budget (larger is better), all 27 "
             r"instances. Best value per instance in bold; -- means no solution within the cutoff. "
             r"Family order: geometric, road, social, web, BHOSLIB.}",
             r"\label{tab:quality}", r"\footnotesize",
             r"\fittable{\begin{tabular}{llr" + "r" * len(SOLVERS) + "}", r"\toprule",
             "Instance & Family & $n$ & " + " & ".join(lab for _, lab in SOLVERS) + r" \\", r"\midrule"]
    last = None
    for i in insts:
        if last is not None and meta[i][0] != last:
            lines.append(r"\midrule")
        last = meta[i][0]
        top = max(best[k].get(i, 0) for k, _ in SOLVERS)
        cells = []
        for key, _ in SOLVERS:
            v = best[key].get(i)
            cells.append("--" if v is None else (r"\textbf{%d}" % v if v == top else str(v)))
        lines.append("%s & %s & %d & %s \\\\" % (esc(i), meta[i][0], meta[i][1], " & ".join(cells)))
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]
    open(os.path.join(out_dir, "quality_all.tex"), "w").write("\n".join(lines) + "\n")


def summary_table(best, meta, out_dir):
    insts = sorted(meta)
    lines = [r"\begin{table}[htbp]", r"\centering",
             r"\caption{Aggregate over all %d instances. The gap of an algorithm on an "
             r"instance is $(\text{best of the seven algorithms} - \text{its value}) / "
             r"\text{best of the seven algorithms listed}$.}" % len(insts),
             r"\label{tab:aggregate}", r"\fittable{\begin{tabular}{lrrrr}", r"\toprule",
             r"Algorithm & \#best & \#solved & mean gap & max gap \\", r"\midrule"]
    for key, label in SOLVERS:
        nb = ns = 0
        gaps = []
        for i in insts:
            top = max(best[k].get(i, 0) for k, _ in SOLVERS)
            v = best[key].get(i)
            if v is None:
                continue
            ns += 1
            nb += v == top
            gaps.append(100.0 * (top - v) / top)
        lines.append("%s & %d & %d & %.3f\\%% & %.3f\\%% \\\\"
                     % (label, nb, ns, sum(gaps) / len(gaps), max(gaps)))
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]
    open(os.path.join(out_dir, "aggregate.tex"), "w").write("\n".join(lines) + "\n")


def ablation_table(path, out_dir):
    if not os.path.exists(path):
        return
    best, meta = load(path)
    variants = [("cascade", "full"), ("cascade-nolns", "no region moves"),
                ("cascade-nopert", "no perturbation/restarts"),
                ("cascade-nolp", "no LP reduction"),
                ("cascade-dive", "decision-space moves")]
    insts = [i for i in ["del16", "del18", "rgg16", "roadNet-PA", "web-Stanford",
                         "frb40-19-1", "frb59-26-1"] if i in meta]
    lines = [r"\begin{table}[htbp]", r"\centering",
             r"\caption{Ablation: each row disables one component. Values in brackets "
             r"are the change from the full algorithm.}", r"\label{tab:ablation}",
             r"\small", r"\fittable{\begin{tabular}{l" + "r" * len(variants) + "}", r"\toprule",
             "Instance & " + " & ".join(l for _, l in variants) + r" \\", r"\midrule"]
    for i in insts:
        cells = []
        for key, label in variants:
            v, full = best[key].get(i), best["cascade"].get(i)
            if v is None:
                cells.append("--")
            elif key == "cascade":
                cells.append(str(v))
            else:
                cells.append("%d (%+d)" % (v, v - full))
        lines.append(esc(i) + " & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]
    open(os.path.join(out_dir, "ablation.tex"), "w").write("\n".join(lines) + "\n")


def budget_table(path, out_dir, budget=60.0):
    """How closely each solver respects the time budget.

    Wall-clock is measured around the whole process, so a solver that checks its
    cutoff only between search steps can overshoot substantially. Reporting this
    keeps the quality comparison honest.
    """
    per = collections.defaultdict(list)
    for r in csv.DictReader(open(path)):
        per[r["solver"]].append(float(r["seconds"]))
    lines = [r"\begin{table}[htbp]", r"\centering",
             r"\caption{Wall-clock time actually taken under a %g\,s budget, over all "
             r"instances. Time is measured around the whole process, so it includes "
             r"reading and any construction phase.}" % budget,
             r"\label{tab:budget}", r"\fittable{\begin{tabular}{lrrrr}", r"\toprule",
             r"Algorithm & median & mean & max & runs $>1.5\times$ budget \\", r"\midrule"]
    for key, label in SOLVERS:
        v = sorted(per.get(key, []))
        if not v:
            continue
        lines.append("%s & %.1f & %.1f & %.1f & %d \\\\"
                     % (label, v[len(v) // 2], sum(v) / len(v), v[-1],
                        sum(1 for x in v if x > 1.5 * budget)))
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}"]
    open(os.path.join(out_dir, "budget.tex"), "w").write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--main", default="cor_main60.csv")
    ap.add_argument("--out", default="paper/tables")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    main_csv = os.path.join(args.results, args.main)
    best, meta = load(main_csv)
    quality_tables(best, meta, args.out)
    quality_all(best, meta, args.out)
    summary_table(best, meta, args.out)
    budget_table(main_csv, args.out)
    ablation_table(os.path.join(args.results, "ablation.csv"), args.out)
    print("wrote %d tables to %s" % (len(os.listdir(args.out)), args.out))


if __name__ == "__main__":
    main()
